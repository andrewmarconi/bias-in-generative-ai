# Data Model
## Interactive TUI for Experiment Monitoring

**Date**: 2025-11-15 | **Feature**: `001-interactive-tui`

## Overview

This document defines the data structures and entities used by the TUI to track experiment state, configuration, and progress. All entities are designed for JSON serialization to support file-based persistence.

---

## Entity Definitions

### 1. ExperimentSession

Represents a single execution of a bias detection experiment, including its current state and progress.

**Purpose**: Track experiment lifecycle from start to completion, persist across TUI restarts.

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | `string` | Yes | Unique identifier (format: `exp_YYYYMMDD_HHMMSS`) |
| `start_time` | `datetime` | Yes | Experiment start timestamp (ISO 8601) |
| `end_time` | `datetime` | No | Experiment end timestamp (null if not complete) |
| `status` | `SessionStatus` | Yes | Current state (see SessionStatus enum) |
| `current_phase` | `int` | Yes | Active phase number (1-10) |
| `config_snapshot` | `dict` | Yes | Complete config at experiment start (for reproducibility) |
| `phase_progress` | `List[PhaseProgress]` | Yes | Progress for each of 10 phases |
| `error` | `ErrorInfo` | No | Error details if status == failed (null otherwise) |
| `metadata` | `SessionMetadata` | Yes | Additional tracking info |

**Persistence**: `data/sessions/sessions/{session_id}.json`

**Lifecycle States** (SessionStatus enum):
- `pending`: Created but not started
- `running`: Actively executing
- `paused`: Temporarily stopped (P4 feature)
- `completed`: Successfully finished all phases
- `failed`: Stopped due to error
- `cancelled`: User-terminated

**Invariants**:
- Only one session can have status=running at a time (FR-016a)
- `current_phase` must be 1-10
- If status=failed, `error` must be non-null
- `config_snapshot` is immutable after experiment starts

**Example**:
```json
{
  "session_id": "exp_20251115_120430",
  "start_time": "2025-11-15T12:04:30Z",
  "end_time": null,
  "status": "running",
  "current_phase": 3,
  "config_snapshot": {
    "generation": {"model": "schnell", "num_images_per_prompt": 50},
    "prompts": {...}
  },
  "phase_progress": [
    {"phase": 1, "name": "Design", "status": "completed", ...},
    {"phase": 2, "name": "Prompts", "status": "completed", ...},
    {"phase": 3, "name": "Generation", "status": "in_progress", ...}
  ],
  "error": null,
  "metadata": {
    "pid": 12345,
    "hostname": "macbook.local",
    "python_version": "3.12.0"
  }
}
```

---

### 2. PhaseProgress

Tracks progress of a single research phase within an experiment.

