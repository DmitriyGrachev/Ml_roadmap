"""An application-owned interface and a deterministic local provider."""

from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class CompletionRequest:
    instruction: str
    source: str
    max_output_tokens: int


@dataclass(frozen=True)
class Completion:
    text: str
    finish_reason: Literal["stop", "length", "refusal"]
    input_tokens: int
    output_tokens: int


class LabelClient(Protocol):
    def complete(self, request: CompletionRequest) -> Completion:
        """Adapt provider-specific transport and response fields to this contract."""
        ...


@dataclass(frozen=True)
class FixedClient:
    response: Completion

    def complete(self, request: CompletionRequest) -> Completion:
        """Return a fixture; this fake neither tokenizes nor performs inference."""
        return self.response


def generate_label(client: LabelClient) -> str:
    request = CompletionRequest(
        instruction="Write one short museum label using only the supplied facts.",
        source="Object: brass telescope. Built in 1890. Maker unknown.",
        max_output_tokens=80,
    )
    result = client.complete(request)
    if result.finish_reason != "stop":
        raise ValueError(f"incomplete label: {result.finish_reason}")
    return result.text


def main() -> None:
    fixture = Completion("A brass telescope built in 1890; its maker is unknown.", "stop", 30, 14)
    print(generate_label(FixedClient(fixture)))
    print("Fixture usage only: 30 input / 14 output tokens; no model was called.")


if __name__ == "__main__":
    main()
