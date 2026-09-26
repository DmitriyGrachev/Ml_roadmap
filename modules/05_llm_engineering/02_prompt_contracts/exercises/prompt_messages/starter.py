"""Construct library-reference messages without promoting data to instructions."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Document:
    identifier: str
    text: str


@dataclass(frozen=True)
class Message:
    role: Literal["system", "user"]
    content: str


def build_messages(
    instruction: str, question: str, documents: tuple[Document, ...]
) -> tuple[Message, ...]:
    """Build two messages using the validation and JSON contract in README.md."""
    raise NotImplementedError("Implement the library prompt boundary")
