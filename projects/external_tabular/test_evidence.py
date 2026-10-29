"""Adversarial tests own their artifacts; no completed learner submission."""

from __future__ import annotations

import importlib
import itertools
import json
from pathlib import Path
from typing import Any

import pytest


def api() -> Any:
    try:
        return importlib.import_module("projects.external_tabular.evidence")
    except ModuleNotFoundError:
        pytest.fail("external experiment evidence validator is not implemented")


def demo() -> Any:
    try:
        return importlib.import_module("projects.external_tabular.demo")
    except ModuleNotFoundError:
        pytest.fail("author walkthrough is not implemented")


@pytest.fixture
def bundle(tmp_path: Path) -> Path:
    root = tmp_path / "author"
    demo().run(root)
    return root


def rewrite(root: Path, logical: str, value: object) -> None:
    module = api()
    manifest = module.read_json(root / "manifest.json")
    record = manifest["artifacts"][logical]
    (root / record["path"]).write_text(json.dumps(value), encoding="utf-8")
    record["sha256"] = module.sha256(root / record["path"])
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_author_fixture_validates_arithmetic_but_cannot_earn_credit(bundle: Path) -> None:
    result = api().validate_bundle(bundle, project_id="ml-external-tabular", author_fixture=True)
    assert result["technical_status"] == "AUTHOR_FIXTURE_ONLY"
    assert result["human_review"] == "REQUIRED"
    with pytest.raises(ValueError, match=r"external|author|evidence_kind"):
        api().validate_bundle(bundle, project_id="ml-external-tabular")


@pytest.mark.parametrize(
    "change",
    [
        "metric",
        "labels",
        "order",
        "overlap",
        "group",
        "missing",
        "hash",
        "path",
        "bool",
        "nan",
        "uncertainty",
        "slice",
    ],
)
def test_adversarial_artifacts_rejected_even_when_rehashed(bundle: Path, change: str) -> None:
    module = api()
    manifest = module.read_json(bundle / "manifest.json")
    if change in {"hash", "path", "bool"}:
        if change == "hash":
            manifest["artifacts"]["data"]["sha256"] = "0" * 64
        elif change == "path":
            manifest["artifacts"]["data"]["path"] = "../outside.json"
        else:
            manifest["schema_version"] = True
        (bundle / "manifest.json").write_text(json.dumps(manifest))
    elif change in {"overlap", "group"}:
        logical = "splits" if change == "overlap" else "data"
        value = module.read_json(bundle / manifest["artifacts"][logical]["path"])
        if change == "overlap":
            value["test"][0] = value["train"][0]
        else:
            value["records"][-1]["group_id"] = value["records"][0]["group_id"]
        rewrite(bundle, logical, value)
    else:
        value = module.read_json(bundle / "evaluation.json")
        if change == "metric":
            value["methods"]["linear"]["metrics"]["accuracy"] = 0.123
        elif change == "labels":
            value["labels"][0] = 1 - value["labels"][0]
        elif change == "order":
            value["row_ids"].reverse()
        elif change == "missing":
            del value["methods"]["linear"]
        elif change == "nan":
            value["methods"]["linear"]["seconds"] = float("nan")
        elif change == "uncertainty":
            value["paired_bootstrap"]["low"] = -0.12345
        else:
            value["slices"][0]["methods"]["linear"]["count"] += 1
        rewrite(bundle, "evaluation", value)
    with pytest.raises(ValueError, match=r".+"):
        module.validate_bundle(bundle, project_id="ml-external-tabular", author_fixture=True)


def test_missing_submission_is_an_unfinished_boundary(tmp_path: Path) -> None:
    with pytest.raises(NotImplementedError, match=r"submission"):
        api().submission_or_incomplete(tmp_path / "submission")


def test_bootstrap_is_paired_deterministic_and_rejects_wrong_alignment() -> None:
    function = api().paired_bootstrap
    result = function([0, 0, 1, 1], [0, 1, 1, 1], [0, 0, 1, 1], [0, 1])
    assert result == function([0, 0, 1, 1], [0, 1, 1, 1], [0, 0, 1, 1], [0, 1])
    assert result["low"] <= result["difference"] <= result["high"]
    with pytest.raises(ValueError, match=r".+"):
        function([0, 1], [0], [0, 1], [0, 1])


