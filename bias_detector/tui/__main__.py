"""
CLI entry point for the Interactive TUI.

Usage:
    python -m bias_detector.tui
    uv run python -m bias_detector.tui
"""

import sys
import logging
from pathlib import Path

from .app import TUIApp


def main():
    """Run the TUI application."""
    # Setup logging to file to avoid interfering with TUI
    log_file = Path("data/tui.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger to redirect ALL logs to file
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        filename=str(log_file),
        filemode='a',
        force=True  # Override any existing configuration
    )
    
    # Completely disable console output for all loggers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        if isinstance(handler, logging.StreamHandler):
            root_logger.removeHandler(handler)
    
    # Add a null handler to completely suppress console output
    null_handler = logging.NullHandler()
    root_logger.addHandler(null_handler)
    
    # Also disable any specific loggers that might output to console
    for logger_name in ['bias_detector', 'textual', 'PIL', 'torch', 'transformers']:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.addHandler(logging.NullHandler())
        logger.propagate = False

    # Create and run app
    app = TUIApp()
    app.run()


if __name__ == "__main__":
    main()
