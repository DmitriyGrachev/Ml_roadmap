"""Read-only product evidence validation."""

import argparse
import json
import math
from pathlib import Path
from typing import Any

from roadmap_tools.open_control_evidence import (
    ids,
    load_bundle,
    object_value,
    read_json,
    require,
    same_numbers,
)

FIXTURES = Path(__file__).parent / "fixtures"


def validate_evidence(root: Path) -> None:
    inputs = {
        name: (FIXTURES / name).read_bytes() for name in ("requests.jsonl", "constraints.json")
    }
    manifest = load_bundle(root, "production-product-study", inputs)
    requests = [json.loads(line) for line in inputs["requests.jsonl"].decode().splitlines()]
    constraints = json.loads(inputs["constraints.json"])
    split = object_value(read_json(root / "split.json"))
    selected = ids(split.get("evaluation_ids"))
    require(selected == [row["id"] for row in requests], "evaluation IDs differ from inputs")
    outputs = object_value(read_json(root / "outputs.json"))
    validate_outputs(requests, constraints, outputs, manifest)


def validate_outputs(
    requests: list[dict[str, Any]],
    constraints: dict[str, Any],
    outputs: dict[str, Any],
    manifest: dict[str, Any],
) -> None:
    for key in ("run_id", "dataset_sha256", "split_sha256"):
        require(outputs.get(key) == manifest[key], f"output {key} differs")
    records: Any = outputs.get("records")
    quantities = summarize(requests, records, constraints["catalog"])
    same_numbers(quantities, outputs.get("accounting"))
    require(quantities["cost_units_total"] <= constraints["max_cost_units_total"], "cost budget")
    require(
        all(row["latency_ms"] <= constraints["max_latency_ms_per_request"] for row in records),
        "latency budget",
    )


def summarize(requests: Any, outputs: Any, catalog: Any) -> dict[str, Any]:
    require(
        isinstance(requests, list)
        and bool(requests)
        and all(isinstance(row, dict) for row in requests),
        "invalid request records",
    )
    require(
        isinstance(outputs, list) and all(isinstance(row, dict) for row in outputs),
        "invalid output records",
    )
    request_ids = ids([row.get("id") for row in requests])
    require([row.get("id") for row in outputs] == request_ids, "output IDs differ")
    require(
        isinstance(catalog, list) and all(isinstance(row, dict) for row in catalog),
        "invalid catalog",
    )
    ids([row.get("id") for row in catalog])
    entries = {row["id"]: row for row in catalog}
    matched, fallback = 0, 0
    latency, cost = 0.0, 0
    for request, output in zip(requests, outputs, strict=True):
        require("route" in output, "missing route")
        route = output["route"]
        if route is None:
            fallback += 1
        else:
            require(isinstance(route, str) and route in entries, "unknown route")
            require(request.get("role") in entries[route]["roles"], "route permission denied")
            matched += int(route in request["acceptable"])
        elapsed, units = output.get("latency_ms"), output.get("cost_units")
        require(
            type(elapsed) in (int, float) and math.isfinite(elapsed) and elapsed >= 0,
            "invalid elapsed time",
        )
        require(type(units) is int and units >= 0, "invalid cost units")
        latency += elapsed
        cost += units
    return {
        "count": len(requests),
        "matched": matched,
        "fallback": fallback,
        "latency_ms_total": latency,
        "cost_units_total": cost,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate saved product artifact consistency")
    parser.add_argument("root", type=Path)
    validate_evidence(parser.parse_args().root)
    print("Artifact consistency verified; provenance and trade-offs REQUIRES_REVIEW")
