"""Read-only comparison of saved investigations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import fixtures


def validate_evidence(root: Path, *, trusted_student_source: Path | None = None) -> None:
    """Verify data/source bytes and replay traces; do not grade the explanation.

    Replay executes local Python. Only an explicit exact path authorizes the
    learner source; saved manifest text and hashes do not authorize execution.
    """
    saved_source = (root / "after" / "source.py").resolve()
    if trusted_student_source is None or trusted_student_source.resolve() != saved_source:
        raise ValueError(
            "trusted_student_source must explicitly name after/source.py; replay executes Python"
        )
    before = fixtures.load_run(root / "before")
    after = fixtures.load_run(root / "after")
    if before["case_id"] != after["case_id"] or before["seed"] != after["seed"]:
        raise ValueError("before/after evidence must use the same case and seed")
    original = Path(fixtures.__file__).with_name(f"case_{before['case_id']}.py")
    if original.read_bytes() != (root / "before" / "source.py").read_bytes():
        raise ValueError("before source differs from original supplied input")
    try:
        report = json.loads((root / "report.json").read_text(encoding="utf-8"))
        assert report["review_status"] == "REQUIRES_REVIEW"
        for field in ("hypotheses", "measurements", "minimal_change", "defense"):
            assert isinstance(report[field], str)
            assert report[field].strip()
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, AssertionError) as exc:
        raise ValueError("review material with REQUIRES_REVIEW is required") from exc
    for saved, source in ((before, original), (after, saved_source)):
        replay = dict(fixtures.observe(source, seed=saved["seed"]), case_id=saved["case_id"])
        try:
            fixtures.assert_same(saved, replay)
        except (AssertionError, TypeError, KeyError) as exc:
            raise ValueError("saved observations differ from actual replay") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument(
        "--trusted-student-source",
        type=Path,
        help="Execute this exact local Python source (not sandboxed)",
    )
    args = parser.parse_args()
    validate_evidence(args.root, trusted_student_source=args.trusted_student_source)
    print("Consistent observations; REQUIRES_REVIEW (not a correction or quality verdict)")


if __name__ == "__main__":
    main()
