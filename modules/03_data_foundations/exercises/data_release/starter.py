"""Learner-owned release boundary; internal stages are deliberately unspecified."""

from collections.abc import Sequence
from pathlib import Path


def build_release(inputs: Sequence[Path], output_dir: Path, *, batch_size: int) -> Path:
    """Return a completed manifest for a deterministic, bounded-resource release."""
    # TODO: implement the documented release semantics and justify resource usage.
    raise NotImplementedError("build and defend a reproducible data release")
