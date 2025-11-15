# Feature Specification: Interactive TUI for Experiment Monitoring

**Feature Branch**: `001-interactive-tui`
**Created**: 2025-11-15
**Status**: Draft
**Input**: User description: "Implement textual to make the interface to the testing fully interactive. This is especially importatnt whilst the experiment is running so that the user can see exactly where the test is at that moment, and what remains to be done. Show relevent metadata and allow user to manage the setup."

## Clarifications

### Session 2025-11-15

- Q: Should experiment sessions persist across TUI restarts, allowing users to close and reopen the TUI to check on a running experiment? → A: Yes - TUI reconnects to running experiments; users can close/reopen to check progress
- Q: Should users be able to run multiple experiments concurrently, or is the system limited to one active experiment at a time? → A: Single active - Only one experiment can run at a time; starting a new one requires previous to complete/stop
- Q: When an experiment is actively running, should configuration changes be allowed? → A: Block changes - Configuration is read-only during active experiments; must pause/cancel first
- Q: When a phase fails during an experiment, how should the retry mechanism function? → A: Retry from failed phase - User can retry just the failed phase; prior completed phases remain
- Q: How long should completed experiment history be retained and displayed in the TUI? → A: Unlimited - Show all experiments ever run (manual cleanup only)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real-Time Experiment Progress Monitoring (Priority: P1)

A researcher runs a bias detection experiment and wants to monitor its progress in real-time without manually checking log files or output directories. The interface displays the current phase, progress percentage, images generated so far, and estimated time remaining.

**Why this priority**: This is the core value proposition - giving users visibility into long-running experiments. Without this, users have no way to know if their experiment is progressing normally or stuck.

**Independent Test**: Can be fully tested by launching an experiment through the TUI and verifying that progress indicators update in real-time as the experiment proceeds through each phase, delivering immediate visibility without any other features.

**Acceptance Scenarios**:

1. **Given** an experiment is configured and ready to run, **When** the user starts the experiment through the TUI, **Then** the interface displays the current phase name, progress bar, and count of completed/total items
2. **Given** an experiment is in Phase 3 (image generation), **When** each image is generated, **Then** the progress counter increments within 1 second and the progress bar updates visually
3. **Given** an experiment is running, **When** the user views the progress screen, **Then** they can see which phase is active, which phases are completed, and which phases are pending
4. **Given** an experiment completes successfully, **When** the final phase finishes, **Then** the interface displays a completion summary with total time, images generated, and results location
5. **Given** an experiment is running in the background, **When** the user closes and reopens the TUI, **Then** the interface automatically reconnects and displays the current progress state
6. **Given** an experiment fails during Phase 4 (VQA analysis), **When** the user selects the retry option, **Then** the system re-runs only Phase 4 while preserving all data from Phases 1-3

---

### User Story 2 - Experiment Metadata Inspection (Priority: P2)

A researcher wants to review the current experiment configuration, including prompts being tested, model settings, statistical parameters, and VQA questions, without opening YAML files or documentation.

**Why this priority**: Essential for experiment validation and reproducibility. Users need to verify their configuration is correct before committing to a long-running experiment.

**Independent Test**: Can be tested independently by loading a configuration and navigating through metadata views to verify all experiment parameters are displayed accurately, providing value even without running an experiment.

**Acceptance Scenarios**:

1. **Given** an experiment configuration is loaded, **When** the user navigates to the metadata view, **Then** they see organized sections for generation settings, prompts, VQA configuration, and statistical parameters
2. **Given** the user is viewing prompt metadata, **When** they select a prompt category (occupational, contextual, neutral), **Then** the interface displays all prompts in that category with their IDs
3. **Given** the user is viewing generation settings, **When** they access the metadata panel, **Then** they see model type, image count per prompt, seed strategy, resolution, and inference steps
4. **Given** the user is reviewing VQA configuration, **When** they view the metadata, **Then** they see the VQA model name, all demographic questions, and available response options

---

### User Story 3 - Interactive Configuration Management (Priority: P3)

A researcher wants to adjust experiment parameters (number of images, model selection, prompts) through the interactive interface rather than editing YAML files manually.

