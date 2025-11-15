"""
Metric Display Widget for Real-Time Experiment Metrics.

Shows elapsed time, estimated time remaining, and processing rate.
"""

from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import Container
from datetime import datetime, timedelta
from typing import Optional


class MetricDisplay(Container):
    """
    Display widget for real-time experiment metrics.

    Shows:
    - Elapsed time since experiment started
    - Estimated time remaining
    - Processing rate (items/second)
    """

    DEFAULT_CSS = """
    MetricDisplay {
        height: auto;
        border: solid $primary;
        padding: 1;
        margin: 1;
    }

    MetricDisplay Static {
        margin: 0 1;
    }

    MetricDisplay .metric-value {
        color: $success;
        text-style: bold;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_time: Optional[datetime] = None
        self.elapsed_seconds = 0
        self.estimated_remaining_seconds: Optional[int] = None
        self.items_per_second: Optional[float] = None

    def compose(self) -> ComposeResult:
        """Compose the metric display."""
        yield Static("Elapsed: --:--:--", id="elapsed-time")
        yield Static("Remaining: --:--:--", id="remaining-time")
        yield Static("Rate: -- items/sec", id="processing-rate")

    def start(self) -> None:
        """Start timing the experiment."""
        self.start_time = datetime.now()
        self.update_metrics(0, None, None)

    def update_metrics(
        self,
        elapsed_seconds: int,
        estimated_remaining_seconds: Optional[int] = None,
        items_per_second: Optional[float] = None
    ) -> None:
        """
        Update displayed metrics.

        Args:
            elapsed_seconds: Seconds since experiment started
            estimated_remaining_seconds: Estimated seconds remaining (None if unknown)
            items_per_second: Processing rate (None if unknown)
        """
        self.elapsed_seconds = elapsed_seconds
        self.estimated_remaining_seconds = estimated_remaining_seconds
        self.items_per_second = items_per_second

        # Update elapsed time
        elapsed_str = self._format_time(elapsed_seconds)
        elapsed_widget = self.query_one("#elapsed-time", Static)
        elapsed_widget.update(f"Elapsed: [bold green]{elapsed_str}[/]")

        # Update remaining time
        if estimated_remaining_seconds is not None:
            remaining_str = self._format_time(estimated_remaining_seconds)
            remaining_widget = self.query_one("#remaining-time", Static)
            remaining_widget.update(f"Remaining: [bold yellow]~{remaining_str}[/]")
        else:
            remaining_widget = self.query_one("#remaining-time", Static)
            remaining_widget.update("Remaining: [dim]calculating...[/]")

        # Update processing rate
        if items_per_second is not None:
            rate_widget = self.query_one("#processing-rate", Static)
            rate_widget.update(f"Rate: [bold cyan]{items_per_second:.3f} items/sec[/]")
        else:
            rate_widget = self.query_one("#processing-rate", Static)
            rate_widget.update("Rate: [dim]--[/]")

    def _format_time(self, seconds: int) -> str:
        """
        Format seconds as HH:MM:SS.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string
        """
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

    def compute_and_update(
        self,
        total_items_done: int,
        total_items: int
    ) -> None:
        """
        Compute metrics from current progress and update display.

        Args:
            total_items_done: Total items completed
            total_items: Total items to complete
        """
        if self.start_time is None:
            return

        # Calculate elapsed time
        elapsed = (datetime.now() - self.start_time).total_seconds()
        elapsed_int = int(elapsed)

        # Calculate processing rate
        items_per_sec = None
        if elapsed > 0 and total_items_done > 0:
            items_per_sec = total_items_done / elapsed

        # Calculate estimated remaining time
        estimated_remaining = None
        if items_per_sec and items_per_sec > 0:
            remaining_items = total_items - total_items_done
            estimated_remaining = int(remaining_items / items_per_sec)

        self.update_metrics(elapsed_int, estimated_remaining, items_per_sec)
