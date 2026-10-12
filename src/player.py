"""Player integration for TubeX using mpv."""
from __future__ import annotations

import subprocess

from src.config import DEFAULT_RESOLUTION_ID, get_resolution
from src.models import VideoItem


def play_video(video: VideoItem, resolution_id: str = DEFAULT_RESOLUTION_ID) -> subprocess.Popen:
    """Launch mpv to stream the given video with the specified resolution.

    Returns the spawned subprocess.Popen instance.
    """
    res_option = get_resolution(resolution_id)

    cmd = [
        "mpv",
        "--ytdl=yes",
        f"--ytdl-format={res_option.format_str}",
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
        return proc
    except FileNotFoundError as exc:
        raise RuntimeError("mpv media player was not found. Please install mpv to play videos.") from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to launch mpv: {exc}") from exc
