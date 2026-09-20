"""Read JSON and translate an invalid status into a domain exception."""

import json
import tempfile
from pathlib import Path
from typing import TypedDict


class Summary(TypedDict):
    document: str
    status: str


class InvalidSummaryStatusError(ValueError):
    """The summary status is not part of the supported domain vocabulary."""


def load_summary(source: Path) -> Summary:
    with source.open(encoding="utf-8") as handle:
        payload: object = json.load(handle)

    if not isinstance(payload, dict):
        raise TypeError("summary must be a JSON object")
    document = payload.get("document")
    status = payload.get("status")
    if not isinstance(document, str):
        raise TypeError("summary document must be a string")
    if not isinstance(status, str) or status not in {"ready", "failed"}:
        raise InvalidSummaryStatusError(f"unsupported summary status: {status}")

    return {"document": document, "status": status}


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "summary.json"
        source.write_text('{"document":"terms","status":"ready"}', encoding="utf-8")
        print(load_summary(source))

        source.write_text('{"document":"terms","status":"pending"}', encoding="utf-8")
        try:
            load_summary(source)
        except InvalidSummaryStatusError as error:
            print(f"rejected: {error}")


if __name__ == "__main__":
    main()
