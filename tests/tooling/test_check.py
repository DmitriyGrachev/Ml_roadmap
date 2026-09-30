"""End-to-end contracts for scoped, strict curriculum checks."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from importlib import metadata
from pathlib import Path

import pytest

from roadmap_tools.cli import _main


def make_repository(
    tmp_path: Path, first_test: str, second_test: str = "def test_other():\n    assert False\n"
) -> Path:
    root = tmp_path / "fixture repository"
    (root / "tests").mkdir(parents=True)
    (root / "README.md").write_text("# Fixture\n", encoding="utf-8")
    (root / "tests" / "test_first.py").write_text(first_test, encoding="utf-8")
    (root / "tests" / "test_second.py").write_text(second_test, encoding="utf-8")
    (root / "pytest.ini").write_text("[pytest]\nxfail_strict = true\n", encoding="utf-8")
    (root / "curriculum.toml").write_text(
        """[[items]]
id = "first"
title = "First"
kind = "lab"
readme = "README.md"
tests = ["tests/test_first.py"]

[[items]]
id = "second"
title = "Second"
kind = "exercise"
readme = "README.md"
tests = ["tests/test_second.py"]
""",
        encoding="utf-8",
    )
    return root


def run_cli(root: Path, command: str = "check", identifier: str = "first") -> tuple[int, str]:
    output = ""

    def runner(arguments: Sequence[str]) -> int:
        nonlocal output
        result = subprocess.run(arguments, cwd=root, capture_output=True, text=True, check=False)
        output = result.stdout + result.stderr
        return result.returncode

    return _main([command, identifier], root, runner), output


def include_second_target(root: Path) -> None:
    catalog_path = root / "curriculum.toml"
    catalog_path.write_text(
        catalog_path.read_text(encoding="utf-8").replace(
            'tests = ["tests/test_first.py"]',
            'tests = ["tests/test_first.py", "tests/test_second.py"]',
            1,
        ),
        encoding="utf-8",
    )


def test_check_passes_only_selected_required_tests(tmp_path: Path) -> None:
    root = make_repository(tmp_path, "def test_complete():\n    assert 2 + 2 == 4\n")

    exit_code, output = run_cli(root)

    assert exit_code == 0, output
    assert "1 passed" in output
    assert "test_other" not in output


def test_new_continuation_does_not_expand_old_lab_check(tmp_path: Path) -> None:
    root = make_repository(tmp_path, "def test_legacy_complete():\n    assert True\n")
    continuation = root / "tests" / "continuation"
    continuation.mkdir()
    (continuation / "test_starter.py").write_text(
        "def test_unfinished():\n    assert False\n", encoding="utf-8"
    )
    catalog = root / "curriculum.toml"
    catalog.write_text(
        catalog.read_text(encoding="utf-8").replace(
            'tests = ["tests/test_second.py"]',
            'tests = ["tests/continuation/test_starter.py"]',
        ),
        encoding="utf-8",
    )

    old_exit, old_output = run_cli(root, identifier="first")
    new_exit, new_output = run_cli(root, identifier="second")

    assert old_exit == 0, old_output
    assert "1 passed" in old_output
    assert "test_unfinished" not in old_output
    assert new_exit == 1, new_output
    assert "test_unfinished" in new_output


def test_check_passes_when_all_required_calls_run(tmp_path: Path) -> None:
    root = make_repository(
        tmp_path,
        "def test_one():\n    assert True\ndef test_two():\n    assert 3 * 3 == 9\n",
    )

    exit_code, output = run_cli(root)

    assert exit_code == 0, output
    assert "2 passed" in output


@pytest.mark.parametrize("addopts", ["--collect-only", "--setup-only", "-k test_one"])
def test_check_rejects_inherited_options_that_omit_required_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, addopts: str
) -> None:
    root = make_repository(
        tmp_path,
        "def test_one():\n    assert True\ndef test_two():\n    assert True\n",
    )
    monkeypatch.setenv("PYTEST_ADDOPTS", addopts)

    exit_code, output = run_cli(root)

    assert exit_code != 0, output
    assert "CHECK INCOMPLETE" in output


@pytest.mark.parametrize(
    ("body", "outcome"),
    [
        ("def test_wrong():\n    assert False\n", "failed"),
        (
            "from roadmap_tools import exercise_call\n"
            "def todo():\n    raise NotImplementedError('TODO')\n"
            "def test_unfinished():\n"
            "    exercise_call(todo)\n",
            "xfailed",
        ),
        (
            "import pytest\n@pytest.mark.skip(reason='missing')\ndef test_skipped():\n    pass\n",
            "skipped",
        ),
        (
            "import pytest\n"
            "@pytest.mark.xfail(strict=False, reason='old TODO')\n"
            "def test_xpass():\n    assert True\n",
            "xpassed",
        ),
        (
            "import pytest\n"
            "@pytest.fixture\n"
            "def gate():\n    pytest.skip('setup skipped')\n"
            "def test_required(gate):\n    assert True\n",
            "skipped",
        ),
    ],
)
def test_check_rejects_incomplete_required_results(tmp_path: Path, body: str, outcome: str) -> None:
    root = make_repository(tmp_path, body)

    exit_code, output = run_cli(root)

    assert exit_code != 0, output
    assert outcome in output.lower()


def test_check_rejects_collection_skip_when_other_test_passes(tmp_path: Path) -> None:
    root = make_repository(
        tmp_path,
        "import pytest\npytest.skip('module skipped', allow_module_level=True)\n",
        "def test_complete():\n    assert True\n",
    )
    include_second_target(root)

    exit_code, output = run_cli(root)

    assert exit_code != 0, output
    assert "1 passed" in output
    assert "collection skips" in output


def test_check_rejects_empty_target_even_when_another_target_passes(tmp_path: Path) -> None:
    root = make_repository(tmp_path, "# no tests\n", "def test_complete():\n    assert True\n")
    include_second_target(root)

    exit_code, output = run_cli(root)

    assert exit_code != 0, output
    assert "1 passed" in output
    assert "no required tests collected from" in output
    assert "test_first.py" in output


def test_check_rejects_optional_only_target_even_when_another_passes(tmp_path: Path) -> None:
    root = make_repository(
        tmp_path,
        "import pytest\n@pytest.mark.optional_live\ndef test_live():\n    assert True\n",
        "def test_complete():\n    assert True\n",
    )
    include_second_target(root)

    exit_code, output = run_cli(root)

    assert exit_code != 0, output
    assert "1 passed" in output
    assert "NOT_RUN" in output
    assert "no required tests collected from" in output
    assert "test_first.py" in output


def test_check_rejects_zero_collected_tests(tmp_path: Path) -> None:
    root = make_repository(tmp_path, "# no tests here\n")

    exit_code, output = run_cli(root)

    assert exit_code != 0, output
    assert "no tests ran" in output.lower() or "collected 0 items" in output.lower()


def test_check_rejects_missing_required_artifact(tmp_path: Path) -> None:
    root = make_repository(
        tmp_path,
        "from pathlib import Path\n"
        "def test_report_exists():\n"
        "    assert Path('generated-reports/lab/report.json').is_file()\n",
    )

    exit_code, output = run_cli(root)

    assert exit_code != 0, output
    assert "test_report_exists" in output


def test_optional_tests_are_not_run_and_do_not_fail_required_cpu_check(tmp_path: Path) -> None:
    root = make_repository(
        tmp_path,
        "import pytest\n"
        "def test_cpu():\n    assert True\n"
        "@pytest.mark.optional_live\n"
        "def test_live():\n    assert False\n"
        "@pytest.mark.optional_gpu\n"
        "def test_gpu():\n    assert False\n",
    )

    exit_code, output = run_cli(root)

    assert exit_code == 0, output
    assert "1 passed" in output
    assert "NOT_RUN" in output
    assert "optional_live" in output
    assert "optional_gpu" in output


def test_optional_only_collection_is_not_a_successful_check(tmp_path: Path) -> None:
    root = make_repository(
        tmp_path,
        "import pytest\n@pytest.mark.optional_live\ndef test_live():\n    assert True\n",
    )

    exit_code, output = run_cli(root)

    assert exit_code != 0, output
    assert "NOT_RUN" in output


def test_health_command_keeps_xfail_compatible(tmp_path: Path) -> None:
    root = make_repository(
        tmp_path,
        "import pytest\ndef test_unfinished():\n    pytest.xfail('unfinished')\n",
    )

    exit_code, output = run_cli(root, "test")

    assert exit_code == 0, output
    assert "xfailed" in output


def test_check_requires_training_distribution_before_running_tests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_repository(tmp_path, "def test_complete():\n    assert True\n")
    catalog_path = root / "curriculum.toml"
    catalog_path.write_text(
        catalog_path.read_text(encoding="utf-8").replace(
            'kind = "lab"', 'kind = "lab"\nrequires_training = true', 1
        ),
        encoding="utf-8",
    )

    def missing_distribution(name: str) -> str:
        assert name == "torch"
        raise metadata.PackageNotFoundError(name)

    monkeypatch.setattr(metadata, "version", missing_distribution)

    def unexpected_runner(command: Sequence[str]) -> int:
        raise AssertionError(f"pytest must not start: {command}")

    exit_code = _main(["check", "first"], root, unexpected_runner)

    assert exit_code != 0
    output = capsys.readouterr().out
    assert "uv sync --group training" in output
    assert "torch" in output
