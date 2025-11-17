#!/usr/bin/env bash
set -euo pipefail

# Compare model runs across multiple diffusion model configurations by orchestrating
# runs of the main experiment with each config and collecting MLflow results.

CONFIGS=(
  "configs/sd_v1_5_config.yaml"
  "configs/sd_2_1_config.yaml"
  "configs/sdxl_config.yaml"
  "configs/flux_config.yaml"
)

OUTPUT_DIR="logs/compare_runs"
mkdir -p "$OUTPUT_DIR"
CSV="$OUTPUT_DIR/summary.csv"
echo "config,run_id,logfile,status" > "$CSV"

PYTHON_SCRIPT="$(pwd)/scripts/compare_model_runs.py"

for cfg in "${CONFIGS[@]}"; do
  base=$(basename "$cfg" .yaml)
  log="$OUTPUT_DIR/${base}.log"
  echo "[INFO] Running: $cfg (log: $log)"
  uv run python "$PYTHON_SCRIPT" --config "$cfg" --log "$log" --output "$CSV" || true
  # The Python script appends an entry to the CSV; if it failed, mark status
  if tail -n 1 "$CSV" | grep -q "failed"; then
    echo "[WARN] Result for $cfg may have failed; check $CSV" >> "$CSV"
  fi
done

echo "Comparison complete. Summary written to $CSV"