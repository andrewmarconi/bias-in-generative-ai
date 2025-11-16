"""
Log Screen for viewing real-time logs.

Full-screen log viewer accessible via F5.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding

from ..widgets.log_viewer import LogViewer


class LogScreen(Screen):
    """
    Full-screen log viewer.
    
    Features:
    - Real-time log updates
    - Scrollable history
    - Color-coded log levels
    """
    
    BINDINGS = [
        Binding("f1", "switch_screen('progress')", "Progress", show=True),
        Binding("f2", "switch_screen('metadata')", "Metadata", show=True),
        Binding("f3", "switch_screen('config')", "Config", show=True),
        Binding("f4", "switch_screen('history')", "History", show=True),
        Binding("f5", "switch_screen('logs')", "Logs", show=True),
        Binding("h", "show_help", "Help", show=True),
        Binding("c", "clear_logs", "Clear", show=True),
        Binding("a", "toggle_autoscroll", "Auto-Scroll", show=True),
        Binding("q", "switch_screen('progress')", "Back", show=True),
    ]

    def __init__(self, **kwargs):
        """Initialize log screen."""
        super().__init__(**kwargs)
        self.log_viewer = LogViewer(max_lines=2000)

    def compose(self) -> ComposeResult:
        """Compose screen."""
        yield self.log_viewer

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Set log file to monitor
        from pathlib import Path
        log_file = Path("data/logs/tui.log")
        self.log_viewer.set_log_file(log_file)
        
    def action_clear_logs(self) -> None:
        """Clear all log entries."""
        self.log_viewer.clear_logs()

    def action_toggle_autoscroll(self) -> None:
        """Toggle auto-scroll."""
        self.log_viewer.auto_scroll = not self.log_viewer.auto_scroll
        status = "enabled" if self.log_viewer.auto_scroll else "disabled"
        self.notify(f"Auto-scroll {status}")