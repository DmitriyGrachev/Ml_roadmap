"""Runs inside the Fargate probe container after the service health check succeeds."""

import json
import os
import uuid
from urllib.request import Request, urlopen


def main() -> None:
    base = "http://127.0.0.1:8000"
    probe = os.environ["PROBE_TOKEN"]
    request_id = uuid.uuid4().hex
    with urlopen(base + "/ready", timeout=5) as response:
        ready = json.load(response)
    request = Request(
        f"{base}/predict?probe_id={request_id}",
        data=json.dumps({"text": probe}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        prediction = json.load(response)
    print(
        json.dumps(
            {
                "request_id": request_id,
                "probe": probe,
                "ready": ready,
                "prediction": prediction,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