**Purpose**: Granular progress tracking for each of the 10 research framework phases.

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phase` | `int` | Yes | Phase number (1-10) |
| `name` | `string` | Yes | Phase name (e.g., "Image Generation") |
| `status` | `PhaseStatus` | Yes | Current phase state |
| `items_done` | `int` | Yes | Completed items (e.g., images generated) |
| `items_total` | `int` | Yes | Total items to complete |
| `start_time` | `datetime` | No | When phase started (null if not started) |
| `end_time` | `datetime` | No | When phase ended (null if not complete) |
| `error_message` | `string` | No | Error details if phase failed |

**Phase Status Enum**:
- `pending`: Not yet started
- `in_progress`: Currently executing
- `completed`: Successfully finished
- `failed`: Stopped due to error
- `skipped`: Bypassed (e.g., counterfactual disabled)

**State Transitions**:
```
pending → in_progress → (completed | failed)
pending → skipped
```

**Validation Rules**:
- `items_done` must be <= `items_total`
- If status = in_progress, `start_time` must be set
- If status = completed or failed, `end_time` must be set
- If status = failed, `error_message` must be set

**Phase Mapping** (from research framework):
1. Experimental Design
2. Prompt Engineering
3. Image Generation
4. VQA Analysis
5. Statistical Analysis
6. Counterfactual Testing
7. Human Validation
8. Documentation (MLflow)
9. Ethical Review
10. Reporting

**Example**:
```json
{
  "phase": 3,
  "name": "Image Generation",
  "status": "in_progress",
  "items_done": 23,
  "items_total": 50,
  "start_time": "2025-11-15T12:05:15Z",
  "end_time": null,
  "error_message": null
}
```

---

### 3. ConfigurationState

Represents the current experiment configuration with validation status.

**Purpose**: Track config changes, provide validation, and enforce locking during active experiments.

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `config_path` | `string` | Yes | Path to YAML config file |
| `locked` | `bool` | Yes | True if experiment is running (read-only) |
| `locked_by_session` | `string` | No | Session ID that locked config (null if unlocked) |
| `last_modified` | `datetime` | Yes | Last config file modification time |
| `validation_status` | `ValidationStatus` | Yes | Config validity state |
| `validation_errors` | `List[string]` | Yes | Validation error messages (empty if valid) |
| `sections` | `dict` | Yes | Parsed config sections (generation, prompts, vqa, etc.) |

**Validation Status Enum**:
- `valid`: Passes all validation rules
- `invalid`: Has validation errors
- `unknown`: Not yet validated

**Validation Rules** (from config.py):
- Required sections present: generation, prompts, vqa_analysis, statistics
- Valid model names: dev, schnell, krea_dev
- num_images_per_prompt > 0
- Valid VQA model string
- All prompts non-empty

**Locking Behavior**:
- Locked automatically when experiment starts (FR-009a)
- Unlocked when experiment completes, fails, or is cancelled
- Lock persists across TUI restarts (checks session status)

**Example**:
```json
{
  "config_path": "/path/to/config/experiment_config.yaml",
  "locked": true,
  "locked_by_session": "exp_20251115_120430",
  "last_modified": "2025-11-15T11:58:22Z",
  "validation_status": "valid",
  "validation_errors": [],
  "sections": {
    "generation": {"model": "schnell", ...},
    "prompts": {...},
    "vqa_analysis": {...},
    "statistics": {...}
  }
}
```

---

### 4. ProgressMetrics

Real-time metrics for UI display, computed from PhaseProgress.

**Purpose**: Derived metrics for progress visualization, updated in real-time.

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `overall_progress_pct` | `float` | Yes | Overall completion % (0-100) |
| `current_phase_progress_pct` | `float` | Yes | Current phase completion % (0-100) |
| `total_items_done` | `int` | Yes | Sum of items_done across all phases |
| `total_items` | `int` | Yes | Sum of items_total across all phases |
| `elapsed_time_sec` | `int` | Yes | Seconds since experiment started |
| `estimated_remaining_sec` | `int` | No | Estimated time to completion (null if unknown) |
| `items_per_second` | `float` | No | Processing rate (null if <2 items done) |

**Computation**:
```python
overall_progress_pct = (total_items_done / total_items) * 100
elapsed = (now - start_time).total_seconds()
items_per_second = total_items_done / elapsed if elapsed > 0 else None
estimated_remaining = (total_items - total_items_done) / items_per_second if items_per_second else None
```

**Update Frequency**: Recomputed on every progress event (max 10/sec per debouncing).

**Example**:
```json
{
  "overall_progress_pct": 46.0,
  "current_phase_progress_pct": 46.0,
  "total_items_done": 23,
  "total_items": 50,
  "elapsed_time_sec": 245,
  "estimated_remaining_sec": 287,
  "items_per_second": 0.094
}
```

---

### 5. SessionMetadata

Additional tracking information for debugging and reproducibility.

**Purpose**: Capture environment details for experiment reproducibility.

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pid` | `int` | Yes | Process ID of experiment runner |
| `hostname` | `string` | Yes | Machine hostname |
| `python_version` | `string` | Yes | Python version (e.g., "3.12.0") |
| `platform` | `string` | Yes | OS platform (e.g., "Darwin") |
| `textual_version` | `string` | Yes | Textual library version |
| `mflux_version` | `string` | Yes | mflux library version |

**Example**:
```json
{
  "pid": 12345,
  "hostname": "macbook.local",
  "python_version": "3.12.0",
  "platform": "Darwin",
  "textual_version": "0.40.0",
  "mflux_version": "0.11.1"
}
```

---

### 6. ErrorInfo

Detailed error information when experiments or phases fail.

**Purpose**: Capture actionable error details for debugging and retry decisions.

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `error_type` | `string` | Yes | Exception class name |
| `error_message` | `string` | Yes | Human-readable error message |
| `phase` | `int` | Yes | Phase number where error occurred |
| `timestamp` | `datetime` | Yes | When error occurred |
| `traceback` | `string` | No | Full Python traceback (truncated to 1000 chars) |
| `remediation_hint` | `string` | No | Suggested fix (if known) |

**Common Error Types**:
- `ModelLoadError`: FLUX or VQA model failed to load
- `DiskFullError`: Insufficient disk space
- `VQATimeoutError`: VQA analysis timed out
- `ConfigValidationError`: Invalid configuration
- `NetworkError`: Model download failed

