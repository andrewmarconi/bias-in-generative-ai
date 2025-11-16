"""
Callback protocol for progress reporting.
"""

from typing import Protocol, Any, Optional
from datetime import datetime


class ProgressCallback(Protocol):
    """Protocol for progress reporting callbacks."""

    def on_experiment_start(
        self,
        session_id: str,
        config: dict,
        total_phases: int
    ) -> None:
        """Called when experiment starts."""
        ...

    def on_experiment_complete(
        self,
        session_id: str,
        total_time_seconds: float,
        phases_completed: int
    ) -> None:
        """Called when experiment completes."""
        ...

    def on_experiment_error(
        self,
        session_id: str,
        error_type: str,
        error_message: str,
        failed_phase: int
    ) -> None:
        """Called when experiment fails."""
        ...

    def on_phase_start(
        self,
        phase_num: int,
        phase_name: str,
        items_total: int
    ) -> None:
        """Called when a phase starts."""
        ...

    def on_phase_complete(
        self,
        phase_num: int,
        items_done: int,
        duration_seconds: float
    ) -> None:
        """Called when a phase completes."""
        ...

    def on_phase_error(
        self,
        phase_num: int,
        error_type: str,
        error_message: str,
        traceback_str: Optional[str]
    ) -> None:
        """Called when a phase fails."""
        ...