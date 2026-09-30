"""Pytest plugin that makes selected curriculum tests a completion check."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

_optional_counts: Counter[str] = Counter()
_optional_seen: set[str] = set()
_incomplete_counts: Counter[str] = Counter()
_required_collected = 0
_required_by_target: dict[Path, int] = {}
_required_nodeids: set[str] = set()
_passed_phases: dict[str, set[str]] = {}


def pytest_configure(config: pytest.Config) -> None:
    """Register opt-in checks so unselected live and GPU tests are explicit."""
    config.addinivalue_line("markers", "optional_live: requires an explicit live evaluation")
    config.addinivalue_line("markers", "optional_gpu: requires an explicit GPU evaluation")


def pytest_sessionstart(session: pytest.Session) -> None:
    """Clear counters when pytest is invoked repeatedly in one interpreter."""
    global _required_collected, _required_by_target
    _required_collected = 0
    _required_by_target = {Path(argument).resolve(): 0 for argument in session.config.args}
    _optional_counts.clear()
    _optional_seen.clear()
    _incomplete_counts.clear()
    _required_nodeids.clear()
    _passed_phases.clear()


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Keep only required checks in this offline completion run."""
    global _required_collected
    required: list[pytest.Item] = []
    optional: list[pytest.Item] = []
    for item in items:
        optional_markers = [
            marker
            for marker in ("optional_live", "optional_gpu")
            if item.get_closest_marker(marker)
        ]
        if optional_markers:
            optional.append(item)
        else:
            required.append(item)
            _required_nodeids.add(item.nodeid)
    if optional:
        config.hook.pytest_deselected(items=optional)
        items[:] = required
    _required_collected = len(required)
    for item in required:
        item_path = item.path.resolve()
        for target in _required_by_target:
            if item_path.is_relative_to(target):
                _required_by_target[target] += 1


def pytest_deselected(items: list[pytest.Item]) -> None:
    """Preserve required items removed by pytest filters such as -k and -m."""
    for item in items:
        optional_markers = [
            marker
            for marker in ("optional_live", "optional_gpu")
            if item.get_closest_marker(marker)
        ]
        if optional_markers:
            if item.nodeid not in _optional_seen:
                _optional_counts.update(optional_markers)
                _optional_seen.add(item.nodeid)
        else:
            _required_nodeids.add(item.nodeid)


def pytest_collectreport(report: pytest.CollectReport) -> None:
    """A module skipped before test items exist is still incomplete."""
    if report.skipped:
        _incomplete_counts["collection skips"] += 1


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """Record incomplete required results across setup, call, and teardown."""
    if report.skipped:
        outcome = "xfails" if hasattr(report, "wasxfail") else "skips"
        _incomplete_counts[outcome] += 1
    elif report.passed and hasattr(report, "wasxfail"):
        _incomplete_counts["xpasses"] += 1
    elif report.passed and report.nodeid in _required_nodeids:
        _passed_phases.setdefault(report.nodeid, set()).add(report.when)


def pytest_sessionfinish(session: pytest.Session, exitstatus: pytest.ExitCode) -> None:
    """Fail checks that pytest would otherwise mark successful despite gaps."""
    if _optional_counts:
        details = ", ".join(f"{name}={count}" for name, count in sorted(_optional_counts.items()))
        print(f"NOT_RUN: {details}")
    if _required_collected == 0:
        print("CHECK INCOMPLETE: no required tests collected")
    missing_targets = [target for target, count in _required_by_target.items() if count == 0]
    for target in missing_targets:
        print(f"CHECK INCOMPLETE: no required tests collected from {target}")
    complete_phases = {"setup", "call", "teardown"}
    incomplete_runs = sorted(
        nodeid
        for nodeid in _required_nodeids
        if not complete_phases.issubset(_passed_phases.get(nodeid, set()))
    )
    if incomplete_runs:
        preview = ", ".join(incomplete_runs[:3])
        print(
            f"CHECK INCOMPLETE: {len(incomplete_runs)} required tests did not run to completion: "
            f"{preview}"
        )
    if _incomplete_counts:
        details = ", ".join(f"{name}={count}" for name, count in sorted(_incomplete_counts.items()))
        print(f"CHECK INCOMPLETE: {details}")
    if (
        _required_collected == 0 or missing_targets or incomplete_runs or _incomplete_counts
    ) and exitstatus == pytest.ExitCode.OK:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
