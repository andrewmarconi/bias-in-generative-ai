# Usage (Diffusers Edition)

This guide describes how to use the Bias Detection Framework with HuggingFace diffusers, enabling testing across multiple diffusion models.

## Model Switching (Diffusers)
Easily switch the diffusion model by editing the experiment config.

### Quick Switch
1) Edit config/experiment_config.yaml:

```yaml
generation:
  model: "stabilityai/stable-diffusion-2-1"  # choose from SD2.1, SD1-5, SDXL, etc.
```
2) Run the generation phase:
```bash
uv run python run_experiment.py --phase generate
```

### Model Performance Comparison
| Model | Quality | Speed | Memory | Best For |
|-------|---------|-------|--------|----------|
| SD v1.5 | Good | Fast | Low | Quick tests |
| SD 2.1 | Balanced | Medium | Medium | General use |
| SDXL | Best quality | Slow | High | High-fidelity output |
| Flux (via diffusers) | Cutting edge | Medium-High | High | Experimental research |

### Tips for Diffusers Models
- Use SD2.1 for quick iterations; SDXL for best quality when you have memory headroom.
- Use smaller image sizes (e.g., 512x512) to speed up tests.
- Enable or disable memory optimizations (attention slicing, xformers) depending on your hardware.

## Quick Test (5-10 minutes)
1) Set a small number of images per prompt:
```yaml
generation:
  num_images_per_prompt: 5
```
2) Run a quick example:
```bash
uv run python example_usage.py --example 1
```

## Phase-by-Phase Testing
- Setup: `uv run python run_experiment.py --phase setup`
- Generate: `uv run python run_experiment.py --phase generate`
- Analyze: `uv run python run_experiment.py --phase analyze`
- Statistics: `uv run python run_experiment.py --phase statistics`

## Viewing Results
- MLflow UI: `mlflow ui` (default port 5000) or your configured port
- Access artifacts and plots in the `data/` directory and MLflow UI

## Next Steps
- Add more models to the config for side-by-side comparisons
- Use multiple config files to compare performance across models
- Use MLflow to track results and artifacts for reproducibility
