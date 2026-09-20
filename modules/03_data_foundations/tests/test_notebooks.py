from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import cast

import nbformat
import pytest
from nbformat import NotebookNode

MODULE_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_ROOT = MODULE_ROOT / "notebooks"
NOTEBOOKS = {
    "01_numpy_payment_arrays.ipynb": (
        "shape",
        "dtype",
        "broadcast",
        "axis",
        "dot",
    ),
    "02_pandas_transaction_analysis.ipynb": (
        "loc",
        "iloc",
        "missing",
        "duplicate",
        "groupby",
        "merge",
        "datetime",
        "categor",
    ),
    "03_fraud_metrics.ipynb": (
        "true positive",
        "false positive",
        "precision",
        "recall",
        "99.9%",
        "roc",
        "pr-auc",
    ),
}
WINDOWS_ABSOLUTE_PATH = re.compile(
    r"(?:^|[\s`\"'(=])(?:[A-Za-z]:[\\/]|\\\\[^\\\s]+[\\/])",
    re.MULTILINE,
)
POSIX_ABSOLUTE_PATH = re.compile(
    r"(?:^|[\s`\"'(=])/(?!/)[A-Za-z0-9._~-]+(?:/[A-Za-z0-9._~-]+)*"
    r"(?=$|[\s`\"'),;])",
    re.MULTILINE,
)
SECRET_ASSIGNMENT = re.compile(
    r"\b(?:api[ _-]?key|access[ _-]?token|auth[ _-]?token|password|passwd|client[ _-]?secret)"
    r"\b\s*(?:=|:)\s*[\"']?[^\s\"',]{6,}",
    re.IGNORECASE,
)
SECRET_SIGNATURE = re.compile(
    r"\b(?:sk-[A-Za-z0-9_-]{8,}|AKIA[0-9A-Z]{12,}|Bearer\s+[A-Za-z0-9._~+/-]{8,})\b"
)
PRIVATE_COLUMN = re.compile(
    r"(?:^|_)(?:api_key|password|passwd|token|secret|card_number|cardholder_name|cvv|pin|"
    r"ssn|email|phone|iban|account_number|customer_name|full_name|date_of_birth|dob)(?:_|$)"
)
EXERCISE_MESSAGE = "Complete this notebook exercise"


def read_notebook(name: str) -> NotebookNode:
    notebook = nbformat.read(  # type: ignore[no-untyped-call]
        NOTEBOOK_ROOT / name,
        as_version=4,
    )
    nbformat.validate(notebook)
    return cast(NotebookNode, notebook)


def parse_code_cell(cell: NotebookNode) -> ast.Module:
    return ast.parse(cast(str, cell.source))


def code_cell_source(notebook: NotebookNode, cell_id: str) -> str:
    matches = [cell for cell in notebook.cells if cell.get("id") == cell_id]
    assert len(matches) == 1
    return cast(str, matches[0].source)


def assert_exact_unfinished_raise(cell: NotebookNode) -> None:
    tree = parse_code_cell(cell)

    assert len(tree.body) == 1
    statement = tree.body[0]
    assert isinstance(statement, ast.Raise)
    assert statement.cause is None
    exception = statement.exc
    assert isinstance(exception, ast.Call)
    assert isinstance(exception.func, ast.Name)
    assert exception.func.id == "NotImplementedError"
    assert len(exception.args) == 1
    assert isinstance(exception.args[0], ast.Constant)
    assert exception.args[0].value == EXERCISE_MESSAGE
    assert exception.keywords == []


