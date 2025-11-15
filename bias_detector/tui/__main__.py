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
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        filename="data/tui.log"
    )

    # Create and run app
    app = TUIApp()
    app.run()


if __name__ == "__main__":
    main()
