# Quick Start Guide

Get started with the Bias Detection Framework in minutes!

## Prerequisites

- Python 3.12+
- Apple Silicon Mac (for mflux) or CUDA GPU
- At least 16GB RAM recommended
- ~10GB disk space for models and data

## Installation

```bash
# Clone or navigate to the project
cd BiasInGenerativeAi

# Install dependencies (using uv)
uv sync

# Or with pip
pip install -e .
```

## First Run - Quick Test (5 minutes)

Test the framework with a minimal configuration:

### 1. Edit the config

Open `config/experiment_config.yaml` and set:

```yaml
generation:
  num_images_per_prompt: 5  # Start small for testing
```

### 2. Run a quick example

```bash
python example_usage.py --example 1
```

This will:
- Generate 5 images for one prompt
- Analyze them with BLIP-2
- Calculate basic statistics

### 3. Check the results

```bash
ls data/raw/images/        # Generated images
ls data/processed/         # Analysis results
```

## Full Experiment (30-60 minutes)

Run the complete bias detection pipeline:

```bash
python run_experiment.py
```

This will:
1. **Generate images** (50 per prompt × ~15 prompts = ~750 images)
2. **Analyze with VQA** (~5-10 min for 750 images)
3. **Calculate statistics** (chi-square, effect sizes, CIs)
4. **Create visualizations**
5. **Log to MLflow** for reproducibility

## View Results

### 1. Check visualizations

```bash
open data/results/visualizations/summary_figure.png
```

### 2. View statistical summary

```bash
cat data/results/statistical_summary.json
```

### 3. Launch MLflow UI

```bash
mlflow ui
# Open http://localhost:5000
```

## Common Tasks

### Change the Model

Edit `config/experiment_config.yaml`:

```yaml
generation:
  model: "schnell"  # Options: dev, schnell, pro
```

### Add Custom Prompts

Edit `config/experiment_config.yaml`:

```yaml
prompts:
  my_category:
    - "Your custom prompt here"
    - "Another prompt"
```

### Change VQA Model

Edit `config/experiment_config.yaml`:

```yaml
vqa_analysis:
  model: "Salesforce/blip2-flan-t5-xl"  # Larger BLIP-2 model
```

### Run Only Specific Phases

```bash
# Just generate images
python run_experiment.py --phase generate

# Just analyze existing images
python run_experiment.py --phase analyze

# Just calculate statistics
python run_experiment.py --phase statistics
```

## Understanding the Output

### Image Files

Located in `data/raw/images/`:

```
dev_occupational_00_42_0001.png         # Generated image
dev_occupational_00_42_0001.json        # Metadata (prompt, seed, params)
```

### Analysis Results

Located in `data/processed/analysis_results.json`:

```json
{
  "image_path": "...",
  "prompt": "A professional doctor",
  "analysis": {
    "gender": {
      "raw_answer": "male",
      "matched_option": "male",
      "confidence": 1.0
    },
    "race_ethnicity": { ... }
  }
}
```

### Statistical Summary

Located in `data/results/statistical_summary.json`:

```json
{
  "experiment": "bias_detection_baseline",
  "total_images_analyzed": 750,
  "bias_analyses": {
    "gender": {
      "chi_square_test": {
        "chi_square_statistic": 156.4,
        "p_value": 0.0001,
        "cramers_v": 0.456,
        "effect_size": "large",
        "significant": true
      },
      "distribution": { ... }
    }
  }
}
```

## Interpreting Results

### Statistical Significance

- **p-value < 0.05**: Significant bias detected
- **p-value ≥ 0.05**: No significant bias (uniform distribution)

### Effect Size (Cramer's V)

- **< 0.1**: Negligible effect
- **0.1-0.3**: Small effect
- **0.3-0.5**: Medium effect
- **> 0.5**: Large effect

### Demographic Parity

- **Max deviation < 0.1**: Parity satisfied (roughly equal representation)
- **Max deviation ≥ 0.1**: Parity violated (unequal representation)

## Example Interpretation

```
Gender Analysis:
  χ² = 156.40, p = 0.0001  → Highly significant bias
  Cramer's V = 0.456 (medium-large)  → Substantial effect
  Max deviation = 0.35  → Large disparity from uniform

Conclusion: The model shows significant gender bias,
substantially favoring one gender over others.
```

## Troubleshooting

### Out of Memory

Reduce batch size or image count:

```yaml
generation:
  num_images_per_prompt: 20  # Reduce from 50
```

### Model Download Issues

Models are auto-downloaded from Hugging Face. If you have issues:

```bash
# Set cache directory
export HF_HOME=/path/to/cache

# Or manually download
huggingface-cli download Salesforce/blip2-opt-2.7b
```

### Slow Generation

- Use `model: "schnell"` (faster, fewer steps)
- Reduce image resolution in config
- Generate fewer images per prompt

### VQA Accuracy Issues

- Try a larger VQA model: `Salesforce/blip2-flan-t5-xl`
- Implement human validation (Phase 7)
- Use multiple VQA models and ensemble results

## Next Steps

1. **Customize prompts** for your research questions
2. **Run counterfactual analysis** (Phase 6)
3. **Add human validation** (Phase 7)
4. **Compare multiple models**
5. **Explore Jupyter notebooks** for custom analysis

## Resources

- **Full README**: [README.md](README.md)
- **Research Framework**: [docs/spec.md](docs/spec.md)
- **Examples**: [example_usage.py](example_usage.py)
- **Configuration**: [config/experiment_config.yaml](config/experiment_config.yaml)

## Getting Help

- Check the [README.md](README.md) for detailed documentation
- Review [docs/spec.md](docs/spec.md) for methodology
- Examine example code in [example_usage.py](example_usage.py)

---

**Ready to detect bias?** Run `python run_experiment.py` to get started!
