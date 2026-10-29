"""Package learner-produced lab-02 real artifacts; never train, download or author analysis."""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path
from typing import Any

from projects.external_tabular.evidence import (
    artifact_path,
    check_equal,
    json_bytes,
    make_evaluation,
    nonempty,
    read_json,
    write_bundle,
)

from .protocol import LAB, validate_submission


def assemble(
    real_run: Path, cache: Path, output: Path, *, study: Path, analysis: Path, code: Path
) -> dict[str, Any]:
    report = read_json(real_run / "report.json")
    if report.get("evidence") != "PRETRAINED_MODEL_STUDENT_RUN":
        raise ValueError("only real pretrained-model evidence can be packaged")
    resources = importlib.import_module(LAB + ".download").verify_cache(cache)
    for key in ("model", "dataset"):
        check_equal(report.get(key), resources[key], f"real report {key}")
    own_study = read_json(study)
    selected = read_json(artifact_path(real_run, report["data"]["path"]))
    splits = read_json(artifact_path(real_run, report["splits"]["path"]))
    groups = own_study.get("groups", {})
    if set(groups) != {row["row_id"] for row in selected["records"]}:
        raise ValueError("independently audited groups must cover exactly all selected row IDs")
    data = {
        "classes": [0, 1, 2, 3],
        "records": [{**row, "group_id": groups[row["row_id"]]} for row in selected["records"]],
    }
    methods = {
        name: {"predictions": row["predictions"], "seconds": row["warm_seconds"]}
        for name, row in report["methods"].items()
    }
    evaluation = make_evaluation(data, splits, methods, "tfidf_linear", "adapted_encoder")
    check_equal(report.get("labels"), evaluation["labels"], "real report labels")
    check_equal(report.get("test_ids"), splits["test"], "real report test IDs")
    own_study.update(
        {
            key: report[key]
            for key in (
                "model",
                "dataset",
                "config",
                "preprocessing",
                "versions",
                "code_revision",
                "code_dirty",
            )
        }
    )
    resource = resources["dataset"]
    payloads = {
        "raw": ("raw.csv", (cache / "dataset" / resource["files"][0]["filename"]).read_bytes()),
        "data": ("data.json", json_bytes(data)),
        "splits": ("splits.json", json_bytes(splits)),
        "evaluation": ("evaluation.json", json_bytes(evaluation)),
        "source": (
            "source.json",
            json_bytes(
                {
                    "provider": resource["id"],
                    "url": f"https://huggingface.co/datasets/{resource['id']}/tree/{resource['revision']}",
                    "license": resource["license"],
                    "retrieved_at": own_study.get("retrieved_at"),
                    "permission_note": own_study.get("permission_note"),
                }
            ),
        ),
        "study": ("study.json", json_bytes(own_study)),
        "original_lab_report": ("lab-report.json", (real_run / "report.json").read_bytes()),
        "analysis": ("analysis.md", analysis.read_bytes()),
        "code": ("experiment.py", code.read_bytes()),
    }
    for spec in resources["model"]["files"]:
        name = spec["filename"]
        payloads["base/" + name] = ("base/" + name, (cache / "model" / name).read_bytes())
    checkpoint = real_run / "checkpoint"
    for path in checkpoint.iterdir():
        if path.is_file() and not path.is_symlink():
            payloads["adapted/" + path.name] = ("adapted/" + path.name, path.read_bytes())
    # Includes the exact learner boundary implementation used by the real runner.
    lab_starter = Path(
        nonempty(importlib.import_module(LAB + ".starter").__file__, "lab starter path")
    )
    payloads["lab_starter"] = ("lab-starter.py", lab_starter.read_bytes())
    write_bundle(
        output,
        project_id="document-external-model-study",
        evidence_kind="INDEPENDENT_EXTERNAL_RUN",
        payloads=payloads,
    )
    return validate_submission(output)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Package and replay your own lab-02 real experiment"
    )
    parser.add_argument("--real-run", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=Path(".cache/roadmap-huggingface"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--code", type=Path, required=True)
    args = parser.parse_args()
    print(
        assemble(
            args.real_run,
            args.cache,
            args.output,
            study=args.study,
            analysis=args.analysis,
            code=args.code,
        )
    )


if __name__ == "__main__":
    main()
