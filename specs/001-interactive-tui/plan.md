# Implementation Plan: Interactive TUI for Experiment Monitoring

**Branch**: `001-interactive-tui` | **Date**: 2025-11-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-interactive-tui/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build an interactive Terminal User Interface (TUI) using Textual that provides real-time monitoring of bias detection experiments. The TUI enables researchers to:
- Monitor experiment progress in real-time with visual indicators
- View and modify experiment configurations interactively
- Reconnect to running experiments after closing the TUI
- Retry failed phases while preserving completed work
- Review unlimited experiment history with manual cleanup

Technical approach: Integrate Textual library with the existing `BiasDetectionExperiment` orchestrator, adding session persistence, progress callbacks, and a state management layer for experiment tracking.

## Technical Context

**Language/Version**: Python >= 3.12 (matching existing project requirement)
**Primary Dependencies**:
- Textual >= 0.40.0 (TUI framework)
- asyncio (for concurrent UI updates and experiment execution)
- YAML (PyYAML >= 6.0.3, already in project)
- Existing: mflux, transformers, mlflow

**Storage**:
- Experiment session state: JSON files in `data/sessions/`
- Configuration: YAML files (existing `config/experiment_config.yaml`)
- Experiment results: Existing structure (`data/raw/`, `data/processed/`, MLflow SQLite)

**Testing**:
- pytest (existing project standard)
- Textual testing framework (textual.testing.App for UI tests)
- Contract tests for progress callback interface

**Target Platform**: macOS/Linux terminals (80x24 minimum), optimized for Apple Silicon
**Project Type**: Single project (extending existing bias_detector package)
**Performance Goals**:
- UI updates within 1 second of experiment progress
- Responsive UI during long-running experiments (50+ images)
- Graceful handling of terminal resize events

**Constraints**:
- Must integrate with existing `BiasDetectionExperiment` without breaking CLI
- Session persistence must be atomic (no corrupted states)
- Configuration locking mechanism must prevent race conditions

**Scale/Scope**:
- Support unlimited experiment history (100s of experiments)
- Handle experiments with 100+ images per prompt
- 4 major views (Progress, Metadata, Configuration, History)
- 26+ functional requirements

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: Project constitution is currently a template. Proceeding with standard Python best practices:

✅ **Single Responsibility**: TUI module separate from experiment logic
✅ **Modularity**: State management, UI components, and experiment integration are distinct
✅ **Testability**: All components testable in isolation
✅ **Documentation**: Inline docstrings + quickstart guide
✅ **Error Handling**: Graceful degradation for all edge cases specified

**Potential Complexity Points** (to monitor):
- State synchronization between TUI and background experiments
- Atomic session persistence during failures
- Callback threading between async UI and sync experiment code

## Project Structure

### Documentation (this feature)

```text
specs/001-interactive-tui/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (architecture decisions, state management)
├── data-model.md        # Phase 1 output (experiment session, progress state)
├── quickstart.md        # Phase 1 output (how to use the TUI)
├── contracts/           # Phase 1 output (progress callbacks, state persistence)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created yet)
```

### Source Code (repository root)

```text
src/bias_detector/
├── tui/                        # NEW: TUI implementation
│   ├── __init__.py
│   ├── app.py                  # Main Textual app
│   ├── screens/                # TUI screens
│   │   ├── __init__.py
│   │   ├── progress.py         # Real-time progress monitoring
│   │   ├── metadata.py         # Configuration inspection
│   │   ├── config_editor.py   # Interactive configuration
│   │   └── history.py          # Experiment history
│   ├── widgets/                # Reusable UI components
│   │   ├── __init__.py
│   │   ├── progress_bar.py    # Phase progress indicators
│   │   ├── phase_list.py      # Phase status list
│   │   └── metric_display.py  # Real-time metrics
│   └── state/                  # State management
│       ├── __init__.py
│       ├── session.py          # Session persistence
│       ├── manager.py          # State manager
│       └── callbacks.py        # Progress callbacks
│
├── experiment.py               # MODIFIED: Add progress callbacks
├── generation/                 # MODIFIED: Emit progress events
├── analysis/                   # MODIFIED: Emit progress events
└── statistics/                 # MODIFIED: Emit progress events

tests/
├── tui/                        # NEW: TUI tests
│   ├── test_screens.py
│   ├── test_widgets.py
│   ├── test_state_manager.py
│   └── test_integration.py
└── contract/                   # NEW: Interface contract tests
    └── test_progress_callbacks.py
```

**Structure Decision**: Extending the existing single-project structure with a new `tui/` package under `src/bias_detector/`. The TUI will integrate with the existing `BiasDetectionExperiment` orchestrator through a well-defined callback interface, keeping experiment logic and UI concerns separated.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| N/A | No constitutional violations | Constitution is template; following standard Python practices |

## Phase 0: Research & Architecture Decisions

See [research.md](research.md) for detailed findings on:
- State management patterns for TUI + background processes
- Session persistence strategies (JSON vs SQLite vs pickle)
- Progress callback architecture (observer pattern vs events)
- Textual screen navigation patterns
- Concurrent execution patterns (asyncio + threading)

## Phase 1: Design Artifacts

### Data Model
See [data-model.md](data-model.md) for:
- ExperimentSession entity (persistence format)
- PhaseProgress state machine
- ConfigurationState structure
- ProgressMetrics real-time updates

### Contracts
See [contracts/](contracts/) for:
- Progress callback interface specification
- Session persistence format (JSON schema)
- State manager public API

### Quickstart
See [quickstart.md](quickstart.md) for:
- Launching the TUI
- Basic navigation
- Starting/monitoring experiments
- Configuration management

## Implementation Notes

### Integration Points

1. **BiasDetectionExperiment**: Add optional progress callback parameter; emit events at phase boundaries
2. **Session Persistence**: JSON files in `data/sessions/` with atomic writes
3. **Configuration Locking**: File-based lock with timeout to prevent concurrent modifications
4. **MLflow Integration**: Read-only; TUI displays but doesn't modify tracking data

### Error Handling Strategy

- **Phase Failures**: Preserve completed phase data, offer retry from failed phase
- **TUI Crashes**: Session state persists; next launch reconnects automatically
- **Config Validation**: Real-time validation with clear error messages
- **Terminal Resize**: Responsive layout with minimum 80x24 graceful degradation

### Performance Considerations

- **Progress Updates**: Debounce rapid updates (max 10/sec) to prevent UI flicker
- **History Loading**: Lazy load experiment history (paginate if >100 entries)
- **Session Persistence**: Write state asynchronously to avoid blocking UI

### Testing Strategy

1. **Unit Tests**: Each screen, widget, and state component in isolation
2. **Contract Tests**: Progress callback interface, session persistence format
3. **Integration Tests**: Full TUI flow with mock experiments
4. **Manual Testing**: Real experiments on macOS and Linux terminals

## Next Steps

After plan approval:
1. Run `/speckit.tasks` to generate detailed task breakdown
2. Implement Phase 0 foundation (state management, session persistence)
3. Build Progress view (P1 user story)
4. Add Metadata view (P2 user story)
5. Implement Configuration editor (P3 user story)
6. Add Control features (P4 user story)
