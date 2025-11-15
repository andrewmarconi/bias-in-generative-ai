"""
History Screen for Experiment Management.

Displays experiment history with filtering, search, pagination, and detail views.
Allows users to view, manage, and delete past experiments.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import (
    DataTable, Input, Label, Static, Button, 
    Select
)
from textual.containers import (
    Horizontal, Vertical, Container
)
from textual.binding import Binding
from textual import log
from textual.geometry import Size

from ..state.manager import StateManager, SessionIndexEntry
from ..state.session import SessionStatus


class HistoryScreen(Screen):
    """
    Experiment history management screen.
    
    Features:
    - List all experiments with status, start time, image count
    - Filter by status (completed, failed, cancelled, etc.)
    - Search by session ID
    - Pagination for large histories (20 entries per page)
    - Experiment detail view on selection
    - Manual delete with confirmation
    """
    
    TITLE = "Experiment History"
    SUB_TITLE = "Browse and Manage Past Experiments"

    BINDINGS = [
        Binding("f1", "switch_screen('progress')", "Progress", show=True),
        Binding("f2", "switch_screen('metadata')", "Metadata", show=True),
        Binding("f3", "switch_screen('config')", "Config", show=True),
        Binding("f4", "switch_screen('history')", "History", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("d", "delete_selected", "Delete Selected", show=True),
        Binding("enter", "view_details", "View Details", show=True),
        Binding("escape", "back", "Back", show=True),
    ]

    def __init__(
        self,
        state_manager: Optional[StateManager] = None,
        **kwargs
    ):
        """
        Initialize history screen.

        Args:
            state_manager: StateManager instance for experiment operations
            **kwargs: Additional arguments passed to Screen
        """
        super().__init__(**kwargs)
        self.state_manager = state_manager or StateManager()
        
        # Data
        self.all_experiments: List[SessionIndexEntry] = []
        self.filtered_experiments: List[SessionIndexEntry] = []
        self.selected_experiment: Optional[SessionIndexEntry] = None
        
        # UI state
        self.current_page: int = 0
        self.page_size: int = 20
        self.status_filter: str = "all"
        self.search_query: str = ""
        
        # UI components
        self.experiments_table: Optional[DataTable] = None
        self.search_input: Optional[Input] = None
        self.status_select: Optional[Select] = None
        self.pagination_label: Optional[Label] = None
        self.detail_panel: Optional[Container] = None

    def compose(self) -> ComposeResult:
        """Compose the history screen UI."""
        yield Container(
            # Header with search and filters
            Vertical(
                Label("Experiment History", classes="section-title"),
                
                # Search and filter controls
                Horizontal(
                    Input(
                        placeholder="Search by session ID...",
                        id="search-input",
                        value="",
                    ),
                    Select(
                        options=[
                            ("all", "All Status"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                            ("cancelled", "Cancelled"),
                            ("running", "Running"),
                            ("paused", "Paused"),
                            ("pending", "Pending"),
                        ],
                        value="all",
                        id="status-filter",
                    ),
                    Button("Refresh", id="refresh-button", variant="primary"),
                    classes="control-row",
                ),
                
                # Pagination info
                Label("", id="pagination-label", classes="pagination-info"),
                
                classes="header-section",
            ),
            
            # Main content area
            Horizontal(
                # Experiments table
                Vertical(
                    DataTable(
                        id="experiments-table",
                        show_header=True,
                        zebra_stripes=True,
                    ),
                    classes="table-container",
                ),
                
                # Detail panel (initially hidden)
                Vertical(
                    Label("Experiment Details", classes="subsection-title"),
                    Static("", id="detail-content", classes="detail-text"),
                    id="detail-panel",
                    classes="detail-container hidden",
                ),
                
                classes="main-content",
            ),
            
            # Action buttons
            Horizontal(
                Button("Delete Selected", id="delete-button", variant="error"),
                Button("View Details", id="details-button", variant="primary"),
                Button("Back", id="back-button", variant="default"),
                classes="action-row",
            ),
            
            id="history-container",
        )

    def on_mount(self) -> None:
        """Initialize the screen when mounted."""
        # Setup UI references
        self.experiments_table = self.query_one("#experiments-table", DataTable)
        self.search_input = self.query_one("#search-input", Input)
        self.status_select = self.query_one("#status-filter", Select)
        self.pagination_label = self.query_one("#pagination-label", Label)
        self.detail_panel = self.query_one("#detail-panel", Container)
        
        # Setup table columns
        self._setup_table()
        
        # Load experiments
        self._load_experiments()
        
        # Apply initial filters
        self._apply_filters()

    def _setup_table(self) -> None:
        """Setup the experiments table with columns."""
        table = self.experiments_table
        
        # Add columns
        table.add_column("Session ID", key="session_id", width=20)
        table.add_column("Status", key="status", width=12)
        table.add_column("Start Time", key="start_time", width=20)
        table.add_column("Config", key="config_name", width=15)
        table.add_column("Images", key="total_images", width=8)
        table.add_column("Phases", key="phases_completed", width=8)
        
        # Make table selectable
        table.cursor_type = "row"

    def _load_experiments(self) -> None:
        """Load all experiments from state manager."""
        try:
            self.all_experiments = self.state_manager.list_sessions()
            log.info(f"Loaded {len(self.all_experiments)} experiments from history")
        except Exception as e:
            log.error(f"Failed to load experiments: {e}")
            self.all_experiments = []

    def _apply_filters(self) -> None:
        """Apply current filters to experiment list."""
        # Start with all experiments
        self.filtered_experiments = self.all_experiments.copy()
        
        # Apply status filter
        if self.status_filter != "all":
            self.filtered_experiments = [
                exp for exp in self.filtered_experiments
                if exp.status == self.status_filter
            ]
        
        # Apply search filter
        if self.search_query:
            search_lower = self.search_query.lower()
            self.filtered_experiments = [
                exp for exp in self.filtered_experiments
                if search_lower in exp.session_id.lower()
            ]
        
        # Update table
        self._update_table()
        self._update_pagination()

    def _update_table(self) -> None:
        """Update the experiments table with current page data."""
        if not self.experiments_table:
            return
            
        # Clear table
        self.experiments_table.clear()
        
        # Calculate pagination
        start_idx = self.current_page * self.page_size
        end_idx = start_idx + self.page_size
        page_data = self.filtered_experiments[start_idx:end_idx]
        
        # Add rows to table
        for experiment in page_data:
            # Format start time
            start_time = experiment.start_time
            if len(start_time) > 16:
                start_time = start_time[:16]  # Remove microseconds if present
            
            self.experiments_table.add_row({
                "session_id": experiment.session_id,
                "status": self._format_status(experiment.status),
                "start_time": start_time,
                "config_name": experiment.config_name,
                "total_images": str(experiment.total_images),
                "phases_completed": f"{experiment.phases_completed}/10",
            })

    def _format_status(self, status: str) -> str:
        """Format status with appropriate styling."""
        status_colors = {
            "completed": "✅",
            "failed": "❌", 
            "cancelled": "⏹",
            "running": "🔄",
            "paused": "⏸",
            "pending": "⏳",
        }
        
        icon = status_colors.get(status, "❓")
        return f"{icon} {status.title()}"

    def _update_pagination(self) -> None:
        """Update pagination label."""
        if not self.pagination_label:
            return
            
        total_experiments = len(self.filtered_experiments)
        total_pages = (total_experiments + self.page_size - 1) // self.page_size
        current_page_num = self.current_page + 1
        
        if total_experiments == 0:
            self.pagination_label.update("No experiments found")
        else:
            self.pagination_label.update(
                f"Showing {len(self.filtered_experiments[self.current_page * self.page_size:(self.current_page + 1) * self.page_size])} "
                f"of {total_experiments} experiments (Page {current_page_num} of {total_pages})"
            )

    def _show_experiment_details(self, experiment: SessionIndexEntry) -> None:
        """Show detailed information for selected experiment."""
        if not self.detail_panel:
            return
            
        # Load full session data
        try:
            session = self.state_manager.get_session(experiment.session_id)
            
            # Format details
            details = f"""
