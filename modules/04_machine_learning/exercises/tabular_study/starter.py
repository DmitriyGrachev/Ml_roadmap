"""Student-owned experiment: reuse completed prerequisites, justify your choices."""

from pathlib import Path


def run_experiment(data_path: Path, output_dir: Path, *, seed: int) -> Path:
    """Create a new output directory and return its local manifest.json path.

    The README defines evidence, budget, and review requirements. Existing output
    directories must raise FileExistsError; no saved learner work is overwritten.
    """
    # TODO: define the study, freeze group folds, compare candidates and calibration.
    # TODO: reuse your threshold/report/paired-statistics work; freeze before test.
    # TODO: persist evidence for replay and a reasoned analysis for human review.
    raise NotImplementedError("independent tabular study")
