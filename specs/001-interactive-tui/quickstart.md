# Quickstart Guide: Interactive TUI
## Bias Detection Experiment Monitoring

**Last Updated**: 2025-11-15
**Feature**: Interactive TUI for Experiment Monitoring

---

## Overview

The Interactive TUI (Terminal User Interface) provides real-time monitoring and management of bias detection experiments. You can:

✅ Monitor experiment progress in real-time
✅ View and edit configurations interactively
✅ Reconnect to running experiments after closing the TUI
✅ Review experiment history
✅ Retry failed phases without re-running the entire experiment

---

## Installation

The TUI is included with the bias detection framework. Ensure you have the required dependencies:

```bash
# Install or update dependencies
uv sync

# Or with pip
pip install -e .
```

**Requirements**:
- Python >= 3.12
- Terminal emulator with ANSI color support (80x24 minimum)
- macOS or Linux (Windows support coming soon)

---

## Quick Start

### 1. Launch the TUI

```bash
# From project root
python -m bias_detector.tui

# Or if you have a custom launcher script
python tui.py
```

The TUI will start and display the main menu.

### 2. Navigate the Interface

Use these keyboard shortcuts to switch between views:

- **F1**: Progress monitoring (default view)
- **F2**: Metadata inspection
- **F3**: Configuration editor
- **F4**: Experiment history
- **h**: Help overlay
- **q**: Quit (with confirmation if experiment is running)

### 3. Start Your First Experiment

1. Press **F3** to open the Configuration editor
2. Review/modify experiment settings:
   - Number of images per prompt
   - FLUX model selection (dev, schnell, krea_dev)
   - Prompts to test
3. Press **s** to save configuration
4. Press **F1** to return to Progress view
5. Press **Enter** or click "Start Experiment" to begin

### 4. Monitor Progress

The Progress view shows:
- Current phase name and number
- Progress bar with percentage
- Items completed / total items
- Elapsed time and estimated time remaining
- Real-time metrics (images/second)

Progress updates appear within 1 second of actual experiment events.

### 5. View Results

When the experiment completes:
- A summary screen shows:
  - Total time elapsed
  - Images generated and analyzed
  - Results location
- Press **F4** to view experiment history
- All data is saved to `data/` directories and tracked in MLflow

---

## Common Workflows

### Workflow 1: Running a Standard Experiment

```
1. python -m bias_detector.tui
2. [F3] Configure experiment
   - Set num_images_per_prompt: 50
   - Select model: schnell
3. [s] Save configuration
4. [F1] Return to Progress view
5. [Enter] Start experiment
6. Monitor progress (phases 1-10 auto-execute)
7. [F4] View completion summary
```

**Time estimate**: 15-45 minutes for 50 images (depends on model and hardware)

---

### Workflow 2: Monitoring a Long-Running Experiment

If you need to close the TUI during a long experiment:

```
1. Experiment is running (Phase 3, generating 100 images)
2. [q] Quit TUI
3. Confirm quit (experiment continues in background)
4. [Later] python -m bias_detector.tui
5. TUI automatically reconnects to running experiment
6. Progress view shows current state
```

**Note**: The experiment process runs independently. Closing the TUI doesn't stop the experiment.

---

### Workflow 3: Retrying a Failed Phase

If an experiment fails (e.g., disk full during image generation):

```
1. [F4] View experiment history
2. Select the failed experiment
3. View error details (phase, message, hint)
4. [Fix the problem] (e.g., free disk space)
5. [r] Retry failed phase
6. Only Phase 3 re-runs; Phases 1-2 data preserved
7. Experiment continues from Phase 4
```

---

### Workflow 4: Reviewing Configuration

Before starting an experiment, verify your configuration:

```
1. [F2] Open Metadata view
2. Review sections:
   - Generation settings (model, image count, steps)
   - Prompts (occupational, contextual, neutral)
   - VQA configuration (model, questions)
   - Statistical parameters (confidence level, thresholds)
3. [F3] Edit if needed
4. [F1] Return to start experiment
```

---

## Configuration Editor

### Navigation

- **↑/↓**: Move between settings
- **Enter**: Edit selected setting
- **Tab**: Next section
- **Shift+Tab**: Previous section
- **s**: Save all changes
- **Esc**: Cancel edits (revert to saved)

### Editable Settings

**Generation Settings**:
- Model (dev, schnell, krea_dev)
- Images per prompt (1-1000)
- Inference steps
- Image resolution
- Seed strategy (fixed, random)

**Prompts**:
- Add/remove prompts in each category
- Edit existing prompt text
- Organize by category

**VQA Settings**:
- VQA model name
- Demographic questions
- Response options

**Statistics**:
- Confidence level
- Significance threshold
- Effect size thresholds

### Validation

Configuration is validated before saving:
- ✅ Green check: Valid setting
- ❌ Red X: Invalid (hover for details)
- ⚠️ Warning: Valid but unusual

You cannot save invalid configurations.

### Locking

⚠️ **Important**: Configuration is locked (read-only) while an experiment is running. You must pause or cancel the active experiment before making changes.

---

## Progress View Details

### Phase List

Shows all 10 research framework phases:

```
[✓] Phase 1: Experimental Design        (completed in 0.5s)
[✓] Phase 2: Prompt Engineering         (completed in 0.2s)
[▶] Phase 3: Image Generation           (in progress: 23/50)
[ ] Phase 4: VQA Analysis               (pending)
[ ] Phase 5: Statistical Analysis       (pending)
[ ] Phase 6: Counterfactual Testing     (pending)
[ ] Phase 7: Human Validation           (skipped)
[ ] Phase 8: Documentation              (pending)
[ ] Phase 9: Ethical Review             (pending)
[ ] Phase 10: Reporting                 (pending)
```

