"""Video item card widget for search results."""
from __future__ import annotations

from textual import events
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import ListItem, Static

from src.models import VideoItem


class VideoCard(ListItem):
    """ListItem representing a YouTube search result."""

    class Clicked(Message):
        """Emitted when a video card is clicked by mouse."""

        def __init__(self, card: VideoCard, click_event: events.Click) -> None:
            super().__init__()
            self.card = card
            self.click_event = click_event

    def __init__(self, video: VideoItem, index: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self.video = video
        self.index = index

    def _handle_mouse_click(self, event: events.Click) -> None:
        if getattr(event, "_tubex_handled", False):
            return
        setattr(event, "_tubex_handled", True)
        event.stop()
        self.post_message(self.Clicked(self, event))

    def _on_click(self, event: events.Click) -> None:
        self._handle_mouse_click(event)

    def on_click(self, event: events.Click) -> None:
        self._handle_mouse_click(event)

    def compose(self) -> ComposeResult:
        with Vertical(classes="item-info"):
            title_text = f"[bold #f43f5e]{self.index + 1:02d}.[/]  [bold #f8fafc]{self.video.title}[/]"
            yield Static(title_text, classes="item-title")

            meta_parts = [
                f"[#94a3b8]{self.video.uploader}[/]",
                f"[bold #38bdf8]{self.video.duration}[/]",
            ]
            if self.video.views:
                meta_parts.append(f"[dim #64748b]{self.video.views}[/]")

            meta_text = f"      {'  [dim]•[/]  '.join(meta_parts)}"
            yield Static(meta_text, classes="item-meta")
