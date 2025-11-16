"""
Simple Log Viewer Widget.

Displays recent log entries in a scrollable format.
"""

from textual.widgets import Static
from textual.containers import Vertical
from textual.reactive import reactive
from textual.app import ComposeResult
from pathlib import Path
import time


class SimpleLogViewer(Vertical):
    """
    Simple log viewer for TUI.

    Shows recent log entries from file.
    """

    DEFAULT_CSS = """
    SimpleLogViewer {
        background: $surface;
        border: solid $primary;
        padding: 1;
        height: 100%;
    }

    #log-content {
        height: 1fr;
        border: solid $panel;
        padding: 1;
    }
    """

    def __init__(self, **kwargs):
        """Initialize log viewer."""
        super().__init__(**kwargs)
        self.log_file = Path("data/logs/experiment.log")

    def compose(self) -> ComposeResult:
        """Compose widget."""
        with Vertical(classes="log-controls"):
            yield Static("📋 Experiment Logs", classes="section-title")
            yield Static(f"Showing last 50 lines from {self.log_file}", classes="log-info")
        yield Static("", id="log-content", classes="log-content")

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        self.refresh_logs()

    def refresh_logs(self) -> None:
        """Refresh log display."""
        try:
            if not self.log_file.exists():
                self.query_one("#log-content", Static).update("No log file found.")
                return

            # Read last 50 lines
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
                recent_lines = lines[-50:]

            # Format for display
            formatted_lines = []
            for line in recent_lines:
                line = line.strip()
                if line:
                    # Simple formatting - just show the line
                    formatted_lines.append(line)

            content = "\n".join(formatted_lines)
            self.query_one("#log-content", Static).update(content)

        except Exception as e:
            self.query_one("#log-content", Static).update(f"Error reading logs: {e}")


class LogScreen(Vertical):
    """
    Full-screen log viewer.
    """

    BINDINGS = [
        ("escape", "dismiss", "Back"),
        ("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        """Compose screen."""
        yield SimpleLogViewer()

    def action_refresh(self) -> None:
        """Refresh logs."""
        log_viewer = self.query_one(SimpleLogViewer)
        log_viewer.refresh_logs()