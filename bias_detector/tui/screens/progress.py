"""
Progress Screen for Real-Time Experiment Monitoring.

Main screen showing phase progress, metrics, and overall experiment status.
"""

from typing import Optional, Dict, Any
from queue import Queue, Empty
import time

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.containers import Container, Vertical
from textual.geometry import Size

from ..widgets.progress_bar import PhaseProgressBar
from ..widgets.phase_list import PhaseList, PhaseListItem
from ..widgets.metric_display import MetricDisplay
from ..widgets.phase_detail_modal import PhaseDetailModal
from ..state.session import PHASE_NAMES


class ProgressScreen(Screen):
    """
    Main progress monitoring screen.

    Displays:
    - Current phase progress bar
    - List of all phases with status
    - Real-time metrics (elapsed, ETA, rate)
    - Experiment status messages
    """

    BINDINGS = [
        ("f1", "switch_screen('progress')", "Progress"),
        ("f2", "switch_screen('metadata')", "Metadata"),
        ("f3", "switch_screen('config')", "Config"),
        ("f4", "switch_screen('history')", "History"),
        ("p", "pause_experiment", "Pause"),
        ("r", "resume_experiment", "Resume"),
        ("c", "cancel_experiment", "Cancel"),
        ("q", "quit", "Quit"),
    ]

    DEFAULT_CSS = """
    ProgressScreen {
        layout: grid;
        grid-size: 2 2;
        grid-rows: 1fr 1fr;
        grid-columns: 2fr 1fr;
    }

    #current-phase-container {
        column-span: 2;
        row-span: 1;
        padding: 1;
    }

    #phase-list-container {
        column-span: 1;
        row-span: 1;
        padding: 1;
    }

    #metrics-container {
        column-span: 1;
        row-span: 1;
        padding: 1;
    }

    .status-message {
        margin: 1;
        padding: 1;
        border: solid $accent;
        text-align: center;
    }
    """

    def __init__(self, event_queue: Optional[Queue] = None, **kwargs):
        super().__init__(**kwargs)
        self.event_queue = event_queue
        self.progress_bar: Optional[PhaseProgressBar] = None
        self.phase_list: Optional[PhaseList] = None
        self.metrics: Optional[MetricDisplay] = None
        self._polling_interval = None

    def compose(self) -> ComposeResult:
        """Compose the progress screen UI."""
        yield Header()

        # Experiment status header
        with Container(id="status-header"):
            yield Static("Experiment Status: Idle", id="experiment-status", classes="experiment-status")
            yield Static("Click on phases for details", classes="status-hint")

        # Current phase progress
        with Container(id="current-phase-container"):
            yield Static("Current Phase Progress", classes="section-title")
            self.progress_bar = PhaseProgressBar(
                phase_name="Waiting to start...",
                items_done=0,
                items_total=100
            )
            yield self.progress_bar

        # Phase list
        with Container(id="phase-list-container"):
            yield Static("All Phases (Click for details)", classes="section-title")
            self.phase_list = PhaseList()
            yield self.phase_list

        # Metrics
        with Container(id="metrics-container"):
            yield Static("Experiment Metrics", classes="section-title")
            self.metrics = MetricDisplay()
            yield self.metrics

        yield Footer()

    def on_mount(self) -> None:
        """Initialize screen on mount."""
        self.sub_title = "Experiment Progress Monitor"

        # Initialize debouncing state
        self._last_update_time = 0
        self._update_debounce_ms = 200  # Debounce updates to 200ms
        self._pending_updates = {}

        # Experiment status tracking
        self.experiment_status = "idle"  # idle, running, paused, completed, failed
        self.experiment_start_time: Optional[float] = None
        self.current_phase_num: Optional[int] = None
        self.phase_start_times: Dict[int, float] = {}
        self.phase_progress: Dict[int, Dict[str, Any]] = {}

        # Start polling loop if event queue is provided
        if self.event_queue:
            self._polling_interval = self.set_interval(0.1, self._poll_events)

    def _should_update(self) -> bool:
        """Check if enough time has passed to allow an update."""
        current_time = time.time() * 1000  # Convert to milliseconds
        return (current_time - self._last_update_time) >= self._update_debounce_ms

    def _mark_update(self) -> None:
        """Mark that an update just occurred."""
        self._last_update_time = time.time() * 1000

    def _flush_pending_updates(self) -> None:
        """Flush all pending updates immediately."""
        if not self._pending_updates:
            return
            
        # Apply the most recent update for each type
        if 'phase_progress' in self._pending_updates:
            update = self._pending_updates['phase_progress']
            if self.progress_bar:
                self.progress_bar.update_phase_name(update['phase_name'])
                self.progress_bar.update_progress(update['items_done'], update['items_total'])
                
        if 'phase_status' in self._pending_updates:
            update = self._pending_updates['phase_status']
            if self.phase_list:
                self.phase_list.update_phase_status(update['phase_num'], update['status'])
                
        if 'metrics' in self._pending_updates:
            update = self._pending_updates['metrics']
            if self.metrics:
                self.metrics.update_metrics(**update)
        
        # Clear pending updates and mark time
        self._pending_updates.clear()
        self._mark_update()

    def update_phase_progress(
        self,
        phase_num: int,
        phase_name: str,
        items_done: int,
        items_total: int
    ) -> None:
        """
        Update current phase progress with debouncing.

        Args:
            phase_num: Phase number (1-10)
            phase_name: Phase name
            items_done: Items completed
            items_total: Total items
        """
        # Ensure screen is mounted and initialized
        if not hasattr(self, '_pending_updates'):
            return
            
        # Store update
        self._pending_updates['phase_progress'] = {
            'phase_name': phase_name,
            'items_done': items_done,
            'items_total': items_total
        }
        
        # Apply immediately if enough time has passed
        if self._should_update():
            self._flush_pending_updates()

    def update_phase_status(self, phase_num: int, status: str) -> None:
        """
        Update phase status in list with debouncing.

        Args:
            phase_num: Phase number (1-10)
            status: New status
        """
        # Ensure screen is mounted and initialized
        if not hasattr(self, '_pending_updates'):
            return
            
        # Store the update
        self._pending_updates['phase_status'] = {
            'phase_num': phase_num,
            'status': status
        }
        
        # Apply immediately if enough time has passed
        if self._should_update():
            self._flush_pending_updates()

    def update_metrics(
        self,
        elapsed_seconds: int,
        estimated_remaining_seconds: Optional[int] = None,
        items_per_second: Optional[float] = None
    ) -> None:
        """
        Update real-time metrics with debouncing.

        Args:
            elapsed_seconds: Time elapsed since experiment start
            estimated_remaining_seconds: Estimated time remaining
            items_per_second: Processing rate
        """
        # Ensure screen is mounted and initialized
        if not hasattr(self, '_pending_updates'):
            return
            
        # Store the update
        self._pending_updates['metrics'] = {
            'elapsed_seconds': elapsed_seconds,
            'estimated_remaining_seconds': estimated_remaining_seconds,
            'items_per_second': items_per_second
        }
        
        # Apply immediately if enough time has passed
        if self._should_update():
            self._flush_pending_updates()

    def start_experiment_tracking(self) -> None:
        """Start tracking experiment time."""
        if self.metrics:
            self.metrics.start()

    def _poll_events(self) -> None:
        """Poll the event queue and process events (runs every 100ms)."""
        if not self.event_queue:
            return

        # Process all available events in the queue
        while True:
            try:
                event = self.event_queue.get_nowait()
                self._handle_event(event)
            except Empty:
                break

    def _handle_event(self, event: Dict[str, Any]) -> None:
        """
        Handle a single progress event.

        Args:
            event: Event dictionary with 'event' and event-specific fields
        """
        event_type = event.get("event")

        # Handle PhaseEvent enum values
        if hasattr(event_type, 'value'):
            event_type = event_type.value

        if event_type == "experiment_start":
            self._handle_experiment_start(event)
        elif event_type == "phase_start":
            self._handle_phase_start(event)
        elif event_type == "phase_progress":
            self._handle_progress(event)
        elif event_type == "phase_complete":
            self._handle_phase_complete(event)
        elif event_type == "phase_error":
            self._handle_phase_error(event)
        elif event_type == "experiment_complete":
            self._handle_experiment_complete(event)
        elif event_type == "experiment_error":
            self._handle_experiment_error(event)

    def _handle_experiment_start(self, event: Dict[str, Any]) -> None:
        """Handle experiment start event."""
        self.experiment_status = "running"
        self.experiment_start_time = time.time()
        self.start_experiment_tracking()
        self._update_experiment_status_display()

        # Reset all phases to pending
        if self.phase_list:
            self.phase_list.reset()

    def _handle_phase_start(self, event: Dict[str, Any]) -> None:
        """Handle phase start event."""
        phase_num = event.get("phase_num")
        phase_name = event.get("phase_name")
        items_total = event.get("items_total", 100)

        # Track phase timing
        if phase_num:
            self.current_phase_num = phase_num
            self.phase_start_times[phase_num] = time.time()
            self.phase_progress[phase_num] = {
                'items_done': 0,
                'items_total': items_total,
                'start_time': time.time()
            }

        # Update phase status in list
        if self.phase_list and phase_num:
            self.phase_list.update_phase_status(phase_num, "in_progress")

        # Update progress bar
        if self.progress_bar and phase_name:
            self.progress_bar.update_phase_name(phase_name)
            self.progress_bar.update_progress(0, items_total)

    def _handle_progress(self, event: Dict[str, Any]) -> None:
        """Handle progress update event."""
        phase_num = event.get("phase_num")
        items_done = event.get("items_done", 0)
        items_total = event.get("items_total", 100)

        # Track phase progress
        if phase_num and phase_num in self.phase_progress:
            self.phase_progress[phase_num]['items_done'] = items_done
            self.phase_progress[phase_num]['items_total'] = items_total

        # Update progress bar
        if self.progress_bar:
            self.progress_bar.update_progress(items_done, items_total)

        # Update metrics with ETA calculation
        if self.metrics:
            eta = self._calculate_eta(phase_num or 1, items_done, items_total)
            elapsed = time.time() - (self.experiment_start_time or time.time())
            rate = items_done / elapsed if elapsed > 0 else 0

            self.metrics.update_metrics(
                elapsed_seconds=int(elapsed),
                estimated_remaining_seconds=int(eta) if eta else None,
                items_per_second=rate
            )

    def _handle_phase_complete(self, event: Dict[str, Any]) -> None:
        """Handle phase completion event."""
        phase_num = event.get("phase_num")

        # Update phase status in list
        if self.phase_list and phase_num:
            self.phase_list.update_phase_status(phase_num, "completed")

        # Update progress bar to show 100%
        if self.progress_bar:
            items_total = self.progress_bar.items_total
            self.progress_bar.update_progress(items_total, items_total)

    def _handle_phase_error(self, event: Dict[str, Any]) -> None:
        """Handle phase error event."""
        phase_num = event.get("phase_num")

        # Update phase status in list
        if self.phase_list and phase_num:
            self.phase_list.update_phase_status(phase_num, "failed")

    def _handle_experiment_complete(self, event: Dict[str, Any]) -> None:
        """Handle experiment completion event."""
        self.experiment_status = "completed"
        self._update_experiment_status_display()

        session_id = event.get("session_id", "unknown")
        total_time = event.get("total_time_seconds", 0)
        phases_completed = event.get("phases_completed", 0)

        # Format completion time
        hours, remainder = divmod(int(total_time), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        # Show completion notification
        self.notify(
            f"Experiment Complete! ✓\n"
            f"Session: {session_id}\n"
            f"Phases: {phases_completed}/10\n"
            f"Time: {time_str}",
            title="Success",
            severity="information",
            timeout=10
        )

    def _handle_experiment_error(self, event: Dict[str, Any]) -> None:
        """Handle experiment error event."""
        self.experiment_status = "failed"
        self._update_experiment_status_display()

        if self.phase_list:
            self.phase_list.update_phase_status(
                event.get("phase_num", 1),
                "error"
            )

    def _update_experiment_status_display(self) -> None:
        """Update the experiment status display."""
        status_widget = self.query_one("#experiment-status", Static)
        if status_widget:
            status_colors = {
                "idle": "dim",
                "running": "bold green",
                "paused": "bold yellow",
                "completed": "bold blue",
                "failed": "bold red"
            }
            color = status_colors.get(self.experiment_status, "white")
            status_widget.update(f"Experiment Status: [{color}]{self.experiment_status.title()}[/]")

    def _calculate_eta(self, current_phase: int, items_done: int, items_total: int) -> Optional[float]:
        """Calculate estimated time remaining for current phase."""
        if not self.experiment_start_time or items_total <= 0:
            return None

        # Calculate progress rate
        elapsed = time.time() - self.experiment_start_time
        if elapsed <= 0 or items_done <= 0:
            return None

        progress_rate = items_done / elapsed  # items per second
        remaining_items = items_total - items_done

        if progress_rate <= 0:
            return None

        return remaining_items / progress_rate

    def on_phase_selected(self, message) -> None:
        """Handle phase selection for detail view."""
        # Show phase detail modal
        phase_progress = self.phase_progress.get(message.phase_num, {})
        eta = self._calculate_eta(message.phase_num,
                                phase_progress.get('items_done', 0),
                                phase_progress.get('items_total', 100))

        # For now, just show a simple notification (modal implementation would be complex)
        self.notify(
            f"Phase {message.phase_num}: {message.phase_name}\n"
            f"Status: {message.status.title()}\n"
            f"Click to view details (modal coming soon)",
            title="Phase Details",
            timeout=5
        )

    def action_pause_experiment(self) -> None:
        """Pause the current experiment."""
        # Get the main app and call its pause method
        app = self.app
        if hasattr(app, 'action_pause_experiment'):
            app.action_pause_experiment()

    def action_resume_experiment(self) -> None:
        """Resume the current experiment."""
        # Get the main app and call its resume method
        app = self.app
        if hasattr(app, 'action_resume_experiment'):
            app.action_resume_experiment()

    def action_cancel_experiment(self) -> None:
        """Cancel the current experiment."""
        # Get the main app and call its cancel method
        app = self.app
        if hasattr(app, 'action_cancel_experiment'):
            app.action_cancel_experiment()

    def handle_resize(self, size: Size) -> None:
        """Handle terminal resize events."""
        # Flush any pending updates before resize
        self._flush_pending_updates()
        
        # Adjust layout based on new size
        if size.width < 80:
            # Compact layout for small terminals
            try:
                self.query_one("#phase-list-container").styles.height = "1fr"
                self.query_one("#metrics-container").styles.height = "1fr"
            except:
                pass  # Ignore if widgets not found
        else:
            # Full layout for normal terminals
            try:
                self.query_one("#phase-list-container").styles.height = None
                self.query_one("#metrics-container").styles.height = None
            except:
                pass  # Ignore if widgets not found
        
        # Refresh metrics display
        if hasattr(self, 'metrics'):
            self.metrics.refresh()
