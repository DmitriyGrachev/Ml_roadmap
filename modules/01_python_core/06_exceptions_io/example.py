"""Export JSON atomically inside a caller-provided temporary directory."""

import json
import tempfile
from pathlib import Path


def export_summary(destination: Path) -> Path:
    temporary = destination.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump({"document": "terms", "status": "ready"}, handle)
    temporary.replace(destination)
    return destination


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        exported = export_summary(Path(directory) / "summary.json")
        print(exported.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
