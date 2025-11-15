# Research & Architecture Decisions
## Interactive TUI for Experiment Monitoring

**Date**: 2025-11-15 | **Feature**: `001-interactive-tui`

## Overview

This document captures architectural research and decisions for integrating a Textual-based TUI with the existing bias detection framework. The key challenges are:
1. Managing state between UI and background experiments
2. Persisting session data for reconnection
3. Integrating async UI with synchronous experiment code
4. Providing real-time progress updates without blocking

---

## Decision 1: State Management Architecture

### Context
The TUI must track experiment state (active, paused, completed) and persist it across TUI restarts while the experiment continues running in the background.

### Options Considered

**Option A: In-Memory State Only**
- State lives in TUI process only
- Lost on TUI closure
- Simple but violates FR-021 (session persistence)

**Option B: Shared Memory (multiprocessing)**
- Use multiprocessing.Manager for shared state
- Real-time synchronization
- Complex, OS-dependent, fragile

**Option C: File-Based State with Polling**
- JSON files in `data/sessions/`
- TUI polls for changes
- Experiment writes state after each phase
- Simple, portable, atomic

### Decision: **Option C - File-Based State with Polling**

**Rationale**:
- Meets persistence requirement (FR-021, FR-022)
- Atomic file writes prevent corruption
- Platform-independent (works on macOS/Linux)
- Easy to debug (human-readable JSON)
- Aligns with existing file-based approach (YAML configs, MLflow SQLite)

**Implementation**:
```python
# State file structure
data/sessions/
├── active_experiment.json      # Symlink to current active session
└── sessions/
    ├── exp_20251115_120430.json
    └── exp_20251115_153022.json
```

**Alternatives Rejected**:
- SQLite would add dependency and complexity for minimal benefit
- Redis/external store overkill for single-user desktop app
- Pickle format not human-readable, security concerns

---

## Decision 2: Progress Callback Architecture

### Context
The experiment orchestrator (`BiasDetectionExperiment`) needs to emit progress events for the TUI to consume, but the experiment runs synchronously while Textual requires async updates.

### Options Considered

**Option A: Direct Observer Pattern**
- Experiment holds reference to UI observers
- Tight coupling between experiment and TUI
- Violates separation of concerns

**Option B: Event Queue (queue.Queue)**
- Experiment pushes to thread-safe queue
- TUI polls queue in async loop
- Decoupled but requires queue management

**Option C: Callback Protocol + File Events**
- Experiment accepts optional callback interface
- Callback writes to state file
- TUI detects file changes and updates
- Fully decoupled, works across processes

### Decision: **Option B - Event Queue with Protocol**

**Rationale**:
- Clean separation: experiment doesn't know about TUI
- Type-safe callback protocol for testing
- Queue is Python standard library, well-understood
- Async TUI can poll queue without blocking

**Implementation**:
```python
from typing import Protocol
from queue import Queue

class ProgressCallback(Protocol):
    def on_phase_start(self, phase_num: int, phase_name: str) -> None: ...
    def on_progress(self, items_done: int, items_total: int) -> None: ...
    def on_phase_complete(self, phase_num: int) -> None: ...
    def on_error(self, phase_num: int, error: str) -> None: ...

# Experiment usage:
experiment = BiasDetectionExperiment(config, callback=my_callback)
```

**Alternatives Rejected**:
- asyncio.Queue would require making experiment async (breaking change)
- Signal/slots (Qt-style) adds framework dependency
- File-polling alone too slow for real-time updates (1s requirement)

---

## Decision 3: Session Persistence Format

### Context
Experiment sessions must persist state to disk for reconnection after TUI restart.

### Options Considered

**Option A: Pickle**
- Native Python serialization
- Easy to use
- Binary, not human-readable, security risks

**Option B: SQLite**
- Structured query capability
- Overkill for simple key-value storage
- Adds query complexity

**Option C: JSON**
- Human-readable
- Standard library support
- Easy to debug and version

