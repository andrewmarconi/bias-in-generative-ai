"""
Phase Detail Modal for Progress Screen.

Shows detailed information about a specific phase.
"""

from typing import Optional
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Center
from textual.screen import ModalScreen
from textual.widgets import Static, Button, ProgressBar
from textual.binding import Binding


class PhaseDetailModal(ModalScreen[None]):
    """
    Modal dialog showing detailed information about a phase.

    Displays:
    - Phase name and description
    - Current progress
    - Sub-tasks if available
    - Time elapsed/remaining
    - Phase-specific metrics
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("enter", "dismiss", "Close"),
    ]

    def __init__(
        self,
        phase_num: int,
        phase_name: str,
        status: str,
        progress: float,
        items_done: int,
        items_total: int,
        elapsed_time: Optional[float] = None,
        estimated_remaining: Optional[float] = None,
        **kwargs
    ):
        """Initialize phase detail modal."""
        super().__init__(**kwargs)
        self.phase_num = phase_num
        self.phase_name = phase_name
        self.status = status
        self.progress = progress
        self.items_done = items_done
        self.items_total = items_total
        self.elapsed_time = elapsed_time
        self.estimated_remaining = estimated_remaining

    def compose(self) -> ComposeResult:
        """Compose the phase detail modal."""
        with Center():
            with Vertical(classes="phase-detail-modal"):
                # Header
                yield Static(f"Phase {self.phase_num}: {self.phase_name}", classes="modal-title")

                # Status
                status_color = {
                    "pending": "dim",
                    "in_progress": "bold green",
                    "completed": "bold blue",
                    "failed": "bold red",
                    "skipped": "dim yellow"
                }.get(self.status, "white")

                yield Static(f"Status: [{status_color}]{self.status.title()}[/]", classes="phase-status")

                # Progress bar
                yield Static("Progress:", classes="progress-label")
                yield ProgressBar(
                    total=self.items_total or 100,
                    show_eta=False,
                    classes="phase-progress-bar"
                )

                # Progress stats
                progress_text = f"{self.items_done}/{self.items_total} items"
                if self.items_total > 0:
                    percentage = (self.items_done / self.items_total) * 100
                    progress_text += f" ({percentage:.1f}%)"

                yield Static(progress_text, classes="progress-stats")

                # Time information
                if self.elapsed_time is not None:
                    elapsed_str = self._format_time(self.elapsed_time)
                    yield Static(f"Elapsed: {elapsed_str}", classes="time-info")

                if self.estimated_remaining is not None:
                    remaining_str = self._format_time(self.estimated_remaining)
                    yield Static(f"Remaining: ~{remaining_str}", classes="time-info")

                # Phase description
                description = self._get_phase_description()
                if description:
                    yield Static("Description:", classes="description-label")
                    yield Static(description, classes="phase-description")

                # Close button
                with Center():
                    yield Button("Close", variant="primary", id="close-button")

    def on_mount(self) -> None:
        """Set progress bar value when mounted."""
        progress_bar = self.query_one(ProgressBar)
        progress_bar.update(progress=self.items_done)

    def on_button_pressed(self, event) -> None:
        """Handle button presses."""
        if event.button.id == "close-button":
            self.dismiss()

    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to human-readable string."""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    def _get_phase_description(self) -> str:
        """Get description for the current phase."""
        descriptions = {
            1: "Setting up experimental design, hypotheses, and statistical parameters.",
            2: "Creating and validating prompt templates for bias detection.",
            3: "Generating images using AI models based on configured prompts.",
            4: "Analyzing generated images with VQA models for demographic characteristics.",
            5: "Performing statistical analysis and bias quantification calculations.",
            6: "Running counterfactual experiments with explicit demographic modifiers.",
            7: "Human validation and annotation of AI-generated results.",
            8: "Logging results and metrics to MLflow tracking system.",
            9: "Ethical review and bias assessment of experimental methodology.",
            10: "Generating final reports and documentation of findings."
        }
        return descriptions.get(self.phase_num, "Processing experiment phase.")

    DEFAULT_CSS = """
    PhaseDetailModal {
        align: center middle;
    }

    .phase-detail-modal {
        width: 70%;
        height: 60%;
        background: $surface;
        border: thick $primary;
        border-radius: 1;
        padding: 2;
    }

    .modal-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .phase-status {
        text-align: center;
        margin-bottom: 1;
    }

    .progress-label {
        margin-bottom: 0.5;
        text-style: bold;
    }

    .phase-progress-bar {
        width: 100%;
        margin-bottom: 1;
    }

    .progress-stats {
        text-align: center;
        margin-bottom: 1;
        color: $text-muted;
    }

    .time-info {
        text-align: center;
        margin-bottom: 0.5;
        color: $text;
    }

    .description-label {
        margin-top: 1;
        margin-bottom: 0.5;
        text-style: bold;
    }

    .phase-description {
        color: $text-muted;
        margin-bottom: 1;
    }
    """