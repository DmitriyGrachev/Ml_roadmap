import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def test_default_mypy_gate_checks_backend_sources() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "mypy", "--verbose"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    output = (completed.stdout + completed.stderr).replace("\\", "/")
    assert completed.returncode == 0, output
    assert "modules/02_python_backend/examples/support_api/models.py" in output
