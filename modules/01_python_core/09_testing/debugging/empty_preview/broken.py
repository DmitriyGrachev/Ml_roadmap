"""Intentional defect, separate from the usable walkthrough."""

import traceback


def broken_preview(text: str, limit: int) -> str:
    """Wrong assumption: every document contains a first character."""
    return text[0] + text[1:limit]


def inspect_document(text: str) -> str:
    return broken_preview(text, 4)


def main() -> int:
    try:
        inspect_document("")
    except IndexError as error:
        print("Actual traceback frames (outermost first):")
        for frame in traceback.extract_tb(error.__traceback__):
            print(f"{frame.name}: {frame.line}")
        print(f"{type(error).__name__}: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
