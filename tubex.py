#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from typing import Any

from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Footer, Input, ListItem, ListView, Static

DEFAULT_RESULTS = 10
MAX_RESULTS = 25
_COUNT_REGEX = re.compile(r"\s*:\s*(\d+)\s*$")


def parse_search_query(raw_query: str, default_count: int = DEFAULT_RESULTS) -> tuple[str, int]:
    """Parse search query and optional count suffix (e.g. 'lo-fi beats : 10')."""
    text = (raw_query or "").strip()
    if not text:
        return "", default_count

    match = _COUNT_REGEX.search(text)
    if not match:
        return text, default_count

    query = text[: match.start()].strip()
    if not query:
        return "", default_count

    count = int(match.group(1))
    if count <= 0:
        return query, default_count

    return query, min(count, MAX_RESULTS)


def format_duration(seconds: int | float | str | None) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    if seconds is None:
        return "unknown"
    if isinstance(seconds, str) and ":" in seconds:
        return seconds

    try:
        total_seconds = int(float(seconds))
    except (ValueError, TypeError):
        return "unknown"

    if total_seconds < 0:
        return "unknown"

    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def run_yt_dlp(args: list[str]) -> str:
    """Execute yt-dlp with given arguments and return stdout."""
    try:
        result = subprocess.run(
            ["yt-dlp", *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as exc:
        error_msg = exc.stderr.strip() if exc.stderr else str(exc)
        raise RuntimeError(f"yt-dlp error: {error_msg}") from exc


def search_youtube(query: str, count: int = DEFAULT_RESULTS) -> list[dict[str, Any]]:
    """Query YouTube for videos using yt-dlp flat playlist dump."""
    if not query:
        return []

    search_term = f"ytsearch{count}:{query}"
    output = run_yt_dlp([
        "--flat-playlist",
        "--no-warnings",
        "--no-playlist",
        "--ignore-errors",
        "--dump-single-json",
        search_term,
    ])

    if not output:
        return []

    try:
        info = json.loads(output)
    except json.JSONDecodeError:
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    info = json.loads(line)
                    break
                except json.JSONDecodeError:
                    continue
        else:
            return []

    entries = info.get("entries")
    if entries is None and info.get("id"):
        entries = [info]
    elif not entries:
        return []

    results: list[dict[str, Any]] = []
    for entry in entries:
        if not entry:
            continue

        if entry.get("ie_key") in ("YoutubeChannel", "YoutubeTab"):
            continue

        webpage_url = entry.get("webpage_url")
        raw_url = entry.get("url")
        video_id = entry.get("id")

        if webpage_url:
            video_url = webpage_url
        elif raw_url and raw_url.startswith("http"):
            if "/channel/" in raw_url:
                continue
            video_url = raw_url
        elif video_id:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
        elif raw_url:
            video_url = f"https://www.youtube.com/watch?v={raw_url}"
        else:
            continue

        title = entry.get("title") or "Untitled video"
        uploader = entry.get("uploader") or entry.get("channel") or "Unknown channel"
        duration = format_duration(entry.get("duration"))

        results.append(
            {
                "title": title,
                "url": video_url,
                "uploader": uploader,
                "duration": duration,
            }
        )

    return results


def resolve_mpv_urls(video_url: str) -> list[str]:
    """Resolve direct streaming URLs using yt-dlp."""
    output = run_yt_dlp([
        "--no-warnings",
        "--no-playlist",
        "--get-url",
        video_url,
    ])
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    return lines if lines else [video_url]


def resolve_mpv_url(video_url: str) -> tuple[str, str | None]:
    """Resolve direct video and audio streaming URLs using yt-dlp.

    Returns (video_stream_url, audio_stream_url) ensuring audio is preserved.
    """
    urls = resolve_mpv_urls(video_url)
    if len(urls) >= 2:
        return urls[0], urls[1]
    return urls[0], None


class YouTubeSearchApp(App):
    TITLE = "TubeX"
    SUB_TITLE = "YouTube in your terminal"
    CSS = """
    Screen {
        background: #0f172a;
        color: #e2e8f0;
    }

    #brand {
        dock: top;
        height: 3;
        padding: 1 2;
        background: #1e293b;
        color: #f8fafc;
        border-bottom: solid #334155;
    }

    #search {
        width: 100%;
        height: 3;
        margin: 1 2 0 2;
        border: round #475569;
        background: #1e293b;
        color: #f8fafc;
    }

    #search:focus {
        border: round #f43f5e;
    }

    #status {
        height: 1;
        margin: 1 2;
        color: #94a3b8;
    }

    ListView {
        height: 1fr;
        margin: 0 2 1 2;
        border: round #334155;
        background: #1e293b;
        scrollbar-gutter: stable;
    }

    ListItem {
        padding: 1 2;
        border-bottom: solid #0f172a;
        background: #1e293b;
    }

    ListItem:hover {
        background: #334155;
    }

    ListView:focus > ListItem.--highlight {
        background: #2563eb;
        color: #ffffff;
    }

    Footer {
        background: #1e293b;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("f", "focus_search", "Search"),
        ("/", "focus_search", "Search"),
        ("c", "clear_search", "Clear"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.search_results: list[dict[str, Any]] = []
        self._search_cache: dict[tuple[str, int], list[dict[str, Any]]] = {}

    def compose(self) -> ComposeResult:
        yield Static("[bold red]▶[/] [bold white]TubeX[/] [dim]• Terminal YouTube Player[/]", id="brand")
        yield Input(placeholder="Search YouTube (e.g. lo-fi hip hop :10)...", id="search")
        yield Static("Type a search phrase above and press Enter. Add :n to change result count.", id="status")
        yield ListView(id="results")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#search", Input).focus()

    def action_focus_search(self) -> None:
        self.query_one("#search", Input).focus()

    def action_clear_search(self) -> None:
        inp = self.query_one("#search", Input)
        inp.value = ""
        inp.focus()

    def set_status(self, message: str) -> None:
        try:
            self.query_one("#status", Static).update(message)
        except Exception:
            pass

    def on_key(self, event) -> None:
        if event.key == "down" and self.query_one("#search", Input).has_focus:
            if self.search_results:
                self.query_one("#results", ListView).focus()
        elif event.key == "escape":
            if self.query_one("#results", ListView).has_focus:
                self.query_one("#search", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value
        final_query, count = parse_search_query(query)
        if not final_query:
            self.set_status("Type a search phrase before pressing Enter.")
            return

        cache_key = (final_query, count)
        if cache_key in self._search_cache:
            self._display_results(final_query, self._search_cache[cache_key])
            return

        self.set_status(f"Searching for: {final_query} ({count} results)...")
        if self.is_running:
            self.perform_search(final_query, count)
        else:
            self._search_sync(final_query, count)

    @work(exclusive=True, thread=True)
    def perform_search(self, final_query: str, count: int) -> None:
        try:
            results = search_youtube(final_query, count)
        except Exception as exc:
            self.call_from_thread(self._handle_search_error, str(exc))
            return

        self._search_cache[(final_query, count)] = results
        self.call_from_thread(self._display_results, final_query, results)

    def _search_sync(self, final_query: str, count: int) -> None:
        try:
            results = search_youtube(final_query, count)
        except Exception as exc:
            self._handle_search_error(str(exc))
            return

        self._search_cache[(final_query, count)] = results
        self._display_results(final_query, results)

    def _display_results(self, final_query: str, results: list[dict[str, Any]]) -> None:
        self.search_results = results
        list_view = self.query_one("#results", ListView)
        list_view.clear()

        if not results:
            self.set_status(f"No videos found for: {final_query}")
            return

        for index, entry in enumerate(results):
            label = (
                f"[bold #f43f5e]{index + 1:02d}.[/]  [bold #f8fafc]{entry['title']}[/]\n"
                f"      [dim #94a3b8]{entry['uploader']}[/]  [dim]•[/]  [#38bdf8]{entry['duration']}[/]"
            )
            list_view.append(ListItem(Static(label)))

        self.set_status(
            f"Found {len(results)} result(s) for '{final_query}'. Use ↑/↓ and press Enter to play a video."
        )
        list_view.focus()

    def _handle_search_error(self, error_message: str) -> None:
        self.set_status(f"Search failed: {error_message}")
        self.search_results = []
        try:
            self.query_one("#results", ListView).clear()
        except Exception:
            pass

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        index = getattr(event, "index", None)
        if index is None:
            index = getattr(self.query_one("#results", ListView), "index", None)

        if index is None or not (0 <= index < len(self.search_results)):
            return

        selected = self.search_results[index]
        video_url = selected["url"]
        self.set_status(f"Opening: {selected['title']}")
        self.play_video(video_url)

    def play_video(self, video_url: str | tuple[str, str | None] | list[str]) -> None:
        try:
            if isinstance(video_url, (tuple, list)):
                video_target = video_url[0]
                audio_target = video_url[1] if len(video_url) > 1 else None
            else:
                video_target = video_url
                audio_target = None

            cmd = [
                "mpv",
                "--ytdl=yes",
                "--ytdl-format=bestvideo+bestaudio/best",
                "--really-quiet",
                "--force-window=yes",
                "--title=TubeX: ${media-title}",
                video_target,
            ]
            if audio_target:
                cmd.append(f"--audio-file={audio_target}")

            subprocess.Popen(
                cmd,
                start_new_session=True,
            )
        except FileNotFoundError as exc:
            self.set_status(f"Player not found: {exc.filename}")
        except Exception as exc:
            self.set_status(f"Playback failed: {exc}")


if __name__ == "__main__":
    YouTubeSearchApp().run()


