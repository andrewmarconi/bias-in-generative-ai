# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Bias Detection Framework for Generative AI Image Models** - a research framework for detecting and analyzing implicit demographic biases in text-to-image models through systematic testing and statistical analysis.

The framework implements a 10-phase research methodology that combines:
- Image generation using mflux (FLUX.1 models optimized for Apple Silicon)
- Vision-Question-Answering (VQA) analysis for demographic classification
- Rigorous statistical testing (chi-square, effect sizes, confidence intervals)
- MLflow experiment tracking for reproducibility

## Core Commands

### Development Setup
```bash
# Install dependencies (uses uv package manager)
uv sync

# Alternative if uv not available
pip install -e .
```

### Running Experiments
```bash
# Run full experiment pipeline
python run_experiment.py

# Run specific phases only
python run_experiment.py --phase setup       # Initialize components
python run_experiment.py --phase generate    # Image generation only
python run_experiment.py --phase analyze     # VQA analysis only
python run_experiment.py --phase statistics  # Statistical analysis only

# Use custom configuration
python run_experiment.py --config path/to/config.yaml
```

### Viewing Results
```bash
# Launch MLflow UI to view experiment tracking
mlflow ui
# Then navigate to http://localhost:5000

# Results are saved to:
# - data/raw/images/              (generated images with metadata)
# - data/processed/               (analysis results)
# - data/results/                 (statistical summaries and visualizations)
```

### Testing
```bash
# Run tests (adjust based on test framework)
uv run python -m pytest tests/
uv run python -m pytest tests/test_setup.py
uv run python -m pytest tests/test_model_init.py
```

## Architecture

### Main Components

The project follows a modular pipeline architecture orchestrated by `BiasDetectionExperiment`:

1. **BiasDetectionExperiment** ([src/bias_detector/experiment.py](src/bias_detector/experiment.py))
   - Main orchestrator that runs the 10-phase research framework
   - Coordinates all components and manages experiment flow
   - Entry point: `run_experiment.py` → `BiasDetectionExperiment.run_full_experiment()`

2. **ImageGenerator** ([src/bias_detector/generation/image_generator.py](src/bias_detector/generation/image_generator.py))
   - Uses mflux library to generate images with FLUX.1 models (dev/schnell/krea_dev)
   - Optimized for Apple Silicon (MPS backend)
   - Supports fixed or random seed strategies for reproducibility
   - Saves images with comprehensive metadata (prompt, seed, timestamp, parameters)

3. **VQAAnalyzer** ([src/bias_detector/analysis/vqa_analyzer.py](src/bias_detector/analysis/vqa_analyzer.py))
   - Vision-Language model analysis using BLIP-2 (default) or other VQA models
   - Asks structured questions about demographic characteristics
   - Automatically selects device: CUDA > MPS > CPU
   - Uses float16 precision on GPU/MPS for memory efficiency

4. **BiasMetrics** ([src/bias_detector/statistics/bias_metrics.py](src/bias_detector/statistics/bias_metrics.py))
   - Statistical analysis: chi-square tests, Cramer's V effect sizes, confidence intervals
   - Demographic parity calculations
   - Generates comprehensive statistical summaries

5. **MLflowTracker** ([src/bias_detector/utils/mlflow_tracker.py](src/bias_detector/utils/mlflow_tracker.py))
   - Experiment tracking and versioning
   - Logs configuration, parameters, metrics, and sample images
   - Results stored in SQLite database (mlflow.db)

### Configuration System

All experiments are controlled via YAML configuration ([config/experiment_config.yaml](config/experiment_config.yaml)):

```yaml
experiment:
  name: "experiment_name"
  description: "Description of the experiment"

generation:
  model: "schnell"              # dev, schnell, or krea_dev
  num_images_per_prompt: 50     # Sample size per prompt
  seed_strategy: "random"       # fixed or random

prompts:
  occupational: [...]           # Occupation-based prompts
  contextual: [...]             # Contextual prompts
  neutral: [...]                # Neutral prompts

vqa_analysis:
  model: "Salesforce/blip2-opt-2.7b"
  questions:                    # Structured questions for demographic classification
    gender: {...}
    race_ethnicity: {...}
    age: {...}
    body_type: {...}

statistics:
  confidence_level: 0.95
  significance_level: 0.05
  effect_size_thresholds: {...}
```

### 10-Phase Research Framework

The framework implements a structured research methodology:

1. **Phase 1**: Experimental Design - Define hypotheses and sample sizes
2. **Phase 2**: Prompt Engineering - Create ambiguous prompts without demographic indicators
3. **Phase 3**: Image Generation - Generate images using mflux (FLUX.1 models)
4. **Phase 4**: VQA Analysis - Classify demographic characteristics using vision-language models
5. **Phase 5**: Statistical Analysis - Chi-square tests, effect sizes, confidence intervals
6. **Phase 6**: Counterfactual Testing - Test with explicit demographic modifiers
7. **Phase 7**: Human Validation - Inter-rater reliability and ground truth
8. **Phase 8**: Documentation - MLflow tracking for reproducibility
9. **Phase 9**: Ethical Considerations - Bias mitigation strategies
10. **Phase 10**: Reporting - Comprehensive visualizations and metrics

See [docs/spec.md](docs/spec.md) for complete methodology details.

### Data Flow

