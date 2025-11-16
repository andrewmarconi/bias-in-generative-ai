#!/usr/bin/env python3
"""
Command-line interface for the Bias Detection Framework.

Usage:
    python -m bias_detector.cli              # Run full experiment
    python -m bias_detector.cli --phase setup     # Just setup
    python -m bias_detector.cli --config custom.yaml  # Custom config
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from bias_detector.experiment import BiasDetectionExperiment


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Setup logging configuration."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path))

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI."""
    parser = argparse.ArgumentParser(
        description="Bias Detection Framework for Generative AI Image Models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Run full experiment
  %(prog)s --phase setup            # Just setup components
  %(prog)s --phase generate         # Just generate images
  %(prog)s --config custom.yaml     # Use custom config
  %(prog)s --log-level DEBUG        # Enable debug logging
        """
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config/experiment_config.yaml',
        help='Path to experiment configuration file'
    )
    parser.add_argument(
        '--phase',
        type=str,
        choices=['all', 'setup', 'generate', 'analyze', 'statistics'],
        default='all',
        help='Which phase to run'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        help='Path to log file (optional)'
    )

    return parser


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)

    try:
        # Create and run experiment
        logger.info("Starting Bias Detection Experiment")
        logger.info(f"Configuration: {args.config}")
        logger.info(f"Phase: {args.phase}")

        experiment = BiasDetectionExperiment(config_path=args.config)
        experiment.setup()

        if args.phase == 'all':
            experiment.run_full_experiment()
        elif args.phase == 'setup':
            logger.info("Setup complete!")
        elif args.phase == 'generate':
            experiment.run_phase_1_design()
            experiment.run_phase_2_prompts()
            experiment.run_phase_3_generation()
        elif args.phase == 'analyze':
            experiment.run_phase_4_analysis()
        elif args.phase == 'statistics':
            experiment.run_phase_5_statistics()

        logger.info("Experiment completed successfully")

    except KeyboardInterrupt:
        logger.info("Experiment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Experiment failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()