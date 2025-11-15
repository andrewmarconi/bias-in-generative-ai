#!/usr/bin/env python3
"""
Simple runner script for the bias detection experiment.

Usage:
    uv run python run_experiment.py              # Run full experiment
    uv run python run_experiment.py --phase setup     # Just setup
    uv run python run_experiment.py --config custom.yaml  # Custom config
"""

import sys
from pathlib import Path

from bias_detector.experiment import main

if __name__ == "__main__":
    main()
