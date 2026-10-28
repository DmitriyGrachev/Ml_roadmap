"""Explicit offline lifecycle teacher: copied releases, recovery and measured toy windows."""

from __future__ import annotations

import argparse
import html
import statistics
import time
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from projects.document_intelligence_lab.artifacts import (
    LocalClassifier,
    file_sha256,
    json_bytes,
    load_trusted_local_classifier,
    predict_documents,
)
from projects.document_intelligence_lab.contracts import normalize_document
from projects.document_intelligence_lab.service.recovery import run_recovery

from .releases import restore_release_new, write_release_new


def measure_window(
    classifier: LocalClassifier,
    name: str,
    texts: Sequence[str],
    truths: Sequence[str | None],
) -> dict[str, Any]:
    """Real warm CPU predictions/timing; supplied toy labels are constructed, never inferred."""
    labels = classifier.bundle.dataset.labels
    if (
        isinstance(truths, (str, bytes))
        or len(truths) != len(texts)
        or any(truth is not None and truth not in labels for truth in truths)
    ):
        raise ValueError("labels must align with texts and belong to the saved label set")
    # Validate the entire bounded input before collecting per-row timings.
    predict_documents(classifier, texts)
    requests: list[dict[str, Any]] = []
    for text, truth in zip(texts, truths, strict=True):
        started = time.perf_counter()
        predicted = predict_documents(classifier, [text])[0]
        elapsed = time.perf_counter() - started
        requests.append({"prediction": predicted, "truth": truth, "seconds": elapsed})
    labeled = [row for row in requests if row["truth"] is not None]
    counts = Counter(row["prediction"] for row in requests)
    return {
        "window": name,
        "data_origin": "constructed teacher texts and label relation",
        "measurement": "actual warm CPU direct-call prediction; not HTTP latency",
        "bundle_sha256": classifier.bundle.manifest_sha256,
        "count": len(texts),
        "labeled_count": len(labeled),
        "label_availability": "absent"
        if not labeled
        else "complete"
        if len(labeled) == len(texts)
        else "partial",
        "accuracy": sum(row["prediction"] == row["truth"] for row in labeled) / len(labeled)
        if labeled
        else None,
        "triangle_token_fraction": sum(
            "triangle" in normalize_document(text).split() for text in texts
        )
        / len(texts),
        "predicted_proportions": {label: counts[label] / len(texts) for label in labels},
        "median_seconds": statistics.median(row["seconds"] for row in requests),
        "requests": requests,
    }


def _monitoring_svg(windows: list[dict[str, Any]]) -> str:
    maximum_ms = max(window["median_seconds"] * 1000 for window in windows)
    rows = []
    for index, window in enumerate(windows):
        y = 100 + 105 * index
        quality = window["accuracy"]
        rows.append(
            f'<text x="15" y="{y}">{html.escape(window["window"])}</text>'
            f'<text x="15" y="{y + 20}">n={window["count"]}; '
            f"labels={window['labeled_count']}/{window['count']}</text>"
            f'<rect x="240" y="{y - 15}" width="{window["triangle_token_fraction"] * 160}" '
            'height="16" fill="#8075b7"/>'
            f'<text x="410" y="{y}">{window["triangle_token_fraction"]:.2f}</text>'
            + (
                f'<rect x="240" y="{y + 10}" width="{quality * 160}" height="16" fill="#238575"/>'
                f'<text x="410" y="{y + 25}">{quality:.2f}</text>'
                if quality is not None
                else f'<text x="240" y="{y + 25}">unknown: no labels</text>'
            )
            + f'<rect x="530" y="{y - 15}" '
            f'width="{window["median_seconds"] * 1000 / maximum_ms * 160:.3f}" '
            'height="16" fill="#c17b35"/>'
            f'<text x="705" y="{y}">{window["median_seconds"] * 1000:.4f} ms</text>'
        )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="555" '
        'role="img" aria-labelledby="title desc">'
        '<title id="title">Constructed windows; measured toy classifier quality and time</title>'
        '<desc id="desc">Window order top to bottom. '
        "Purple is constructed triangle token fraction; "
        "green is actual accuracy on available constructed labels only; orange is measured warm "
        "median CPU direct call time. No-label quality is unknown. "
        "Not real population drift evidence.</desc>"
        '<rect width="900" height="555" fill="white"/>'
        '<g font-family="sans-serif" font-size="14" fill="#192c39">'
        '<text x="15" y="25">Constructed windows in order; '
        "actual toy inference (CPU, batch=1)</text>"
        '<text x="240" y="50">Feature fraction / accuracy</text>'
        '<text x="240" y="70">0                           1 (160 px)</text>'
        '<text x="530" y="50">Median warm call (ms)</text>'
        f'<text x="530" y="70">0 — {maximum_ms:.4f} ms (160 px)</text>'
        + "".join(rows)
        + '<text x="15" y="530">Purple: constructed inputs; green: measured accuracy; '
        "orange: measured time. No retraining policy.</text>"
        "</g></svg>"
    )


def run_demo(output: Path) -> Path:
    if output.exists():
        raise FileExistsError(f"lifecycle output already exists: {output}")
    output.mkdir(parents=True, exist_ok=False)
    recovery = run_recovery(output / "service-recovery", samples=2)
    releases = {}
    for name, method in (("A", "rules"), ("B", "tfidf-linear")):
        bundle = recovery / "teacher" / method
        manifest = write_release_new(
            bundle,
            output / f"release-{name}",
            expected_bundle_sha256=file_sha256(bundle / "manifest.json"),
        )
        releases[name] = file_sha256(manifest)
    restore_release_new(
        output / "release-A", output / "recovered-A", expected_release_sha256=releases["A"]
    )
    bundle_root = output / "recovered-A" / "bundle"
    classifier = load_trusted_local_classifier(
        bundle_root, file_sha256(bundle_root / "manifest.json")
    )
    base = ["circle", "square", "circle", "square"]
    shift = ["triangle", "triangle", "square", "circle"]
    windows = [
        measure_window(classifier, "reference", base, base),
        measure_window(classifier, "input-shift", shift, shift),
        measure_window(
            classifier, "label-relation-change", base, ["square", "circle", "square", "circle"]
        ),
        measure_window(classifier, "labels-delayed", shift, [None] * 4),
    ]
    (output / "lifecycle.json").write_bytes(
        json_bytes(
            {
                "evidence_kind": "AUTHOR_CONSTRUCTED_WINDOWS_ACTUAL_CPU_SMOKE_ONLY",
                "release_sha256": releases,
                "windows": windows,
                "registry": "NOT_RUN",
                "index_rollback": "NOT_RUN",
                "cloud_deployment": "NOT_RUN",
                "learner_defense": "REQUIRES_REVIEW",
                "memory_bytes": None,
                "memory_unknown_reason": (
                    "Process/native peak memory not instrumented; timings do not estimate memory."
                ),
            }
        )
    )
    (output / "monitoring.svg").write_text(_monitoring_svg(windows), encoding="utf-8")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(run_demo(args.output))
