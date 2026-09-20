from __future__ import annotations

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
ABSOLUTE_LOCAL_PATH = re.compile(r"(?:[A-Za-z]:[\\/]|/(?:Users|home|tmp)/)")
EXERCISE_EXCEPTION = 'raise NotImplementedError("Complete this notebook exercise")'


def read_notebook(name: str) -> NotebookNode:
    notebook = nbformat.read(  # type: ignore[no-untyped-call]
        NOTEBOOK_ROOT / name,
        as_version=4,
    )
    nbformat.validate(notebook)
    return cast(NotebookNode, notebook)


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
    assert any("setup" in cell.metadata.get("tags", []) for cell in code_cells)
    assert cells[-1].cell_type == "markdown"
    assert "self-check" in cells[-1].source.lower()
    assert notebook.metadata.kernelspec.name == "python3"
    assert notebook.metadata.language_info.name == "python"


@pytest.mark.parametrize("name", NOTEBOOKS)
def test_notebook_keeps_student_cells_explicitly_unfinished(name: str) -> None:
    notebook = read_notebook(name)
    exercises = [
        cell
        for cell in notebook.cells
        if cell.cell_type == "code" and "exercise" in cell.metadata.get("tags", [])
    ]

    assert len(exercises) >= 3
    for cell in exercises:
        assert EXERCISE_EXCEPTION in cell.source
        assert cell.source.lstrip().startswith("#")
        assert cell.source.rstrip().splitlines()[-1] == EXERCISE_EXCEPTION
        assert cell.outputs == []
        assert cell.execution_count is None


@pytest.mark.parametrize("name", NOTEBOOKS)
def test_notebook_is_portable_small_and_offline(name: str) -> None:
    notebook = read_notebook(name)
    source = "\n".join(cell.source for cell in notebook.cells)

    assert 'DATA_PATH = Path("datasets/transactions.csv")' in source
    assert "files.upload" in source
    assert not ABSOLUTE_LOCAL_PATH.search(source)
    assert "http://" not in source
    assert "https://" not in source
    for cell in notebook.cells:
        if cell.cell_type == "code":
            assert cell.outputs == []
            assert len(json.dumps(cell.outputs, ensure_ascii=False).encode("utf-8")) < 20_000


@pytest.mark.parametrize(("name", "required_terms"), NOTEBOOKS.items())
def test_notebook_covers_its_documented_topics(name: str, required_terms: tuple[str, ...]) -> None:
    notebook = read_notebook(name)
    source = "\n".join(cell.source for cell in notebook.cells).lower()

    for term in required_terms:
        assert term in source
    if name == "01_numpy_payment_arrays.ipynb":
        assert "payment_matrix" not in source


def test_notebook_readme_documents_local_and_colab_workflows() -> None:
    readme = (NOTEBOOK_ROOT / "README.md").read_text(encoding="utf-8")

    assert "PyCharm" in readme
    assert "Jupyter" in readme
    assert "Colab" in readme
    assert "datasets/transactions.csv" in readme
    assert "uv run jupyter lab" in readme
    assert "NotImplementedError" in readme
