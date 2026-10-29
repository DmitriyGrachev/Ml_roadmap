"""Author wheel runner: installed uv_build, bundled ensurepip, no network resolution."""

import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


def build_and_install(project_dir: Path, work_dir: Path) -> Path:
    """Build locally, install into a fresh venv, return its un-resolved Python path."""
    project_dir = project_dir.resolve()
    work_dir = work_dir.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    wheel_dir = work_dir / "wheels"
    wheel_dir.mkdir()
    backend_env = os.environ.copy()
    backend_env["PATH"] = (
        str(Path(sys.executable).parent) + os.pathsep + backend_env.get("PATH", "")
    )
    # uv_build locates uv-build through PATH even when Python is invoked by absolute path.
    # Direct PEP 517 backend invocation avoids isolated-build dependency downloads.
    subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import sys, uv_build; uv_build.build_wheel(sys.argv[1])",
            str(wheel_dir),
        ],
        cwd=project_dir,
        env=backend_env,
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(wheel_dir.glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError("expected exactly one locally built wheel")
    environment = work_dir / "venv"
    venv.EnvBuilder(with_pip=True).create(environment)
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run(
        [
            str(python),
            "-I",
            "-m",
            "pip",
            "--isolated",
            "--disable-pip-version-check",
            "install",
            "--no-index",
            "--no-deps",
            "--no-cache-dir",
            str(wheels[0]),
        ],
        cwd=work_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    return python


def main() -> None:
    project = Path(__file__).with_name("example_project")
    with tempfile.TemporaryDirectory(prefix="parcel-wheel-") as temporary:
        work = Path(temporary)
        python = build_and_install(project, work / "delivery")
        # cwd and -I prevent accidental imports from the repository or PYTHONPATH.
        subprocess.run([str(python), "-I", "-m", "parcel_features"], cwd=work, check=True)


if __name__ == "__main__":
    main()
