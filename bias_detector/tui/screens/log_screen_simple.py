"""
Log Screen for viewing experiment logs.

Simple screen that shows recent log entries.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Button, Static
from textual.containers import Horizontal, Vertical

from ..widgets.simple_log_viewer import SimpleLogViewer


class LogScreen(Screen):
    """
    Log viewer screen.

    Features:
    - Shows recent experiment logs
    - Refresh capability
    - Clean interface
    """

    BINDINGS = [
        Binding("f1", "switch_screen('progress')", "Progress", show=True),
        Binding("f2", "switch_screen('metadata')", "Metadata", show=True),
        Binding("f3", "switch_screen('config')", "Config", show=True),
        Binding("f4", "switch_screen('history')", "History", show=True),
        Binding("f5", "switch_screen('logs')", "Logs", show=True),
        Binding("h", "show_help", "Help", show=True),
        Binding("r", "refresh_logs", "Refresh", show=True),
        # Removed 'q' binding to avoid conflict with app quit
    ]

    def compose(self) -> ComposeResult:
        """Compose screen."""
        with Vertical():
            # Header with navigation hint
            yield Static("📋 Experiment Logs - Press 'F1' to return to Progress", classes="screen-header")

            yield SimpleLogViewer(id="log-viewer")

            # Footer with navigation hints
            yield Static("Navigation: F1=Back to Progress  F2-F5=Other screens  R=Refresh logs  H=Help", classes="screen-footer")

    def action_refresh_logs(self) -> None:
        """Refresh log display."""
        try:
            log_viewer = self.query_one("#log-viewer", SimpleLogViewer)
            log_viewer.refresh_logs()
        except Exception:
            pass  # Ignore if log viewer not found

    def action_go_back(self) -> None:
        """Go back to the progress screen."""
        try:
            self.app.switch_screen("progress")
        except Exception as e:
            # If switch_screen fails, try to dismiss the screen
            self.dismiss()

    def on_button_pressed(self, event) -> None:
        """Handle button presses."""
        if event.button.id == "back-button":
            self.action_go_back()
        elif event.button.id == "refresh-button":
            self.action_refresh_logs()

    DEFAULT_CSS = """
    LogScreen {
        layout: vertical;
    }

    .screen-header {
        height: 3;
        background: $primary-darken-1;
        color: $text;
        text-align: center;
        text-style: bold;
        padding: 1;
        margin-bottom: 1;
    }

    .screen-footer {
        height: 3;
        background: $surface-darken-1;
        color: $text-muted;
        text-align: center;
        padding: 1;
        margin-top: 1;
        text-style: italic;
    }
    """