"""Student boundary for lazily parsing NDJSON transaction objects."""

from collections.abc import Iterable, Iterator

type TransactionObject = dict[str, object]


def stream_transactions(lines: Iterable[str]) -> Iterator[TransactionObject]:
    """Yield one JSON object per input line without materializing the input."""
    del lines
    yield from ()
    raise NotImplementedError("stream NDJSON transaction objects lazily")
