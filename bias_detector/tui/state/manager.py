"""
State Manager for Experiment Session Persistence.

Manages experiment session lifecycle, persistence, and configuration locking.
Provides atomic file operations and thread-safe state management.

Version: 1.0.0
Date: 2025-11-15
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import os
import tempfile
import socket
import sys
import platform

try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

from .session import (
    ExperimentSession,
    PhaseProgress,
    SessionStatus,
    PhaseStatus,
    SessionMetadata,
    ErrorInfo,
    PHASE_NAMES
)


class SessionIndexEntry:
    """Index entry for fast session lookup."""

    def __init__(
        self,
        session_id: str,
        start_time: str,
        status: str,
        config_name: str,
        total_images: int,
        phases_completed: int
    ):
        self.session_id = session_id
        self.start_time = start_time
        self.status = status
        self.config_name = config_name
        self.total_images = total_images
        self.phases_completed = phases_completed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "status": self.status,
            "config_name": self.config_name,
            "total_images": self.total_images,
            "phases_completed": self.phases_completed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionIndexEntry':
        return cls(**data)


class StateManager:
    """
    Central state management for experiment sessions.

    Handles session creation, persistence, updates, and configuration locking.
    All file operations are atomic to prevent corruption.
    """

    def __init__(self, sessions_dir: Path = Path("data/sessions")):
        """
        Initialize StateManager.

        Args:
            sessions_dir: Directory for session storage (default: data/sessions/)

        Side effects:
            - Creates sessions_dir if it doesn't exist
            - Creates sessions/ subdirectory
            - Loads or initializes index.json
        """
        self.sessions_dir = Path(sessions_dir)
        self.sessions_subdir = self.sessions_dir
        self.index_path = self.sessions_dir / "index.json"
        self.active_link_path = self.sessions_dir / "active_experiment.json"

        # Create directories
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_subdir.mkdir(exist_ok=True)

        # Load or initialize index
        self._load_index()

        # Track config locks
        self._config_locks: Dict[Path, Any] = {}

    def _load_index(self):
        """Load session index from disk or initialize empty."""
        if self.index_path.exists() and self.index_path.stat().st_size > 0:
            try:
                with open(self.index_path, 'r') as f:
                    data = json.load(f)
                    self._index = {
                        "version": data.get("version", 1),
                        "last_updated": data.get("last_updated", datetime.now().isoformat()),
                        "experiments": [SessionIndexEntry.from_dict(e) for e in data.get("experiments", [])]
                    }
            except (json.JSONDecodeError, ValueError):
                # File is corrupted, initialize empty
                self._index = {
                    "version": 1,
                    "last_updated": datetime.now().isoformat(),
                    "experiments": []
                }
                self._save_index()
        else:
            self._index = {
                "version": 1,
                "last_updated": datetime.now().isoformat(),
                "experiments": []
            }
            self._save_index()

    def _save_index(self):
        """Atomically save index to disk."""
        data = {
            "version": self._index["version"],
            "last_updated": datetime.now().isoformat(),
            "experiments": [e.to_dict() for e in self._index["experiments"]]
        }

        # Atomic write using tempfile + rename
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=self.sessions_dir,
            delete=False,
            suffix='.tmp'
        ) as f:
            json.dump(data, f, indent=2)
            temp_path = f.name

        os.replace(temp_path, self.index_path)

    def create_session(self, config: Dict[str, Any]) -> ExperimentSession:
        """
        Create a new experiment session.

        Args:
            config: Complete experiment configuration dictionary

        Returns:
            ExperimentSession with status=pending

        Raises:
            ValueError: If another session is already running

        Side effects:
            - Generates unique session_id
            - Writes session file atomically
            - Updates index
            - Sets as active session
        """
        # Check for active sessions
        active = self.get_active_session()
        if active:
            raise ValueError(
                f"Cannot create session: experiment {active.session_id} is already {active.status.value}"
            )

        # Generate session ID
        session_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create metadata
        try:
            import textual
            textual_version = textual.__version__
        except:
            textual_version = "unknown"

        try:
            import mflux
            mflux_version = mflux.__version__
        except:
            mflux_version = "unknown"

        metadata = SessionMetadata(
            pid=os.getpid(),
            hostname=socket.gethostname(),
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            platform=platform.system(),
            textual_version=textual_version,
            mflux_version=mflux_version
        )

        # Initialize phase progress for all 10 phases
        phase_progress = []
        for phase_num in range(1, 11):
            phase_progress.append(PhaseProgress(
                phase=phase_num,
                name=PHASE_NAMES[phase_num],
                status=PhaseStatus.PENDING,
                items_done=0,
                items_total=0
            ))

        # Create session
        session = ExperimentSession(
            session_id=session_id,
            start_time=datetime.now().isoformat(),
            status=SessionStatus.PENDING,
            current_phase=1,
            config_snapshot=config,
            phase_progress=phase_progress,
            metadata=metadata
        )

        # Save session file
        self._save_session(session)

        # Update index
        index_entry = SessionIndexEntry(
            session_id=session_id,
            start_time=session.start_time,
            status=session.status.value,
            config_name="experiment_config.yaml",
            total_images=0,
            phases_completed=0
        )
        self._index["experiments"].insert(0, index_entry)
        self._save_index()

        # Set as active
        self._set_active_session(session_id)

        return session

    def get_session(self, session_id: str) -> ExperimentSession:
        """
        Retrieve a specific session by ID.

        Args:
            session_id: Unique session identifier

        Returns:
            ExperimentSession object

        Raises:
            FileNotFoundError: If session doesn't exist
        """
        session_path = self.sessions_subdir / f"{session_id}.json"
        if not session_path.exists():
            raise FileNotFoundError(f"Session {session_id} not found")

        with open(session_path, 'r') as f:
            data = json.load(f)
            return ExperimentSession.from_dict(data)

    def get_active_session(self) -> Optional[ExperimentSession]:
        """
        Get the currently active experiment session.

        Returns:
            ExperimentSession if one is active, None otherwise

        Active definition: Session with status in [pending, running, paused]
        """
        # Check for active link
        if self.active_link_path.exists():
            with open(self.active_link_path, 'r') as f:
                data = json.load(f)
                session_id = data.get("session_id")
                if session_id:
                    try:
                        session = self.get_session(session_id)
                        if session.status in (SessionStatus.PENDING, SessionStatus.RUNNING, SessionStatus.PAUSED):
                            return session
                    except FileNotFoundError:
                        pass

        # Fallback: scan index for active sessions
        for entry in self._index["experiments"]:
            if entry.status in ("pending", "running", "paused"):
                try:
                    return self.get_session(entry.session_id)
                except FileNotFoundError:
                    continue

        return None

    def list_sessions(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        status_filter: Optional[List[str]] = None
    ) -> List[SessionIndexEntry]:
        """
        List all experiment sessions.

        Args:
            limit: Maximum number to return (default: all)
            offset: Number to skip for pagination
            status_filter: List of statuses to include

        Returns:
            List of SessionIndexEntry sorted by start_time desc (newest first)
        """
        experiments = self._index["experiments"]

        # Filter by status
        if status_filter:
            experiments = [e for e in experiments if e.status in status_filter]

        # Apply pagination
        experiments = experiments[offset:]
        if limit:
            experiments = experiments[:limit]

        return experiments

    def delete_session(self, session_id: str) -> None:
        """
        Delete an experiment session.

        Args:
            session_id: Session to delete

        Raises:
            ValueError: If trying to delete a running session
            FileNotFoundError: If session doesn't exist

        Side effects:
            - Removes session file
            - Updates index
            - Clears active session link if this was active
        """
        session = self.get_session(session_id)

        # Prevent deletion of running sessions
        if session.status == SessionStatus.RUNNING:
            raise ValueError("Cannot delete a running session")

        # Remove session file
        session_path = self.sessions_subdir / f"{session_id}.json"
        session_path.unlink()

        # Update index
        self._index["experiments"] = [
            e for e in self._index["experiments"]
            if e.session_id != session_id
        ]
        self._save_index()

        # Clear active link if this was active
        if self.active_link_path.exists():
            with open(self.active_link_path, 'r') as f:
                data = json.load(f)
                if data.get("session_id") == session_id:
                    self.active_link_path.unlink()

    def update_session_status(
        self,
        session_id: str,
        new_status: str,
        error: Optional[ErrorInfo] = None
    ) -> None:
        """
        Update the status of an experiment session.

        Args:
            session_id: Session to update
            new_status: New status value
            error: Error details if status is "failed"

        Side effects:
            - Updates session file atomically
            - Updates index entry
            - Sets end_time if terminal status
        """
        session = self.get_session(session_id)

        # Validate status transition
        new_status_enum = SessionStatus(new_status)

        # Validate error requirement
        if new_status_enum == SessionStatus.FAILED and error is None:
            raise ValueError("Failed status requires error parameter")

        # Update session
        session.status = new_status_enum
        if error:
            session.error = error

        # Set end_time for terminal statuses
        if new_status_enum in (SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.CANCELLED):
            session.end_time = datetime.now().isoformat()

        # Save session
        self._save_session(session)

        # Update index
        for entry in self._index["experiments"]:
            if entry.session_id == session_id:
                entry.status = new_status
                break
        self._save_index()

    def update_phase_progress(
        self,
        session_id: str,
        phase_num: int,
        status: Optional[str] = None,
        items_done: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update progress for a specific phase.

        Args:
            session_id: Session to update
            phase_num: Phase number (1-10)
            status: New phase status (if changing)
            items_done: Updated items completed
            error_message: Error details (if phase failed)

        Side effects:
            - Updates session file atomically
            - Updates current_phase if status changed to in_progress
        """
        session = self.get_session(session_id)

        # Find phase
        phase = next((p for p in session.phase_progress if p.phase == phase_num), None)
        if not phase:
            raise ValueError(f"Phase {phase_num} not found in session")

        # Update status
        if status:
            new_status = PhaseStatus(status)
            phase.status = new_status

            if new_status == PhaseStatus.IN_PROGRESS:
                phase.start_time = datetime.now().isoformat()
                session.current_phase = phase_num
            elif new_status in (PhaseStatus.COMPLETED, PhaseStatus.FAILED):
                phase.end_time = datetime.now().isoformat()

        # Update items done
        if items_done is not None:
            phase.items_done = items_done

        # Update error message
        if error_message:
            phase.error_message = error_message

        # Save session
        self._save_session(session)

    def rebuild_index(self) -> int:
        """
        Rebuild session index from scratch.

        Returns:
            Number of sessions indexed

        Side effects:
            - Scans all session files
            - Rebuilds index.json
        """
        experiments = []

        for session_path in self.sessions_subdir.glob("*.json"):
            try:
                with open(session_path, 'r') as f:
                    data = json.load(f)
                    session = ExperimentSession.from_dict(data)

                    # Calculate total images
                    total_images = sum(
                        p.items_total for p in session.phase_progress
                        if p.phase == 3  # Image generation phase
                    )

                    # Count completed phases
                    phases_completed = sum(
                        1 for p in session.phase_progress
                        if p.status == PhaseStatus.COMPLETED
                    )

                    entry = SessionIndexEntry(
                        session_id=session.session_id,
                        start_time=session.start_time,
                        status=session.status.value,
                        config_name="experiment_config.yaml",
                        total_images=total_images,
                        phases_completed=phases_completed
                    )
                    experiments.append(entry)
            except Exception:
                continue

        # Sort by start_time descending
        experiments.sort(key=lambda e: e.start_time, reverse=True)

        self._index["experiments"] = experiments
        self._save_index()

        return len(experiments)

    def lock_config(self, config_path: Path, session_id: str) -> None:
        """
        Lock configuration for exclusive use by an experiment.

        Args:
            config_path: Path to YAML configuration file
            session_id: Session that is locking the config

        Raises:
            RuntimeError: If config is already locked by another session
        """
        config_path = Path(config_path)

        # Check if already locked
        if self.is_config_locked(config_path):
            lock_file_path = config_path.with_suffix(config_path.suffix + '.lock')
            if lock_file_path.exists():
                with open(lock_file_path, 'r') as f:
                    lock_data = json.load(f)
                    locked_by = lock_data.get("session_id")
                    if locked_by != session_id:
                        raise RuntimeError(f"Config already locked by session {locked_by}")

        # Create lock file
        lock_file_path = config_path.with_suffix(config_path.suffix + '.lock')
        lock_data = {
            "session_id": session_id,
            "locked_at": datetime.now().isoformat()
        }

        if HAS_FCNTL:
            # Use fcntl for POSIX systems
            lock_fd = open(lock_file_path, 'w')
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                json.dump(lock_data, lock_fd)
                self._config_locks[config_path] = lock_fd
            except BlockingIOError:
                lock_fd.close()
                raise RuntimeError("Config is locked by another process")
        else:
            # Fallback: lock file for Windows
            with open(lock_file_path, 'w') as f:
                json.dump(lock_data, f)

    def unlock_config(self, config_path: Path, session_id: str) -> None:
        """
        Unlock configuration.

        Args:
            config_path: Path to YAML configuration file
            session_id: Session that owns the lock (must match)

        Raises:
            ValueError: If session_id doesn't match lock owner
        """
        config_path = Path(config_path)
        lock_file_path = config_path.with_suffix(config_path.suffix + '.lock')

        if lock_file_path.exists():
            with open(lock_file_path, 'r') as f:
                lock_data = json.load(f)
                locked_by = lock_data.get("session_id")
                if locked_by != session_id:
                    raise ValueError(f"Lock owned by {locked_by}, not {session_id}")

            # Release lock
            if HAS_FCNTL and config_path in self._config_locks:
                fcntl.flock(self._config_locks[config_path], fcntl.LOCK_UN)
                self._config_locks[config_path].close()
                del self._config_locks[config_path]

            # Remove lock file
            lock_file_path.unlink()

    def is_config_locked(self, config_path: Path) -> bool:
        """
        Check if configuration is currently locked.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            True if locked by active experiment, False otherwise
        """
        config_path = Path(config_path)
        lock_file_path = config_path.with_suffix(config_path.suffix + '.lock')
        return lock_file_path.exists()

    def _save_session(self, session: ExperimentSession):
        """Atomically save session to disk."""
        session_path = self.sessions_subdir / f"{session.session_id}.json"

        # Atomic write using tempfile + rename
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=self.sessions_subdir,
            delete=False,
            suffix='.tmp'
        ) as f:
            f.write(session.to_json())
            temp_path = f.name

        os.replace(temp_path, session_path)

    def _set_active_session(self, session_id: str):
        """Mark a session as active."""
        active_data = {"session_id": session_id}

        # Atomic write
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=self.sessions_dir,
            delete=False,
            suffix='.tmp'
        ) as f:
            json.dump(active_data, f, indent=2)
            temp_path = f.name

        os.replace(temp_path, self.active_link_path)

    def get_config_state(self, config_path: str = "config/experiment_config.yaml"):
        """
        Load and validate experiment configuration.
        
        Args:
            config_path: Path to YAML configuration file
            
        Returns:
            Dictionary with configuration state and validation status
            
        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        # Import from utils module (sibling to tui)
        from ..utils.config import load_config, validate_config
        
        config_path_obj = Path(config_path)
        
        # Check if file exists
        if not config_path_obj.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Get file modification time
        last_modified = datetime.fromtimestamp(config_path_obj.stat().st_mtime)
        
        # Check if config is locked
        locked = self.is_config_locked(config_path_obj)
        locked_by_session = None
        
        if locked:
            lock_file_path = config_path_obj.with_suffix(config_path_obj.suffix + '.lock')
            if lock_file_path.exists():
                with open(lock_file_path, 'r') as f:
                    lock_data = json.load(f)
                    locked_by_session = lock_data.get("session_id")
        
        # Load and validate configuration
        try:
            config = load_config(config_path)
            validation_errors = []
            
            # Validate configuration
            try:
                validate_config(config)
                validation_status = "valid"
            except ValueError as e:
                validation_errors = [str(e)]
                validation_status = "invalid"
            
            return {
                "config_path": str(config_path_obj.absolute()),
                "locked": locked,
                "locked_by_session": locked_by_session,
                "last_modified": last_modified,
                "validation_status": validation_status,
                "validation_errors": validation_errors,
                "sections": config
            }
            
        except Exception as e:
            return {
                "config_path": str(config_path_obj.absolute()),
                "locked": locked,
                "locked_by_session": locked_by_session,
                "last_modified": last_modified,
                "validation_status": "invalid",
                "validation_errors": [f"Failed to load config: {str(e)}"],
                "sections": {}
            }
