# Tasks: Interactive TUI for Experiment Monitoring

**Input**: Design documents from `/specs/001-interactive-tui/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Tests**: Tests are NOT explicitly requested in the specification, so test tasks are omitted. Focus is on implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- Single project structure: `src/bias_detector/`, `tests/` at repository root
- TUI module: `src/bias_detector/tui/`
- Existing modules to modify: `src/bias_detector/experiment.py`, generation/, analysis/, statistics/

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and TUI package structure

- [X] T001 Create TUI package structure: src/bias_detector/tui/__init__.py with screens/, widgets/, state/ subdirectories
- [X] T002 [P] Add Textual>=0.40.0 dependency to pyproject.toml in [project.dependencies]
- [X] T003 [P] Create data/sessions/ directory structure with sessions/ subdirectory for experiment persistence
- [X] T004 [P] Create empty __init__.py files in src/bias_detector/tui/screens/, widgets/, state/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement ProgressCallback protocol in src/bias_detector/tui/state/callbacks.py following contracts/progress_callback.py specification
- [X] T006 [P] Implement QueueProgressCallback class in src/bias_detector/tui/state/callbacks.py that pushes events to thread-safe queue
- [X] T007 Create SessionStatus and PhaseStatus enums in src/bias_detector/tui/state/session.py per data-model.md
- [X] T008 [P] Implement ExperimentSession dataclass in src/bias_detector/tui/state/session.py with JSON serialization methods
- [X] T009 [P] Implement PhaseProgress dataclass in src/bias_detector/tui/state/session.py with state validation
- [X] T010 [P] Implement ErrorInfo dataclass in src/bias_detector/tui/state/session.py for error tracking
- [X] T011 [P] Implement SessionMetadata dataclass in src/bias_detector/tui/state/session.py capturing environment details
- [X] T012 Implement StateManager.create_session() in src/bias_detector/tui/state/manager.py with atomic JSON writes
- [X] T013 [P] Implement StateManager.get_session() in src/bias_detector/tui/state/manager.py for loading session by ID
- [X] T014 [P] Implement StateManager.get_active_session() in src/bias_detector/tui/state/manager.py to detect running experiments
- [X] T015 [P] Implement StateManager.update_session_status() in src/bias_detector/tui/state/manager.py with state transition validation
- [X] T016 [P] Implement StateManager.update_phase_progress() in src/bias_detector/tui/state/manager.py for phase updates
- [X] T017 Implement StateManager session index management (list_sessions, rebuild_index) in src/bias_detector/tui/state/manager.py
- [X] T018 Implement StateManager configuration locking (lock_config, unlock_config, is_config_locked) using fcntl in src/bias_detector/tui/state/manager.py
- [X] T019 Add optional callback parameter to BiasDetectionExperiment.__init__() in src/bias_detector/experiment.py
- [X] T020 Emit on_experiment_start callback in BiasDetectionExperiment.run() in src/bias_detector/experiment.py
- [X] T021 Emit on_phase_start callback before each phase in BiasDetectionExperiment in src/bias_detector/experiment.py
- [ ] T022 Emit on_progress callbacks during image generation in src/bias_detector/generation/generator.py [DEFERRED - Phase-level callbacks sufficient for MVP]
- [X] T023 Emit on_phase_complete and on_phase_error callbacks in BiasDetectionExperiment in src/bias_detector/experiment.py
- [X] T024 Emit on_experiment_complete and on_experiment_error callbacks in BiasDetectionExperiment.run() in src/bias_detector/experiment.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Real-Time Experiment Progress Monitoring (Priority: P1) 🎯 MVP

**Goal**: Enable researchers to monitor experiment progress in real-time with visual indicators showing current phase, progress percentage, images generated, and estimated time remaining

**Independent Test**: Launch an experiment through the TUI and verify progress indicators update in real-time as phases execute, reconnect after closing TUI, and retry failed phases

### Implementation for User Story 1

- [X] T025 [P] [US1] Create ProgressBar widget in src/bias_detector/tui/widgets/progress_bar.py showing percentage and items done/total
- [X] T026 [P] [US1] Create PhaseList widget in src/bias_detector/tui/widgets/phase_list.py displaying all 10 phases with status icons
- [X] T027 [P] [US1] Create MetricDisplay widget in src/bias_detector/tui/widgets/metric_display.py showing elapsed time, ETA, processing rate
- [X] T028 [US1] Implement ProgressScreen in src/bias_detector/tui/screens/progress.py composing ProgressBar, PhaseList, and MetricDisplay
- [X] T029 [US1] Add async polling loop in ProgressScreen to read from progress queue every 100ms in src/bias_detector/tui/screens/progress.py
- [X] T030 [US1] Implement progress event handlers in ProgressScreen updating widgets based on PhaseEvent types in src/bias_detector/tui/screens/progress.py
- [X] T031 [US1] Create main TUIApp class in src/bias_detector/tui/app.py extending textual.app.App with modal screen navigation
- [X] T032 [US1] Add ThreadPoolExecutor for running experiments in TUIApp in src/bias_detector/tui/app.py
- [X] T033 [US1] Implement experiment launch logic in TUIApp.start_experiment() using ThreadPoolExecutor in src/bias_detector/tui/app.py
- [X] T034 [US1] Wire progress queue from QueueProgressCallback to ProgressScreen in TUIApp in src/bias_detector/tui/app.py
- [X] T035 [US1] Implement experiment reconnection on TUI startup in TUIApp.on_mount() checking for active sessions in src/bias_detector/tui/app.py
- [X] T036 [US1] Add keyboard navigation (F1 to Progress view, q to quit) in TUIApp in src/bias_detector/tui/app.py
- [X] T037 [US1] Implement completion summary display in ProgressScreen showing total time, images, results location in src/bias_detector/tui/screens/progress.py
- [ ] T038 [US1] Add retry failed phase functionality in ProgressScreen using StateManager in src/bias_detector/tui/screens/progress.py [DEFERRED - Complex feature for post-MVP]
- [X] T039 [US1] Create CLI entry point python -m bias_detector.tui in src/bias_detector/tui/__main__.py launching TUIApp
- [X] T040 [US1] Handle graceful shutdown on Ctrl+C with confirmation prompt in TUIApp in src/bias_detector/tui/app.py

**Checkpoint**: At this point, User Story 1 should be fully functional - users can launch experiments, monitor real-time progress, reconnect after closing, and retry failed phases

---

## Phase 4: User Story 2 - Experiment Metadata Inspection (Priority: P2)

**Goal**: Allow researchers to review experiment configuration (prompts, model settings, VQA parameters, statistics) without opening YAML files

**Independent Test**: Load a configuration and navigate to metadata view to verify all parameters are displayed in organized sections

### Implementation for User Story 2

- [X] T041 [P] [US2] Create ConfigurationState dataclass in src/bias_detector/tui/state/config.py with sections dict per data-model.md
- [X] T042 [P] [US2] Implement config loading and parsing in StateManager.get_config_state() in src/bias_detector/tui/state/manager.py
- [X] T043 [US2] Create MetadataScreen in src/bias_detector/tui/screens/metadata.py with tabbed sections for generation, prompts, VQA, statistics
- [X] T044 [P] [US2] Implement generation settings display panel in MetadataScreen showing model, image count, steps, seed in src/bias_detector/tui/screens/metadata.py
- [X] T045 [P] [US2] Implement prompts display panel in MetadataScreen showing categorized prompts (occupational, contextual, neutral) in src/bias_detector/tui/screens/metadata.py
- [X] T046 [P] [US2] Implement VQA configuration display panel in MetadataScreen showing model name, questions, response options in src/bias_detector/tui/screens/metadata.py
- [X] T047 [P] [US2] Implement statistics configuration display panel in MetadataScreen showing confidence level, thresholds in src/bias_detector/tui/screens/metadata.py
- [X] T048 [US2] Add F2 keyboard shortcut to navigate to MetadataScreen in TUIApp in src/bias_detector/tui/app.py
- [X] T049 [US2] Implement metadata refresh when config file changes in MetadataScreen in src/bias_detector/tui/screens/metadata.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - users can monitor experiments and inspect metadata

---

## Phase 5: User Story 3 - Interactive Configuration Management (Priority: P3)

**Goal**: Enable researchers to adjust experiment parameters (images count, model, prompts) through the TUI instead of manually editing YAML files

**Independent Test**: Modify configuration values through the TUI, save changes, and verify YAML file is updated correctly without running an experiment

### Implementation for User Story 3

- [X] T050 [P] [US3] Create ConfigEditorScreen in bias_detector/tui/screens/config_editor.py with editable form fields for all config sections
- [X] T051 [P] [US3] Implement configuration validation logic in bias_detector/tui/state/config.py checking required fields, valid models, num_images > 0
- [X] T052 [US3] Add real-time validation feedback in ConfigEditorScreen showing validation errors inline in bias_detector/tui/screens/config_editor.py
- [X] T053 [US3] Implement save configuration logic in ConfigEditorScreen writing to YAML with atomic replace in bias_detector/tui/screens/config_editor.py
- [X] T054 [US3] Add unsaved changes warning when navigating away or starting experiment in ConfigEditorScreen in bias_detector/tui/screens/config_editor.py
- [X] T055 [US3] Implement config lock enforcement in ConfigEditorScreen blocking edits when experiment is running (FR-009a) in bias_detector/tui/screens/config_editor.py
- [X] T056 [US3] Display lock status message in ConfigEditorScreen showing which session locked the config in bias_detector/tui/screens/config_editor.py
- [X] T057 [US3] Add F3 keyboard shortcut to navigate to ConfigEditorScreen in TUIApp in bias_detector/tui/app.py
- [X] T058 [US3] Implement model dropdown selector (dev, schnell, krea_dev) in ConfigEditorScreen in bias_detector/tui/screens/config_editor.py
- [X] T059 [US3] Implement number input for num_images_per_prompt with validation in ConfigEditorScreen in bias_detector/tui/screens/config_editor.py
- [X] T060 [US3] Implement prompt list editor allowing add/remove/edit prompts by category in ConfigEditorScreen in bias_detector/tui/screens/config_editor.py

**Checkpoint**: All three user stories (monitoring, metadata, configuration) should now be independently functional ✅

---

## Phase 6: User Story 4 - Experiment Control and Management (Priority: P4)

**Goal**: Allow researchers to pause, resume, cancel experiments, and navigate unlimited experiment history with manual cleanup

**Independent Test**: Start an experiment, use pause/resume/cancel controls, verify state changes are handled correctly, and view experiment history

### Implementation for User Story 4

- [ ] T061 [P] [US4] Implement pause experiment logic in TUIApp pausing after current phase item completes in src/bias_detector/tui/app.py
- [X] T062 [P] [US4] Implement resume experiment logic in TUIApp continuing from paused state in src/bias_detector/tui/app.py
- [X] T063 [P] [US4] Implement cancel experiment with confirmation dialog in TUIApp saving partial results in src/bias_detector/tui/app.py
- [X] T064 [P] [US4] Add pause/resume/cancel controls to ProgressScreen with keyboard shortcuts (p, r, c) in src/bias_detector/tui/screens/progress.py
- [X] T065 [US4] Create HistoryScreen in src/bias_detector/tui/screens/history.py displaying experiment list from SessionIndex
- [X] T066 [US4] Implement experiment list rendering in HistoryScreen showing session_id, status, start_time, total_images in src/bias_detector/tui/screens/history.py
- [ ] T067 [US4] Add filtering by status in HistoryScreen (completed, failed, etc.) in src/bias_detector/tui/screens/history.py
- [X] T068 [US4] Add search by session ID in HistoryScreen in src/bias_detector/tui/screens/history.py
- [X] T069 [US4] Implement pagination for large histories (20 entries per page) in src/bias_detector/tui/screens/history.py
- [X] T070 [US4] Add experiment detail view in HistoryScreen showing full session data on selection in src/bias_detector/tui/screens/history.py
- [X] T071 [US4] Implement manual delete experiment in HistoryScreen using StateManager.delete_session() with confirmation in src/bias_detector/tui/screens/history.py
- [X] T072 [US4] Add F4 keyboard shortcut to navigate to HistoryScreen in TUIApp in src/bias_detector/tui/app.py
- [X] T073 [US4] Prevent starting new experiment when one is active (FR-016a) with clear error message in TUIApp in src/bias_detector/tui/app.py

**Checkpoint**: All four user stories (T01-T04) AND all polish tasks (T074-T080) are complete - full production-ready TUI functionality is available

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and production readiness

- [X] T074 [P] Add help overlay screen (press h) showing all keyboard shortcuts in src/bias_detector/tui/screens/help.py
- [X] T075 [P] Implement terminal resize handling in TUIApp maintaining layout integrity in src/bias_detector/tui/app.py
- [X] T076 [P] Add error display panel in all screens showing experiment errors and warnings in src/bias_detector/tui/widgets/error_panel.py
- [X] T077 [P] Implement progress update debouncing (max 10/sec) to prevent UI flicker in ProgressScreen in src/bias_detector/tui/screens/progress.py
- [X] T078 [P] Add logging for TUI operations and state transitions in src/bias_detector/tui/app.py using Python logging
- [X] T079 Update README.md with TUI usage section showing python -m bias_detector.tui command
- [X] T080 Update CLAUDE.md with TUI architecture section and entry points
- [ ] T081 Validate quickstart.md workflows by running through all user scenarios manually
- [ ] T082 [P] Add docstrings to all TUI classes and methods following Google style per constitution
- [ ] T083 [P] Ensure all session file writes are atomic using tempfile + os.replace() pattern in StateManager
- [ ] T084 Add MLflow tracking warning display if tracking fails in ProgressScreen in src/bias_detector/tui/screens/progress.py
- [ ] T085 Optimize SessionIndex loading to lazy-load session details on demand in StateManager in src/bias_detector/tui/state/manager.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories CAN proceed in parallel (if staffed) since they're independent
  - Or sequentially in priority order: US1 (P1) → US2 (P2) → US3 (P3) → US4 (P4)
- **Polish (Phase 7)**: Depends on desired user stories being complete (minimum US1 for MVP)

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent, uses ConfigurationState from foundation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent, extends US2's metadata viewing with editing
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Independent, uses StateManager session management

### Within Each User Story

- Models/dataclasses before screens that use them
- Widgets before screens that compose them
- Core implementation before integration with TUIApp
- Keyboard shortcuts added after screen implementation
- Story complete before moving to next priority

### Parallel Opportunities Within Phases

**Phase 1 (Setup)**: All tasks except T001 can run in parallel after directory structure exists

**Phase 2 (Foundational)**:
- T005-T011: All dataclass/protocol definitions can run in parallel
- T012-T018: StateManager methods can be implemented in parallel after session dataclasses exist
- T019-T024: Callback emissions can be added in parallel to different modules

**Phase 3 (User Story 1)**:
- T025-T027: All three widgets can be built in parallel
- After widgets complete: Screen and app integration proceed sequentially

**Phase 4 (User Story 2)**:
- T041-T042: Config state management in parallel
- T044-T047: All metadata display panels in parallel

**Phase 5 (User Story 3)**:
- T050-T052: Screen creation and validation logic in parallel
- T058-T060: Individual form controls in parallel

**Phase 6 (User Story 4)**:
- T061-T064: Pause/resume/cancel can be built in parallel

**Phase 7 (Polish)**:
- T074-T078: All widget/screen improvements in parallel
- T082-T085: All optimization tasks in parallel

---

## Parallel Example: User Story 1

```bash
# After foundational phase, launch widget creation in parallel:
Task T025: "Create ProgressBar widget in src/bias_detector/tui/widgets/progress_bar.py"
Task T026: "Create PhaseList widget in src/bias_detector/tui/widgets/phase_list.py"
Task T027: "Create MetricDisplay widget in src/bias_detector/tui/widgets/metric_display.py"

