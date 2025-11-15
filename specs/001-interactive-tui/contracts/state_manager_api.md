# State Manager Public API Contract

**Version**: 1.0.0
**Date**: 2025-11-15
**Module**: `bias_detector.tui.state.manager`

## Overview

The `StateManager` class provides the central interface for managing experiment session state, coordinating between the TUI, background experiments, and persistent storage. This contract defines the public API that TUI components depend on.

---

## Class: StateManager

### Initialization

```python
StateManager(sessions_dir: Path = Path("data/sessions"))
```

**Parameters**:
- `sessions_dir`: Directory containing session files and index (default: `data/sessions/`)

**Side Effects**:
- Creates `sessions_dir` if it doesn't exist
- Creates subdirectory `sessions/` for session files
- Loads or initializes `index.json`

---

## Session Management

### create_session()

Create a new experiment session.

```python
def create_session(self, config: Dict[str, Any]) -> ExperimentSession
```

**Parameters**:
- `config`: Complete experiment configuration dictionary

**Returns**: `ExperimentSession` object with status=pending

**Side Effects**:
- Generates unique session_id (format: `exp_YYYYMMDD_HHMMSS`)
- Writes session file to `sessions/{session_id}.json`
- Updates index
- Sets as active session

**Raises**:
- `ValueError` if another session is already running (violates single-active constraint)

**Example**:
```python
manager = StateManager()
session = manager.create_session(config)
# session.session_id = "exp_20251115_120430"
# session.status = "pending"
```

---

### get_active_session()

Get the currently active experiment session.

```python
def get_active_session(self) -> Optional[ExperimentSession]
```

**Returns**: `ExperimentSession` if one is active, `None` otherwise

**Active Definition**: Session with status in `["pending", "running", "paused"]`

**Example**:
```python
active = manager.get_active_session()
if active:
    print(f"Experiment {active.session_id} is {active.status}")
else:
    print("No active experiment")
```

---

### get_session()

Retrieve a specific session by ID.

```python
def get_session(self, session_id: str) -> ExperimentSession
```

**Parameters**:
- `session_id`: Unique session identifier

**Returns**: `ExperimentSession` object

**Raises**:
- `FileNotFoundError` if session doesn't exist

**Example**:
```python
session = manager.get_session("exp_20251115_120430")
```

---

### list_sessions()

List all experiment sessions.

```python
def list_sessions(
    self,
    limit: Optional[int] = None,
    offset: int = 0,
    status_filter: Optional[List[str]] = None
) -> List[SessionIndexEntry]
```

**Parameters**:
- `limit`: Maximum number of sessions to return (default: all)
- `offset`: Number of sessions to skip (for pagination)
- `status_filter`: List of statuses to include (e.g., `["completed", "failed"]`)

**Returns**: List of `SessionIndexEntry` objects, sorted by start_time descending (newest first)

**Example**:
```python
# Get 20 most recent sessions
recent = manager.list_sessions(limit=20)

# Get failed experiments only
failed = manager.list_sessions(status_filter=["failed"])

# Pagination: skip first 20, get next 20
page2 = manager.list_sessions(limit=20, offset=20)
```

---

### delete_session()

Delete an experiment session (manual cleanup per FR-023a).

```python
def delete_session(self, session_id: str) -> None
```

**Parameters**:
- `session_id`: Session to delete

**Side Effects**:
- Removes session file from `sessions/` directory
- Updates index
- If this was the active session, clears active session link

**Raises**:
- `ValueError` if trying to delete a running session
- `FileNotFoundError` if session doesn't exist

**Example**:
```python
manager.delete_session("exp_20251113_162245")
```

---

## State Updates

### update_session_status()

Update the status of an experiment session.

```python
def update_session_status(
    self,
    session_id: str,
    new_status: str,
    error: Optional[ErrorInfo] = None
) -> None
```