**Example**:
```json
{
  "error_type": "DiskFullError",
  "error_message": "No space left on device",
  "phase": 3,
  "timestamp": "2025-11-15T12:15:30Z",
  "traceback": "Traceback (most recent call last):\n  File ...",
  "remediation_hint": "Free up disk space and retry Phase 3"
}
```

---

### 7. SessionIndex

Index of all experiments for fast history loading.

**Purpose**: Enable efficient experiment history display without loading all session files.

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | `int` | Yes | Index schema version (currently 1) |
| `last_updated` | `datetime` | Yes | When index was last rebuilt |
| `experiments` | `List[SessionIndexEntry]` | Yes | List of all experiments |

**SessionIndexEntry**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | `string` | Yes | Unique session ID |
| `start_time` | `datetime` | Yes | When experiment started |
| `status` | `SessionStatus` | Yes | Current status |
| `config_name` | `string` | Yes | Config file basename |
| `total_images` | `int` | Yes | Total images generated (computed) |
| `phases_completed` | `int` | Yes | Number of completed phases |

**Persistence**: `data/sessions/index.json`

**Rebuild Triggers**:
- New experiment created
- Experiment status changes to completed/failed
- User manually refreshes history

**Example**:
```json
{
  "version": 1,
  "last_updated": "2025-11-15T14:30:00Z",
  "experiments": [
    {
      "session_id": "exp_20251115_120430",
      "start_time": "2025-11-15T12:04:30Z",
      "status": "completed",
      "config_name": "experiment_config.yaml",
      "total_images": 400,
      "phases_completed": 10
    },
    {
      "session_id": "exp_20251114_093015",
      "start_time": "2025-11-14T09:30:15Z",
      "status": "failed",
      "config_name": "experiment_config.yaml",
      "total_images": 120,
      "phases_completed": 3
    }
  ]
}
```

---

## Relationships

```
ExperimentSession 1──* PhaseProgress (composition)
ExperimentSession 1──1 ErrorInfo (composition, optional)
ExperimentSession 1──1 SessionMetadata (composition)
ExperimentSession 1──1 ConfigurationState (association via config_snapshot)

SessionIndex 1──* SessionIndexEntry (composition)
SessionIndexEntry *──1 ExperimentSession (reference via session_id)

ProgressMetrics derived from PhaseProgress (computed, not persisted)
```

---

## File Layout

```
data/sessions/
├── index.json                      # SessionIndex
├── active_experiment.json          # Symlink to current session (or null)
└── sessions/
    ├── exp_20251115_120430.json    # ExperimentSession
    ├── exp_20251114_093015.json    # ExperimentSession
    └── exp_20251113_162245.json    # ExperimentSession
```

---

## State Machine Diagrams

### ExperimentSession Status

```
     ┌──────────┐
     │ pending  │
     └────┬─────┘
          │ start
          ▼
     ┌──────────┐      ┌──────────┐
     │ running  │─────▶│ paused   │
     └────┬─────┘      └────┬─────┘
          │                 │ resume
          │◀────────────────┘
          │
    ┌─────┼─────┐
    │     │     │
    ▼     ▼     ▼
┌────┐ ┌────┐ ┌────┐
│comp│ │fail│ │canc│
│lete│ │ed  │ │eled│
└────┘ └────┘ └────┘
```

### PhaseProgress Status

```
     ┌──────────┐
     │ pending  │
     └────┬─────┘
          │
     ┌────┼────┐
     │    │    │
     │    ▼    ▼
     │ ┌────┐ ┌────┐
     │ │ in │ │skip│
     │ │prog│ │ped │
     │ └──┬─┘ └────┘
     │    │
     │  ┌─┼──┐
     │  │ │  │
     ▼  ▼ ▼  ▼
   ┌────┐ ┌────┐
   │comp│ │fail│
   │lete│ │ed  │
   └────┘ └────┘
```

---

## Validation Rules Summary

### ExperimentSession
- Only one session can have status=running
- current_phase must be 1-10
- If status=failed, error must be set
- config_snapshot immutable after start

### PhaseProgress
- items_done <= items_total
- Status transitions follow state machine
- Timestamps required for terminal states

### ConfigurationState
- Must validate before experiment start
- Lock mechanism must be atomic
- Config changes rejected if locked

---

## Performance Considerations

- **Session Files**: Target <100KB per session (with truncated tracebacks)
- **Index Rebuild**: O(n) where n = number of sessions; should be <1s for 1000 sessions
- **JSON Parse Time**: <10ms per session file on SSD
- **Memory Footprint**: Index kept in memory (~100KB per 1000 sessions)

---

**Review Date**: 2025-11-15
**Status**: Approved for implementation
