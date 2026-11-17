"""Reload both image contexts through the classifier used at service startup."""

from pathlib import Path

from ..artifacts import load_trusted_local_classifier, predict_documents, read_json
from ..production_readiness._test_support import make_bundles
from .prepare import prepare


def test_two_reloadable_json_models_serve_distinct_answers(tmp_path: Path) -> None:
    source = make_bundles(tmp_path / "source") / "rules"
    run = tmp_path / "evidence"
    prepare(source, run, "exampletoken", "triangle")
    expected = read_json(run / "expect.json")
    for variant, label in (("a", "circle"), ("b", "triangle")):
        config = read_json(run / variant / "service.json")
        bundle = run / variant / "bundle"
        digest = config["expected_manifest_sha256"]
        loaded = load_trusted_local_classifier(bundle, digest)
        assert predict_documents(loaded, [expected["probe"]]) == [label]
        assert expected[variant] == {
            "predicted_label": label,
            "bundle_sha256": digest,
            "model_id": loaded.bundle.manifest["model"]["id"],
            "preprocessing_version": loaded.bundle.manifest["preprocessing"]["version"],
        }
