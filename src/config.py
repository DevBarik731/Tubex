"""Configuration constants and themes for TubeX."""
from __future__ import annotations

from pathlib import Path
from src.models import ResolutionOption

# Search configuration
DEFAULT_RESULTS = 10
MAX_RESULTS = 25

# Available resolutions
RESOLUTIONS: list[ResolutionOption] = [
    ResolutionOption(
        id="best",
        name="Auto / Best Quality",
        description="Source quality (up to 4K/8K available)",
        format_str="bestvideo+bestaudio/best",
        is_audio_only=False,
        key_shortcut="1",
    ),
    ResolutionOption(
        id="2160p",
        name="2160p (4K UHD)",
        description="Ultra HD 4K streaming",
        format_str="bestvideo[height<=?2160]+bestaudio/best[height<=?2160]",
        is_audio_only=False,
        key_shortcut="2",
    ),
    ResolutionOption(
        id="1440p",
        name="1440p (2K QHD)",
        description="Quad HD 1440p streaming",
        format_str="bestvideo[height<=?1440]+bestaudio/best[height<=?1440]",
        is_audio_only=False,
        key_shortcut="3",
    ),
    ResolutionOption(
        id="1080p",
        name="1080p (Full HD)",
        description="Recommended default high definition",
        format_str="bestvideo[height<=?1080]+bestaudio/best[height<=?1080]",
        is_audio_only=False,
        key_shortcut="4",
    ),
    ResolutionOption(
        id="720p",
        name="720p (HD)",
        description="Fast loading high definition",
        format_str="bestvideo[height<=?720]+bestaudio/best[height<=?720]",
        is_audio_only=False,
        key_shortcut="5",
    ),
    ResolutionOption(
        id="480p",
        name="480p (SD)",
        description="Standard definition",
        format_str="bestvideo[height<=?480]+bestaudio/best[height<=?480]",
        is_audio_only=False,
        key_shortcut="6",
    ),
    ResolutionOption(
        id="360p",
        name="360p (Data Saver)",
        description="Low bandwidth definition",
        format_str="bestvideo[height<=?360]+bestaudio/best[height<=?360]",
        is_audio_only=False,
        key_shortcut="7",
    ),
    ResolutionOption(
        id="audio",
        name="Audio Only (Music)",
        description="Streams audio stream only (saves data & CPU)",
        format_str="bestaudio/best",
        is_audio_only=True,
        key_shortcut="8",
    ),
]

RESOLUTION_MAP: dict[str, ResolutionOption] = {res.id: res for res in RESOLUTIONS}
DEFAULT_RESOLUTION_ID = "1080p"


def get_resolution(res_id: str) -> ResolutionOption:
    """Get resolution option by ID, defaulting to 1080p."""
    return RESOLUTION_MAP.get(res_id, RESOLUTION_MAP[DEFAULT_RESOLUTION_ID])


# CSS styling for TubeX
APP_CSS = """
Screen {
    background: #0f172a;
    color: #e2e8f0;
}

#brand-bar {
    dock: top;
    height: 3;
    padding: 0 2;
    background: #1e293b;
    color: #f8fafc;
    border-bottom: solid #334155;
    layout: horizontal;
    align: left middle;
}

#brand-title {
    width: 1fr;
    text-style: bold;
}

#brand-quality {
    width: auto;
    color: #38bdf8;
    text-style: bold;
    padding: 0 1;
    background: #0f172a;
    border: round #334155;
}

#brand-quality:hover {
    background: #1e293b;
    border: round #f43f5e;
}

#search-bar {
    dock: top;
    height: auto;
    padding: 0 1;
    background: #0f172a;
}

#search {
    width: 100%;
    height: 3;
    margin: 1 1 0 1;
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

#main-content {
    height: 1fr;
    margin: 0 1 1 1;
    layout: horizontal;
}

#results {
    width: 1fr;
    height: 100%;
    margin-right: 1;
    border: round #334155;
    background: #1e293b;
    scrollbar-gutter: stable;
}

#results:focus {
    border: round #3b82f6;
}

ListItem {
    height: auto;
    padding: 1 2;
    border-bottom: solid #0f172a;
    background: #1e293b;
    border-left: thick transparent;
}

ListItem:hover {
    background: #253347;
}

/* Keyboard navigation & active selection highlight */
ListItem.-highlight,
ListItem.--highlight,
ListView:focus > ListItem.-highlight,
ListView:focus > ListItem.--highlight {
    background: #1e3a8a;
    border-left: thick #f43f5e;
    color: #ffffff;
}

ListItem.-highlight .item-title,
ListItem.--highlight .item-title {
    color: #ffffff;
}

ListItem.-highlight .item-meta,
ListItem.--highlight .item-meta {
    color: #93c5fd;
}

.item-info {
    width: 100%;
    height: auto;
}

.item-title {
    text-style: bold;
    color: #f8fafc;
}

.item-meta {
    color: #94a3b8;
}

#preview-panel {
    width: 38;
    height: 100%;
    border: round #334155;
    background: #1e293b;
    padding: 1 2;
    display: block;
}

#preview-title-bar {
    height: 1;
    text-align: center;
    color: #f43f5e;
    text-style: bold;
    margin-bottom: 1;
}

#preview-details {
    height: auto;
    color: #cbd5e1;
}

#preview-actions {
    margin-top: 1;
    padding-top: 1;
    border-top: solid #334155;
    color: #94a3b8;
}

Footer {
    background: #1e293b;
}

/* Modal styles */
ResolutionModal {
    align: center middle;
    background: rgba(15, 23, 42, 0.85);
}

#modal-dialog {
    width: 58;
    height: auto;
    max-height: 28;
    border: round #f43f5e;
    background: #1e293b;
    padding: 1 2;
}

#modal-title {
    text-align: center;
    text-style: bold;
    color: #f43f5e;
    margin-bottom: 1;
}

#modal-video-label {
    color: #94a3b8;
    margin-bottom: 1;
}

#res-option-list {
    height: auto;
    max-height: 14;
    border: solid #334155;
    background: #0f172a;
    margin-bottom: 1;
}

#modal-hint {
    color: #64748b;
    text-align: center;
}
"""
