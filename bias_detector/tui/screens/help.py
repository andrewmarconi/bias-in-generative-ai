"""
Help overlay screen for TUI application.

Provides keyboard shortcuts, navigation help, and feature overview.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Static, DataTable
from textual.reactive import reactive
from textual.geometry import Size


class HelpScreen(ModalScreen[str]):
    """
    Modal help screen displaying keyboard shortcuts and navigation.
    
    Features:
    - Keyboard shortcuts table
    - Feature overview
    - Navigation instructions
    - Dismissible with Escape or button
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close Help", show=True),
    ]

    CSS = """
    HelpScreen {
        align: center middle;
    }

    .help-container {
        width: 80%;
        height: 80%;
        background: $surface;
        border: thick $primary;
        border-radius: 1;
        padding: 1;
    }

    .help-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin: 1 0;
    }

    .help-section {
        margin: 1 0;
    }

    .help-section-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .shortcuts-table {
        height: 20;
        border: solid $primary;
        margin: 1 0;
    }

    .feature-grid {
        height: 15;
        margin: 1 0;
    }

    .close-button {
        margin: 1 0;
        align: center;
    }

    .help-text {
        margin: 0 1;
        color: $text;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the help screen layout."""
        with Center():
            with Vertical(classes="help-container"):
                # Title
                yield Static("🎯 Bias Detection Framework - Help", classes="help-title")
                
                # Navigation shortcuts
                yield Static("📱 Navigation", classes="help-section-title")
                yield Static("Use F1-F5 keys to switch between screens, Q to quit", classes="help-text")
                
                # Keyboard shortcuts table
                yield Static("⌨️  Keyboard Shortcuts", classes="help-section-title")
                yield DataTable(classes="shortcuts-table")
                
                # Feature overview
                yield Static("🚀 Features", classes="help-section-title")
                yield DataTable(classes="feature-grid")
                
                # Close button
                with Center():
                    yield Button("Close Help", variant="primary", classes="close-button")

    def on_mount(self) -> None:
        """Initialize data tables when screen is mounted."""
        self._populate_shortcuts_table()
        self._populate_features_table()

    def _populate_shortcuts_table(self) -> None:
        """Populate the keyboard shortcuts table."""
        table = self.query_one(".shortcuts-table", DataTable)
        table.add_columns("Key", "Action", "Description")
        
        shortcuts = [
            ("F1", "Progress Screen", "Monitor experiment progress in real-time"),
            ("F2", "Metadata Screen", "Inspect experiment metadata and results"),
            ("F3", "Config Screen", "Edit experiment configuration"),
            ("F4", "History Screen", "Browse experiment history"),
            ("F5", "Logs Screen", "View experiment logs"),
            ("Ctrl+N", "New Experiment", "Start a new bias detection experiment"),
            ("P", "Pause", "Pause the current experiment"),
            ("R", "Resume", "Resume a paused experiment"),
            ("C", "Cancel", "Cancel the current experiment"),
            ("Q", "Quit", "Quit the application"),
            ("H", "Help", "Show this help overlay"),
            ("Escape", "Close Modal", "Close current dialog/modal"),
            ("Tab", "Navigate", "Navigate between widgets"),
            ("Enter", "Select", "Select focused item or confirm action"),
        ]
        
        for key, action, description in shortcuts:
            table.add_row(key, action, description)

    def _populate_features_table(self) -> None:
        """Populate the features overview table."""
        table = self.query_one(".feature-grid", DataTable)
        table.add_columns("Screen", "Key Features")
        
        features = [
            ("Progress", "• Real-time phase progress\n• Live metrics tracking\n• Pause/resume/cancel controls"),
            ("Metadata", "• Experiment configuration\n• Session information\n• Results inspection"),
            ("Config", "• YAML configuration editing\n• Validation and locking\n• Parameter management"),
            ("History", "• Experiment history list\n• Search and filtering\n• Session management"),
            ("Logs", "• File-based logging\n• Clean TUI display\n• View with external tools"),
        ]
        
        for screen, key_features in features:
            table.add_row(screen, key_features)
            
        # Add log viewing information
        yield Static("📋 Log Files", classes="help-section-title")
        yield Static(
            "All experiment logs are now saved to:\n"
            "  • data/logs/experiment.log (main experiment logs)\n"
            "  • data/logs/tui.log (TUI-specific logs)\n\n"
            "Use external tools to view logs:\n"
            "  • tail -f data/logs/experiment.log (live follow)\n"
            "  • cat data/logs/experiment.log (view all)\n"
            "  • Code editor with file watching",
            classes="help-text"
        )
            
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle close button press."""
        self.dismiss()

    async def action_dismiss(self, result: str | None = None) -> None:
        """Dismiss the help screen."""
        self.dismiss(result)

    def handle_resize(self, size: Size) -> None:
        """Handle terminal resize events."""
        # Adjust help container size based on terminal size
        if size.width < 100 or size.height < 30:
            # Compact layout for small terminals
            try:
                self.query_one(".help-container").styles.width = "90%"
                self.query_one(".help-container").styles.height = "90%"
            except:
                pass
        else:
            # Full layout for normal terminals
            try:
                self.query_one(".help-container").styles.width = "80%"
                self.query_one(".help-container").styles.height = "80%"
            except:
                pass