### Decision: **Option C - JSON**

**Rationale**:
- Human-readable for debugging
- Version-controlled easily (can track schema changes)
- Standard library (no dependencies)
- Sufficient for session data size (<1MB)
- Consistent with MLflow artifact storage

**Schema**:
```json
{
  "session_id": "exp_20251115_120430",
  "start_time": "2025-11-15T12:04:30Z",
  "status": "running|paused|completed|failed",
  "current_phase": 3,
  "config_snapshot": {...},
  "phase_progress": [
    {"phase": 1, "status": "completed", "items_done": 1, "items_total": 1},
    {"phase": 2, "status": "completed", "items_done": 8, "items_total": 8},
    {"phase": 3, "status": "in_progress", "items_done": 23, "items_total": 50}
  ],
  "error": null
}
```

**Write Strategy**: Atomic writes using `tempfile` + `os.replace()` to prevent corruption.

**Alternatives Rejected**:
- YAML slower to parse, less standard for data
- MessagePack faster but less debuggable
- Protocol Buffers overkill, requires schema compilation

---

## Decision 4: Textual Screen Navigation Pattern

### Context
The TUI has 4 primary views (Progress, Metadata, Configuration, History). Users need intuitive navigation.

### Options Considered

**Option A: Tab-Based Navigation**
- Tabs at top like browser
- Simple but uses vertical space
- Standard pattern

**Option B: Sidebar Navigation**
- Menu on left side
- More space for content
- Common in TUIs (htop, lazygit)

**Option C: Modal Screens (Push/Pop)**
- Each view is full-screen modal
- Keyboard shortcuts to switch (F1, F2, etc.)
- Maximum content space

### Decision: **Option C - Modal Screens with Footer Navigation**

**Rationale**:
- Maximizes content space for progress visualization
- Standard TUI pattern (e.g., midnight commander, htop)
- Keyboard-first navigation aligns with terminal usage
- Footer shows available keys at all times

**Navigation Keys**:
- `F1`: Progress (default view)
- `F2`: Metadata
- `F3`: Configuration
- `F4`: History
- `q`: Quit
- `h`: Help overlay

**Alternatives Rejected**:
- Tabs waste vertical space on small terminals
- Sidebar reduces horizontal space for wide content (prompt lists)

---

## Decision 5: Concurrent Execution Pattern

### Context
The TUI must run async (Textual requirement) while the experiment runs sync (CPU-bound image generation/VQA).

### Options Considered

**Option A: Make Experiment Async**
- Refactor entire experiment to async/await
- Breaking change to existing CLI
- Not beneficial (CPU-bound work)

**Option B: Thread Pool**
- Run experiment in thread
- TUI polls progress queue
- Compatible with sync code

**Option C: Subprocess**
- Run experiment as separate process
- Complete isolation
- IPC complexity

### Decision: **Option B - Thread Pool with Queue**

**Rationale**:
- No breaking changes to existing experiment code
- Thread-safe queue for progress updates
- Async TUI can poll queue in event loop
- Simpler than subprocess IPC

**Implementation**:
```python
from concurrent.futures import ThreadPoolExecutor
import asyncio

class TUIApp(App):
    def __init__(self):
        self.progress_queue = Queue()
        self.executor = ThreadPoolExecutor(max_workers=1)

    async def run_experiment(self, config):
        # Run sync experiment in thread
        future = self.executor.submit(
            run_experiment_with_callback,
            config,
            QueueCallback(self.progress_queue)
        )

        # Poll queue in async loop
        while not future.done():
            try:
                event = self.progress_queue.get_nowait()
                await self.handle_progress(event)
            except queue.Empty:
                await asyncio.sleep(0.1)
```

**Alternatives Rejected**:
- asyncio.to_thread() requires async refactor of experiment
- Subprocess adds IPC overhead and complexity
- Green threads (gevent) incompatible with Textual's async model

---

## Decision 6: Configuration Locking Mechanism

