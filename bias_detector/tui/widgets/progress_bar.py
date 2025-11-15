"""
Progress Bar Widget for Phase Progress Display.

Shows completion percentage and items done/total for current phase.
"""

from textual.app import ComposeResult
from textual.widgets import Static, ProgressBar as TextualProgressBar
from textual.containers import Container


class PhaseProgressBar(Container):
    """
    Progress bar widget showing phase completion.

    Displays:
    - Visual progress bar
    - Percentage complete
    - Items done / total items
    """

    DEFAULT_CSS = """
    PhaseProgressBar {
        height: auto;
        margin: 1;
        padding: 1;
        border: solid $primary;
    }

    PhaseProgressBar .progress-label {
        text-align: center;
        margin-bottom: 1;
    }

    PhaseProgressBar .progress-stats {
        text-align: center;
        margin-top: 1;
        color: $text-muted;
    }
    """

    def __init__(
        self,
        phase_name: str = "Unknown",
        items_done: int = 0,
        items_total: int = 100,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.phase_name = phase_name
        self.items_done = items_done
        self.items_total = items_total

    def compose(self) -> ComposeResult:
        """Compose the progress bar widget."""
        yield Static(f"Phase: {self.phase_name}", classes="progress-label")
        yield TextualProgressBar(total=self.items_total, show_eta=False)
        yield Static("", classes="progress-stats", id="progress-stats")

    def on_mount(self) -> None:
        """Update progress bar on mount."""
        self.update_progress(self.items_done, self.items_total)

    def update_progress(self, items_done: int, items_total: int) -> None:
        """
        Update progress bar state.

        Args:
            items_done: Number of items completed
            items_total: Total number of items
        """
        self.items_done = items_done
        self.items_total = items_total if items_total > 0 else 1  # Avoid division by zero

        # Update progress bar
        progress_bar = self.query_one(TextualProgressBar)
        progress_bar.total = self.items_total
        progress_bar.update(progress=items_done)

        # Update stats text
        percentage = (items_done / self.items_total) * 100 if self.items_total > 0 else 0
        stats = self.query_one("#progress-stats", Static)
        stats.update(f"{percentage:.1f}% ({items_done}/{self.items_total})")

    def update_phase_name(self, phase_name: str) -> None:
        """Update the displayed phase name."""
        self.phase_name = phase_name
        label = self.query_one(".progress-label", Static)
        label.update(f"Phase: {phase_name}")
