"""Export JSON and translate an invalid status into a domain exception."""

import json
import tempfile
from pathlib import Path


class InvalidSummaryStatusError(ValueError):
    """The summary status is not part of the supported domain vocabulary."""


def export_summary(destination: Path, *, status: str = "ready") -> Path:
    if status not in {"ready", "failed"}:
        raise InvalidSummaryStatusError(f"unsupported summary status: {status}")

    temporary = destination.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump({"document": "terms", "status": status}, handle)
    temporary.replace(destination)
    return destination


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        exported = export_summary(Path(directory) / "summary.json")
        print(exported.read_text(encoding="utf-8"))
        try:
            export_summary(Path(directory) / "invalid.json", status="pending")
        except InvalidSummaryStatusError as error:
            print(f"rejected: {error}")


if __name__ == "__main__":
    main()
