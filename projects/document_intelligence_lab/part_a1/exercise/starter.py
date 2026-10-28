"""Independent reproduction boundary. Do not call the shape teacher demo."""

from pathlib import Path


def run_reproduction(fixtures: Path, output: Path, *, seed: int = 23) -> Path:
    """Create two own library-notice bundles and report.json in a NEW output path.

    Use contracts/artifacts helpers; choose rules and a train-only sklearn pipeline,
    freeze choices on validation, measure actual timings, record code/config/version,
    and verify relocation/reload. Read README.md for the output and defense contract.
    """
    raise NotImplementedError("Create and reproduce your independent library-notice experiment")