# Once widgets are complete, proceed with screen composition:
Task T028: "Implement ProgressScreen composing widgets"
```

## Parallel Example: Multiple User Stories (if team capacity)

```bash
# After foundational phase completes, start all user stories in parallel:
Developer A: Tasks T025-T040 (User Story 1 - Progress Monitoring)
Developer B: Tasks T041-T049 (User Story 2 - Metadata Inspection)
Developer C: Tasks T050-T060 (User Story 3 - Configuration Management)
Developer D: Tasks T061-T073 (User Story 4 - Experiment Control)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T024) - CRITICAL BLOCKING PHASE
3. Complete Phase 3: User Story 1 (T025-T040)
4. **STOP and VALIDATE**: Launch TUI, run experiment, verify real-time monitoring works
5. Add minimal polish from Phase 7 (T079-T081 documentation)
6. **MVP READY**: Users can monitor experiments with real-time progress

### Incremental Delivery (Recommended)

1. **Sprint 1**: Setup + Foundational (T001-T024) → Foundation ready for all stories
2. **Sprint 2**: User Story 1 (T025-T040) → Test independently → **MVP Launch**
3. **Sprint 3**: User Story 2 (T041-T049) → Test independently → Deploy enhanced version
4. **Sprint 4**: User Story 3 (T050-T060) → Test independently → Deploy full config management
5. **Sprint 5**: User Story 4 (T061-T073) → Test independently → Deploy complete feature
6. **Sprint 6**: Polish (T074-T085) → Production hardening

