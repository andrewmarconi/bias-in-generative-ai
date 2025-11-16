#!/usr/bin/env python3
"""
Simple runner script for the bias detection experiment.

Usage:
    uv run python run_experiment.py              # Run full experiment
    uv run python run_experiment.py --phase setup     # Just setup
    uv run python run_experiment.py --config custom.yaml  # Custom config
"""

from bias_detector.cli import main

if __name__ == "__main__":
    main()
