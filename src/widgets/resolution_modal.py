"""Modal dialog screen for selecting video playback resolution."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from src.config import RESOLUTIONS, get_resolution
from src.models import ResolutionOption


class ResolutionModal(ModalScreen[str | None]):
    """Modal screen for choosing resolution before playback."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("q", "cancel", "Cancel"),
        Binding("1", "select_num('1')", "Auto/Best", show=False),
        Binding("2", "select_num('2')", "4K", show=False),
        Binding("3", "select_num('3')", "2K", show=False),
        Binding("4", "select_num('4')", "1080p", show=False),
        Binding("5", "select_num('5')", "720p", show=False),
        Binding("6", "select_num('6')", "480p", show=False),
        Binding("7", "select_num('7')", "360p", show=False),
        Binding("8", "select_num('8')", "Audio", show=False),
    ]

    def __init__(
        self,
        current_res_id: str,
        video_title: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.current_res_id = current_res_id
        self.video_title = video_title

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-dialog"):
            yield Static("🎬  SELECT PLAYBACK RESOLUTION", id="modal-title")

            if self.video_title:
                truncated_title = (
                    self.video_title[:50] + "..." if len(self.video_title) > 50 else self.video_title
                )
                yield Static(
                    f"Target: [bold white]{truncated_title}[/]",
                    id="modal-video-label",
                )
            else:
                yield Static("Configure default streaming resolution:", id="modal-video-label")

            options: list[Option] = []
            initial_index = 0
            for idx, res in enumerate(RESOLUTIONS):
                is_active = res.id == self.current_res_id
                badge = "  [bold #38bdf8]● Active[/]" if is_active else ""
                label = f"[{res.key_shortcut}]  {res.name:<20} [dim]{res.description}[/]{badge}"
                options.append(Option(prompt=label, id=res.id))
                if is_active:
                    initial_index = idx

            opt_list = OptionList(*options, id="res-option-list")
            opt_list.highlighted = initial_index
            yield opt_list

            yield Static(
                "[dim]Press [bold white]1-8[/] to choose instantly • [bold white]↑/↓ + Enter[/] to select • [bold white]Esc[/] to cancel[/]",
                id="modal-hint",
            )

    def on_mount(self) -> None:
        self.query_one("#res-option-list", OptionList).focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        selected_id = event.option.id
        self.dismiss(selected_id)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_select_num(self, num_str: str) -> None:
        for res in RESOLUTIONS:
            if res.key_shortcut == num_str:
                self.dismiss(res.id)
                return
