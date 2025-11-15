"""
Phase List Widget for Displaying All 10 Research Phases.

Shows phase status with icons for pending, in-progress, completed, failed, skipped.
"""

from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import VerticalScroll
from typing import Dict, List


class PhaseListItem(Static):
    """Single phase item in the list."""

    def __init__(self, phase_num: int, name: str, status: str = "pending", **kwargs):
        self.phase_num = phase_num
        self.phase_name = name
        self.status = status
        super().__init__(self._format_text(), **kwargs)

    def _format_text(self) -> str:
        """Format the phase item text with status icon."""
        icons = {
            "pending": "[ ]",
            "in_progress": "[▶]",
            "completed": "[✓]",
            "failed": "[✗]",
            "skipped": "[−]"
        }
        icon = icons.get(self.status, "[ ]")
        return f"{icon} Phase {self.phase_num}: {self.phase_name}"

    def update_status(self, status: str) -> None:
        """Update phase status."""
        self.status = status
        self.update(self._format_text())


class PhaseList(VerticalScroll):
    """
    List widget displaying all 10 research framework phases.

    Shows each phase with:
    - Status icon (pending, in-progress, completed, failed, skipped)
    - Phase number and name
    """

    DEFAULT_CSS = """
    PhaseList {
        height: auto;
        border: solid $primary;
        padding: 1;
    }

    PhaseList PhaseListItem {
        margin: 0 1;
    }

    PhaseList .in_progress {
        color: $warning;
        text-style: bold;
    }

    PhaseList .completed {
        color: $success;
    }

    PhaseList .failed {
        color: $error;
    }

    PhaseList .pending {
        color: $text-muted;
    }

    PhaseList .skipped {
        color: $text-disabled;
    }
    """

    # Phase names from research framework
    PHASE_NAMES = {
        1: "Experimental Design",
        2: "Prompt Engineering",
        3: "Image Generation",
        4: "VQA Analysis",
        5: "Statistical Analysis",
        6: "Counterfactual Testing",
        7: "Human Validation",
        8: "Documentation (MLflow)",
        9: "Ethical Review",
        10: "Reporting"
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.phase_items: Dict[int, PhaseListItem] = {}

    def compose(self) -> ComposeResult:
        """Compose the phase list."""
        for phase_num in range(1, 11):
            name = self.PHASE_NAMES[phase_num]
            item = PhaseListItem(phase_num, name, status="pending", classes="pending")
            self.phase_items[phase_num] = item
            yield item

    def update_phase_status(self, phase_num: int, status: str) -> None:
        """
        Update the status of a specific phase.

        Args:
            phase_num: Phase number (1-10)
            status: New status (pending, in_progress, completed, failed, skipped)
        """
        if phase_num in self.phase_items:
            item = self.phase_items[phase_num]
            item.update_status(status)
            # Update styling
            item.remove_class("pending", "in_progress", "completed", "failed", "skipped")
            item.add_class(status)

    def reset(self) -> None:
        """Reset all phases to pending status."""
        for phase_num in range(1, 11):
            self.update_phase_status(phase_num, "pending")