**Parameters**:
- `session_id`: Session to update
- `new_status`: New status value (must be valid SessionStatus enum)
- `error`: Error details if status is "failed"

**Side Effects**:
- Updates session file
- Updates index entry
- If status is terminal (completed/failed/cancelled), sets end_time

**Validation**:
- Enforces valid state transitions (e.g., can't go from "completed" to "running")
- Requires error parameter if new_status is "failed"

**Example**:
```python
manager.update_session_status("exp_20251115_120430", "running")
manager.update_session_status(
    "exp_20251115_120430",
    "failed",
    error=ErrorInfo(...)
)
```

---

### update_phase_progress()

Update progress for a specific phase within a session.

```python
def update_phase_progress(
    self,
    session_id: str,
    phase_num: int,
    status: Optional[str] = None,
    items_done: Optional[int] = None,
    error_message: Optional[str] = None
) -> None
```

**Parameters**:
- `session_id`: Session to update
- `phase_num`: Phase number (1-10)
- `status`: New phase status (if changing)
- `items_done`: Updated items completed (if progressing)
- `error_message`: Error details (if phase failed)

**Side Effects**:
- Updates session file (atomic write)
- Updates session.current_phase if phase status changed to "in_progress"

**Example**:
```python
# Mark phase 3 as in progress
manager.update_phase_progress("exp_20251115_120430", 3, status="in_progress")

# Update progress within phase 3
manager.update_phase_progress("exp_20251115_120430", 3, items_done=25)

# Mark phase 3 complete
manager.update_phase_progress("exp_20251115_120430", 3, status="completed")
```

---

## Configuration Management

### get_config_state()

Get the current configuration state including lock status.

```python
def get_config_state(self, config_path: Path) -> ConfigurationState
```

**Parameters**:
- `config_path`: Path to YAML configuration file

**Returns**: `ConfigurationState` object with lock status and validation

**Example**:
```python
config_state = manager.get_config_state(Path("config/experiment_config.yaml"))
if config_state.locked:
    print(f"Config locked by {config_state.locked_by_session}")
```

---

### is_config_locked()

Check if configuration is currently locked.

```python
def is_config_locked(self, config_path: Path) -> bool
```

**Parameters**:
- `config_path`: Path to YAML configuration file

**Returns**: `True` if locked by active experiment, `False` otherwise

**Example**:
```python
if manager.is_config_locked(config_path):
    print("Cannot modify config - experiment is running")
```

---

### lock_config()

Lock configuration for exclusive use by an experiment.

```python
def lock_config(
    self,
    config_path: Path,
    session_id: str
) -> None
```

**Parameters**:
- `config_path`: Path to YAML configuration file
- `session_id`: Session that is locking the config

**Side Effects**:
- Creates file lock using fcntl (POSIX) or lock file (Windows)
- Stores lock ownership in ConfigurationState

**Raises**:
- `RuntimeError` if config is already locked by another session

**Example**:
```python
manager.lock_config(config_path, "exp_20251115_120430")
```

---

### unlock_config()

Unlock configuration.

```python
def unlock_config(
    self,
    config_path: Path,
    session_id: str
) -> None
```

**Parameters**:
- `config_path`: Path to YAML configuration file
- `session_id`: Session that owns the lock (must match)

**Side Effects**:
- Releases file lock
- Clears lock ownership

**Raises**:
- `ValueError` if session_id doesn't match lock owner

**Example**:
```python
manager.unlock_config(config_path, "exp_20251115_120430")
```

---

## Metrics & Monitoring

### get_progress_metrics()

Compute real-time progress metrics for a session.

```python
def get_progress_metrics(
    self,
    session_id: str
) -> ProgressMetrics
```

**Parameters**:
- `session_id`: Session to compute metrics for

**Returns**: `ProgressMetrics` object with computed values

**Computation**: See [data-model.md](data-model.md) for formulas

**Example**:
```python
metrics = manager.get_progress_metrics("exp_20251115_120430")
print(f"Overall progress: {metrics.overall_progress_pct:.1f}%")
print(f"ETA: {metrics.estimated_remaining_sec}s")
```

---

### rebuild_index()

Rebuild the session index from scratch.

```python
def rebuild_index(self) -> int
```

**Returns**: Number of sessions indexed

**Side Effects**:
- Scans all files in `sessions/` directory
- Rebuilds `index.json` with current metadata
- Useful after manual file modifications

**Example**:
```python
num_sessions = manager.rebuild_index()
print(f"Indexed {num_sessions} sessions")
```

---

## Error Handling

### Exceptions

All methods follow these error conventions:

- **ValueError**: Invalid input (wrong type, out of range, violates constraint)
- **FileNotFoundError**: Session or config file doesn't exist
- **RuntimeError**: System-level error (file lock, permissions, corrupted state)
- **PermissionError**: Insufficient file system permissions

### Atomic Operations

All state-modifying operations are atomic:
- Session file updates use temporary file + atomic rename
- Index updates write to temp file first
- Lock operations are OS-level atomic primitives

---

## Thread Safety

`StateManager` is **not** thread-safe. The TUI runs in a single async event loop, so only one StateManager operation executes at a time.

For background experiments updating state:
- Experiment writes session state directly to file (atomic)
- StateManager detects changes via file modification time
- No shared memory between TUI and experiment processes

---

## Performance Characteristics

| Operation | Time Complexity | Notes |
|-----------|----------------|-------|
| `create_session()` | O(1) | Single file write + index append |
| `get_session()` | O(1) | Single file read |
| `get_active_session()` | O(1) | Symlink read or index scan (max 1 active) |
| `list_sessions()` | O(1) | Index already in memory |
| `update_session_status()` | O(1) | Single file write + index update |
| `update_phase_progress()` | O(1) | Single file write |
| `rebuild_index()` | O(n) | n = total sessions |

Target performance:
- Session create/update: <10ms
- Index operations: <1ms
- Rebuild index (1000 sessions): <1s

---

## Example Usage

### Complete Experiment Lifecycle

```python
from bias_detector.tui.state.manager import StateManager
from pathlib import Path

manager = StateManager()

# 1. Create new session
config = load_config("config/experiment_config.yaml")
session = manager.create_session(config)
print(f"Created session: {session.session_id}")

# 2. Check if config is available
if manager.is_config_locked(Path("config/experiment_config.yaml")):
    raise RuntimeError("Config is locked")

# 3. Lock config and start experiment
manager.lock_config(Path("config/experiment_config.yaml"), session.session_id)
manager.update_session_status(session.session_id, "running")

# 4. Monitor progress (in TUI event loop)
while True:
    current_session = manager.get_session(session.session_id)
    if current_session.status in ["completed", "failed", "cancelled"]:
        break

    metrics = manager.get_progress_metrics(session.session_id)
    print(f"Progress: {metrics.overall_progress_pct:.1f}%")
    await asyncio.sleep(0.5)

# 5. Cleanup
manager.unlock_config(Path("config/experiment_config.yaml"), session.session_id)

# 6. Later: manual cleanup
old_sessions = manager.list_sessions(status_filter=["failed"])
for entry in old_sessions[:10]:  # Delete oldest 10 failed
    manager.delete_session(entry.session_id)
```

---

## Contract Tests

Implementations must pass these contract tests:

1. **Single Active Session**: Creating session when one is running raises ValueError
2. **Atomic Updates**: Concurrent reads during write never see partial state
3. **Lock Enforcement**: Cannot lock already-locked config
4. **State Transitions**: Invalid transitions raise ValueError
5. **Index Consistency**: list_sessions() always matches actual files
6. **Performance**: All O(1) operations complete in <10ms

---

**Approval**: Ready for implementation
**Next**: Implement in `src/bias_detector/tui/state/manager.py`
