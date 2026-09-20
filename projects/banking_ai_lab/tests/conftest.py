"""Make the project package importable from repository-root pytest runs."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]
PROJECT_ROOT_TEXT = str(PROJECT_ROOT)

if PROJECT_ROOT_TEXT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_TEXT)
