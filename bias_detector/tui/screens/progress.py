"""
Progress Screen for Real-Time Experiment Monitoring.

Main screen showing phase progress, metrics, and overall experiment status.
"""

from typing import Optional, Dict, Any
from queue import Queue, Empty

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.containers import Container, Vertical

from ..widgets.progress_bar import PhaseProgressBar
from ..widgets.phase_list import PhaseList
from ..widgets.metric_display import MetricDisplay
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
        """Compose the progress screen."""
        yield Header()

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
            yield Static("All Phases", classes="section-title")
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

        # Start polling loop if event queue is provided
        if self.event_queue:
            self._polling_interval = self.set_interval(0.1, self._poll_events)

    def update_phase_progress(
        self,
        phase_num: int,
        phase_name: str,
        items_done: int,
        items_total: int
    ) -> None:
        """
        Update current phase progress.

        Args:
            phase_num: Phase number (1-10)
            phase_name: Phase name
            items_done: Items completed
            items_total: Total items
        """
        if self.progress_bar:
            self.progress_bar.update_phase_name(phase_name)
            self.progress_bar.update_progress(items_done, items_total)

    def update_phase_status(self, phase_num: int, status: str) -> None:
        """
        Update phase status in the list.

        Args:
            phase_num: Phase number (1-10)
            status: Status (pending, in_progress, completed, failed, skipped)
        """
        if self.phase_list:
            self.phase_list.update_phase_status(phase_num, status)

    def update_metrics(
        self,
        elapsed_seconds: int,
        estimated_remaining_seconds: Optional[int] = None,
        items_per_second: Optional[float] = None
    ) -> None:
        """
        Update real-time metrics.

        Args:
            elapsed_seconds: Time elapsed since experiment start
            estimated_remaining_seconds: Estimated time remaining
            items_per_second: Processing rate
        """
        if self.metrics:
            self.metrics.update_metrics(
                elapsed_seconds,
                estimated_remaining_seconds,
                items_per_second
            )

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
            event: Event dictionary with 'type' and event-specific fields
        """
        event_type = event.get("type")

        if event_type == "experiment_start":
            self._handle_experiment_start(event)
        elif event_type == "phase_start":
            self._handle_phase_start(event)
        elif event_type == "progress":
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
        self.start_experiment_tracking()
        # Reset all phases to pending
        if self.phase_list:
            self.phase_list.reset()

    def _handle_phase_start(self, event: Dict[str, Any]) -> None:
        """Handle phase start event."""
        phase_num = event.get("phase_num")
        phase_name = event.get("phase_name")
        items_total = event.get("items_total", 100)

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

        # Update progress bar
        if self.progress_bar:
            self.progress_bar.update_progress(items_done, items_total)

        # Update metrics if we have a metric display
        if self.metrics:
            self.metrics.compute_and_update(items_done, items_total)

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
        session_id = event.get("session_id", "unknown")
        error_type = event.get("error_type", "Unknown")
        error_message = event.get("error_message", "No details available")
        failed_phase = event.get("failed_phase", 0)

        # Show error notification
        self.notify(
            f"Experiment Failed ✗\n"
            f"Session: {session_id}\n"
            f"Failed at Phase {failed_phase}\n"
            f"Error: {error_type}\n"
            f"{error_message[:100]}...",
            title="Error",
            severity="error",
            timeout=15
        )
