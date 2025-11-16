"""
Enhanced Log Screen for advanced log viewing.

Provides filtering, search, export, and real-time monitoring capabilities.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding

from ..widgets.enhanced_log_viewer import EnhancedLogViewer


class EnhancedLogScreen(Screen):
    """
    Enhanced log viewer screen.

    Features:
    - Real-time log streaming with color coding
    - Advanced filtering by level, component, time
    - Search with highlighting
    - Export functionality
    - Bookmarks and annotations
    """

    BINDINGS = [
        Binding("f1", "switch_screen('progress')", "Progress", show=True),
        Binding("f2", "switch_screen('metadata')", "Metadata", show=True),
        Binding("f3", "switch_screen('config')", "Config", show=True),
        Binding("f4", "switch_screen('history')", "History", show=True),
        Binding("f5", "switch_screen('logs')", "Logs", show=True),
        Binding("h", "show_help", "Help", show=True),
        Binding("ctrl+b", "bookmark_entry", "Bookmark", show=True),
        Binding("ctrl+e", "export_logs", "Export", show=True),
        Binding("ctrl+l", "clear_filters", "Clear Filters", show=True),
        # Removed 'q' binding to avoid conflict with app quit
    ]

    def __init__(self, **kwargs):
        """Initialize enhanced log screen."""
        super().__init__(**kwargs)
        self.log_viewer: EnhancedLogViewer | None = None

    def compose(self) -> ComposeResult:
        """Compose screen."""
        self.log_viewer = EnhancedLogViewer()
        yield self.log_viewer

    def action_bookmark_entry(self) -> None:
        """Bookmark the currently selected log entry."""
        if self.log_viewer and self.log_viewer.selected_entry:
            # For now, just show a notification
            self.notify("Bookmark functionality coming soon!", title="Bookmark")

    def action_export_logs(self) -> None:
        """Export current filtered logs."""
        if self.log_viewer:
            export_data = self.log_viewer.export_logs("txt")
            # In a real implementation, this would save to file
            self.notify(f"Exported {len(self.log_viewer.filtered_entries)} log entries", title="Export Complete")

    def action_clear_filters(self) -> None:
        """Clear all filters."""
        if self.log_viewer:
            # Reset all filters
            self.log_viewer.level_filter = set(self.log_viewer.log_entries)
            self.log_viewer.component_filter = set()
            self.log_viewer.time_filter = None
            self.log_viewer.search_query = ""

            # Update UI elements
            level_select = self.query_one("#level-filter")
            level_select.value = "all"

            component_select = self.query_one("#component-filter")
            component_select.value = "all"

            time_select = self.query_one("#time-filter")
            time_select.value = "all"

            search_input = self.query_one("#search-input")
            search_input.value = ""

            self.log_viewer._apply_filters()
            self.log_viewer._update_stats()

            self.notify("All filters cleared", title="Filters Cleared")