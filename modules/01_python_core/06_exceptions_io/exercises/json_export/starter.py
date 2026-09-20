"""Student boundary for exporting JSON with atomic replacement."""

from pathlib import Path


def export_json_atomic(payload: object, destination: Path) -> Path:
    """Write UTF-8 JSON through a sibling temporary file and return destination.

    Preserve an existing destination and clean up the temporary path if serialization
    or replacement fails. Propagate the original error unchanged.
    """
    raise NotImplementedError("export JSON with atomic replacement")