Session ID: {session.session_id}
Status: {session.status.value}
Start Time: {session.start_time}
End Time: {session.end_time or 'Still running'}
Current Phase: {session.current_phase}

Configuration Snapshot:
- Experiment: {session.config_snapshot.get('experiment', {}).get('name', 'Unknown')}
- Model: {session.config_snapshot.get('generation', {}).get('model', 'Unknown')}
- Images per Prompt: {session.config_snapshot.get('generation', {}).get('num_images_per_prompt', 'Unknown')}

Phase Progress:
"""
            
            # Add phase details
            for phase in session.phase_progress:
                details += f"- Phase {phase.phase}: {phase.status.value}"
                if phase.items_total > 0:
                    details += f" ({phase.items_done}/{phase.items_total})"
                details += "\n"
            
            # Update detail panel
            detail_content = self.detail_panel.query_one("#detail-content", Static)
            detail_content.update(details.strip())
            
            # Show detail panel
            self.detail_panel.remove_class("hidden")
            
        except Exception as e:
            log.error(f"Failed to load experiment details: {e}")
            if self.detail_panel:
                detail_content = self.detail_panel.query_one("#detail-content", Static)
                detail_content.update(f"Error loading details: {e}")

    def _hide_experiment_details(self) -> None:
        """Hide experiment details panel."""
        if self.detail_panel:
            self.detail_panel.add_class("hidden")

    # Event handlers
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            self.search_query = event.value
            self.current_page = 0  # Reset to first page
            self._apply_filters()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle status filter changes."""
        if event.select.id == "status-filter":
            self.status_filter = event.value
            self.current_page = 0  # Reset to first page
            self._apply_filters()

    def on_data_table_selected(self, event: DataTable.RowSelected) -> None:
        """Handle experiment selection in table."""
        if event.data_table.id == "experiments-table":
            if event.row_key:
                # Find selected experiment
                for exp in self.filtered_experiments:
                    if exp.session_id == event.row_key.get("session_id"):
                        self.selected_experiment = exp
                        self._show_experiment_details(exp)
                        break

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "refresh-button":
            self._load_experiments()
            self._apply_filters()
            
        elif button_id == "delete-button":
            self._delete_selected_experiment()
            
        elif button_id == "details-button":
            if self.selected_experiment:
                self._show_experiment_details(self.selected_experiment)
                
        elif button_id == "back-button":
            self._hide_experiment_details()

    def _delete_selected_experiment(self) -> None:
        """Delete the selected experiment with confirmation."""
        if not self.selected_experiment:
            log.warning("No experiment selected for deletion")
            return
            
        # For now, delete without confirmation dialog
        # TODO: Add confirmation dialog in polish phase
        try:
            self.state_manager.delete_session(self.selected_experiment.session_id)
            log.info(f"Deleted experiment: {self.selected_experiment.session_id}")
            
            # Reload experiments
            self._load_experiments()
            self._apply_filters()
            
            # Clear selection
            self.selected_experiment = None
            self._hide_experiment_details()
            
        except Exception as e:
            log.error(f"Failed to delete experiment: {e}")

    # Actions
    def action_delete_selected(self) -> None:
        """Delete selected experiment."""
        self._delete_selected_experiment()

    def action_view_details(self) -> None:
        """View details of selected experiment."""
        if self.selected_experiment:
            self._show_experiment_details(self.selected_experiment)

    def action_back(self) -> None:
        """Go back to previous screen."""
        self._hide_experiment_details()
        self.dismiss()

    CSS = """
    HistoryScreen {
        layout: grid;
        grid-size: 3 1;
        grid-rows: auto 1fr;
        grid-columns: 1fr;
    }

    .header-section {
        height: auto;
        margin-bottom: 1;
    }

    .control-row {
        height: 3;
        margin-bottom: 1;
    }

    .main-content {
        height: 1fr;
    }

    .table-container {
        height: 100%;
        margin-right: 1;
    }

    .detail-container {
        width: 40%;
        border-left: solid $primary;
        padding: 1;
    }

    .detail-container.hidden {
        display: none;
    }

    .subsection-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .detail-text {
        margin: 1;
        padding: 1;
        background: $surface;
        border: solid $primary;
        height: 100%;
        text-style: normal;
    }

    .pagination-info {
        text-style: italic;
        color: $text-muted;
        margin: 1;
    }

    .action-row {
        height: 3;
        margin-top: 1;
    }

    DataTable {
        height: 100%;
    }

    Button {
        margin: 0 1;
    }

    Input {
        width: 30%;
    }

    Select {
        width: 20%;
    }
    """

    def handle_resize(self, size: Size) -> None:
        """Handle terminal resize events."""
        # Adjust layout based on new size
        if size.width < 100:
            # Compact layout for small terminals
            try:
                self.query_one("Input").styles.width = "50%"
                self.query_one("Select").styles.width = "40%"
            except:
                pass
        else:
            # Full layout for normal terminals
            try:
                self.query_one("Input").styles.width = "30%"
                self.query_one("Select").styles.width = "20%"
            except:
                pass
        
        # Refresh table
        if hasattr(self, 'experiments_table') and self.experiments_table:
            self.experiments_table.refresh()