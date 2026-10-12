"""Main Textual application for TubeX."""
from __future__ import annotations

import time

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Footer, Input, ListView, Static

from src.config import APP_CSS, DEFAULT_RESOLUTION_ID, get_resolution
from src.models import VideoItem
from src.player import play_video
from src.widgets.preview_panel import PreviewPanel
from src.widgets.resolution_modal import ResolutionModal
from src.widgets.video_card import VideoCard
from src.youtube import parse_search_query, search_youtube


class TubeXApp(App):
    """TubeX TUI Application."""

    TITLE = "TubeX"
    SUB_TITLE = "YouTube in your terminal"
    CSS = APP_CSS

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("f", "focus_search", "Search"),
        Binding("/", "focus_search", "Search"),
        Binding("c", "clear_search", "Clear"),
        Binding("r", "change_resolution", "Quality"),
        Binding("t", "toggle_preview", "Toggle Preview"),
        Binding("1", "quick_res('best')", "Best", show=False),
        Binding("2", "quick_res('2160p')", "4K", show=False),
        Binding("3", "quick_res('1440p')", "2K", show=False),
        Binding("4", "quick_res('1080p')", "1080p", show=False),
        Binding("5", "quick_res('720p')", "720p", show=False),
        Binding("6", "quick_res('480p')", "480p", show=False),
        Binding("7", "quick_res('360p')", "360p", show=False),
        Binding("8", "quick_res('audio')", "Audio", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.search_results: list[VideoItem] = []
        self._search_cache: dict[tuple[str, int], list[VideoItem]] = {}
        self.current_resolution_id: str = DEFAULT_RESOLUTION_ID
        self._cards_by_id: dict[str, VideoCard] = {}
        self._highlighted_index: int = 0
        self._preview_visible: bool = True
        self._last_click_time: float = 0.0
        self._last_clicked_video_id: str | None = None

    def compose(self) -> ComposeResult:
        res = get_resolution(self.current_resolution_id)
        with Horizontal(id="brand-bar"):
            yield Static(
                "[bold red]▶[/] [bold white]TubeX[/] [dim]• Terminal YouTube Player[/]",
                id="brand-title",
            )
            yield Static(
                f"[bold #38bdf8]Quality: {res.name}[/] [dim](press 'r')[/]",
                id="brand-quality",
            )

        with Static(id="search-bar"):
            yield Input(
                placeholder="Search YouTube (e.g. lo-fi hip hop :10)...",
                id="search",
            )
            yield Static(
                "Type query & Enter. Append :n for count. 1-click preview, 2-click or Enter to play. 'r' for quality.",
                id="status",
            )

        with Horizontal(id="main-content"):
            yield ListView(id="results")
            yield PreviewPanel(id="preview-panel")

        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#search", Input).focus()

    def action_focus_search(self) -> None:
        self.query_one("#search", Input).focus()

    def action_clear_search(self) -> None:
        inp = self.query_one("#search", Input)
        inp.value = ""
        inp.focus()

    def action_toggle_preview(self) -> None:
        """Toggle preview panel visibility."""
        panel = self.query_one("#preview-panel", PreviewPanel)
        self._preview_visible = not self._preview_visible
        panel.styles.display = "block" if self._preview_visible else "none"
        state = "visible" if self._preview_visible else "hidden"
        self.set_status(f"Preview panel {state}.")

    def on_resize(self, event) -> None:
        """Dynamically adapt layout for narrow terminals."""
        try:
            panel = self.query_one("#preview-panel", PreviewPanel)
            if event.size.width < 90:
                panel.styles.display = "none"
            elif self._preview_visible:
                panel.styles.display = "block"
        except Exception:
            pass

    def action_quick_res(self, res_id: str) -> None:
        """Quick resolution switch via number keys (when not typing in search)."""
        inp = self.query_one("#search", Input)
        if inp.has_focus:
            return
        self.set_resolution(res_id)

    def action_change_resolution(self) -> None:
        """Open resolution selection modal."""
        curr_video = (
            self.search_results[self._highlighted_index]
            if 0 <= self._highlighted_index < len(self.search_results)
            else None
        )
        title = curr_video.title if curr_video else None

        def on_modal_close(selected_id: str | None) -> None:
            if selected_id:
                self.set_resolution(selected_id)
                self.set_status(f"Resolution updated to: {get_resolution(selected_id).name}")

        self.push_screen(
            ResolutionModal(self.current_resolution_id, video_title=title),
            on_modal_close,
        )

    def set_resolution(self, res_id: str) -> None:
        """Set active playback resolution and update UI badges."""
        self.current_resolution_id = res_id
        res = get_resolution(res_id)
        try:
            self.query_one("#brand-quality", Static).update(
                f"[bold #38bdf8]Quality: {res.name}[/] [dim](press 'r')[/]"
            )
        except Exception:
            pass

        if self.search_results and 0 <= self._highlighted_index < len(self.search_results):
            self._update_preview(self._highlighted_index)

    def set_status(self, message: str) -> None:
        try:
            self.query_one("#status", Static).update(message)
        except Exception:
            pass

    def on_key(self, event) -> None:
        if event.key == "down" and self.query_one("#search", Input).has_focus:
            if self.search_results:
                list_view = self.query_one("#results", ListView)
                list_view.focus()
                if list_view.index is None:
                    list_view.index = 0
                    self._highlighted_index = 0
                    self._update_preview(0)
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

    def _display_results(self, final_query: str, results: list[VideoItem]) -> None:
        self.search_results = results
        self._cards_by_id.clear()
        self._highlighted_index = 0

        list_view = self.query_one("#results", ListView)
        list_view.clear()

        if not results:
            self.set_status(f"No videos found for: '{final_query}'")
            panel = self.query_one("#preview-panel", PreviewPanel)
            panel.update_video(None, get_resolution(self.current_resolution_id))
            return

        for index, video in enumerate(results):
            card = VideoCard(video=video, index=index)
            self._cards_by_id[video.id] = card
            list_view.append(card)

        res = get_resolution(self.current_resolution_id)
        self.set_status(
            f"Found {len(results)} videos for '{final_query}'. "
            f"Click to preview, Double-click or Enter to play [{res.name}]."
        )

        list_view.index = 0
        self._update_preview(0)
        list_view.focus()

    def _update_preview(self, index: int) -> None:
        """Update preview panel for the video at index."""
        if not self.search_results or not (0 <= index < len(self.search_results)):
            return

        video = self.search_results[index]
        panel = self.query_one("#preview-panel", PreviewPanel)
        panel.update_video(video, get_resolution(self.current_resolution_id))

    def _handle_search_error(self, error_message: str) -> None:
        self.set_status(f"Search failed: {error_message}")
        self.search_results = []
        try:
            self.query_one("#results", ListView).clear()
        except Exception:
            pass

    def on_video_card_clicked(self, message: VideoCard.Clicked) -> None:
        """Handle 1-click to preview video, 2-click (double-click) to open and play."""
        card = message.card
        list_view = self.query_one("#results", ListView)
        list_view.index = card.index
        list_view.focus()
        self._highlighted_index = card.index
        self._update_preview(card.index)

        now = time.monotonic()
        is_double_click = False

        if getattr(message.click_event, "chain", 1) >= 2:
            is_double_click = True
        elif (
            self._last_clicked_video_id == card.video.id
            and (now - self._last_click_time) <= 0.5
        ):
            is_double_click = True

        if is_double_click:
            self._last_click_time = 0.0
            self._last_clicked_video_id = None
            self.play_video_item(card.video)
        else:
            self._last_click_time = now
            self._last_clicked_video_id = card.video.id
            res = get_resolution(self.current_resolution_id)
            self.set_status(f"Selected: {card.video.title} (Double-click or Enter to play [{res.name}])")

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Track highlighted video item when navigating using keyboard and refresh preview."""
        index = getattr(self.query_one("#results", ListView), "index", None)
        if index is not None and 0 <= index < len(self.search_results):
            self._highlighted_index = index
            self._update_preview(index)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Play selected video on Enter."""
        index = getattr(event, "index", None)
        if index is None:
            index = getattr(self.query_one("#results", ListView), "index", None)

        if index is None or not (0 <= index < len(self.search_results)):
            return

        selected_video = self.search_results[index]
        self.play_video_item(selected_video)

    def play_video_item(self, video: VideoItem) -> None:
        """Stream video via mpv with current resolution."""
        res = get_resolution(self.current_resolution_id)
        self.set_status(f"Opening in mpv [{res.name}]: {video.title}")
        try:
            play_video(video, self.current_resolution_id)
        except RuntimeError as exc:
            self.set_status(str(exc))
        except Exception as exc:
            self.set_status(f"Playback error: {exc}")
