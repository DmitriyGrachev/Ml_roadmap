"""Derive honest, small summaries from raw records; never infer tokens from chunks."""

import math
from collections.abc import Mapping, Sequence


def summarize(
    records: Sequence[Mapping[str, object]],
    *,
    elapsed_s: float,
    evidence: str,
) -> dict[str, object]:
    if type(elapsed_s) not in (int, float) or not math.isfinite(elapsed_s) or elapsed_s <= 0:
        raise ValueError("elapsed_s must be finite and positive")
    if evidence not in ("synthetic", "live_endpoint"):
        raise ValueError("evidence must explicitly label synthetic or live_endpoint")
    completed = [record for record in records if record.get("status") == "ok"]
    for record in records:
        if record.get("status") not in ("ok", "error", "deadline"):
            raise ValueError("unknown raw status")
        tokens = record.get("completion_tokens")
        if tokens is not None and (type(tokens) is not int or tokens < 0):
            raise ValueError("raw completion_tokens must be nonnegative integer or null")
    counts = [record.get("completion_tokens") for record in completed]
    token_rate = None
    if completed and all(type(count) is int for count in counts):
        token_rate = sum(count for count in counts if isinstance(count, int)) / elapsed_s
    return {
        "evidence": evidence,
        "requests": len(records),
        "completed": len(completed),
        "errors": len(records) - len(completed),
        "completed_requests_per_s": len(completed) / elapsed_s,
        "completed_output_tokens_per_s": token_rate,
    }
