"""Offline library example, independent of the learner's TODO."""

from importlib import import_module

import pytest


def test_library_example_is_offline_and_has_expected_trace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("torch", reason="Install the optional training group")
    import socket

    def deny_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("offline example attempted network access")

    monkeypatch.setattr(socket, "create_connection", deny_network)
    monkeypatch.setattr(socket.socket, "connect", deny_network)
    example = import_module("labs.02_huggingface_models.attention_mechanics.example")
    result = example.run_example()
    assert result["output_shape"] == [1, 2, 3, 4]
    assert result["finite_output"] is True
    assert result["future_change_first_query_max_abs"] == 0.0
    assert result["padded_change_max_abs"] == 0.0
    assert result["evidence"] == "LIBRARY_SDPA_SYNTHETIC_ONLY"


def test_example_import_is_lazy_in_base_environment() -> None:
    example = import_module("labs.02_huggingface_models.attention_mechanics.example")
    assert callable(example.run_example)