**Why this priority**: Improves user experience and reduces configuration errors, but the experiment can still run with static configuration files. This is a convenience feature that builds on the core monitoring capability.

**Independent Test**: Can be tested independently by modifying configuration values through the TUI, saving changes, and verifying the YAML file is updated correctly, without needing to run an experiment.

**Acceptance Scenarios**:

1. **Given** the user is in the configuration view and no experiment is active, **When** they select "Generation Settings" and modify the number of images per prompt, **Then** the change is reflected immediately in the interface and persisted to the config file
2. **Given** the user wants to change the FLUX model and no experiment is active, **When** they select from available models (dev, schnell, krea_dev), **Then** the interface updates the configuration and shows any model-specific settings
3. **Given** the user has modified multiple configuration values, **When** they choose to save changes, **Then** the system validates the configuration and either saves successfully or displays specific validation errors
4. **Given** the user has unsaved configuration changes, **When** they attempt to start an experiment, **Then** the system prompts them to save or discard changes before proceeding
5. **Given** an experiment is actively running, **When** the user attempts to modify any configuration value, **Then** the system prevents the modification and displays a message requiring the experiment to be paused or cancelled first

---

### User Story 4 - Experiment Control and Management (Priority: P4)

A researcher wants to pause, resume, or cancel a running experiment, and navigate between different experiment phases if the TUI supports multi-phase workflows.

**Why this priority**: Useful for long-running experiments but not essential for MVP. Users can still terminate via Ctrl+C and restart manually.

**Independent Test**: Can be tested by starting an experiment and using pause/resume/cancel controls to verify state changes are handled correctly.

**Acceptance Scenarios**:

1. **Given** an experiment is running, **When** the user presses the pause control, **Then** the current phase completes its current item and pauses before starting the next item
2. **Given** an experiment is paused, **When** the user presses resume, **Then** the experiment continues from where it was paused
3. **Given** an experiment is running or paused, **When** the user chooses to cancel, **Then** the interface prompts for confirmation and terminates gracefully, saving partial results
4. **Given** an experiment has completed Phase 3 (generation), **When** the user wants to skip to Phase 5 (statistics), **Then** the interface allows jumping to specific phases that have their prerequisites met

---

### Edge Cases

- What happens when an experiment fails mid-run (model error, disk full, VQA timeout)? The interface displays the error clearly, preserves partial results from completed phases, and provides a retry option that re-runs only the failed phase while keeping all previously completed phases intact.
- How does the system handle very fast experiments (e.g., 10 images with schnell model)? Progress updates should still be visible even if phases complete in under 1 second.
- What happens when the terminal window is resized during operation? The TUI should gracefully reflow content and maintain readability.
- How does the system handle configuration changes while an experiment is running? The interface prevents all configuration modifications during active experiments and displays a clear message indicating that the user must pause or cancel the experiment before making changes.
- What happens when MLflow tracking fails? The interface should continue the experiment but display a warning that tracking is not available.
- How does the system handle keyboard interrupts (Ctrl+C)? The TUI should catch the interrupt, display a confirmation prompt, and allow graceful shutdown with partial result preservation.
- What happens when a user attempts to start a new experiment while one is already running? The system should display a clear message indicating an experiment is active and provide options to view the active experiment or cancel it before starting a new one.
- What happens when the experiment history contains hundreds of entries? The interface should provide filtering, search, and pagination capabilities to navigate large experiment histories efficiently without performance degradation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display real-time progress for all experiment phases (1-6) with visual progress indicators
- **FR-002**: System MUST update progress metrics (items completed, percentage, elapsed time) within 1 second of actual progress
- **FR-003**: System MUST show the current experiment phase name and status (not started, in progress, completed, failed)
- **FR-004**: System MUST display a list of remaining tasks/phases for the current experiment
- **FR-005**: System MUST present experiment metadata in organized, readable sections (generation, prompts, VQA, statistics)
- **FR-006**: System MUST allow users to view all configured prompts organized by category
- **FR-007**: System MUST display current generation settings (model, image count, seed strategy, resolution, steps)
- **FR-008**: System MUST show VQA configuration (model name, demographic questions, response options)
- **FR-009**: System MUST allow users to modify configuration values through interactive controls when no experiment is active
- **FR-009a**: System MUST block all configuration modifications while an experiment is running and display a clear message requiring pause or cancellation first
- **FR-010**: System MUST validate configuration changes before saving to prevent invalid experiments
- **FR-011**: System MUST persist configuration changes to the YAML file when user saves
- **FR-012**: System MUST provide keyboard navigation for all interface elements
- **FR-013**: System MUST handle terminal resize events without crashing or corrupting display
- **FR-014**: System MUST display experiment errors and warnings in a dedicated message area
- **FR-015**: System MUST show experiment start time, elapsed time, and estimated completion time
- **FR-016**: System MUST allow users to start a new experiment from the interface
- **FR-016a**: System MUST prevent starting a new experiment if one is already active, requiring the user to complete, pause, or cancel the active experiment first
- **FR-017**: System MUST display a summary screen when experiments complete, showing results location and key metrics
- **FR-018**: System MUST support navigation between different views (progress, metadata, configuration, results)
- **FR-019**: System MUST handle graceful shutdown on keyboard interrupt with option to save partial results
- **FR-020**: System MUST display the total number of images generated and analyzed in real-time
- **FR-021**: System MUST persist experiment session state to allow reconnection after TUI closure
- **FR-022**: System MUST automatically detect and reconnect to running experiments when TUI is reopened
- **FR-023**: System MUST display a list of all experiments (active and completed) with unlimited history retention; cleanup is manual only
- **FR-023a**: System MUST allow users to manually delete old experiment history entries from the TUI
- **FR-024**: System MUST preserve partial results from completed phases when an experiment fails
- **FR-025**: System MUST provide a retry option for failed experiments that re-runs only the failed phase
- **FR-026**: System MUST retain all successfully completed phase data when retrying a failed phase

