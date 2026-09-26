"""Fingerprint an exact approval target without executing or persisting an action."""

import hashlib
import json


def approval_digest(workflow_id: str, version: int, tool: str, arguments: dict[str, str]) -> str:
    payload = {"workflow_id": workflow_id, "version": version, "tool": tool, "arguments": arguments}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def main() -> None:
    original = approval_digest("room-request", 2, "reserve", {"room": "Studio", "slot": "10"})
    changed = approval_digest("room-request", 2, "reserve", {"room": "Hall", "slot": "10"})
    print(f"Approval target unchanged: {original == changed}")
    print("A digest binds content; it does not authenticate the person granting permission.")


if __name__ == "__main__":
    main()
