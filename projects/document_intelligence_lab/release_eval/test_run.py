import json
from contextlib import nullcontext
from pathlib import Path
from typing import Any

import pytest

from projects.document_intelligence_lab.release_eval import run, service
from projects.document_intelligence_lab.release_eval.run import main


@pytest.mark.parametrize(("candidate", "code"), [("candidate", 0), ("regressed", 1)])
def test_release_cli(tmp_path: Path, candidate: str, code: int) -> None:
    out = tmp_path / "output"
    assert main(["--output-dir", str(out), "--candidate", candidate]) == code
    report = json.loads((out / "report.json").read_bytes())
    assert report["passed"] == (code == 0)
    assert report["mode"] == "offline"
    assert report["usage_unit"] == "whitespace_proxy"
    assert report["baseline"]["metrics"]["quality_rate"] == 0.8
    assert report["candidate"]["metrics"]["quality_rate"] == (1.0 if code == 0 else 0.4)
    assert report["candidate"]["metrics"]["estimated_cost_usd"] is None
    assert len({row["trace_id"] for row in report["candidate"]["cases"]}) == 5
    exact = next(row for row in report["candidate"]["cases"] if row["case_id"] == "q-exact")
    assert exact["retrieved_ids"] == ["A-SCAN@1:p1"]
    assert bool(exact["context_ids"]) == (code == 0)
    assert "digitisation resolution" not in (out / "traces.json").read_text()
    assert main(["--output-dir", str(out)]) == 2


def test_live_rejects_incomplete_config(tmp_path: Path) -> None:
    assert main(["--output-dir", str(tmp_path / "out"), "--mode", "local"]) == 2


def test_provider_distinguishes_abstention_bad_output_and_missing_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def stub_reply(content: str, *, usage: bool = True, model: str = "fixture") -> None:
        response = {
            "model": model,
            "choices": [{"finish_reason": "stop", "message": {"content": content}}],
            "usage": {"prompt_tokens": 15, "completion_tokens": 5} if usage else {},
        }
        monkeypatch.setattr(service, "post_json", lambda *_: response)

    answer = service.local_generator("http://127.0.0.1/v1/chat/completions", "fixture", None)
    public = service.Passage("p1", "s1", "Reading at noon.")
    stub_reply('{"answer":null,"citation":null}')
    assert answer("what time?", public).status == "no_answer"
    stub_reply('{"answer":"noon","citation":"absent"}')
    assert answer("what time?", public).status == "invalid_output"
    stub_reply("bad JSON")
    assert answer("what time?", public).status == "invalid_output"
    stub_reply("{}", usage=False)
    with pytest.raises(ValueError, match="incomplete chat completion"):
        answer("time?", public)
    stub_reply("{}", model="other")
    with pytest.raises(ValueError, match="model ID differs"):
        answer("time?", public)


def test_model_only_comparison_calls_each_model_with_the_same_evidence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    first = "http://127.0.0.1:8123/v1/chat/completions"
    second = "http://127.0.0.1:8456/v1/chat/completions"
    calls: dict[str, list[tuple[str, str]]] = {"m-a": [], "m-b": []}

    def completion(url: str, payload: dict[str, Any], token: str | None) -> dict[str, Any]:
        model = payload["model"]
        msg = payload["messages"][1]["content"]
        calls[model].append((url, msg))
        passage = json.loads(msg)["evidence"]
        answer = passage["text"].split(". ", 1)[0].rstrip(".")
        reply = {"answer": answer, "citation": passage["chunk_id"]}
        return {
            "model": model,
            "usage": {"prompt_tokens": 10, "completion_tokens": 7},
            "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(reply)}}],
        }

    # Exercise model selection and scoring independently of TCP availability.
    monkeypatch.setattr(run, "serve_api", lambda api: nullcontext(api.answer))
    monkeypatch.setattr(service, "post_json", completion)
    out = tmp_path / "out"
    argv = [
        "--output-dir",
        str(out),
        "--mode",
        "local",
        "--candidate",
        "matched",
        "--endpoint",
        first,
        "--model",
        "m-a",
        "--model-revision",
        "r1",
        "--candidate-endpoint",
        second,
        "--candidate-model",
        "m-b",
        "--candidate-model-revision",
        "r2",
        "--candidate-input-usd-per-million",
        "1",
        "--candidate-output-usd-per-million",
        "2",
    ]
    assert main(argv) == 0
    report = json.loads((out / "report.json").read_bytes())
    assert report["baseline"]["model"] == {"id": "m-a", "revision": "r1"}
    assert report["candidate"]["model"] == {"id": "m-b", "revision": "r2"}
    assert report["baseline"]["metrics"]["estimated_cost_usd"] is None
    assert report["candidate"]["metrics"]["estimated_cost_usd"] == pytest.approx(48 / 1e6)
    assert len(calls["m-a"]) == len(calls["m-b"]) == 2
    assert [u for u, _ in calls["m-a"]] == [first, first]
    assert [u for u, _ in calls["m-b"]] == [second, second]
    assert [msg for _, msg in calls["m-a"]] == [msg for _, msg in calls["m-b"]]
    out2 = tmp_path / "incomplete"
    assert main([*argv[:1], str(out2), *argv[2:16]]) == 2