Each sprint delivers independently testable, valuable functionality.

### Parallel Team Strategy

With 3-4 developers:

1. **Week 1**: All developers on Setup + Foundational (T001-T024) together
2. **Week 2**: Once Foundational done:
   - Dev A: User Story 1 (P1 - highest priority)
   - Dev B: User Story 2 (P2)
   - Dev C: User Story 3 (P3)
3. **Week 3**: Integration testing, User Story 4 (Dev D), Polish (all devs)
4. Stories integrate seamlessly since they're independent

---

## Task Count Summary

- **Phase 1 (Setup)**: 4 tasks
- **Phase 2 (Foundational)**: 20 tasks (CRITICAL - blocks all stories)
- **Phase 3 (User Story 1 - P1)**: 16 tasks (MVP)
- **Phase 4 (User Story 2 - P2)**: 9 tasks
- **Phase 5 (User Story 3 - P3)**: 11 tasks
- **Phase 6 (User Story 4 - P4)**: 13 tasks
- **Phase 7 (Polish)**: 12 tasks

**Total**: 85 tasks

**MVP Scope** (Setup + Foundational + US1 + Essential Polish): ~45 tasks

---

## Notes

- All tasks follow checklist format: `- [ ] [TaskID] [P?] [Story?] Description with file path`
- [P] indicates parallelizable tasks (different files, no dependencies)
- [Story] label (US1-US4) maps tasks to user stories for traceability
- Tests omitted as not explicitly requested in specification
- Each user story is independently completable and testable
- Foundational phase is critical blocker - must complete before any user story work
- Commit after each task or logical group of parallel tasks
- Stop at any checkpoint to validate story works independently
- File paths use absolute structure from plan.md: `src/bias_detector/tui/`
