"""Player integration for TubeX using mpv."""
from __future__ import annotations

import subprocess

from src.config import DEFAULT_RESOLUTION_ID, get_resolution
from src.models import VideoItem
from src.youtube import get_playback_format


def play_video(
    video: VideoItem,
    resolution_id: str = DEFAULT_RESOLUTION_ID,
    format_override: str | None = None,
) -> subprocess.Popen:
    """Launch mpv to stream the given video with the specified resolution.

    Resolves optimal video + audio streams (VID_ID+AUDIO_ID) to avoid HTTP 403 errors.
    Returns the spawned subprocess.Popen instance.
    """
    res_option = get_resolution(resolution_id)
    format_str = format_override or get_playback_format(video.url, resolution_id)

    cmd = [
        "mpv",
        "--ytdl=yes",
        f"--ytdl-format={format_str}",
        "--really-quiet",
        f"--title=TubeX: ${{media-title}} [{res_option.name}]",
    ]

    if res_option.is_audio_only:
        cmd.extend(["--video=no", "--no-video"])
    else:
        cmd.append("--force-window=yes")

    cmd.append(video.url)

    try:
        proc = subprocess.Popen(
            cmd,
            start_new_session=True,
        )
        proc.format_used = format_str  # type: ignore[attr-defined]
        return proc
    except FileNotFoundError as exc:
        raise RuntimeError("mpv media player was not found. Please install mpv to play videos.") from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to launch mpv: {exc}") from exc
