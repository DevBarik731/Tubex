"""CLI entrypoint for TubeX."""
from __future__ import annotations

import sys
from src.app import TubeXApp


def main() -> None:
    """Run the TubeX terminal player application."""
    app = TubeXApp()
    app.run()


if __name__ == "__main__":
    main()
