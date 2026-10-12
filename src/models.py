"""Data models for TubeX."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VideoItem:
    """Represents a YouTube video item found via search."""

    id: str
    title: str
    url: str
    uploader: str
    duration: str
    views: str | None = None


@dataclass
class ResolutionOption:
    """Represents a playback resolution option."""

    id: str
    name: str
    description: str
    format_str: str
    is_audio_only: bool = False
    key_shortcut: str = ""
