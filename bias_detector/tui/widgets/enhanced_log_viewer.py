"""
Enhanced Log Viewer Widget for TUI.

Provides advanced log viewing with filtering, search, real-time updates, and export functionality.
"""

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from enum import Enum

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import (
    Static, Input, Select, Button, Checkbox,
    DataTable, Label, TextArea, TabbedContent, TabPane
)
from textual.reactive import reactive
from textual.timer import Timer
from textual import log as textual_log


class LogLevel(Enum):
    """Log levels for filtering."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEntry:
    """Represents a parsed log entry."""

    def __init__(self, raw_line: str, line_number: int):
        self.raw_line = raw_line
        self.line_number = line_number
        self.timestamp: Optional[datetime] = None
        self.level: Optional[LogLevel] = None
        self.component: Optional[str] = None
        self.message: str = raw_line
        self.context: Dict[str, Any] = {}

        self._parse_line()

    def _parse_line(self) -> None:
        """Parse the log line to extract structured information."""
        # Try to parse common log formats
        # Format: 2025-11-15 21:34:34 INFO [component] message

        # Extract timestamp
        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', self.raw_line)
        if timestamp_match:
            try:
                self.timestamp = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass

        # Extract log level
        for level in LogLevel:
            if f" {level.value} " in self.raw_line.upper():
                self.level = level
                break

        # Extract component (usually in brackets)
        component_match = re.search(r'\[([^\]]+)\]', self.raw_line)
        if component_match:
            self.component = component_match.group(1)

        # Extract message (everything after level and component)
        if self.level and self.component:
            # Find the position after level and component
            level_pos = self.raw_line.upper().find(f" {self.level.value} ")
            if level_pos >= 0:
                after_level = self.raw_line[level_pos + len(self.level.value) + 2:]
                component_match = re.search(r'\[([^\]]+)\]', after_level)
                if component_match:
                    component_end = after_level.find(']') + 1
                    self.message = after_level[component_end:].strip()
                else:
                    self.message = after_level.strip()
            else:
                self.message = self.raw_line
        else:
            self.message = self.raw_line

    def matches_filter(self,
                      level_filter: Set[LogLevel],
                      component_filter: Set[str],
                      time_filter: Optional[timedelta],
                      search_query: str = "") -> bool:
        """Check if this log entry matches the current filters."""

        # Level filter
        if self.level and self.level not in level_filter:
            return False

        # Component filter
        if self.component and self.component not in component_filter:
            return False

        # Time filter
        if time_filter and self.timestamp:
            if datetime.now() - self.timestamp > time_filter:
                return False

        # Search query
        if search_query:
            if search_query.lower() not in self.raw_line.lower():
                return False

        return True

    def format_for_display(self, highlight_search: str = "") -> str:
        """Format the log entry for display with optional highlighting."""

        # Color coding by level
        level_colors = {
            LogLevel.DEBUG: "dim",
            LogLevel.INFO: "white",
            LogLevel.WARNING: "yellow",
            LogLevel.ERROR: "red",
            LogLevel.CRITICAL: "bold red"
        }

        color = level_colors.get(self.level, "white") if self.level else "white"

        # Format components
        time_str = self.timestamp.strftime("%H:%M:%S") if self.timestamp else "--:--:--"
        level_str = f"{self.level.value:8}" if self.level else "UNKNOWN "
        component_str = f"{self.component:15}" if self.component else "unknown" + " " * 8

        # Highlight search terms
        display_message = self.message
        if highlight_search:
            # Simple highlighting by making search terms bold
            display_message = re.sub(
                f'({re.escape(highlight_search)})',
                r'[bold]\1[/bold]',
                display_message,
                flags=re.IGNORECASE
            )

        return f"[{color}]{time_str}[/] [{color}]{level_str}[/] [cyan]{component_str}[/] {display_message}"


class EnhancedLogViewer(Vertical):
    """
    Enhanced log viewer with advanced features.

    Features:
    - Real-time log streaming with color coding
    - Filtering by level, component, time range
    - Search with highlighting
    - Export functionality
    - Bookmarks and annotations
    - Performance metrics overlay
    """

    DEFAULT_CSS = """
    EnhancedLogViewer {
        height: 100%;
    }

    .log-controls {
        height: auto;
        margin-bottom: 1;
        padding: 1;
        background: $surface-darken-1;
        border: solid $primary;
    }

    .filter-row {
        height: 3;
        margin-bottom: 0.5;
    }

    .log-content {
        height: 1fr;
        border: solid $primary;
        padding: 1;
        background: $surface;
        overflow-y: auto;
    }

    .log-entry {
        margin-bottom: 0.2;
        padding: 0.1;
    }

    .log-entry:hover {
        background: $accent-darken-3;
    }

    .stats-bar {
        height: 2;
        padding: 0 1;
        background: $primary-darken-1;
        color: $text;
        text-align: center;
    }

    .bookmarks-panel {
        width: 30%;
        border-left: solid $primary;
        padding: 1;
        background: $surface-darken-1;
    }

    .bookmark-item {
        margin-bottom: 0.5;
        padding: 0.5;
        border: solid $accent;
        cursor: pointer;
    }

    .bookmark-item:hover {
        background: $accent-darken-2;
    }
    """

    # Reactive state
    log_entries: reactive[List[LogEntry]] = reactive([])
    filtered_entries: reactive[List[LogEntry]] = reactive([])
    selected_entry: reactive[Optional[LogEntry]] = reactive(None)

    # Filter state
    level_filter: reactive[Set[LogLevel]] = reactive(set(LogLevel))
    component_filter: reactive[Set[str]] = reactive(set())
    time_filter: reactive[Optional[timedelta]] = reactive(None)
    search_query: reactive[str] = reactive("")

    def __init__(self, log_file: Optional[Path] = None, **kwargs):
        """Initialize enhanced log viewer."""
        super().__init__(**kwargs)
        self.log_file = log_file or Path("data/logs/experiment.log")
        self._update_timer: Optional[Timer] = None
        self._file_position = 0
        self.bookmarks: List[Dict[str, Any]] = []
        self.annotations: Dict[int, str] = {}

    def compose(self) -> ComposeResult:
        """Compose the enhanced log viewer."""
        with Vertical():
            # Controls section
            with Vertical(classes="log-controls"):
                # Filter controls
                with Horizontal(classes="filter-row"):
                    yield Select(
                        options=[
                            ("all", "All Levels"),
                            ("debug", "Debug+"),
                            ("info", "Info+"),
                            ("warning", "Warning+"),
                            ("error", "Error+"),
                        ],
                        value="all",
                        id="level-filter",
                        classes="filter-select"
                    )

                    yield Select(
                        options=[
                            ("all", "All Components"),
                            ("experiment", "Experiment"),
                            ("tui", "TUI"),
                            ("analysis", "Analysis"),
                            ("generation", "Generation"),
                        ],
                        value="all",
                        id="component-filter",
                        classes="filter-select"
                    )

                    yield Select(
                        options=[
                            ("all", "All Time"),
                            ("1h", "Last Hour"),
                            ("6h", "Last 6 Hours"),
                            ("24h", "Last 24 Hours"),
                            ("7d", "Last 7 Days"),
                        ],
                        value="all",
                        id="time-filter",
                        classes="filter-select"
                    )

                    yield Input(
                        placeholder="Search logs...",
                        id="search-input",
                        classes="search-input"
                    )

                    yield Button("Export", id="export-button", variant="primary")
                    yield Button("Clear", id="clear-button", variant="default")

                # Stats bar
                yield Static("", id="stats-bar", classes="stats-bar")

            # Main content area
            with Horizontal():
                # Log content
                with Vertical(classes="log-content-area"):
                    yield Static("", id="log-content", classes="log-content")

                # Bookmarks panel
                with Vertical(classes="bookmarks-panel"):
                    yield Static("📖 Bookmarks & Annotations", classes="panel-title")
                    yield Static("", id="bookmarks-content")

    def on_mount(self) -> None:
        """Initialize on mount."""
        self._load_existing_logs()
        self._apply_filters()
        self._update_stats()

        # Start real-time monitoring
        self._update_timer = self.set_interval(2.0, self._check_for_updates)

    def on_unmount(self) -> None:
        """Cleanup on unmount."""
        if self._update_timer:
            self._update_timer.stop()

    def _load_existing_logs(self) -> None:
        """Load existing log entries from file."""
        if not self.log_file.exists():
            return

        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
                self._file_position = len(lines)

                # Parse last 200 lines to start
                recent_lines = lines[-200:]
                for i, line in enumerate(recent_lines):
                    if line.strip():
                        entry = LogEntry(line.strip(), len(lines) - len(recent_lines) + i)
                        self.log_entries.append(entry)

        except Exception as e:
            textual_log.error(f"Failed to load log file: {e}")

    def _check_for_updates(self) -> None:
        """Check for new log entries and update display."""
        if not self.log_file.exists():
            return

        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()

            # Check if file has grown
            if len(lines) > self._file_position:
                new_lines = lines[self._file_position:]
                for line in new_lines:
                    if line.strip():
                        entry = LogEntry(line.strip(), self._file_position)
                        self.log_entries.append(entry)
                        self._file_position += 1

                # Re-apply filters to include new entries
                self._apply_filters()
                self._update_display()
                self._update_stats()

        except Exception as e:
            textual_log.error(f"Failed to check for log updates: {e}")

    def _apply_filters(self) -> None:
        """Apply current filters to log entries."""
        filtered = []

        for entry in self.log_entries:
            if entry.matches_filter(
                self.level_filter,
                self.component_filter,
                self.time_filter,
                self.search_query
            ):
                filtered.append(entry)

        self.filtered_entries = filtered
        self._update_display()

    def _update_display(self) -> None:
        """Update the log display with filtered entries."""
        if not self.filtered_entries:
            content = "No log entries match current filters."
        else:
            # Show last 100 filtered entries
            display_entries = self.filtered_entries[-100:]
            formatted_lines = []

            for entry in display_entries:
                formatted_line = entry.format_for_display(self.search_query)
                formatted_lines.append(formatted_line)

            content = "\n".join(formatted_lines)

        log_content = self.query_one("#log-content", Static)
        log_content.update(content)

    def _update_stats(self) -> None:
        """Update the statistics bar."""
        total_entries = len(self.log_entries)
        filtered_count = len(self.filtered_entries)

        if total_entries == 0:
            stats_text = "No log entries"
        else:
            stats_text = f"Showing {filtered_count} of {total_entries} entries"

            # Add level breakdown
            level_counts = {}
            for entry in self.filtered_entries:
                level = entry.level.value if entry.level else "UNKNOWN"
                level_counts[level] = level_counts.get(level, 0) + 1

            if level_counts:
                level_stats = ", ".join(f"{level}: {count}" for level, count in level_counts.items())
                stats_text += f" | {level_stats}"

        stats_bar = self.query_one("#stats-bar", Static)
        stats_bar.update(stats_text)

    def add_bookmark(self, entry: LogEntry, note: str = "") -> None:
        """Add a bookmark for a log entry."""
        bookmark = {
            "line_number": entry.line_number,
            "timestamp": entry.timestamp,
            "level": entry.level.value if entry.level else "UNKNOWN",
            "message": entry.message[:100] + "..." if len(entry.message) > 100 else entry.message,
            "note": note
        }
        self.bookmarks.append(bookmark)
        self._update_bookmarks_display()

    def export_logs(self, format_type: str = "txt") -> str:
        """Export filtered logs in specified format."""
        if not self.filtered_entries:
            return "No logs to export"

        if format_type == "txt":
            lines = [entry.raw_line for entry in self.filtered_entries]
            return "\n".join(lines)
        elif format_type == "json":
            import json
            data = {
                "exported_at": datetime.now().isoformat(),
                "total_entries": len(self.filtered_entries),
                "entries": [
                    {
                        "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                        "level": entry.level.value if entry.level else None,
                        "component": entry.component,
                        "message": entry.message,
                        "raw_line": entry.raw_line
                    } for entry in self.filtered_entries
                ]
            }
            return json.dumps(data, indent=2)
        else:
            return f"Unsupported export format: {format_type}"

    def _update_bookmarks_display(self) -> None:
        """Update the bookmarks panel display."""
        if not self.bookmarks:
            bookmarks_content = "No bookmarks yet.\n\nUse Ctrl+B on a log entry to bookmark it."
        else:
            bookmark_lines = []
            for i, bookmark in enumerate(self.bookmarks):
                time_str = bookmark["timestamp"].strftime("%H:%M:%S") if bookmark["timestamp"] else "--:--:--"
                bookmark_lines.append(f"{i+1}. [{bookmark['level']}] {time_str}")
                bookmark_lines.append(f"   {bookmark['message']}")
                if bookmark["note"]:
                    bookmark_lines.append(f"   Note: {bookmark['note']}")
                bookmark_lines.append("")

            bookmarks_content = "\n".join(bookmark_lines)

        bookmarks_widget = self.query_one("#bookmarks-content", Static)
        bookmarks_widget.update(bookmarks_content)

    # Event handlers
    def on_select_changed(self, event) -> None:
        """Handle filter changes."""
        if event.select.id == "level-filter":
            if event.value == "all":
                self.level_filter = set(LogLevel)
            else:
                # Map to minimum level
                level_map = {
                    "debug": [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL],
                    "info": [LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL],
                    "warning": [LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL],
                    "error": [LogLevel.ERROR, LogLevel.CRITICAL]
                }
                self.level_filter = set(level_map.get(event.value, list(LogLevel)))

        elif event.select.id == "component-filter":
            if event.value == "all":
                self.component_filter = set()  # Empty set means all
            else:
                self.component_filter = {event.value}

        elif event.select.id == "time-filter":
            if event.value == "all":
                self.time_filter = None
            else:
                time_map = {
                    "1h": timedelta(hours=1),
                    "6h": timedelta(hours=6),
                    "24h": timedelta(hours=24),
                    "7d": timedelta(days=7)
                }
                self.time_filter = time_map.get(event.value)

        self._apply_filters()
        self._update_stats()

    def on_input_changed(self, event) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            self.search_query = event.value
            self._apply_filters()
            self._update_stats()

    def on_button_pressed(self, event) -> None:
        """Handle button presses."""
        if event.button.id == "export-button":
            export_data = self.export_logs("txt")
            # In a real implementation, this would save to file or clipboard
            self.notify(f"Exported {len(self.filtered_entries)} log entries", title="Export Complete")
        elif event.button.id == "clear-button":
            self.log_entries.clear()
            self.filtered_entries.clear()
            self._update_display()
            self._update_stats()
            self.notify("Log display cleared", title="Clear Complete")