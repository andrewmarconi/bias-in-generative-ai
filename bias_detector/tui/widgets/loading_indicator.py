"""
Loading Indicator Widget for TUI.

Provides visual feedback during long operations.
"""

from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.screen import ModalScreen
from textual.widgets import Static, ProgressBar
from textual.timer import Timer
from typing import Optional


class LoadingSpinner(Static):
    """
    Animated loading spinner widget.

    Shows rotating characters to indicate activity.
    """

    DEFAULT_CSS = """
    LoadingSpinner {
        content-align: center middle;
        color: $accent;
        text-style: bold;
    }
    """

    def __init__(self, message: str = "Loading...", **kwargs):
        """Initialize loading spinner."""
        super().__init__(**kwargs)
        self.message = message
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.frame_index = 0
        self._timer: Optional[Timer] = None
        self.update(f"{self.frames[0]} {self.message}")

    def on_mount(self) -> None:
        """Start animation when mounted."""
        self._timer = self.set_interval(0.1, self.animate_spinner)

    def on_unmount(self) -> None:
        """Stop animation when unmounted."""
        if self._timer:
            self._timer.stop()
            self._timer = None

    def animate_spinner(self) -> None:
        """Animate the spinner."""
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        spinner = self.frames[self.frame_index]
        self.update(f"{spinner} {self.message}")

    def update_message(self, message: str) -> None:
        """Update the loading message."""
        self.renderable = message


class LoadingIndicator(Static):
    """
    General loading indicator with optional progress bar.

    Can show indeterminate spinner or determinate progress.
    """

    DEFAULT_CSS = """
    LoadingIndicator {
        layout: vertical;
        height: auto;
        border: solid $primary;
        padding: 1;
        background: $surface;
    }

    LoadingIndicator .message {
        text-align: center;
        margin-bottom: 1;
        color: $text;
    }

    LoadingIndicator .progress-bar {
        width: 100%;
        margin: 0 2;
    }
    """

    def __init__(
        self,
        message: str = "Loading...",
        show_progress: bool = False,
        total: Optional[int] = None,
        **kwargs
    ):
        """Initialize loading indicator."""
        super().__init__(**kwargs)
        self.message = message
        self.show_progress = show_progress
        self.total = total
        self.current = 0

    def compose(self) -> ComposeResult:
        """Compose the loading indicator."""
        yield Static(self.message, classes="message")

        if self.show_progress:
            yield ProgressBar(
                total=self.total or 100,
                show_eta=False,
                classes="progress-bar"
            )

    def update_progress(self, current: int, total: Optional[int] = None, message: Optional[str] = None) -> None:
        """Update progress if showing progress bar."""
        if message:
            self.message = message
            message_widget = self.query_one(".message", Static)
            message_widget.update(message)

        if self.show_progress and total is not None:
            self.total = total
            self.current = current
            progress_bar = self.query_one(ProgressBar)
            progress_bar.total = total
            progress_bar.update(progress=current)

    def update_message(self, message: str) -> None:
        """Update the loading message."""
        self.message = message
        message_widget = self.query_one(".message", Static)
        message_widget.update(message)


class LoadingOverlay(ModalScreen[None]):
    """
    Full-screen loading overlay for long operations.

    Blocks user interaction while showing loading status.
    """

    DEFAULT_CSS = """
    LoadingOverlay {
        background: rgba(0, 0, 0, 0.7);
    }

    LoadingOverlay .overlay-content {
        width: 60%;
        height: 30%;
        background: $surface;
        border: thick $primary;
        border-radius: 1;
        padding: 2;
    }

    LoadingOverlay .spinner {
        margin-bottom: 2;
    }

    LoadingOverlay .message {
        text-align: center;
        color: $text;
        text-style: bold;
    }

    LoadingOverlay .sub-message {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    """

    def __init__(
        self,
        title: str = "Loading",
        message: str = "Please wait...",
        sub_message: str = "",
        **kwargs
    ):
        """Initialize loading overlay."""
        super().__init__(**kwargs)
        self.title = title
        self.message = message
        self.sub_message = sub_message

    def compose(self) -> ComposeResult:
        """Compose the loading overlay."""
        with Center():
            with Vertical(classes="overlay-content"):
                yield Static(self.title or "Loading", classes="title")
                yield LoadingSpinner(self.message, classes="spinner")
                if self.sub_message:
                    yield Static(self.sub_message, classes="sub-message")

    def update_message(self, message: str, sub_message: str = "") -> None:
        """Update the loading messages."""
        spinner = self.query_one(LoadingSpinner)
        spinner.update_message(message)

        if sub_message:
            self.sub_message = sub_message
            sub_widget = self.query_one(".sub-message", Static)
            if sub_widget:
                sub_widget.update(sub_message)


class LoadingManager:
    """
    Manager for loading indicators and overlays.

    Provides convenient methods for showing/hiding loading states.
    """

    def __init__(self):
        """Initialize loading manager."""
        self._active_loadings = {}  # id -> loading widget

    def show_inline_loading(
        self,
        container,
        message: str = "Loading...",
        show_progress: bool = False,
        total: Optional[int] = None
    ) -> str:
        """Show inline loading indicator in a container."""
        loading_id = f"loading_{id(container)}_{len(self._active_loadings)}"

        loading = LoadingIndicator(
            message=message,
            show_progress=show_progress,
            total=total,
            id=loading_id
        )

        container.mount(loading)
        self._active_loadings[loading_id] = loading

        return loading_id

    def update_inline_loading(
        self,
        loading_id: str,
        current: Optional[int] = None,
        total: Optional[int] = None,
        message: Optional[str] = None
    ) -> None:
        """Update inline loading progress."""
        if loading_id in self._active_loadings:
            loading = self._active_loadings[loading_id]
            loading.update_progress(current or 0, total, message)

    def hide_inline_loading(self, loading_id: str) -> None:
        """Hide inline loading indicator."""
        if loading_id in self._active_loadings:
            loading = self._active_loadings[loading_id]
            loading.remove()
            del self._active_loadings[loading_id]

    def show_overlay_loading(
        self,
        app,
        title: str = "Loading",
        message: str = "Please wait...",
        sub_message: str = ""
    ) -> str:
        """Show full-screen loading overlay."""
        overlay_id = f"overlay_{len(self._active_loadings)}"

        overlay = LoadingOverlay(
            title=title,
            message=message,
            sub_message=sub_message,
            id=overlay_id
        )

        app.push_screen(overlay)
        self._active_loadings[overlay_id] = overlay

        return overlay_id

    def update_overlay_loading(
        self,
        overlay_id: str,
        message: Optional[str] = None,
        sub_message: Optional[str] = None
    ) -> None:
        """Update overlay loading messages."""
        if overlay_id in self._active_loadings:
            overlay = self._active_loadings[overlay_id]
            if message or sub_message:
                overlay.update_message(
                    message or overlay.message,
                    sub_message or overlay.sub_message
                )

    def hide_overlay_loading(self, overlay_id: str) -> None:
        """Hide loading overlay."""
        if overlay_id in self._active_loadings:
            overlay = self._active_loadings[overlay_id]
            overlay.dismiss()
            del self._active_loadings[overlay_id]


# Global loading manager instance
loading_manager = LoadingManager()