"""Student boundary: build and deliver the independent ticket package offline."""

from pathlib import Path


def deliver(project_dir: Path, work_dir: Path) -> Path:
    """Build a wheel, install into work_dir's clean venv, return its Python executable."""
    # TODO: use the available backend, no editable install and no source-path injection.
    raise NotImplementedError("deliver a ticket-features wheel into a clean environment")
