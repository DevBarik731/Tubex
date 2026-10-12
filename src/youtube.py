
"""YouTube search and metadata service using yt-dlp."""
from __future__ import annotations

import json
import re
import subprocess
from typing import Any

from src.config import DEFAULT_RESULTS, MAX_RESULTS
from src.models import VideoItem

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


def search_youtube(query: str, count: int = DEFAULT_RESULTS) -> list[VideoItem]:
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

    entries: list[dict[str, Any]] | None = info.get("entries")
    if entries is None and info.get("id"):
        entries = [info]
    elif not entries:
        return []

    results: list[VideoItem] = []
    for entry in entries:
        if not entry:
            continue

        if entry.get("ie_key") in ("YoutubeChannel", "YoutubeTab"):
            continue

        webpage_url = entry.get("webpage_url")
        raw_url = entry.get("url")
        video_id = str(entry.get("id") or "").strip()

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

        # Extract video ID from URL if empty
        if not video_id:
            id_match = re.search(r"v=([a-zA-Z0-9_-]{11})", video_url)
            if id_match:
                video_id = id_match.group(1)

        title = entry.get("title") or "Untitled video"
        uploader = entry.get("uploader") or entry.get("channel") or "Unknown channel"
        duration = format_duration(entry.get("duration"))

        view_count = entry.get("view_count")
        views_str: str | None = None
        if view_count is not None:
            try:
                v = int(view_count)
                if v >= 1_000_000:
                    views_str = f"{v / 1_000_000:.1f}M views"
                elif v >= 1_000:
                    views_str = f"{v / 1_000:.1f}K views"
                else:
                    views_str = f"{v} views"
            except (ValueError, TypeError):
                views_str = None

        results.append(
            VideoItem(
                id=video_id,
                title=title,
                url=video_url,
                uploader=uploader,
                duration=duration,
                views=views_str,
            )
        )

    return results
