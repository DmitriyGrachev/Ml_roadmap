"""Executable integration contracts for notebooks and synthetic datasets."""

from __future__ import annotations

import ast
import copy
import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import cast

import nbformat
import pytest
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError
from nbformat import NotebookNode

pytestmark = pytest.mark.filterwarnings(
    "ignore:Proactor event loop does not implement add_reader family.*:RuntimeWarning"
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_PATHS = (
    Path("modules/03_data_foundations/notebooks/01_numpy_payment_arrays.ipynb"),
    Path("modules/03_data_foundations/notebooks/02_pandas_transaction_analysis.ipynb"),
    Path("modules/03_data_foundations/notebooks/03_fraud_metrics.ipynb"),
    Path("projects/banking_ai_lab/notebooks/transaction_eda.ipynb"),
)
DATASET_NAMES = ("transactions.csv", "transactions_dirty.csv")
NETWORK_IMPORT_ROOTS = {
    "aiohttp",
    "ftplib",
    "http",
    "httpx",
    "requests",
    "smtplib",
    "socket",
    "urllib",
}
NETWORK_CELL_TAGS = {"download", "network", "requires-network"}
NETWORK_DISABLED_MESSAGE = "Network access is disabled during notebook tests"
NETWORK_DENIAL_SOURCE = f"""
import socket as _roadmap_socket


def _roadmap_deny_network(*_args, **_kwargs):
    raise RuntimeError({NETWORK_DISABLED_MESSAGE!r})


class _RoadmapOfflineSocket(_roadmap_socket.socket):
    def connect(self, *_args, **_kwargs):
        _roadmap_deny_network()

    def connect_ex(self, *_args, **_kwargs):
        _roadmap_deny_network()

    def sendto(self, *_args, **_kwargs):
        _roadmap_deny_network()

    def sendmsg(self, *_args, **_kwargs):
        _roadmap_deny_network()


_roadmap_socket.socket = _RoadmapOfflineSocket
_roadmap_socket.SocketType = _RoadmapOfflineSocket
for _roadmap_function_name in (
    "create_connection",
    "create_server",
    "getaddrinfo",
    "gethostbyaddr",
    "gethostbyname",
    "gethostbyname_ex",
    "getnameinfo",
):
    setattr(_roadmap_socket, _roadmap_function_name, _roadmap_deny_network)
""".strip()


def read_notebook(relative_path: Path) -> NotebookNode:
    notebook = nbformat.read(  # type: ignore[no-untyped-call]
        REPOSITORY_ROOT / relative_path,
        as_version=4,
    )
    nbformat.validate(notebook)
    return cast(NotebookNode, notebook)


def cell_tags(cell: NotebookNode) -> set[str]:
    return set(cast(list[str], cell.metadata.get("tags", [])))


def is_exercise_code_cell(cell: NotebookNode) -> bool:
    return cell.cell_type == "code" and "exercise" in cell_tags(cell)


def assert_notebook_has_no_network_requirement(notebook: NotebookNode) -> None:
    for cell in notebook.cells:
        source = cast(str, cell.source)
        assert NETWORK_CELL_TAGS.isdisjoint(cell_tags(cell)), "network-tagged cell is not allowed"
        assert "http://" not in source, "network URL is not allowed"
        assert "https://" not in source, "network URL is not allowed"
        if cell.cell_type != "code":
            continue

        tree = ast.parse(source)
        imported_roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_roots.add(node.module.split(".", maxsplit=1)[0])
        blocked_imports = imported_roots & NETWORK_IMPORT_ROOTS
        assert not blocked_imports, f"network imports are not allowed: {sorted(blocked_imports)}"


def offline_kernel_environment(temporary_root: Path) -> dict[str, str]:
    blocked_names = {
        "IPYTHONDIR",
        "JUPYTER_CONFIG_DIR",
        "JUPYTER_DATA_DIR",
        "JUPYTER_PATH",
        "JUPYTER_RUNTIME_DIR",
        "PYTHONPATH",
        "PYTHONSTARTUP",
    }
    environment = {
        name: value
        for name, value in os.environ.items()
        if name.upper() not in blocked_names and not name.upper().endswith("_PROXY")
    }
    isolated_home = temporary_root / ".notebook-kernel"
    locations = {
        "HOME": isolated_home,
        "USERPROFILE": isolated_home,
        "IPYTHONDIR": isolated_home / "ipython",
        "JUPYTER_CONFIG_DIR": isolated_home / "jupyter-config",
        "JUPYTER_DATA_DIR": isolated_home / "jupyter-data",
        "JUPYTER_RUNTIME_DIR": isolated_home / "jupyter-runtime",
        "MPLCONFIGDIR": isolated_home / "matplotlib",
    }
    for location in locations.values():
        location.mkdir(parents=True, exist_ok=True)
    environment.update({name: str(path) for name, path in locations.items()})
    environment.update(
        {
            "ALL_PROXY": "http://127.0.0.1:9",
            "HTTP_PROXY": "http://127.0.0.1:9",
            "HTTPS_PROXY": "http://127.0.0.1:9",
            "NO_PROXY": "",
            "all_proxy": "http://127.0.0.1:9",
            "http_proxy": "http://127.0.0.1:9",
            "https_proxy": "http://127.0.0.1:9",
            "no_proxy": "",
            "PIP_NO_INDEX": "1",
            "PYTHONNOUSERSITE": "1",
            "UV_OFFLINE": "1",
        }
    )
    return environment


def execute_completed_notebook(
    notebook: NotebookNode,
    *,
    temporary_root: Path,
) -> NotebookNode:
    nbformat.validate(notebook)
    assert_notebook_has_no_network_requirement(notebook)
    executable = copy.deepcopy(notebook)
    replaced = 0
    for original_cell, executable_cell in zip(notebook.cells, executable.cells, strict=True):
        if is_exercise_code_cell(original_cell):
            executable_cell.source = "pass"
            replaced += 1
        else:
            assert executable_cell.source == original_cell.source
    assert replaced > 0, "notebook must contain at least one exercise-tagged code cell"
    isolation_cell = nbformat.v4.new_code_cell(  # type: ignore[no-untyped-call]
        source=NETWORK_DENIAL_SOURCE,
        metadata={"tags": ["test-infrastructure"]},
    )
    executable.cells.insert(0, isolation_cell)
    nbformat.validate(executable)

    executed = NotebookClient(
        executable,
        timeout=30,
        kernel_name="python3",
        allow_errors=False,
    ).execute(
        cwd=str(REPOSITORY_ROOT),
        env=offline_kernel_environment(temporary_root),
    )
    return executed


def generate_datasets(output_directory: Path) -> tuple[Path, Path]:
    assert not output_directory.resolve().is_relative_to(REPOSITORY_ROOT)
    result = subprocess.run(
        [
            sys.executable,
            str(REPOSITORY_ROOT / "scripts" / "generate_transactions.py"),
            "--output",
            str(output_directory),
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    clean = output_directory / DATASET_NAMES[0]
    dirty = output_directory / DATASET_NAMES[1]
    assert clean.is_file()
    assert dirty.is_file()
    return clean, dirty


def sha256_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_generated_hashes_match(output_directory: Path) -> None:
    expected = {name: sha256_digest(REPOSITORY_ROOT / "datasets" / name) for name in DATASET_NAMES}
    actual = {name: sha256_digest(output_directory / name) for name in DATASET_NAMES}
    assert actual == expected


def test_notebook_inventory_covers_every_checked_in_notebook() -> None:
    result = subprocess.run(
        ["git", "ls-files", "--", "*.ipynb"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    tracked = tuple(Path(line) for line in result.stdout.splitlines() if line)

    assert tracked == NOTEBOOK_PATHS


@pytest.mark.parametrize("relative_path", NOTEBOOK_PATHS, ids=lambda path: path.stem)
def test_completed_notebook_executes_without_changing_source(
    relative_path: Path,
    tmp_path: Path,
) -> None:
    notebook_path = REPOSITORY_ROOT / relative_path
    original_bytes = notebook_path.read_bytes()
    notebook = read_notebook(relative_path)
    original_sources = tuple(cast(str, cell.source) for cell in notebook.cells)
    original_exercise_count = sum(is_exercise_code_cell(cell) for cell in notebook.cells)

    executed = execute_completed_notebook(notebook, temporary_root=tmp_path)

    assert original_exercise_count > 0
    assert notebook_path.read_bytes() == original_bytes
    assert tuple(cast(str, cell.source) for cell in notebook.cells) == original_sources
    assert len(executed.cells) == len(notebook.cells) + 1
    assert cell_tags(executed.cells[0]) == {"test-infrastructure"}
    executed_source_cells = executed.cells[1:]
    for original_cell, executed_cell in zip(notebook.cells, executed_source_cells, strict=True):
        if is_exercise_code_cell(original_cell):
            assert cast(str, executed_cell.source) == "pass"
        else:
            assert executed_cell.source == original_cell.source
    executed_exercises = [cell for cell in executed_source_cells if is_exercise_code_cell(cell)]
    assert len(executed_exercises) == original_exercise_count
    assert all(cast(str, cell.source) == "pass" for cell in executed_exercises)
    assert all(
        cell.execution_count is not None for cell in executed.cells if cell.cell_type == "code"
    )


def test_kernel_environment_is_isolated_and_offline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HTTPS_PROXY", "https://ambient-proxy.invalid")
    monkeypatch.setenv("PYTHONPATH", "ambient-import-path")

    environment = offline_kernel_environment(tmp_path)

    assert "PYTHONPATH" not in environment
    assert environment["HTTP_PROXY"] == "http://127.0.0.1:9"
    assert environment["HTTPS_PROXY"] == "http://127.0.0.1:9"
    assert environment["ALL_PROXY"] == "http://127.0.0.1:9"
    assert environment["NO_PROXY"] == ""
    assert environment["PIP_NO_INDEX"] == "1"
    for variable in (
        "HOME",
        "USERPROFILE",
        "IPYTHONDIR",
        "JUPYTER_CONFIG_DIR",
        "JUPYTER_DATA_DIR",
        "JUPYTER_RUNTIME_DIR",
        "MPLCONFIGDIR",
    ):
        assert Path(environment[variable]).is_relative_to(tmp_path)


@pytest.mark.parametrize(
    "unsafe_source",
    [
        "import socket\nsocket.create_connection(('example.test', 443))",
        ('import http.client\nhttp.client.HTTPConnection("example.test").request("GET", "/")'),
    ],
    ids=["socket-import", "stdlib-http-client"],
)
def test_network_dependent_cell_is_rejected_before_execution(unsafe_source: str) -> None:
    notebook = cast(
        NotebookNode,
        nbformat.v4.new_notebook(  # type: ignore[no-untyped-call]
            cells=[
                nbformat.v4.new_code_cell(  # type: ignore[no-untyped-call]
                    source=unsafe_source
                )
            ]
        ),
    )

    with pytest.raises(AssertionError, match="network"):
        assert_notebook_has_no_network_requirement(notebook)


@pytest.mark.parametrize(
    "unsafe_source",
    [
        (
            "from importlib import import_module as load\n"
            'socket = load("socket")\n'
            'socket.create_connection(("127.0.0.1", 9), timeout=0.05)'
        ),
        (
            "from builtins import __import__ as load\n"
            'socket = load("socket")\n'
            'socket.create_connection(("127.0.0.1", 9), timeout=0.05)'
        ),
        (
            "load = __import__\n"
            'socket = load("socket")\n'
            'socket.create_connection(("127.0.0.1", 9), timeout=0.05)'
        ),
        'import asyncio\nawait asyncio.open_connection("127.0.0.1", 9)',
    ],
    ids=["importlib-alias", "builtins-alias", "assigned-alias", "asyncio-open-connection"],
)
def test_kernel_network_denial_blocks_static_policy_bypasses(
    unsafe_source: str,
    tmp_path: Path,
) -> None:
    notebook = copy.deepcopy(read_notebook(NOTEBOOK_PATHS[0]))
    notebook.cells.append(
        nbformat.v4.new_code_cell(source=unsafe_source)  # type: ignore[no-untyped-call]
    )

    with pytest.raises(CellExecutionError, match=NETWORK_DISABLED_MESSAGE):
        execute_completed_notebook(notebook, temporary_root=tmp_path)


def test_safe_dynamic_math_import_executes(tmp_path: Path) -> None:
    notebook = copy.deepcopy(read_notebook(NOTEBOOK_PATHS[0]))
    notebook.cells.append(
        nbformat.v4.new_code_cell(  # type: ignore[no-untyped-call]
            source=(
                'from importlib import import_module\nassert import_module("math").sqrt(81) == 9'
            )
        )
    )

    executed = execute_completed_notebook(notebook, temporary_root=tmp_path)

    assert executed.cells[-1].execution_count is not None


def test_execution_detects_an_untagged_broken_cell(tmp_path: Path) -> None:
    notebook = copy.deepcopy(read_notebook(NOTEBOOK_PATHS[0]))
    completed_cell = next(
        cell
        for cell in notebook.cells
        if cell.cell_type == "code" and not is_exercise_code_cell(cell)
    )
    completed_cell.source = (
        f'{cast(str, completed_cell.source)}\nraise RuntimeError("untagged mutation detected")'
    )

    with pytest.raises(CellExecutionError, match="untagged mutation detected"):
        execute_completed_notebook(notebook, temporary_root=tmp_path)


def test_default_generation_matches_both_checked_in_dataset_hashes(tmp_path: Path) -> None:
    output_directory = tmp_path / "generated"

    generated = generate_datasets(output_directory)

    assert tuple(path.name for path in generated) == DATASET_NAMES
    assert_generated_hashes_match(output_directory)


@pytest.mark.parametrize("dataset_name", DATASET_NAMES)
def test_dataset_hash_contract_detects_a_changed_generated_byte(
    dataset_name: str,
    tmp_path: Path,
) -> None:
    output_directory = tmp_path / "generated"
    generate_datasets(output_directory)
    generated_path = output_directory / dataset_name
    payload = generated_path.read_bytes()
    generated_path.write_bytes(payload[:-1] + bytes([payload[-1] ^ 1]))

    with pytest.raises(AssertionError):
        assert_generated_hashes_match(output_directory)
