"""
Progress Callback Interface and Implementation.

Defines the contract for experiment progress callbacks and provides
a queue-based implementation for async UI updates.

Contract Version: 1.0.0
Date: 2025-11-15
"""

from typing import Protocol, Optional, Dict, Any
from enum import Enum
from queue import Queue


class PhaseEvent(Enum):
    """Types of phase lifecycle events."""
    PHASE_START = "phase_start"
    PHASE_PROGRESS = "phase_progress"
    PHASE_COMPLETE = "phase_complete"
    PHASE_ERROR = "phase_error"
    EXPERIMENT_START = "experiment_start"
    EXPERIMENT_COMPLETE = "experiment_complete"
    EXPERIMENT_ERROR = "experiment_error"


class ProgressCallback(Protocol):
    """
    Protocol defining the contract for experiment progress callbacks.

    Implementations must be thread-safe as they may be called from background threads.
    All methods are fire-and-forget (no return value expected).
    """

    def on_experiment_start(
        self,
        session_id: str,
        config: Dict[str, Any],
        total_phases: int
    ) -> None:
        """
        Called when experiment begins.

        Args:
            session_id: Unique identifier for this experiment run
            config: Complete configuration dictionary (snapshot)
            total_phases: Total number of phases to execute
        """
        ...

    def on_phase_start(
        self,
        phase_num: int,
        phase_name: str,
        items_total: int
    ) -> None:
        """
        Called when a new phase begins execution.

        Args:
            phase_num: Phase number (1-10)
            phase_name: Human-readable phase name (e.g., "Image Generation")
            items_total: Total items to process in this phase (0 if not applicable)
        """
        ...

    def on_progress(
        self,
        phase_num: int,
        items_done: int,
        items_total: int,
        message: Optional[str] = None
    ) -> None:
        """
        Called periodically during phase execution to report progress.

        This may be called very frequently (e.g., after each image generation).
        Implementations should debounce updates if displaying to UI.

        Args:
            phase_num: Current phase number
            items_done: Number of items completed so far
            items_total: Total items in this phase
            message: Optional status message (e.g., "Generating image 23/50")
        """
        ...

    def on_phase_complete(
        self,
        phase_num: int,
        items_done: int,
        elapsed_seconds: float
    ) -> None:
        """
        Called when a phase completes successfully.

        Args:
            phase_num: Completed phase number
            items_done: Total items processed
            elapsed_seconds: Time taken to complete this phase
        """
        ...

    def on_phase_error(
        self,
        phase_num: int,
        error_type: str,
        error_message: str,
        traceback_str: Optional[str] = None
    ) -> None:
        """
        Called when a phase fails with an error.

        Args:
            phase_num: Phase number where error occurred
            error_type: Exception class name (e.g., "DiskFullError")
            error_message: Human-readable error description
            traceback_str: Optional full Python traceback
        """
        ...

    def on_experiment_complete(
        self,
        session_id: str,
        total_time_seconds: float,
        phases_completed: int
    ) -> None:
        """
        Called when experiment completes successfully.

        Args:
            session_id: Experiment identifier
            total_time_seconds: Total elapsed time
            phases_completed: Number of phases that completed successfully
        """
        ...

    def on_experiment_error(
        self,
        session_id: str,
        error_type: str,
        error_message: str,
        failed_phase: int
    ) -> None:
        """
        Called when experiment fails.

        Args:
            session_id: Experiment identifier
            error_type: Exception class name
            error_message: Human-readable error description
            failed_phase: Phase number where experiment failed
        """
        ...


class QueueProgressCallback:
    """
    Queue-based progress callback implementation for async UI updates.

    Pushes progress events to a thread-safe queue that can be polled
    by the async TUI event loop.
    """

    def __init__(self, event_queue: Queue):
        """
        Initialize callback with event queue.

        Args:
            event_queue: Thread-safe queue for progress events
        """
        self.queue = event_queue

    def on_experiment_start(
        self,
        session_id: str,
        config: Dict[str, Any],
        total_phases: int
    ) -> None:
        """Push experiment start event to queue."""
        self.queue.put({
            "event": PhaseEvent.EXPERIMENT_START,
            "session_id": session_id,
            "config": config,
            "total_phases": total_phases
        })

    def on_phase_start(
        self,
        phase_num: int,
        phase_name: str,
        items_total: int
    ) -> None:
        """Push phase start event to queue."""
        self.queue.put({
            "event": PhaseEvent.PHASE_START,
            "phase_num": phase_num,
            "phase_name": phase_name,
            "items_total": items_total
        })

    def on_progress(
        self,
        phase_num: int,
        items_done: int,
        items_total: int,
        message: Optional[str] = None
    ) -> None:
        """Push progress event to queue."""
        self.queue.put({
            "event": PhaseEvent.PHASE_PROGRESS,
            "phase_num": phase_num,
            "items_done": items_done,
            "items_total": items_total,
            "message": message
        })

    def on_phase_complete(
        self,
        phase_num: int,
        items_done: int,
        elapsed_seconds: float
    ) -> None:
        """Push phase complete event to queue."""
        self.queue.put({
            "event": PhaseEvent.PHASE_COMPLETE,
            "phase_num": phase_num,
            "items_done": items_done,
            "elapsed_seconds": elapsed_seconds
        })

    def on_phase_error(
        self,
        phase_num: int,
        error_type: str,
        error_message: str,
        traceback_str: Optional[str] = None
    ) -> None:
        """Push phase error event to queue."""
        self.queue.put({
            "event": PhaseEvent.PHASE_ERROR,
            "phase_num": phase_num,
            "error_type": error_type,
            "error_message": error_message,
            "traceback": traceback_str
        })

    def on_experiment_complete(
        self,
        session_id: str,
        total_time_seconds: float,
        phases_completed: int
    ) -> None:
        """Push experiment complete event to queue."""
        self.queue.put({
            "event": PhaseEvent.EXPERIMENT_COMPLETE,
            "session_id": session_id,
            "total_time_seconds": total_time_seconds,
            "phases_completed": phases_completed
        })

    def on_experiment_error(
        self,
        session_id: str,
        error_type: str,
        error_message: str,
        failed_phase: int
    ) -> None:
        """Push experiment error event to queue."""
        self.queue.put({
            "event": PhaseEvent.EXPERIMENT_ERROR,
            "session_id": session_id,
            "error_type": error_type,
            "error_message": error_message,
            "failed_phase": failed_phase
        })
