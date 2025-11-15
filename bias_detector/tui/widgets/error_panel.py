"""
Error Display Panel for TUI Application.

Provides a modal overlay for displaying and managing errors.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical, Horizontal, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Button, Static, DataTable
from textual.reactive import reactive


class ErrorPanel(ModalScreen[None]):
    """
    Modal error panel for displaying exception information.
    
    Features:
    - Error list with timestamps
    - Error details and stack traces
    - Clear/dismiss functionality
    - Auto-dismiss on timeout option
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close", show=True),
        Binding("c", "clear_errors", "Clear All", show=True),
    ]

    CSS = """
    ErrorPanel {
        align: center middle;
    }

    .error-container {
        width: 90%;
        height: 80%;
        background: $surface;
        border: thick $error;
        border-radius: 1;
        padding: 1;
    }

    .error-title {
        text-align: center;
        text-style: bold;
        color: $error;
        margin: 1 0;
    }

    .error-table {
        height: 20;
        border: solid $error;
        margin: 1 0;
    }

    .error-details {
        height: 10;
        border: solid $warning;
        margin: 1 0;
        padding: 1;
        background: $panel;
    }

    .button-row {
        height: 3;
        margin-top: 1;
        align: center middle;
    }

    .error-count {
        text-style: bold;
        color: $warning;
        margin: 0 1;
    }

    .error-text {
        color: $error;
        text-style: bold;
    }

    .warning-text {
        color: $warning;
        text-style: bold;
    }

    .info-text {
        color: $accent;
        text-style: bold;
    }
    """

    errors: reactive[List[Dict[str, Any]]] = reactive([])

    def __init__(self, errors: Optional[List[Dict[str, Any]]] = None, **kwargs):
        """Initialize error panel with optional initial errors."""
        super().__init__(**kwargs)
        self.errors = errors or []

    def compose(self) -> ComposeResult:
        """Compose the error panel layout."""
        with Center():
            with Vertical(classes="error-container"):
                # Title
                yield Static("🚨 Error Panel", classes="error-title")
                
                # Error count
                yield Static(f"Total Errors: {len(self.errors)}", classes="error-count")
                
                # Error list table
                yield DataTable(classes="error-table")
                
                # Error details
                with ScrollableContainer(classes="error-details"):
                    yield Static("Select an error to view details", id="error-details-text")
                
                # Button row
                with Horizontal(classes="button-row"):
                    yield Button("Clear All", variant="error", id="clear-btn")
                    yield Button("Close", variant="primary", id="close-btn")

    def on_mount(self) -> None:
        """Initialize data table when screen is mounted."""
        self._populate_error_table()

    def _populate_error_table(self) -> None:
        """Populate the error table with current errors."""
        table = self.query_one(DataTable)
        table.clear(columns=True)
        table.add_columns("Time", "Level", "Message", "Source")
        
        for error in self.errors:
            timestamp = error.get('timestamp', datetime.now()).strftime("%H:%M:%S")
            level = error.get('level', 'ERROR')
            message_text = error.get('message', 'Unknown error') or ''
            message = (message_text[:47] + "...") if len(message_text) > 50 else message_text
            source_text = error.get('source', 'Unknown') or ''
            source = (source_text[:17] + "...") if len(source_text) > 20 else source_text
            
            # Style based on error level
            row_key = table.add_row(timestamp, level, message, source)
            
            # Note: Textual styling would be applied via CSS classes
            # This is a placeholder for styling logic

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle error row selection to show details."""
        if event.row_key is None:
            return
            
        try:
            # Get the row key as string and convert to index
            row_key_str = str(event.row_key)
            if row_key_str.isdigit():
                error_index = int(row_key_str)
            else:
                # Fallback: try to get index from table data
                table = self.query_one(DataTable)
                error_index = list(table.rows).index(event.row_key)
            
            if 0 <= error_index < len(self.errors):
                error = self.errors[error_index]
                self._show_error_details(error)
        except (IndexError, AttributeError, ValueError, TypeError):
            pass

    def _show_error_details(self, error: Dict[str, Any]) -> None:
        """Display detailed error information."""
        details_text = self.query_one("#error-details-text", Static)
        
        timestamp = error.get('timestamp', datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
        level = error.get('level', 'ERROR')
        message = error.get('message', 'Unknown error')
        source = error.get('source', 'Unknown')
        traceback = error.get('traceback', 'No traceback available')
        
        details = f"""
Time: {timestamp}
Level: {level}
Source: {source}

Message:
{message}

Traceback:
{traceback}
        """.strip()
        
        details_text.update(details)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "clear-btn":
            self.action_clear_errors()
        elif event.button.id == "close-btn":
            self.dismiss()

    def action_clear_errors(self) -> None:
        """Clear all errors and dismiss."""
        self.errors.clear()
        self._populate_error_table()
        self.query_one("#error-details-text", Static).update("All errors cleared")

    async def action_dismiss(self, result: str | None = None) -> None:
        """Dismiss error panel."""
        self.dismiss()

    @classmethod
    def show_error(cls, message: str, source: str = "Unknown", level: str = "ERROR", traceback: Optional[str] = None) -> None:
        """
        Convenience method to show a single error.
        
        Args:
            message: Error message
            source: Error source/location
            level: Error level (ERROR, WARNING, INFO)
            traceback: Optional traceback information
        """
        error = {
            'timestamp': datetime.now(),
            'level': level,
            'message': message,
            'source': source,
            'traceback': traceback or "No traceback available"
        }
        
        panel = cls(errors=[error])
        # Note: This would need to be called from the app instance
        # app.push_screen(panel)

    def add_error(self, message: str, source: str = "Unknown", level: str = "ERROR", traceback: Optional[str] = None) -> None:
        """
        Add a new error to the panel.
        
        Args:
            message: Error message
            source: Error source/location
            level: Error level (ERROR, WARNING, INFO)
            traceback: Optional traceback information
        """
        error = {
            'timestamp': datetime.now(),
            'level': level,
            'message': message,
            'source': source,
            'traceback': traceback or "No traceback available"
        }
        
        self.errors.append(error)
        self._populate_error_table()