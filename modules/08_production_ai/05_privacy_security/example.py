"""Application-owned permissions protect a local fixture, independently of model text."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Principal:
    tenant: str
    scopes: frozenset[str]


def read_private_note(principal: Principal, owner_tenant: str) -> str:
    if principal.tenant != owner_tenant or "notes:read" not in principal.scopes:
        raise PermissionError("note access denied")
    return "Synthetic museum conservation note."


def main() -> None:
    principal = Principal("museum-a", frozenset({"notes:read"}))
    print(read_private_note(principal, "museum-a"))
    try:
        read_private_note(principal, "museum-b")
    except PermissionError:
        print("Cross-tenant request denied; no private note was returned.")


if __name__ == "__main__":
    main()