```
Config (YAML) → BiasDetectionExperiment
                    ↓
    ┌───────────────┼────────────────┐
    ↓               ↓                ↓
ImageGenerator  VQAAnalyzer    BiasMetrics
    ↓               ↓                ↓
  Images        Analysis         Statistics
    └───────────────┼────────────────┘
                    ↓
              MLflowTracker
```

## Project Structure

```
BiasInGenerativeAi/
├── config/
│   └── experiment_config.yaml      # Main configuration file
├── data/
│   ├── raw/images/                 # Generated images with JSON metadata
│   ├── processed/                  # VQA analysis results
│   └── results/                    # Statistical summaries and visualizations
├── src/bias_detector/
│   ├── experiment.py               # Main orchestrator
│   ├── generation/
│   │   └── image_generator.py      # mflux/FLUX image generation
│   ├── analysis/
│   │   └── vqa_analyzer.py         # VQA demographic classification
│   ├── statistics/
│   │   ├── bias_metrics.py         # Statistical calculations
│   │   └── visualizations.py       # Plotting and visualization
│   └── utils/
│       ├── config.py               # Configuration loading/validation
│       └── mlflow_tracker.py       # Experiment tracking
├── docs/
│   ├── spec.md                     # Complete research framework specification
│   ├── GETTING_STARTED.md          # Quick start guide
│   ├── USAGE.md                    # Detailed usage instructions
│   └── tech.md                     # Technical implementation details
├── tests/
│   ├── test_setup.py
│   └── test_model_init.py
├── run_experiment.py               # CLI entry point
└── example_usage.py                # Python API usage examples
```

## Key Technical Details

### Apple Silicon Optimization
- Uses mflux for FLUX.1 models, optimized for Apple Silicon M-series chips
- VQA models automatically use MPS (Metal Performance Shaders) when available
- Falls back to CUDA for NVIDIA GPUs, then CPU

### Memory Management
- VQA models use float16 precision on GPU/MPS to reduce memory usage
- Lazy loading of FLUX model (initialized on first generation)
- Batch processing for large image sets

### Reproducibility
- All generation parameters tracked (seed, model version, timestamp)
- MLflow logs all experiment configurations and results
- Images saved with comprehensive metadata in JSON format
- Configuration versioning via YAML

### Statistical Rigor
- Sample size recommendations: 50-100 images per prompt minimum
- Chi-square tests compare to uniform distribution (or population baselines)
- Cramer's V effect size: small (0.1), medium (0.3), large (0.5+)
- 95% confidence intervals using Wilson method
- Bootstrap sampling for uncertainty quantification

## Extension Points

### Adding New VQA Models
Modify `VQAAnalyzer.__init__()` to support additional vision-language models (LLaVA, Qwen2-VL, etc.)

### Adding New Prompts
Edit `config/experiment_config.yaml` under the `prompts` section

### Adding New Bias Categories
Add to `bias_categories` and `vqa_analysis.questions` in config

### Custom Statistical Tests
Extend `BiasMetrics` class with new statistical methods

## Important Notes

- **Hardware Requirements**: Optimized for Apple Silicon; CUDA GPUs also supported
- **Model Downloads**: First run downloads FLUX and BLIP-2 models (several GB)
- **VQA Model Bias**: Be aware that VQA models themselves contain biases - validate against human annotations
- **Ethical Considerations**: This tool is for research and auditing purposes; results require careful interpretation
- **Documentation**: See [docs/spec.md](docs/spec.md) for complete research methodology and literature references

## Interactive TUI Interface

The framework includes a comprehensive Terminal User Interface (TUI) for real-time experiment monitoring:

### TUI Features
- **Real-time Progress Monitoring**: Live phase progress with metrics and ETA
- **Experiment Control**: Pause, resume, and cancel experiments
- **Configuration Management**: Interactive YAML editor with validation and locking
- **Metadata Inspection**: Browse experiment results and configurations
- **History Management**: Search, filter, and manage past experiments
- **Help System**: Built-in help overlay (press H)
- **Error Display**: Structured error panel with tracebacks
- **Resize Handling**: Adaptive layouts for different terminal sizes
- **Progress Debouncing**: Prevents UI spam from rapid updates
- **Structured Logging**: Enhanced logging with performance timing and context

### TUI Commands
```bash
# Launch interactive TUI
uv run python -m bias_detector.tui

# With custom configuration
uv run python -m bias_detector.tui --config custom_config.yaml

# With custom sessions directory
uv run python -m bias_detector.tui --sessions /custom/path
```

### TUI Architecture
- **Screens**: ProgressScreen, MetadataScreen, ConfigEditorScreen, HistoryScreen, HelpScreen
- **Widgets**: PhaseProgressBar, PhaseList, MetricDisplay, ErrorPanel
- **State Management**: StateManager with session persistence
- **Event System**: Queue-based progress updates with debouncing
- **Error Handling**: StructuredLogger with JSON output and performance timing

### TUI Polish Features (Phase 7)
- **Help Overlay**: Modal help screen with keyboard shortcuts (H)
- **Terminal Resize**: Responsive layouts for all screen sizes
- **Error Panel**: Comprehensive error display with filtering and details
- **Update Debouncing**: 200ms debounce to prevent UI spam
- **Structured Logging**: Component-aware logging with performance metrics


## Active Technologies
- Python >= 3.12 (matching existing project requirement) (001-interactive-tui)

## Recent Changes
- 001-interactive-tui: Added Python >= 3.12 (matching existing project requirement)
