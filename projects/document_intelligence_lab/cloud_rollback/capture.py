"""Capture one ECS rollout stage and correlate its HTTP probe with CloudWatch."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

STAGES = ("A", "B", "restored")
APP = "document-service"
type JsonObject = dict[str, Any]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read(path: Path) -> JsonObject:
    result = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError(f"expected a JSON object in {path.name}")
    return result


def save(path: Path, obj: object, mode: str = "w") -> None:
    with path.open(mode, encoding="utf-8") as file:
        json.dump(obj, file, indent=2, ensure_ascii=False)
        file.write("\n")


def aws(*args: str, timeout: int = 90) -> JsonObject:
    result = subprocess.run(
        ["aws", *args, "--output", "json", "--no-cli-pager"],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
    )
    payload = json.loads(result.stdout) if result.stdout.strip() else {}
    if not isinstance(payload, dict):
        raise ValueError("expected an AWS CLI JSON object")
    return payload


def verify(
    stage: str,
    expected: JsonObject,
    definition: JsonObject,
    service: JsonObject,
    task: JsonObject,
    events: list[JsonObject],
    previous: list[JsonObject],
) -> JsonObject:
    variant = "b" if stage == "B" else "a"
    predicted = expected[variant]
    for key in ("a", "b"):
        payload = expected[key]
        require(
            set(payload)
            == {"predicted_label", "model_id", "preprocessing_version", "bundle_sha256"}
            and all(
                isinstance(payload[k], str) and payload[k] for k in ("predicted_label", "model_id")
            )
            and type(payload["preprocessing_version"]) is int
            and re.fullmatch(r"[a-f0-9]{64}", payload["bundle_sha256"]) is not None,
            "invalid local expectation for /predict",
        )
    require(
        isinstance(expected["probe"], str) and len(expected["probe"].split()) == 1,
        "expected one synthetic probe token",
    )
    require(
        expected["a"]["predicted_label"] != expected["b"]["predicted_label"],
        "A and B must classify the same probe differently",
    )
    require(
        expected["a"]["bundle_sha256"] != expected["b"]["bundle_sha256"],
        "A and B must have different bundles",
    )
    revision = definition["taskDefinitionArn"]
    registered = {c["name"]: c["image"] for c in definition["containerDefinitions"]}
    image = registered[APP]
    digest = image.rsplit("@", 1)[-1]
    require(
        registered.get("probe") == image
        and "@" in image
        and re.fullmatch(r"sha256:[a-f0-9]{64}", digest) is not None,
        "both registered containers must pin the same image digest",
    )
    require(
        service["status"] == "ACTIVE"
        and service["serviceName"] == "classifier"
        and service["launchType"] == "FARGATE"
        and service["desiredCount"] == service["runningCount"] == 1
        and service["pendingCount"] == 0
        and len(service["deployments"]) == 1,
        "service did not settle at one Fargate task",
    )
    require(
        service["deployments"][0]["status"] == "PRIMARY"
        and service["deployments"][0]["taskDefinition"]
        == service["taskDefinition"]
        == task["taskDefinitionArn"]
        == revision,
        "wrong task definition",
    )
    containers = {c["name"]: c for c in task["containers"]}
    require(
        task["lastStatus"] == "RUNNING"
        and task["group"] == "service:classifier"
        and task["clusterArn"] == service["clusterArn"]
        and containers[APP]["lastStatus"] == "RUNNING"
        and containers[APP].get("imageDigest") == digest,
        "wrong running service image/task",
    )
    require(
        containers["probe"].get("imageDigest") == digest
        and containers["probe"].get("lastStatus") == "STOPPED"
        and containers["probe"].get("exitCode") == 0,
        "probe did not exit successfully with the pinned image",
    )
    task_id = task["taskArn"].rsplit("/", 1)[-1]
    probe_rows = [e for e in events if e["logStreamName"] == f"ecs/probe/{task_id}"]
    require(len(probe_rows) == 1, "expected one probe log event")
    row = json.loads(probe_rows[0]["message"])
    require(
        row["probe"] == expected["probe"] and row["prediction"] == predicted,
        "HTTP prediction differs from the local bundle on the chosen input",
    )
    require(
        row["ready"] == {"ready": True, "bundle_sha256": predicted["bundle_sha256"]},
        "readiness and prediction identify different bundles",
    )
    request_id = row["request_id"]
    require(re.fullmatch(r"[a-f0-9]{32}", request_id) is not None, "invalid probe request ID")
    observed = probe_rows[0]["timestamp"]
    require(type(observed) is int and observed > 0, "invalid CloudWatch event timestamp")
    access = re.compile(rf'"POST /predict\?probe_id={request_id} HTTP/1\.[01]" 200\b')
    require(
        any(
            e["logStreamName"] == f"ecs/{APP}/{task_id}" and access.search(e["message"])
            for e in events
        ),
        "missing HTTP 200 for this request ID in the service log",
    )
    record = {
        "stage": stage,
        "service": service["serviceArn"],
        "task": task["taskArn"],
        "task_definition": revision,
        "image_digest": digest,
        "probe": row["probe"],
        "request_id": request_id,
        "prediction": row["prediction"],
        "observed_at_ms": observed,
    }
    require(
        [p["stage"] for p in previous] == list(STAGES[: STAGES.index(stage)]),
        "missing earlier rollout evidence",
    )
    for prior in previous:
        require(
            record["service"] == prior["service"] and record["probe"] == prior["probe"],
            "service or probe changed between stages",
        )
        require(
            record["task"] != prior["task"] and request_id != prior["request_id"],
            "reused task or request",
        )
        require(observed > prior["observed_at_ms"], "CloudWatch events are out of rollout order")
    if stage == "B":
        require(
            revision != previous[0]["task_definition"]
            and digest != previous[0]["image_digest"]
            and predicted["predicted_label"] != previous[0]["prediction"]["predicted_label"]
            and predicted["bundle_sha256"] != previous[0]["prediction"]["bundle_sha256"],
            "B must change the task definition, image, bundle and prediction",
        )
    if stage == "restored":
        for field in ("task_definition", "image_digest", "prediction"):
            require(record[field] == previous[0][field], f"rollback differs from A: {field}")
    return record


def check_files(run: Path, stage: str, raw: Path, previous: list[JsonObject]) -> JsonObject:
    stack_id = read(run / "stack.json")["StackId"]
    arn_prefix, stack, _ = stack_id.split("/")
    prefix = arn_prefix.split(":")
    require(
        len(prefix) == 6 and prefix[2] == "cloudformation" and prefix[5] == "stack",
        "expected a CloudFormation stack ARN",
    )
    ecs_prefix = ":".join([prefix[0], prefix[1], "ecs", prefix[3], prefix[4], ""])
    services = read(raw / "service.json")
    listed = read(raw / "list-tasks.json")["taskArns"]
    tasks = read(raw / "task.json")
    require(
        not services.get("failures") and len(services["services"]) == 1,
        "expected one service from describe-services",
    )
    require(
        not tasks.get("failures") and len(tasks["tasks"]) == 1,
        "expected one task from describe-tasks",
    )
    service, task = services["services"][0], tasks["tasks"][0]
    require(
        service["clusterArn"] == ecs_prefix + "cluster/" + stack
        and service["serviceArn"]
        in (ecs_prefix + "service/classifier", ecs_prefix + f"service/{stack}/classifier"),
        "service is outside the recorded stack",
    )
    require(listed == [task["taskArn"]], "listed service task differs from described task")
    variant = "b" if stage == "B" else "a"
    definition = read(run / f"td-{variant}.json")["taskDefinition"]
    return verify(
        stage,
        read(run / "expect.json"),
        definition,
        service,
        task,
        read(raw / "logs.json")["events"],
        previous,
    )


def checked_stages(run: Path, stages: Sequence[str]) -> list[JsonObject]:
    previous: list[JsonObject] = []
    for stage in stages:
        folder = run / stage
        name = read(folder / "verified.json")["raw"]
        require(
            isinstance(name, str) and re.fullmatch(r"attempt-[a-zA-Z0-9_-]+", name) is not None,
            "invalid evidence directory",
        )
        raw = (folder / name).resolve()
        require(raw.parent == folder.resolve(), "evidence directory escapes the stage")
        previous.append(check_files(run, stage, raw, previous))
    return previous


def verify_run(run: Path) -> list[JsonObject]:
    """Recalculate all three stages from saved AWS responses without contacting AWS."""
    return checked_stages(run, STAGES)


def capture(run: Path, stage: str) -> Path:
    stack_id = read(run / "stack.json")["StackId"]
    stack = stack_id.split("/")[1]
    require(os.environ["AWS_REGION"] == stack_id.split(":")[3], "wrong AWS_REGION")
    require(os.environ.get("STACK", stack) == stack, "STACK differs from stack.json")
    variant = "b" if stage == "B" else "a"
    definition = read(run / f"td-{variant}.json")["taskDefinition"]
    previous = checked_stages(run, STAGES[: STAGES.index(stage)])
    folder = run / stage
    folder.mkdir(mode=0o700, exist_ok=True)
    verified = folder / "verified.json"
    require(not verified.exists(), f"{stage} already verified; use a new run for a new exercise")
    raw = Path(tempfile.mkdtemp(prefix="attempt-", dir=folder))
    print(f"Private capture: {raw}", flush=True)
    service_args = ("--cluster", stack, "--services", "classifier")
    services = aws("ecs", "describe-services", *service_args)
    save(raw / "service.json", services)
    aws("ecs", "wait", "services-stable", *service_args, timeout=660)
    services = aws("ecs", "describe-services", *service_args)
    save(raw / "service.json", services)
    require(len(services["services"]) == 1, "classifier service missing")
    tasks = aws(
        "ecs",
        "list-tasks",
        "--cluster",
        stack,
        "--service-name",
        "classifier",
        "--desired-status",
        "RUNNING",
    )
    save(raw / "list-tasks.json", tasks)
    require(len(tasks["taskArns"]) == 1, "expected exactly one service task")
    arn = tasks["taskArns"][0]
    task_id = arn.rsplit("/", 1)[-1]
    probe_stream, app_stream = f"ecs/probe/{task_id}", f"ecs/{APP}/{task_id}"
    # The service can be stable before the sidecar exits or awslogs flushes the request.
    for attempt in range(25):
        tasks = aws("ecs", "describe-tasks", "--cluster", stack, "--tasks", arn)
        save(raw / "task.json", tasks)
        require(len(tasks["tasks"]) == 1, "task disappeared")
        task = tasks["tasks"][0]
        require(
            task["taskDefinitionArn"] == definition["taskDefinitionArn"],
            "running task has an unexpected revision",
        )
        probe = next(c for c in task["containers"] if c["name"] == "probe")
        require(probe.get("exitCode") in (None, 0), f"probe failed: {probe.get('exitCode')}")
        try:
            logs = aws(
                "logs",
                "filter-log-events",
                "--log-group-name",
                f"/ecs/{stack}",
                "--log-stream-names",
                probe_stream,
                app_stream,
            )
        except subprocess.CalledProcessError as exc:
            if "ResourceNotFoundException" not in exc.stderr or attempt == 24:
                raise
            logs = {"events": []}
        save(raw / "logs.json", logs)
        events = logs["events"]
        if (
            probe.get("exitCode") == 0
            and any(e["logStreamName"] == probe_stream for e in events)
            and any(
                e["logStreamName"] == app_stream and "POST /predict?" in e["message"]
                for e in events
            )
        ):
            break
        if attempt < 24:
            time.sleep(5)
    record = check_files(run, stage, raw, previous)
    record["raw"] = raw.name
    save(verified, record, "x")
    return verified


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("stage", choices=STAGES)
    args = parser.parse_args()
    try:
        print(capture(args.run, args.stage))
    except subprocess.CalledProcessError as error:
        parser.exit(1, error.stderr or str(error))
