
"""YouTube search and metadata service using yt-dlp."""
from __future__ import annotations

import json
import re
import subprocess
from typing import Any

from src.config import DEFAULT_RESOLUTION_ID, DEFAULT_RESULTS, MAX_RESULTS
from src.models import VideoItem

_COUNT_REGEX = re.compile(r"\s*:\s*(\d+)\s*$")
_RES_REGEX = re.compile(r"(\d+)x(\d+)")
_BITRATE_REGEX = re.compile(r"(\d+)k\s+(m3u8|https)")
_FORMAT_CACHE: dict[tuple[str, str], tuple[str | None, str | None]] = {}


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


def extract_stream_formats(
    url_or_id: str,
    resolution_id: str = DEFAULT_RESOLUTION_ID,
) -> tuple[str | None, str | None]:
    """Extract optimal video and audio stream IDs using yt-dlp -F format listings.

    Logic:
    - Video streams: filter lines with '$NF == "only" && $(NF-1) == "video"' (m3u8 streams)
      to avoid YouTube HTTP 403 Forbidden errors and skip Premium streams.
      Matches target resolution (default 1080p).
    - Audio streams: filter lines with 'audio only' (m3u8 high quality e.g. 234/233),
      prioritizing original language if present, or default language.

    Returns:
        tuple[str | None, str | None]: (video_stream_id, audio_stream_id)
    """
    cache_key = (url_or_id, resolution_id)
    if cache_key in _FORMAT_CACHE:
        return _FORMAT_CACHE[cache_key]

    target_height_map = {
        "2160p": 2160,
        "1440p": 1440,
        "1080p": 1080,
        "720p": 720,
        "480p": 480,
        "360p": 360,
        "best": 99999,
        "audio": 0,
    }
    target_height = target_height_map.get(resolution_id, 1080)

    try:
        output = run_yt_dlp(["-F", "--no-warnings", url_or_id])
    except Exception:
        return None, None

    lines = output.splitlines()
    video_candidates: list[tuple[float, str, int]] = []
    audio_candidates: list[tuple[float, str]] = []

    for line in lines:
        line_clean = line.strip()
        if not line_clean or line_clean.startswith("[") or line_clean.startswith("ID") or line_clean.startswith("---"):
            continue

        parts = line_clean.split()
        if len(parts) < 3:
            continue

        f_id = parts[0]

        # Video stream detection:
        # Awk rule: $NF == "only" && $(NF-1) == "video"
        is_m3u8_video = len(parts) >= 2 and parts[-1] == "only" and parts[-2] == "video"
        is_video_only = "video only" in line_clean

        if is_video_only:
            m = _RES_REGEX.search(line_clean)
            height = int(m.group(2)) if m else 0

            b_match = _BITRATE_REGEX.search(line_clean)
            bitrate = int(b_match.group(1)) if b_match else 0
            is_premium = "Premium" in line_clean

            score = 0.0
            # Prefer m3u8 formats as they do not get blocked by HTTP 403 Forbidden
            if is_m3u8_video:
                score += 2000.0
            if not is_premium:
                score += 1000.0

            if target_height == 99999:  # best
                score += height * 2.0
            elif height == target_height:
                score += 5000.0
            elif height < target_height:
                score += 2000.0 + height
            else:
                score += 1000.0 - (height - target_height)

            score += (bitrate / 100.0)
            video_candidates.append((score, f_id, height))

        # Audio stream detection:
        if "audio only" in line_clean:
            is_m3u8 = "m3u8" in line_clean or f_id.startswith("233") or f_id.startswith("234")
            line_lower = line_clean.lower()
            is_original = "original" in line_lower
            is_default = "default" in line_lower
            is_high = "high" in line_lower or f_id.startswith("234") or "medium" in line_lower

            score = 0.0
            if is_m3u8:
                score += 2000.0  # Prefer m3u8 audio to avoid 403 errors
            if is_original:
                score += 800.0   # Original language track
            elif is_default:
                score += 500.0   # Default language track
            if is_high:
                score += 300.0   # High quality track
            if "drc" in f_id:
                score -= 100.0   # Avoid dynamic range compression if normal available

            audio_candidates.append((score, f_id))

    video_candidates.sort(key=lambda x: x[0], reverse=True)
    audio_candidates.sort(key=lambda x: x[0], reverse=True)

    selected_video = video_candidates[0][1] if video_candidates else None
    selected_audio = audio_candidates[0][1] if audio_candidates else None

    result = (selected_video, selected_audio)
    _FORMAT_CACHE[cache_key] = result
    return result


def get_playback_format(
    url_or_id: str,
    resolution_id: str = DEFAULT_RESOLUTION_ID,
) -> str:
    """Determine the optimal --ytdl-format string for mpv.

    Returns:
        Format string in format "VID_ID+AUDIO_ID" (or "AUDIO_ID" for audio-only).
        Falls back to config default if extraction fails.
    """
    from src.config import get_resolution
    res_option = get_resolution(resolution_id)

    vid_id, audio_id = extract_stream_formats(url_or_id, resolution_id)

    if res_option.is_audio_only:
        return audio_id or res_option.format_str

    if vid_id and audio_id:
        return f"{vid_id}+{audio_id}"
    elif vid_id:
        return vid_id
    elif audio_id:
        return audio_id

    return res_option.format_str


if __name__ == "__main__":
    import sys
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://youtu.be/AQGFT_C1Ly4?si=N_0XQ7euCOdkC-uo"
    print(f"Inspecting stream formats for: {test_url}")
    vid, aid = extract_stream_formats(test_url, "1080p")
    fmt = get_playback_format(test_url, "1080p")
    print(f"Video Stream ID : {vid}")
    print(f"Audio Stream ID : {aid}")
    print(f"Combined Format : {fmt}")
    print(f"Suggested mpv command:")
    print(f'  mpv --ytdl-format="{fmt}" "{test_url}"')
