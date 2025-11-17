#!/usr/bin/env python3
"""
Batch runner to compare multiple diffusion model configurations.
Runs the experiment for each config and aggregates results in a CSV.

Usage:
  python scripts/compare_model_runs.py [--configs config1.yaml config2.yaml ...] [--output logs/compare_runs/summary.csv]

Defaults:
  configs/sd_v1_5_config.yaml
  configs/sd_2_1_config.yaml
  configs/sdxl_config.yaml
  configs/flux_config.yaml
"""
import argparse
import subprocess
from pathlib import Path
import re
import csv
from datetime import datetime

DEFAULT_CONFIGS = [
    "configs/sd_v1_5_config.yaml",
    "configs/sd_2_1_config.yaml",
    "configs/sdxl_config.yaml",
    "configs/flux_config.yaml",
]

def run_config(cfg_path: str, log_path: Path) -> dict:
    cmd = ["uv", "run", "python", "run_experiment.py", "--config", cfg_path]
    with log_path.open("w") as logf:
        proc = subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT, text=True, timeout=60*60*3)
    # Parse MLflow run id from log
    run_id = None
    try:
        with log_path.open("r") as logf:
            for line in logf:
                m = re.search(r"Started MLflow run: (\S+)", line)
                if m:
                    run_id = m.group(1)
    except Exception:
        pass
    status = "completed" if proc.returncode == 0 else "failed"
    return {
        "config": cfg_path,
        "run_id": run_id or "",
        "log": str(log_path),
        "status": status,
        "exit_code": proc.returncode,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--configs", nargs="*", default=None, help="List of config files to run")
    parser.add_argument("--output", default="logs/compare_runs/summary.csv", help="CSV summary path")
    parser.add_argument("--log-dir", default="logs/compare_runs", help="Directory to store per-config logs")
    args = parser.parse_args()

    cfgs = args.configs if args.configs else DEFAULT_CONFIGS
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    summary_path = Path(args.output)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    with summary_path.open("w", newline="") as csvf:
        writer = csv.writer(csvf)
        writer.writerow(["config", "run_id", "logfile", "status", "exit_code"])
        results = []
        for cfg in cfgs:
            log_file = log_dir / (Path(cfg).stem + ".log")
            res = run_config(cfg, log_file)
            results.append(res)
            writer.writerow([res["config"], res["run_id"], res["log"], res["status"], res["exit_code"]])
    print(f"Comparison complete. Summary at {summary_path}")

if __name__ == "__main__":
    main()
