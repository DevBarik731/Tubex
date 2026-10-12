#!/usr/bin/env python3
"""TubeX - Terminal YouTube Player.

Main executable wrapper delegating to the modular src/ application.
"""
from __future__ import annotations

import os
import sys

# Ensure repository root is on sys.path
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.main import main

if __name__ == "__main__":
    main()
