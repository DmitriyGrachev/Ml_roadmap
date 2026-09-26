"""Evidence envelopes retain identity and mark the text as data."""

import json
from importlib import import_module

import pytest

example = import_module("modules.06_rag.01_retrieval_contracts.example")


def test_envelope_is_json_compatible_and_preserves_source_revision() -> None:
    envelope = example.evidence_envelope()
    assert json.loads(json.dumps(envelope)) == envelope
    assert envelope["content_role"] == "untrusted_reference_data"
    assert envelope["corpus_snapshot"] == "library-fixture-v3"
    assert envelope["evidence"][0]["source_id"] == "library-north"
    assert envelope["evidence"][0]["revision"] == "r3"


def test_main_is_deterministic(capsys: pytest.CaptureFixture[str]) -> None:
    example.main()
    first = capsys.readouterr().out
    example.main()
    assert capsys.readouterr().out == first
