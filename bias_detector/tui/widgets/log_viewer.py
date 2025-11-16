"""
Log Viewer Widget for TUI.

Displays real-time log messages in a scrollable widget.
"""

from typing import List, Optional, Dict, Any
import time
from pathlib import Path

from textual.widgets import Static
from textual.containers import Vertical
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.css.query import NoMatches
from textual.scroll_view import ScrollView


class LogEntry:
    """Represents a single log entry."""
    
    def __init__(self, timestamp: str, level: str, component: str, message: str, context: Optional[Dict[str, Any]] = None):
        self.timestamp = timestamp
        self.level = level
        self.component = component
        self.message = message
        self.context = context or {}
        
    def format_for_display(self) -> str:
        """Format log entry for display."""
        # Color coding by level
        level_colors = {
            'DEBUG': 'dim',
            'INFO': 'white',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold red'
        }
        color = level_colors.get(self.level, 'white')
        
        # Format timestamp
        try:
            ts = time.strptime(self.timestamp[:19], '%Y-%m-%dT%H:%M:%S')
            time_str = time.strftime('%H:%M:%S', ts)
        except:
            time_str = self.timestamp[:8]
            
        # Format context indicators
        context_str = ''
        if self.context.get('performance_type') == 'timing':
            operation = self.context.get('operation', 'unknown')
            duration = self.context.get('duration_ms', 0)
            context_str = f" [{operation} {duration:.0f}ms]"
        elif self.context.get('interaction_type') == 'user_action':
            action = self.context.get('action', 'unknown')
            context_str = f" [ACTION: {action}]"
        elif self.context.get('experiment_event'):
            event_type = self.context.get('event_type', 'unknown')
            session_id = self.context.get('session_id', 'unknown')[:8]
            context_str = f" [EXP: {event_type} {session_id}]"
            
        return f"[{color}]#{time_str}[/] [{color}]{self.level:8}[/] [cyan]{self.component:15}[/] {self.message}{context_str}"


class LogViewer(ScrollView):
    """
    Scrollable log viewer widget.
    
    Features:
    - Real-time log updates
    - Color-coded log levels
    - Auto-scroll to latest
    - Configurable max lines
    """
    
    DEFAULT_CSS = """
    LogViewer {
        background: $surface;
        border: solid $primary;
        padding: 1;
        height: 100%;
    }
    """
    
    max_lines: reactive[int] = reactive(1000)
    auto_scroll: reactive[bool] = reactive(True)
    
    def __init__(self, max_lines: int = 1000, **kwargs):
        """Initialize log viewer."""
        super().__init__(**kwargs)
        self.max_lines = max_lines
        self.log_entries: List[LogEntry] = []
        self._log_file_path: Optional[Path] = None
        
    def compose(self) -> ComposeResult:
        """Compose widget."""
        yield Static("", id="log-content")
        
    def on_mount(self) -> None:
        """Called when widget is mounted."""
        self._load_existing_logs()
        self._update_display()
        
    def add_log_entry(self, entry: LogEntry) -> None:
        """Add a new log entry."""
        self.log_entries.append(entry)
        
        # Trim if too many entries
        if len(self.log_entries) > self.max_lines:
            self.log_entries = self.log_entries[-self.max_lines:]
            
        self._update_display()
        
        if self.auto_scroll:
            self.scroll_end(animate=False)
            
    def add_log(self, timestamp: str, level: str, component: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Add a log message."""
        entry = LogEntry(timestamp, level, component, message, context)
        self.add_log_entry(entry)
        
    def clear_logs(self) -> None:
        """Clear all log entries."""
        self.log_entries.clear()
        self._update_display()
        
    def _update_display(self) -> None:
        """Update the display with current log entries."""
        try:
            content_widget = self.query_one("#log-content", Static)
        except NoMatches:
            return
            
        if not self.log_entries:
            content_widget.update("No log entries yet...")
            return
            
        # Format all entries
        formatted_lines = [entry.format_for_display() for entry in self.log_entries]
        content = "\n".join(formatted_lines)
        content_widget.update(content)
        
    def _load_existing_logs(self) -> None:
        """Load existing log entries from file."""
        if not self._log_file_path or not self._log_file_path.exists():
            return
            
        try:
            with open(self._log_file_path, 'r') as f:
                lines = f.readlines()
                
            # Parse last N lines
            recent_lines = lines[-200:]  # Load last 200 lines
            for line in recent_lines:
                try:
                    import json
                    log_data = json.loads(line.strip())
                    self.add_log(
                        timestamp=log_data.get('timestamp', ''),
                        level=log_data.get('level', 'INFO'),
                        component=log_data.get('component', 'unknown'),
                        message=log_data.get('message', ''),
                        context=log_data.get('context', {})
                    )
                except:
                    # Skip malformed lines
                    continue
        except Exception as e:
            # If loading fails, start fresh
            pass
            
    def set_log_file(self, log_file_path: Path) -> None:
        """Set the log file to monitor."""
        self._log_file_path = log_file_path


class LogScreen(Vertical):
    """
    Full-screen log viewer.
    
    Can be accessed via F5 or from menu.
    """
    
    DEFAULT_CSS = """
    LogScreen {
        layout: vertical;
    }
    
    LogViewer {
        height: 1fr;
    }
    
    .log-controls {
        height: 3;
        dock: top;
        padding: 1;
        background: $panel;
    }
    """
    
    def __init__(self, **kwargs):
        """Initialize log screen."""
        super().__init__(**kwargs)
        self.log_viewer = LogViewer(max_lines=2000)
        
    def compose(self) -> ComposeResult:
        """Compose screen."""
        with Vertical(classes="log-controls"):
            yield Static("📋 Real-Time Log Viewer", classes="section-title")
            yield Static("Press 'c' to clear, 'a' to toggle auto-scroll, 'q' to return")
        yield self.log_viewer
        
    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Set log file to monitor
        log_file = Path("data/logs/tui.log")
        self.log_viewer.set_log_file(log_file)