def assert_real_colab_upload(setup_cell: NotebookNode) -> None:
    tree = parse_code_cell(setup_cell)
    imports_files = any(
        isinstance(node, ast.ImportFrom)
        and node.module == "google.colab"
        and any(alias.name == "files" and alias.asname is None for alias in node.names)
        for node in ast.walk(tree)
    )
    calls_upload = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "upload"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "files"
        and node.args == []
        and node.keywords == []
        for node in ast.walk(tree)
    )
    relative_data_path = any(
        isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "DATA_PATH" for target in node.targets
        )
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "Path"
        and len(node.value.args) == 1
        and isinstance(node.value.args[0], ast.Constant)
        and node.value.args[0].value == "datasets/transactions.csv"
        for node in ast.walk(tree)
    )

    assert imports_files
    assert calls_upload
    assert relative_data_path


def assert_no_sensitive_content(notebook: NotebookNode) -> None:
    source = "\n".join(cast(str, cell.source) for cell in notebook.cells)

    assert not WINDOWS_ABSOLUTE_PATH.search(source)
    assert not POSIX_ABSOLUTE_PATH.search(source)
    assert not SECRET_ASSIGNMENT.search(source)
    assert not SECRET_SIGNATURE.search(source)

    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        for node in ast.walk(parse_code_cell(cell)):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            normalized = re.sub(r"[^a-z0-9]+", "_", node.value.lower()).strip("_")
            assert PRIVATE_COLUMN.search(normalized) is None


@pytest.mark.parametrize("name", NOTEBOOKS)
def test_notebook_has_learning_structure_and_python_metadata(name: str) -> None:
    notebook = read_notebook(name)
    cells = notebook.cells

    assert notebook.nbformat == 4
    assert cells
    assert cells[0].cell_type == "markdown"
    assert cells[0].source.lstrip().startswith("# ")
    assert "learning goals" in "\n".join(cell.source for cell in cells).lower()
    code_cells = [cell for cell in cells if cell.cell_type == "code"]
    assert len(code_cells) >= 3
    setup_cells = [cell for cell in code_cells if "setup" in cell.metadata.get("tags", [])]
    assert len(setup_cells) == 1
    assert_real_colab_upload(setup_cells[0])
    assert cells[-1].cell_type == "markdown"
    assert "self-check" in cells[-1].source.lower()
    assert notebook.metadata.kernelspec.name == "python3"
    assert notebook.metadata.language_info.name == "python"

    for cell in code_cells:
        assert cell.outputs == []
        assert cell.execution_count is None


@pytest.mark.parametrize("name", NOTEBOOKS)
def test_notebook_keeps_student_cells_raise_only_and_explicitly_unfinished(name: str) -> None:
    notebook = read_notebook(name)
    exercises = [
        cell
        for cell in notebook.cells
        if cell.cell_type == "code" and "exercise" in cell.metadata.get("tags", [])
    ]

    assert len(exercises) >= 3
    for cell in exercises:
        assert cast(str, cell.source).lstrip().startswith("#")
        assert_exact_unfinished_raise(cell)


@pytest.mark.parametrize("name", NOTEBOOKS)
def test_notebook_is_portable_small_private_data_free_and_offline(name: str) -> None:
    notebook = read_notebook(name)
    source = "\n".join(cell.source for cell in notebook.cells)

    assert_no_sensitive_content(notebook)
    assert "http://" not in source
    assert "https://" not in source
    for cell in notebook.cells:
        if cell.cell_type == "code":
            assert len(json.dumps(cell.outputs, ensure_ascii=False).encode("utf-8")) < 20_000


@pytest.mark.parametrize(("name", "required_terms"), NOTEBOOKS.items())
def test_notebook_covers_its_documented_topics(name: str, required_terms: tuple[str, ...]) -> None:
    notebook = read_notebook(name)
    source = "\n".join(cell.source for cell in notebook.cells).lower()

    for term in required_terms:
        assert term in source
    if name == "01_numpy_payment_arrays.ipynb":
        assert "payment_matrix" not in source