### Context
Configuration must be read-only while experiment is running (FR-009a) to prevent inconsistent state.

### Options Considered

**Option A: In-Memory Flag**
- TUI checks flag before allowing edits
- Lost if TUI restarts during experiment
- Race condition if multiple TUI instances

**Option B: File Lock**
- `fcntl.flock()` on config file
- OS-level mutual exclusion
- Portable (macOS/Linux)

**Option C: Lock File**
- Create `.lock` file when experiment starts
- Check for existence before edits
- Manual cleanup required

### Decision: **Option B - File Lock (with fallback)**

**Rationale**:
- OS-level guarantee of mutual exclusion
- Automatic cleanup on process exit
- Standard POSIX mechanism

**Implementation**:
```python
import fcntl

class ConfigLock:
    def __init__(self, config_path):
        self.lock_file = config_path + ".lock"

    def acquire(self):
        self.fd = open(self.lock_file, 'w')
        fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def release(self):
        fcntl.flock(self.fd, fcntl.LOCK_UN)
        self.fd.close()
```

**Fallback**: For Windows compatibility (future), fall back to lock file if `fcntl` unavailable.

**Alternatives Rejected**:
- Database-level locking overkill for YAML file
- Advisory locks too easy to bypass accidentally

---

## Decision 7: Experiment History Storage

### Context
Unlimited experiment history (FR-023) with manual cleanup (FR-023a) requires efficient retrieval and display.

### Options Considered

**Option A: Flat File per Experiment**
- Each experiment = one JSON file
- Simple, no indexing needed
- Slow to list all experiments

**Option B: Single Append-Only Log**
- All experiments in one file
- Fast append
- Slow to read partial data

**Option C: Directory with Index File**
- Sessions in `data/sessions/sessions/*.json`
- Index file `data/sessions/index.json` with metadata
- Fast listing, lazy loading

### Decision: **Option C - Directory with Index**

**Rationale**:
- Fast startup (load index only, ~1KB per 100 experiments)
- Lazy load full session details on demand
- Easy to delete individual experiments (remove file + index entry)
- Efficient for filtering/searching

**Index Schema**:
```json
{
  "experiments": [
    {
      "session_id": "exp_20251115_120430",
      "start_time": "2025-11-15T12:04:30Z",
      "status": "completed",
      "config_name": "baseline_10images",
      "total_images": 80
    }
  ]
}
```

**Pagination**: Load index, display 20 at a time, load session details on selection.

**Alternatives Rejected**:
- SQLite adds dependency for marginal benefit
- Single log file requires full parse for filtering
- Flat files slow for large histories (>1000 experiments)

---

## Technical Debt & Future Considerations

### Known Limitations

1. **Thread Safety**: Progress queue assumes single experiment at a time. If FR-013 changed to allow concurrent experiments, would need separate queues.

2. **File I/O Performance**: Polling session files every 100ms. If performance degrades with large state, consider inotify (Linux) or FSEvents (macOS) for change detection.

3. **Windows Compatibility**: `fcntl` not available on Windows. Need to implement lock file fallback or use `msvcrt.locking()`.

### Potential Optimizations

- **State Compression**: If session files exceed 1MB, consider gzip compression
- **Index Caching**: Cache index in memory, only reload on file modification
- **Progress Batching**: Batch rapid progress updates (image generation) to reduce queue overhead

### Monitoring Metrics

- Session file write latency (should be <10ms)
- Queue depth (should be <100 items)
- UI frame rate (should be 30+ FPS)
- Memory usage (should be <50MB for TUI process)

---

## References

- Textual documentation: https://textual.textualize.io/
- Python asyncio + threading: https://docs.python.org/3/library/asyncio-task.html
- File locking best practices: https://docs.python.org/3/library/fcntl.html
- Atomic file writes: https://github.com/untitaker/python-atomicwrites

---

**Review Date**: 2025-11-15
**Reviewers**: Claude Code
**Status**: Approved for Phase 1 implementation
