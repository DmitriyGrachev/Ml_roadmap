"""Run learning roadmap workflows from a repository checkout."""

from __future__ import annotations

from pathlib import Path

from roadmap_tools.cli import main

if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[1]
    raise SystemExit(main(repository_root=repository_root))
