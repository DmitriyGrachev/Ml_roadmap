"""Both tenant ownership and application-issued scope must permit access."""

import pytest

from .example import Principal, main, read_private_note


def test_authorized_read_is_explicit() -> None:
    assert read_private_note(Principal("a", frozenset({"notes:read"})), "a").startswith("Synthetic")


@pytest.mark.parametrize(
    ("tenant", "scopes"), [("b", frozenset({"notes:read"})), ("a", frozenset())]
)
def test_denied_read_does_not_return_private_data(tenant: str, scopes: frozenset[str]) -> None:
    with pytest.raises(PermissionError, match="denied"):
        read_private_note(Principal(tenant, scopes), "a")


def test_example_is_repeatable(capsys: pytest.CaptureFixture[str]) -> None:
    main()
    first = capsys.readouterr().out
    main()
    assert capsys.readouterr().out == first
