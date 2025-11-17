#!/usr/bin/env python3
"""MLflow healthcheck CLI.

Verifies that MLflow can initialize an experiment, start a run, log configuration, and end the run.
Returns non-zero exit code on failure.
"""
import sys
from bias_detector.utils.config import load_config
from bias_detector.utils.mlflow_tracker import MLflowTracker


def main():
    try:
        config = load_config("config/experiment_config.yaml")
        tracker = MLflowTracker(config)
        run_id = tracker.start_run("healthcheck_cli")
        if run_id:
            tracker.log_configuration()
            tracker.end_run()
            print(f"MLflow healthcheck OK: run_id={run_id}")
            sys.exit(0)
        else:
            print("MLflow healthcheck failed: no run_id returned", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"MLflow healthcheck exception: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
