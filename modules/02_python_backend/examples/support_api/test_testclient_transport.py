import subprocess
import sys


def test_testclient_uses_the_supported_httpx2_transport() -> None:
    import_script = """
import warnings
from starlette.exceptions import StarletteDeprecationWarning

warnings.simplefilter("error", StarletteDeprecationWarning)
from fastapi.testclient import TestClient

assert TestClient
"""

    completed = subprocess.run(
        [sys.executable, "-c", import_script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