**Status Icons**:
- `[✓]`: Completed successfully
- `[▶]`: Currently in progress
- `[ ]`: Pending (not started)
- `[✗]`: Failed with error
- `[−]`: Skipped (not applicable)

### Progress Bar

```
Phase 3: Image Generation
████████████████░░░░░░░░░░ 46% (23/50)
Elapsed: 4m 05s | Remaining: ~4m 47s | 0.094 images/sec
```

### Real-Time Metrics

- **Elapsed Time**: Since experiment started
- **Estimated Remaining**: Based on current processing rate
- **Processing Rate**: Items per second
- **Overall Progress**: Across all phases

---

## Experiment History

### Viewing Past Experiments

Press **F4** to see all experiments:

```
┌─ Experiment History ─────────────────────────────────────┐
│ ID                    Started              Status  Images │
├──────────────────────────────────────────────────────────│
│ exp_20251115_120430   2025-11-15 12:04:30  ✓ Done  400   │
│ exp_20251114_093015   2025-11-14 09:30:15  ✗ Failed 120  │
│ exp_20251113_162245   2025-11-13 16:22:45  ✓ Done  500   │
└──────────────────────────────────────────────────────────┘
```

**Controls**:
- **↑/↓**: Navigate list
- **Enter**: View details
- **d**: Delete selected experiment (with confirmation)
- **f**: Filter by status (completed, failed, etc.)
- **s**: Search by ID or config name

### Experiment Details

Select an experiment to view:
- Full configuration used
- Phase-by-phase progress
- Total time elapsed
- Error details (if failed)
- Location of results
- Option to retry failed phases

### Cleanup

Experiments are retained indefinitely (FR-023). To delete old experiments:

1. Press **F4** (History view)
2. Select experiment(s) to delete
3. Press **d** (delete)
4. Confirm deletion

**Bulk deletion**: Press **Shift+d** to delete multiple selected experiments.

---

## Keyboard Shortcuts Reference

### Global

| Key | Action |
|-----|--------|
| F1  | Progress monitoring view |
| F2  | Metadata inspection view |
| F3  | Configuration editor view |
| F4  | Experiment history view |
| h   | Show help overlay |
| q   | Quit (prompts if experiment running) |
| Ctrl+C | Force quit (saves partial results) |

### Progress View

| Key | Action |
|-----|--------|
| Enter | Start new experiment |
| p | Pause active experiment |
| r | Resume paused experiment |
| c | Cancel active experiment (with confirmation) |
| ↑/↓ | Scroll phase list |

### Configuration Editor

| Key | Action |
|-----|--------|
| ↑/↓ | Navigate settings |
| Enter | Edit selected setting |
| Tab | Next section |
| s | Save all changes |
| Esc | Cancel (revert unsaved changes) |

### History View

| Key | Action |
|-----|--------|
| ↑/↓ | Navigate experiment list |
| Enter | View experiment details |
| d | Delete selected experiment |
| f | Filter by status |
| s | Search experiments |

---

## Troubleshooting

### TUI Won't Start

**Issue**: `ModuleNotFoundError: No module named 'textual'`

**Solution**:
```bash
uv sync  # or pip install textual>=0.40.0
```

---

### Cannot Connect to Running Experiment

**Issue**: TUI starts but doesn't show active experiment

**Solution**:
1. Check `data/sessions/active_experiment.json` exists
2. Verify experiment process is still running:
   ```bash
   ps aux | grep python | grep experiment
   ```
3. If process died, session state remains - you can view history but not reconnect

---

### Configuration Locked

**Issue**: Cannot edit config, says "locked by experiment"

**Solution**:
1. Check if experiment is actually running (Progress view)
2. If not running but still locked, the experiment may have crashed
3. Manually unlock: Delete `config/experiment_config.yaml.lock`

---

### Progress Updates Slow

**Issue**: Progress bar only updates every few seconds

**Solution**: This is normal for CPU-intensive phases (image generation, VQA). Progress events are debounced to max 10/second to prevent UI lag.

---

### Terminal Too Small

**Issue**: "Terminal too small" error message

**Solution**: Resize terminal to at least 80 characters wide, 24 lines tall. Or use smaller font size.

---

## Performance Tips

### For Faster Experiments

1. Use `schnell` model (2-4 inference steps vs. 20+ for `dev`)
2. Reduce `num_images_per_prompt` for testing (10 instead of 50)
3. Generate smaller images (512x512 vs. 1024x1024)
4. Close other GPU-intensive applications

### For Better UI Responsiveness

1. Use a GPU-accelerated terminal (Alacritty, WezTerm)
2. Reduce animation settings in Textual (TUI auto-detects)
3. Monitor on a different machine via SSH (experiment runs locally)

---

## Next Steps

After completing the quickstart:

1. **Read the full spec**: [spec.md](spec.md) for feature requirements
2. **Understand the architecture**: [plan.md](plan.md) for technical design
3. **Explore the data model**: [data-model.md](data-model.md) for session structure
4. **View results**: `mlflow ui` to visualize experiment tracking

---

## Support

- **Issues**: Report bugs on GitHub
- **Questions**: See [USAGE.md](../../../docs/USAGE.md) for detailed experiment guidance
- **Architecture**: See [plan.md](plan.md) for implementation details

---

**Happy Experimenting!** 🚀