### Key Entities

- **Experiment Session**: Represents a running or completed experiment with start time, current phase, progress metrics, configuration snapshot, completion status, and persistence state allowing reconnection across TUI restarts
- **Phase Progress**: Tracks progress for each of the 10 research phases with name, status (pending/in-progress/completed/failed), items completed, total items, and elapsed time
- **Configuration State**: Represents the current experiment configuration with sections for generation, prompts, VQA, statistics, and validation status
- **Progress Metrics**: Real-time metrics including current phase, items completed/total, percentage complete, elapsed time, and estimated time remaining
- **User Action**: Represents user interactions with the TUI including navigation commands, configuration changes, and experiment control actions (start/pause/cancel)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can monitor experiment progress without checking log files or directories, with all relevant information visible in a single interface
- **SC-002**: Progress updates appear within 1 second of actual experiment progress (image generation, VQA analysis completion)
- **SC-003**: Users can view complete experiment configuration within 3 navigation actions from the main screen
- **SC-004**: 100% of experiment parameters in the YAML config file are accessible through the TUI metadata view
- **SC-005**: Configuration changes made through the TUI are persisted correctly to YAML with validation, achieving zero invalid configuration saves
- **SC-006**: Users can start, monitor, and complete a full experiment without using command-line arguments or editing files manually
- **SC-007**: The interface remains responsive and usable during long-running experiments (50+ images per prompt)
- **SC-008**: Terminal resize events are handled gracefully without data loss or requiring restart
- **SC-009**: Experiment failures display clear error messages with suggested remediation actions within the TUI
- **SC-010**: Users can determine experiment completion status and locate results within 2 seconds of experiment finishing

## Assumptions

- The TUI will be built using the Textual Python library (version 0.40.0 or later)
- Users have terminal emulators that support ANSI colors and Unicode characters
- The TUI will run in the same Python environment as the existing bias detection framework
- Configuration changes will be applied to the same YAML file structure currently used
- The experiment runner will be refactored to support progress callbacks for real-time updates
- Standard terminal size is assumed to be at least 80x24 characters, with graceful degradation for smaller terminals
- Users will access the TUI via a command-line interface (e.g., `python tui.py` or similar)
- The TUI will integrate with existing MLflow tracking without requiring changes to the tracking backend