@pytest.mark.parametrize(
    ("project_id", "names", "central"),
    [
        ("ml-external-tabular", ("dummy", "linear", "tree"), ("linear", "tree")),
        (
            "document-external-model-study",
            ("frozen_embeddings", "tfidf_linear", "adapted_encoder"),
            ("tfidf_linear", "adapted_encoder"),
        ),
    ],
)
def test_central_bootstrap_pair_is_required_for_each_project(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    project_id: str,
    names: tuple[str, str, str],
    central: tuple[str, str],
) -> None:
    module, walkthrough = api(), demo()

    def saved_predictions(data: Any, splits: Any) -> dict[str, Any]:
        # Reuse the current bundle fixture with fixed predictions, never fit models.
        return {
            name: {"predictions": [0] * len(splits["test"]), "seconds": 0.0}
            for name in ("dummy", "linear", "tree")
        }

    monkeypatch.setattr(walkthrough, "fit_candidates", saved_predictions)
    root = tmp_path / "metadata-only"
    walkthrough.run(root)
    data, splits = (module.read_json(root / f"{name}.json") for name in ("data", "splits"))
    methods = dict(zip(names, saved_predictions(data, splits).values(), strict=True))
    manifest = module.read_json(root / "manifest.json")
    manifest["project_id"] = project_id
    (root / "manifest.json").write_bytes(module.json_bytes(manifest))
    rewrite(root, "evaluation", module.make_evaluation(data, splits, methods, *central))
    result = module.validate_bundle(root, project_id=project_id, author_fixture=True)
    assert result["technical_status"] == "AUTHOR_FIXTURE_ONLY"
    for pair in itertools.permutations(names, 2):
        if pair == central:
            continue
        # Recompute/re-hash all arithmetic so only the endpoint rule can reject it.
        rewrite(root, "evaluation", module.make_evaluation(data, splits, methods, *pair))
        with pytest.raises(ValueError, match="documented central baseline/candidate"):
            module.validate_bundle(root, project_id=project_id, author_fixture=True)


def test_tabular_rejects_source_rows_that_do_not_reproduce_saved_features(bundle: Path) -> None:
    module = api()
    data = module.read_json(bundle / "data.json")
    data["records"][0]["features"]["alcohol"] += 3
    rewrite(bundle, "data", data)
    with pytest.raises(ValueError, match=r"source|raw|features"):
        importlib.import_module("projects.external_tabular.protocol").validate_submission(bundle)


def test_relabelling_synthetic_csv_with_uci_url_does_not_make_it_external(bundle: Path) -> None:
    module = api()
    manifest = module.read_json(bundle / "manifest.json")
    manifest["evidence_kind"] = "INDEPENDENT_EXTERNAL_RUN"
    (bundle / "manifest.json").write_bytes(module.json_bytes(manifest))
    source = module.read_json(bundle / "source.json")
    source.update(
        provider="UCI Wine Quality",
        license="CC-BY-4.0",
        url="https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/"
        "winequality-red.csv",
    )
    rewrite(bundle, "source", source)
    with pytest.raises(ValueError, match="pinned raw"):
        importlib.import_module("projects.external_tabular.protocol").validate_submission(bundle)


def test_tabular_model_replay_catches_predictions_detached_from_fit(bundle: Path) -> None:
    module = importlib.import_module("projects.external_tabular.protocol")
    evidence = api().validate_bundle(bundle, project_id="ml-external-tabular", author_fixture=True)
    study = {
        "seed": 17,
        "configs": {
            "linear": {"C": 1.0},
            "tree": {"kind": "decision_tree", "max_depth": 2, "min_samples_leaf": 3},
        },
    }
    assert hasattr(module, "replay_tabular"), "tabular fit replay is not implemented"
    module.replay_tabular(
        evidence["data"], evidence["splits"], evidence["evaluation"]["methods"], study
    )
    prediction = evidence["evaluation"]["methods"]["linear"]["predictions"]
    prediction[0] = 1 - prediction[0]
    with pytest.raises(ValueError, match="replayed"):
        module.replay_tabular(
            evidence["data"], evidence["splits"], evidence["evaluation"]["methods"], study
        )
