#!/usr/bin/env python3
"""Health check for MLflow integration.

This script verifies that the MLflow tracker can initialize an experiment and start a run
without crashing, and that configuration logging can be performed.
"""
import sys
from bias_detector.utils.config import load_config
from bias_detector.utils.mlflow_tracker import MLflowTracker

def main():
    try:
        config = load_config("config/experiment_config.yaml")
        tracker = MLflowTracker(config)
        run_id = tracker.start_run("healthcheck")
        if run_id:
            tracker.log_configuration()
            print(f"MLflow healthcheck OK: run_id={run_id}")
            tracker.end_run()
            sys.exit(0)
        else:
            print("MLflow healthcheck failed: no run_id returned")
            sys.exit(1)
    except Exception as e:
        print(f"MLflow healthcheck exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
