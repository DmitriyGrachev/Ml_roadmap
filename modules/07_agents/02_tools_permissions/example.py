"""Filter a trusted tool catalogue before exposing names to a model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolCard:
    name: str
    required_permission: str
    description: str


CATALOGUE = (
    ToolCard("lookup_exhibit", "catalog:read", "Read a public exhibit description."),
    ToolCard("reserve_workshop", "workshops:reserve", "Reserve a workshop place."),
)


def visible_tools(permissions: frozenset[str]) -> tuple[str, ...]:
    return tuple(sorted(card.name for card in CATALOGUE if card.required_permission in permissions))


def main() -> None:
    print(visible_tools(frozenset({"catalog:read"})))
    print("Discovery filtering helps; dispatch must recheck permission for every call.")


if __name__ == "__main__":
    main()
