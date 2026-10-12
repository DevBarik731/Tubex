"""Sidebar preview panel showing video details."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from src.models import ResolutionOption, VideoItem


class PreviewPanel(Vertical):
    """Sidebar widget displaying selected video information."""

    def compose(self) -> ComposeResult:
        yield Static("[bold #f43f5e]▶[/] [bold #f8fafc]VIDEO DETAILS[/]", id="preview-title-bar")
        yield Static(
            "[dim #94a3b8]Select a video from results with ↑/↓ to inspect.[/]",
            id="preview-details",
        )
        yield Static(
            "[dim]Double-click or [bold white]Enter[/] to play • [bold white]r[/] for quality[/]",
            id="preview-actions",
        )

    def update_video(
        self,
        video: VideoItem | None,
        current_res: ResolutionOption,
    ) -> None:
        """Update preview panel with video metadata."""
        if not video:
            try:
                self.query_one("#preview-details", Static).update(
                    "[dim #94a3b8]No video selected.[/]"
                )
            except Exception:
                pass
            return

        details_text = (
            f"[bold #f8fafc]{video.title}[/]\n\n"
            f"[bold #38bdf8]Channel:[/]  [#e2e8f0]{video.uploader}[/]\n"
            f"[bold #38bdf8]Length:[/]   [#e2e8f0]{video.duration}[/]\n"
        )
        if video.views:
            details_text += f"[bold #38bdf8]Views:[/]    [#94a3b8]{video.views}[/]\n"
        details_text += f"[dim #64748b]Video ID:[/] [dim #94a3b8]{video.id}[/]"

        try:
            self.query_one("#preview-details", Static).update(details_text)
        except Exception:
            pass

        action_text = (
            f"[bold #f43f5e]Quality:[/] [bold #38bdf8]{current_res.name}[/]\n"
            f"[dim]Double-Click or [bold white]Enter[/] to play  •  [bold white]r[/] for quality[/]"
        )
        try:
            self.query_one("#preview-actions", Static).update(action_text)
        except Exception:
            pass
