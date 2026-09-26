"""Student boundary for finite batches of streamed response events."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class StreamEvent:
    """A numbered event from one logical stream."""

    stream_id: str
    sequence: int
    kind: Literal["delta", "done", "error"]
    text: str = ""


@dataclass(frozen=True)
class StreamResult:
    """Assembled delta text plus completion or error status."""

    text: str
    status: Literal["incomplete", "complete", "error"]
    error: str | None


def assemble_stream(stream_id: str, events: tuple[StreamEvent, ...]) -> StreamResult:
    """Validate stream structure and assemble events in sequence order."""
    if not isinstance(stream_id, str) or not stream_id.strip():
        raise ValueError("stream_id must be a nonblank string")
    for event in events:
        if event.stream_id != stream_id:
            raise ValueError("every event must belong to the requested stream")
        if type(event.sequence) is not int or event.sequence < 0:
            raise ValueError("sequence must be a nonnegative integer")
        if event.kind not in ("delta", "done", "error") or not isinstance(event.text, str):
            raise ValueError("event kind or text is invalid")
        if event.kind == "done" and event.text != "":
            raise ValueError("done events must have empty text")
        if event.kind == "error" and not event.text.strip():
            raise ValueError("error events must have a nonblank message")
    # TODO: enforce contiguous unique sequence numbers and terminal-event policy.
    # TODO: assemble exact delta text and derive completion/error metadata.
    raise NotImplementedError("assemble a museum-answer stream")
