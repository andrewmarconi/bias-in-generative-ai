"""
Experiment Session Data Models.

Defines session state structures for experiment tracking, progress monitoring,
and persistence across TUI restarts.

Data Model Version: 1.0.0
Date: 2025-11-15
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import json


class SessionStatus(Enum):
    """Experiment session lifecycle states."""
    PENDING = "pending"  # Created but not started
    RUNNING = "running"  # Actively executing
    PAUSED = "paused"  # Temporarily stopped (P4 feature)
    COMPLETED = "completed"  # Successfully finished all phases
    FAILED = "failed"  # Stopped due to error
    CANCELLED = "cancelled"  # User-terminated


class PhaseStatus(Enum):
    """Research phase execution states."""
    PENDING = "pending"  # Not yet started
    IN_PROGRESS = "in_progress"  # Currently executing
    COMPLETED = "completed"  # Successfully finished
    FAILED = "failed"  # Stopped due to error
    SKIPPED = "skipped"  # Bypassed (e.g., counterfactual disabled)


@dataclass
class PhaseProgress:
    """
    Progress tracking for a single research phase within an experiment.

    Attributes:
        phase: Phase number (1-10)
        name: Human-readable phase name (e.g., "Image Generation")
        status: Current phase state
        items_done: Completed items (e.g., images generated)
        items_total: Total items to complete
        start_time: When phase started (None if not started)
        end_time: When phase ended (None if not complete)
        error_message: Error details if phase failed (None otherwise)
    """
    phase: int
    name: str
    status: PhaseStatus
    items_done: int
    items_total: int
    start_time: Optional[str] = None  # ISO 8601
    end_time: Optional[str] = None  # ISO 8601
    error_message: Optional[str] = None

    def __post_init__(self):
        """Validate phase progress state."""
        # Convert enum to string if needed (for JSON serialization)
        if isinstance(self.status, str):
            self.status = PhaseStatus(self.status)

        # Validation rules from data-model.md
        if self.items_done > self.items_total:
            raise ValueError(f"items_done ({self.items_done}) cannot exceed items_total ({self.items_total})")

        if self.status == PhaseStatus.IN_PROGRESS and self.start_time is None:
            raise ValueError("in_progress phase must have start_time set")

        if self.status in (PhaseStatus.COMPLETED, PhaseStatus.FAILED) and self.end_time is None:
            raise ValueError(f"{self.status.value} phase must have end_time set")

        if self.status == PhaseStatus.FAILED and not self.error_message:
            raise ValueError("failed phase must have error_message set")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PhaseProgress':
        """Create from dictionary (JSON deserialization)."""
        data = data.copy()
        data['status'] = PhaseStatus(data['status'])
        return cls(**data)


@dataclass
class ErrorInfo:
    """
    Detailed error information when experiments or phases fail.

    Attributes:
        error_type: Exception class name (e.g., "DiskFullError")
        error_message: Human-readable error description
        phase: Phase number where error occurred (1-10)
        timestamp: When error occurred (ISO 8601)
        traceback: Full Python traceback (truncated to 2000 chars)
        remediation_hint: Suggested fix if known
    """
    error_type: str
    error_message: str
    phase: int
    timestamp: str  # ISO 8601
    traceback: Optional[str] = None
    remediation_hint: Optional[str] = None

    def __post_init__(self):
        """Truncate traceback if too long."""
        if self.traceback and len(self.traceback) > 2000:
            self.traceback = self.traceback[:2000] + "\n... (truncated)"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorInfo':
        """Create from dictionary (JSON deserialization)."""
        return cls(**data)


@dataclass
class SessionMetadata:
    """
    Additional tracking information for debugging and reproducibility.

    Attributes:
        pid: Process ID of experiment runner
        hostname: Machine hostname
        python_version: Python version (e.g., "3.12.0")
        platform: OS platform (e.g., "Darwin")
        textual_version: Textual library version
        mflux_version: mflux library version
    """
    pid: int
    hostname: str
    python_version: str
    platform: str
    textual_version: str
    mflux_version: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionMetadata':
        """Create from dictionary (JSON deserialization)."""
        return cls(**data)


@dataclass
class ExperimentSession:
    """
    Complete state of a bias detection experiment run.

    Tracks experiment lifecycle from start to completion and persists
    across TUI restarts.

    Attributes:
        session_id: Unique identifier (format: exp_YYYYMMDD_HHMMSS)
        start_time: Experiment start timestamp (ISO 8601)
        status: Current lifecycle state
        current_phase: Active phase number (1-10)
        config_snapshot: Complete config at experiment start (immutable)
        phase_progress: Progress for each of 10 phases
        metadata: Environment and versioning metadata
        end_time: Experiment end timestamp (None if not complete)
        error: Error details if status == failed (None otherwise)
    """
    session_id: str
    start_time: str  # ISO 8601
    status: SessionStatus
    current_phase: int
    config_snapshot: Dict[str, Any]
    phase_progress: List[PhaseProgress]
    metadata: SessionMetadata
    end_time: Optional[str] = None  # ISO 8601
    error: Optional[ErrorInfo] = None

    def __post_init__(self):
        """Validate experiment session state."""
        # Convert enum to string if needed (for JSON serialization)
        if isinstance(self.status, str):
            self.status = SessionStatus(self.status)

        # Convert nested objects if needed
        if self.phase_progress and isinstance(self.phase_progress[0], dict):
            self.phase_progress = [PhaseProgress.from_dict(p) for p in self.phase_progress]

        if self.metadata and isinstance(self.metadata, dict):
            self.metadata = SessionMetadata.from_dict(self.metadata)

        if self.error and isinstance(self.error, dict):
            self.error = ErrorInfo.from_dict(self.error)

        # Invariants from data-model.md
        if not (1 <= self.current_phase <= 10):
            raise ValueError(f"current_phase must be 1-10, got {self.current_phase}")

        if self.status == SessionStatus.FAILED and self.error is None:
            raise ValueError("failed session must have error set")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status.value,
            "current_phase": self.current_phase,
            "config_snapshot": self.config_snapshot,
            "phase_progress": [p.to_dict() for p in self.phase_progress],
            "error": self.error.to_dict() if self.error else None,
            "metadata": self.metadata.to_dict()
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExperimentSession':
        """Create from dictionary (JSON deserialization)."""
        data = data.copy()
        data['status'] = SessionStatus(data['status'])
        data['phase_progress'] = [PhaseProgress.from_dict(p) for p in data['phase_progress']]
        data['metadata'] = SessionMetadata.from_dict(data['metadata'])
        if data.get('error'):
            data['error'] = ErrorInfo.from_dict(data['error'])
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'ExperimentSession':
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


# Phase name mapping (from research framework)
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