def test_numpy_exercises_require_algorithms_distinct_from_completed_branch_demo() -> None:
    notebook = read_notebook("01_numpy_payment_arrays.ipynb")
    exercises = [
        cast(str, cell.source).lower()
        for cell in notebook.cells
        if "exercise" in cell.metadata.get("tags", [])
    ]
    completed = "\n".join(
        cast(str, cell.source).lower()
        for cell in notebook.cells
        if cell.cell_type == "code"
        and "setup" not in cell.metadata.get("tags", [])
        and "exercise" not in cell.metadata.get("tags", [])
    )

    assert len(exercises) == 3
    assert all(term in completed for term in ("branch_features", "slow_branches", "column_scales"))
    assert all(term in exercises[0] for term in ("reshape", "two conditions", "amount", "retry"))
    assert all(
        term in exercises[1]
        for term in ("currency-code indexes", "one rate per transaction", "reshape", "broadcast")
    )
    assert all(
        term in exercises[2] for term in ("column_stack", "standardize", "intercept", "threshold")
    )
    assert not any(
        demo_name in "\n".join(exercises)
        for demo_name in ("branch_features", "slow_branches", "column_scales", "risk_weights")
    )


def test_pandas_completed_mechanics_use_settlement_provider_data_only() -> None:
    notebook = read_notebook("02_pandas_transaction_analysis.ipynb")
    load_source = code_cell_source(notebook, "pandas-load").lower()
    completed_mechanics = "\n".join(
        cast(str, cell.source).lower()
        for cell in notebook.cells
        if cell.cell_type == "code"
        and cell.get("id") != "pandas-load"
        and "setup" not in cell.metadata.get("tags", [])
        and "exercise" not in cell.metadata.get("tags", [])
    )

    assert "pd.read_csv(data_path)" in load_source
    assert all(
        term in load_source for term in ("transactions.head", "transactions.shape", "columns")
    )
    assert not any(
        term in load_source
        for term in (".loc[", ".iloc[", ".groupby(", ".merge(", "pd.to_datetime(")
    )
    assert all(
        term in completed_mechanics
        for term in ("settlements", "provider_directory", "gross_text", "provider_code")
    )
    assert "transactions" not in completed_mechanics


def test_pandas_exercises_define_different_transaction_contracts() -> None:
    notebook = read_notebook("02_pandas_transaction_analysis.ipynb")
    exercises = [
        cast(str, cell.source).lower()
        for cell in notebook.cells
        if "exercise" in cell.metadata.get("tags", [])
    ]

    assert len(exercises) == 3
    assert all(
        term in exercises[0]
        for term in (
            "merchant_id",
            "three uppercase letters",
            "composite duplicate",
            "without mutating",
        )
    )
    assert all(
        term in exercises[1] for term in ("utc day", "channel", "named aggregations", "stable")
    )
    assert all(
        term in exercises[2]
        for term in ("merchant_profiles", "many_to_one", "unmatched", "row order")
    )


def test_notebook_readme_documents_exact_local_and_colab_workflows() -> None:
    readme = (NOTEBOOK_ROOT / "README.md").read_text(encoding="utf-8")

    assert "PyCharm" in readme
    assert "Jupyter" in readme
    assert "datasets/transactions.csv" in readme
    assert "uv run jupyter lab" in readme
    assert "NotImplementedError" in readme

    numbered_steps = [
        (int(match.group(1)), match.group(2).lower())
        for line in readme.splitlines()
        if (match := re.fullmatch(r"(\d+)\.\s+(.+)", line)) is not None
    ]
    assert len(numbered_steps) == 5
    assert [number for number, _ in numbered_steps] == [1, 2, 3, 4, 5]
    step_text = [text for _, text in numbered_steps]
    assert all(term in step_text[0] for term in ("colab", "upload notebook", ".ipynb"))
    assert all(term in step_text[1] for term in ("run", "setup"))
    assert all(term in step_text[2] for term in ("choose", "transactions.csv", "prompt"))
    assert all(term in step_text[3] for term in ("run", "exercise"))
    assert all(term in step_text[4] for term in ("clear", "download", ".ipynb"))
