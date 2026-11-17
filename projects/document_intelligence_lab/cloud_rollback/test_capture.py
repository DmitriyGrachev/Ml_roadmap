"""Synthetic AWS records for exercising the offline checker; no live evidence."""

import json
from pathlib import Path
from unittest import mock

import pytest

from projects.document_intelligence_lab.cloud_rollback import capture


@pytest.fixture
def saved_run(tmp_path: Path) -> Path:
    dump = capture.save
    prefix = "arn:aws:ecs:us-west-2:000000000000:"
    stack = "synthetic"
    dump(
        tmp_path / "stack.json",
        {"StackId": "arn:aws:cloudformation:us-west-2:000000000000:stack/synthetic/unit-test"},
    )
    expected: dict[str, object] = {"probe": "sample"}
    for index, stage in enumerate(capture.STAGES, start=1):
        variant = "b" if stage == "B" else "a"
        digest = "sha256:" + variant * 64
        payload = {
            "bundle_sha256": variant * 64,
            "model_id": variant,
            "preprocessing_version": 1,
            "predicted_label": "circle" if variant == "a" else "triangle",
        }
        expected[variant] = payload
        task_id = str(index) * 32
        request_id = str(index + 3) * 32
        task_arn = prefix + f"task/{stack}/{task_id}"
        definition = prefix + "task-definition/synthetic:" + ("1" if variant == "a" else "2")
        cluster = prefix + f"cluster/{stack}"
        dump(
            tmp_path / f"td-{variant}.json",
            {
                "taskDefinition": {
                    "taskDefinitionArn": definition,
                    "containerDefinitions": [
                        {"name": name, "image": f"example.invalid/synthetic@{digest}"}
                        for name in (capture.APP, "probe")
                    ],
                }
            },
        )
        raw = tmp_path / stage / "attempt-homework"
        raw.mkdir(parents=True)
        dump(raw.parent / "verified.json", {"raw": raw.name})
        dump(
            raw / "service.json",
            {
                "services": [
                    {
                        "serviceArn": prefix + f"service/{stack}/classifier",
                        "serviceName": "classifier",
                        "status": "ACTIVE",
                        "launchType": "FARGATE",
                        "clusterArn": cluster,
                        "desiredCount": 1,
                        "runningCount": 1,
                        "pendingCount": 0,
                        "taskDefinition": definition,
                        "deployments": [{"status": "PRIMARY", "taskDefinition": definition}],
                    }
                ]
            },
        )
        dump(raw / "list-tasks.json", {"taskArns": [task_arn]})
        dump(
            raw / "task.json",
            {
                "tasks": [
                    {
                        "taskArn": task_arn,
                        "group": "service:classifier",
                        "lastStatus": "RUNNING",
                        "taskDefinitionArn": definition,
                        "clusterArn": cluster,
                        "containers": [
                            {
                                "name": capture.APP,
                                "lastStatus": "RUNNING",
                                "imageDigest": digest,
                            },
                            {
                                "name": "probe",
                                "lastStatus": "STOPPED",
                                "exitCode": 0,
                                "imageDigest": digest,
                            },
                        ],
                    }
                ]
            },
        )
        probe = {
            "probe": expected["probe"],
            "request_id": request_id,
            "prediction": payload,
            "ready": {"ready": True, "bundle_sha256": payload["bundle_sha256"]},
        }
        dump(
            raw / "logs.json",
            {
                "events": [
                    {
                        "logStreamName": f"ecs/{capture.APP}/{task_id}",
                        "timestamp": index,
                        "message": f'"POST /predict?probe_id={request_id} HTTP/1.1" 200 OK',
                    },
                    {
                        "logStreamName": f"ecs/probe/{task_id}",
                        "timestamp": index,
                        "message": json.dumps(probe),
                    },
                ]
            },
        )
    dump(tmp_path / "expect.json", expected)
    return tmp_path


def test_offline_rechecks_original_aws_records(saved_run: Path) -> None:
    with mock.patch.object(capture, "aws", side_effect=AssertionError("offline verifier used AWS")):
        a, b, restored = capture.verify_run(saved_run)
    assert a["prediction"] != b["prediction"]
    assert a["prediction"] == restored["prediction"]
    assert a["task"] != restored["task"]


def test_rejects_success_summary_without_matching_application_access_log(saved_run: Path) -> None:
    path = saved_run / "B/attempt-homework/logs.json"
    saved = capture.read(path)
    saved["events"][0]["message"] = 'INFO: "POST /predict?probe_id=another HTTP/1.1" 200 OK'
    capture.save(path, saved)
    with pytest.raises(ValueError, match="missing HTTP 200"):
        capture.verify_run(saved_run)


def test_rejects_new_image_after_rollback_even_when_prediction_matches(saved_run: Path) -> None:
    path = saved_run / "restored/attempt-homework/task.json"
    saved = capture.read(path)
    saved["tasks"][0]["containers"][0]["imageDigest"] = "sha256:" + "b" * 64
    capture.save(path, saved)
    with pytest.raises(ValueError, match="wrong running service image"):
        capture.verify_run(saved_run)


def test_rejects_stale_prediction_from_a_on_b(saved_run: Path) -> None:
    path = saved_run / "B/attempt-homework/logs.json"
    saved = capture.read(path)
    probe = json.loads(saved["events"][1]["message"])
    probe["prediction"] = capture.read(saved_run / "expect.json")["a"]
    saved["events"][1]["message"] = json.dumps(probe)
    capture.save(path, saved)
    with pytest.raises(ValueError, match="HTTP prediction"):
        capture.verify_run(saved_run)


def test_rejects_out_of_order_rollback_probe(saved_run: Path) -> None:
    path = saved_run / "restored/attempt-homework/logs.json"
    saved = capture.read(path)
    saved["events"][1]["timestamp"] = 1
    capture.save(path, saved)
    with pytest.raises(ValueError, match="out of rollout order"):
        capture.verify_run(saved_run)


def test_rejects_wrong_cloudformation_account(saved_run: Path) -> None:
    path = saved_run / "stack.json"
    saved = capture.read(path)
    saved["StackId"] = saved["StackId"].replace("000000000000", "111111111111")
    capture.save(path, saved)
    with pytest.raises(ValueError, match="outside the recorded stack"):
        capture.verify_run(saved_run)
