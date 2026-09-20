"""Static and executable contracts for the Stage 7 exploratory notebook."""

from __future__ import annotations

import ast
import copy
import csv
import hashlib
import json
import os
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import cast

import nbformat
import pytest
from nbclient import NotebookClient
from nbformat import NotebookNode

pytestmark = pytest.mark.filterwarnings(
    "ignore:Proactor event loop does not implement add_reader family.*:RuntimeWarning"
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
NOTEBOOK_PATH = (
    REPOSITORY_ROOT / "projects" / "banking_ai_lab" / "notebooks" / "transaction_eda.ipynb"
)
EXERCISE_MESSAGE = "Complete this project stage"
EXPECTED_EXERCISES = {
    "exercise-missing-values": ("missing", "column", "count"),
    "exercise-duplicates": ("duplicate", "full row", "id"),
    "exercise-amount-distribution": ("amount", "distribution", "quantile"),
    "exercise-merchant-category": ("merchant", "category", "aggregate"),
    "exercise-temporal-patterns": ("utc", "hour", "day"),
    "exercise-fraud-metrics": ("fraud", "precision", "recall", "imbalance"),
}
PRIVATE_FIELD_NAMES = (
    "account_number",
    "api_key",
    "card_number",
    "customer_name",
    "cvv",
    "email_address",
    "iban",
    "password",
    "phone_number",
    "pin_code",
)
SECRET_SIGNATURE = re.compile(
    r"\b(?:sk-(?:proj-)?[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|"
    r"gh[pousr]_[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9._~+/-]{20,})\b"
)
EMAIL_LITERAL = re.compile(
    r"\b[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+\b"
)
ABSOLUTE_LOCAL_PATH = re.compile(
    r"(?<![A-Za-z0-9_])(?:[A-Za-z]:[\\/]|\\\\|/(?:Users|content|home|mnt|tmp)/)"
)
SENSITIVE_ENV_FRAGMENTS = (
    "API_KEY",
    "APIKEY",
    "AUTH",
    "AWS_",
    "AZURE_",
    "COOKIE",
    "CREDENTIAL",
    "DATABASE_URL",
    "GITHUB_",
    "GITLAB_",
    "GOOGLE_",
    "KUBE",
    "OPENAI_",
    "PASSWORD",
    "PASSWD",
    "POSTGRES",
    "SECRET",
    "SSH_",
    "TOKEN",
)


def read_notebook() -> NotebookNode:
    notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)  # type: ignore[no-untyped-call]
    nbformat.validate(notebook)
    return cast(NotebookNode, notebook)


def code_cells(notebook: NotebookNode) -> list[NotebookNode]:
    return [cell for cell in notebook.cells if cell.cell_type == "code"]


def parse_cell(cell: NotebookNode) -> ast.Module:
    return ast.parse(cast(str, cell.source))


def assert_exact_exercise_raise(cell: NotebookNode) -> None:
    tree = parse_cell(cell)
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


def fold_static_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = fold_static_string(node.left)
        right = fold_static_string(node.right)
        return None if left is None or right is None else left + right
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            elif (
                isinstance(value, ast.FormattedValue)
                and isinstance(value.value, ast.Constant)
                and isinstance(value.value.value, (str, int, float, bool, type(None)))
                and value.format_spec is None
                and value.conversion == -1
            ):
                parts.append(str(value.value.value))
            else:
                return None
        return "".join(parts)
    return None


def call_leaf_name(func: ast.expr) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    raise AssertionError("Completed cells may only use direct named or attribute calls")


def expected_transaction_digest() -> str:
    rows: list[tuple[str, str, str, str, str, str | None, str, str, bool]] = []
    dataset_path = REPOSITORY_ROOT / "datasets" / "transactions.csv"
    with dataset_path.open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            timestamp = datetime.fromisoformat(row["timestamp"]).astimezone(UTC)
            rows.append(
                (
                    row["id"],
                    row["user_id"],
                    format(float(row["amount"]), ".17g"),
                    row["currency"],
                    row["merchant"],
                    row["category"] or None,
                    timestamp.isoformat(),
                    row["status"],
                    row["is_fraud"].lower() == "true",
                )
            )
    payload = json.dumps(rows, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def expected_category_order() -> tuple[str, ...]:
    dataset_path = REPOSITORY_ROOT / "datasets" / "transactions.csv"
    with dataset_path.open(encoding="utf-8", newline="") as source:
        categories = {row["category"] for row in csv.DictReader(source) if row["category"]}
    return tuple(sorted(categories))


def isolated_kernel_environment(cwd: Path) -> dict[str, str]:
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
        if name.upper() not in blocked_names
        and not name.upper().endswith("_PROXY")
        and not any(fragment in name.upper() for fragment in SENSITIVE_ENV_FRAGMENTS)
    }
    isolated_home = cwd / ".notebook-kernel"
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
        }
    )
    return environment


def execute_completed_notebook(
    notebook: NotebookNode,
    *,
    cwd: Path,
    verifier_sources: tuple[str, ...] = (),
) -> NotebookNode:
    assert_notebook_safe_for_execution(notebook)
    executable = copy.deepcopy(notebook)
    for cell in code_cells(executable):
        if "exercise" in cell.metadata.get("tags", []):
            cell.source = "pass"
    executable.cells.extend(
        nbformat.v4.new_code_cell(source=source)  # type: ignore[no-untyped-call]
        for source in verifier_sources
    )
    executed = NotebookClient(
        executable,
        timeout=60,
        kernel_name="python3",
        allow_errors=False,
    ).execute(cwd=str(cwd), env=isolated_kernel_environment(cwd))
    return executed


def assert_completed_cells_are_narrow_infrastructure(notebook: NotebookNode) -> None:
    expected_assignment_counts = {
        "setup": Counter({"RANDOM_SEED": 1, "DATA_PATH": 1, "uploaded": 1}),
        "load": Counter(
            {
                "EXPECTED_COLUMNS": 1,
                "transactions": 1,
                "currency_order": 1,
                "category_order": 1,
                "fraud_labels": 1,
                "raw_fraud": 1,
                "status_order": 1,
                "value": 1,
            }
        ),
        "inspect": Counter({"inspection": 1}),
        "safe-counts": Counter({"status_counts": 1, "safe_counts": 1, "label": 1, "count": 1}),
    }
    expected_call_counts = {
        "setup": Counter(
            {
                "seed": 2,
                "FileNotFoundError": 2,
                "Path": 1,
                "exists": 1,
                "upload": 1,
                "mkdir": 1,
                "write_bytes": 1,
            }
        ),
        "load": Counter(
            {
                "astype": 6,
                "ValueError": 4,
                "set": 4,
                "CategoricalDtype": 3,
                "read_csv": 1,
                "sorted": 1,
                "lower": 1,
                "tuple": 1,
                "all": 1,
                "to_numeric": 1,
                "str": 1,
                "replace": 1,
                "to_datetime": 1,
                "map": 1,
                "isin": 1,
            }
        ),
        "inspect": Counter({"tuple": 1, "to_dict": 1, "astype": 1}),
        "safe-counts": Counter(
            {
                "int": 2,
                "len": 2,
                "str": 1,
                "items": 1,
                "sum": 1,
                "sort_index": 1,
                "value_counts": 1,
            }
        ),
    }
    expected_imports = {
        "setup": sorted(
            [
                ("from", "google.colab", "files", ""),
                ("from", "pathlib", "Path", ""),
                ("import", "", "numpy", "np"),
                ("import", "", "pandas", "pd"),
                ("import", "", "random", ""),
            ]
        ),
        "load": [],
        "inspect": [],
        "safe-counts": [],
    }
    expected_top_level = {
        "setup": (
            "Import",
            "ImportFrom",
            "Import",
            "Import",
            "Assign",
            "Expr",
            "Expr",
            "Assign",
            "If",
        ),
        "load": (
            "Assign",
            "Assign",
            "If",
            "Assign",
            "Assign",
            "If",
            "Assign",
            "Assign",
            "Assign",
            "Assign",
            "Assign",
            "Assign",
            "If",
            "Assign",
            "Assign",
            "If",
            "Assign",
        ),
        "inspect": ("Assign", "Expr"),
        "safe-counts": ("Assign", "Assign", "Expr"),
    }
    expected_expressions = {
        "setup": ["call:seed", "call:seed", "call:mkdir", "call:write_bytes"],
        "load": [],
        "inspect": ["name:inspection"],
        "safe-counts": ["name:safe_counts"],
    }
    required_statements = {
        "setup": (
            "random.seed(RANDOM_SEED)",
            "np.random.seed(RANDOM_SEED)",
            "uploaded = files.upload()",
            "DATA_PATH.parent.mkdir(parents=True, exist_ok=True)",
            "DATA_PATH.write_bytes(uploaded[DATA_PATH.name])",
        ),
        "load": (
            """
EXPECTED_COLUMNS = (
    "id",
    "user_id",
    "amount",
    "currency",
    "merchant",
    "category",
    "timestamp",
    "status",
    "is_fraud",
)
""",
            """
if tuple(transactions.columns) != EXPECTED_COLUMNS:
    raise ValueError("Unexpected transaction columns")
""",
            """
transactions["amount"] = pd.to_numeric(
    transactions["amount"], errors="raise"
).astype("float64")
""",
            'currency_order = ("EUR", "GBP", "MDL", "USD")',
            """
transactions["category"] = (
    transactions["category"]
    .replace("", pd.NA)
    .astype(pd.CategoricalDtype(categories=category_order, ordered=True))
)
""",
            'fraud_labels = {"true": True, "false": False}',
            """
if not raw_fraud.isin(fraud_labels).all():
    raise ValueError("Unexpected synthetic fraud label")
""",
            'status_order = ("approved", "declined", "pending", "refunded")',
        ),
        "inspect": (),
        "safe-counts": (
            """
safe_counts = {
    "rows": len(transactions),
    "columns": len(transactions.columns),
    "fraud_rows": int(transactions["is_fraud"].sum()),
    "status_counts": status_counts,
}
""",
        ),
    }
    allowed_attributes = {
        "setup": {"exists", "mkdir", "name", "parent", "random", "seed", "upload", "write_bytes"},
        "load": {
            "CategoricalDtype",
            "NA",
            "all",
            "astype",
            "columns",
            "isin",
            "lower",
            "map",
            "read_csv",
            "replace",
            "str",
            "to_datetime",
            "to_numeric",
        },
        "inspect": {"astype", "columns", "dtypes", "shape", "to_dict"},
        "safe-counts": {"columns", "items", "sort_index", "sum", "value_counts"},
    }
    allowed_transaction_columns = {
        "setup": set(),
        "load": {"amount", "category", "currency", "is_fraud", "status", "timestamp"},
        "inspect": set(),
        "safe-counts": {"is_fraud", "status"},
    }
    allowed_expression_names = {
        "setup": [],
        "load": [],
        "inspect": ["inspection"],
        "safe-counts": ["safe_counts"],
    }

    completed = {
        cast(str, cell.id): cell
        for cell in code_cells(notebook)
        if "exercise" not in cell.metadata.get("tags", [])
    }
    assert set(completed) == set(expected_assignment_counts)
    for cell_id, cell in completed.items():
        tree = parse_cell(cell)
        assert tuple(type(node).__name__ for node in tree.body) == expected_top_level[cell_id]
        assert not any(
            isinstance(
                node,
                (
                    ast.AugAssign,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.Delete,
                    ast.For,
                    ast.FunctionDef,
                    ast.Global,
                    ast.IfExp,
                    ast.Lambda,
                    ast.NamedExpr,
                    ast.Nonlocal,
                    ast.While,
                ),
            )
            for node in ast.walk(tree)
        )

        assigned = Counter(
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
        )
        assert assigned == expected_assignment_counts[cell_id]

        imports: list[tuple[str, str, str, str]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(
                    ("import", "", alias.name, alias.asname or "") for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom):
                imports.extend(
                    ("from", node.module or "", alias.name, alias.asname or "")
                    for alias in node.names
                )
        assert sorted(imports) == expected_imports[cell_id]

        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        call_counts = Counter(call_leaf_name(node.func) for node in calls)
        assert call_counts == expected_call_counts[cell_id]

        attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        assert attributes == allowed_attributes[cell_id]

        transaction_columns: set[str] = set()
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Subscript)
                and isinstance(node.value, ast.Name)
                and node.value.id == "transactions"
            ):
                continue
            assert isinstance(node.slice, ast.Constant)
            assert isinstance(node.slice.value, str)
            transaction_columns.add(node.slice.value)
        assert transaction_columns == allowed_transaction_columns[cell_id]

        expression_names = [
            node.value.id
            for node in tree.body
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Name)
        ]
        assert expression_names == allowed_expression_names[cell_id]

        expression_signatures: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Expr):
                continue
            if isinstance(node.value, ast.Name):
                expression_signatures.append(f"name:{node.value.id}")
            else:
                assert isinstance(node.value, ast.Call)
                expression_signatures.append(f"call:{call_leaf_name(node.value.func)}")
        assert expression_signatures == expected_expressions[cell_id]

        statement_dumps = {
            ast.dump(node, include_attributes=False)
            for node in ast.walk(tree)
            if isinstance(node, ast.stmt)
        }
        for required_source in required_statements[cell_id]:
            required = ast.parse(required_source.strip()).body
            assert len(required) == 1
            assert ast.dump(required[0], include_attributes=False) in statement_dumps

        if cell_id == "setup":
            fallback = tree.body[-1]
            assert isinstance(fallback, ast.If)
            expected_test = ast.parse("not DATA_PATH.exists()", mode="eval").body
            assert ast.dump(fallback.test, include_attributes=False) == ast.dump(
                expected_test, include_attributes=False
            )


def test_notebook_is_v4_python_three_with_title_goals_and_self_check() -> None:
    notebook = read_notebook()
    cells = notebook.cells
    all_source = "\n".join(cast(str, cell.source) for cell in cells)

    assert notebook.nbformat == 4
    assert cells[0].cell_type == "markdown"
    assert cast(str, cells[0].source).startswith("# Banking AI Lab")
    assert "learning goals" in all_source.lower()
    assert cells[-1].cell_type == "markdown"
    assert "self-check" in cast(str, cells[-1].source).lower()
    assert notebook.metadata.kernelspec.name == "python3"
    assert notebook.metadata.kernelspec.language == "python"
    assert notebook.metadata.language_info.name == "python"
    assert cast(str, notebook.metadata.language_info.version).startswith("3")


def assert_exact_seed_path_and_colab_contract(notebook: NotebookNode) -> None:
    trees = [parse_cell(cell) for cell in code_cells(notebook)]
    assignments = [
        node for tree in trees for node in ast.walk(tree) if isinstance(node, ast.Assign)
    ]

    seed_values = [
        node.value.value
        for node in assignments
        if any(
            isinstance(target, ast.Name) and target.id == "RANDOM_SEED" for target in node.targets
        )
        and isinstance(node.value, ast.Constant)
    ]
    data_paths = [
        node.value
        for node in assignments
        if any(isinstance(target, ast.Name) and target.id == "DATA_PATH" for target in node.targets)
    ]

    assert seed_values == [20260919]
    assert len(data_paths) == 1
    data_path = data_paths[0]
    assert isinstance(data_path, ast.Call)
    assert isinstance(data_path.func, ast.Name)
    assert data_path.func.id == "Path"
    assert len(data_path.args) == 1
    assert isinstance(data_path.args[0], ast.Constant)
    assert data_path.args[0].value == "datasets/transactions.csv"

    source = "\n".join(cast(str, cell.source) for cell in notebook.cells)
    assert "Colab" in source
    assert "no network download" in source.lower()

    imports_files = any(
        isinstance(node, ast.ImportFrom)
        and node.module == "google.colab"
        and any(alias.name == "files" and alias.asname is None for alias in node.names)
        for tree in trees
        for node in ast.walk(tree)
    )
    calls_upload = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "files"
        and node.func.attr == "upload"
        and node.args == []
        and node.keywords == []
        for tree in trees
        for node in ast.walk(tree)
    )
    assert imports_files
    assert calls_upload


def test_notebook_uses_exact_seed_relative_dataset_and_manual_colab_fallback() -> None:
    assert_exact_seed_path_and_colab_contract(read_notebook())


def assert_exact_exercise_contract(notebook: NotebookNode) -> None:
    exercises = {
        cast(str, cell.id): cell
        for cell in code_cells(notebook)
        if "exercise" in cell.metadata.get("tags", [])
    }

    assert set(exercises) == set(EXPECTED_EXERCISES)
    for cell_id, required_terms in EXPECTED_EXERCISES.items():
        cell = exercises[cell_id]
        source = cast(str, cell.source)
        assert source.lstrip().startswith("# Exercise")
        assert source.count("#") >= 2
        assert all(term in source.lower() for term in required_terms)
        assert_exact_exercise_raise(cell)


def test_notebook_has_six_distinct_raise_only_student_analyses() -> None:
    assert_exact_exercise_contract(read_notebook())


def test_completed_cells_load_parse_and_inspect_without_solving_student_analyses() -> None:
    notebook = read_notebook()
    assert_completed_cells_are_narrow_infrastructure(notebook)
    completed = {
        cast(str, cell.id): cast(str, cell.source)
        for cell in code_cells(notebook)
        if "exercise" not in cell.metadata.get("tags", [])
    }
    completed_source = "\n".join(completed.values())

    assert {"setup", "load", "inspect", "safe-counts"} <= set(completed)
    assert "pd.read_csv(DATA_PATH" in completed_source
    assert "pd.to_numeric" in completed_source
    assert "float64" in completed_source
    assert "pd.to_datetime" in completed_source
    assert "utc=True" in completed_source
    assert "transactions.shape" in completed_source
    assert "transactions.dtypes" in completed_source
    assert "value_counts" in completed_source
    inspect_attributes = {
        node.attr
        for node in ast.walk(ast.parse(completed["inspect"]))
        if isinstance(node, ast.Attribute)
    }
    assert {"columns", "shape", "dtypes"} <= inspect_attributes

    forbidden_attributes = {
        "corr",
        "describe",
        "drop_duplicates",
        "duplicated",
        "groupby",
        "head",
        "hist",
        "isna",
        "nlargest",
        "notna",
        "nsmallest",
        "pivot",
        "pivot_table",
        "plot",
        "quantile",
        "resample",
        "rolling",
        "sample",
        "tail",
    }

    for cell in code_cells(notebook):
        if "exercise" in cell.metadata.get("tags", []):
            continue
        tree = parse_cell(cell)
        imported_roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_roots.add(node.module.split(".", maxsplit=1)[0])
            if isinstance(node, ast.Attribute):
                assert node.attr not in forbidden_attributes
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"compile", "eval", "exec", "getattr", "__import__"}
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Name):
                assert node.value.id != "transactions"
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"display", "print"}
            ):
                assert not any(
                    isinstance(argument, ast.Name) and argument.id == "transactions"
                    for argument in node.args
                )
        assert imported_roots <= {"google", "numpy", "pandas", "pathlib", "random"}


@pytest.mark.parametrize(
    "prohibited_source",
    [
        pytest.param(
            """
from numpy import quantile as hidden_quantile
hidden_quantile(transactions["amount"], (0.25, 0.5, 0.75))
""",
            id="import-alias-quantile",
        ),
        pytest.param(
            """
vars(__builtins__)["eval"](
    'transactions["amount"].quantile([0.25, 0.5, 0.75])'
)
""",
            id="eval-quantile",
        ),
        pytest.param(
            '(hidden_getattr := getattr)(transactions["amount"], "head")(3)',
            id="getattr-head",
        ),
        pytest.param(
            '(hidden_getattr := getattr)(transactions["amount"], "tail")(3)',
            id="getattr-tail",
        ),
        pytest.param(
            '(hidden_getattr := getattr)(transactions["amount"], "sample")('
            "3, random_state=RANDOM_SEED)",
            id="getattr-sample",
        ),
        pytest.param(
            '(hidden_getattr := getattr)("", "join")(("C", ":/", "Use", "rs/demo/private.csv"))',
            id="composed-absolute-path",
        ),
        pytest.param(
            '(hidden_getattr := getattr)("", "join")(("ht", "tps://example.invalid/data"))',
            id="composed-url",
        ),
        pytest.param(
            '(hidden_getattr := getattr)("", "join")(("sk-", "AAAAAAAAAAAAAAAAAAAAAAAA"))',
            id="composed-credential",
        ),
        pytest.param(
            'vars(__builtins__)["eval"](\'__import__("socket")\')',
            id="eval-hidden-socket",
        ),
    ],
)
def test_completed_cells_reject_indirected_analysis_and_sensitive_values(
    prohibited_source: str,
) -> None:
    notebook = copy.deepcopy(read_notebook())
    load_cell = next(cell for cell in code_cells(notebook) if cell.id == "load")
    load_cell.source = f"{load_cell.source}\n{prohibited_source.strip()}"

    with pytest.raises(AssertionError):
        assert_completed_cells_are_narrow_infrastructure(notebook)


@pytest.mark.parametrize(
    "replacements",
    [
        pytest.param(
            (
                ("setup", "random.seed(RANDOM_SEED)", "random.seed()"),
                ("setup", "np.random.seed(RANDOM_SEED)", "np.random.seed()"),
            ),
            id="seed-calls-ignore-fixed-seed",
        ),
        pytest.param(
            (
                (
                    "setup",
                    "if not DATA_PATH.exists():",
                    "if not DATA_PATH.exists() and False:",
                ),
            ),
            id="colab-fallback-disabled",
        ),
        pytest.param(
            (
                (
                    "setup",
                    "DATA_PATH.write_bytes(uploaded[DATA_PATH.name])",
                    "DATA_PATH.parent.write_bytes(uploaded[DATA_PATH.name])",
                ),
            ),
            id="colab-write-target-is-directory",
        ),
        pytest.param(
            (
                (
                    "setup",
                    "DATA_PATH.write_bytes(uploaded[DATA_PATH.name])",
                    'DATA_PATH.write_bytes(uploaded["wrong.csv"])',
                ),
            ),
            id="colab-reads-wrong-upload-key",
        ),
        pytest.param(
            (
                (
                    "load",
                    'pd.to_numeric(transactions["amount"], errors="raise").astype("float64")',
                    'pd.to_numeric(transactions["amount"], errors="raise").astype('
                    '"float64") * 0 + 1.0',
                ),
            ),
            id="amount-values-flattened",
        ),
        pytest.param(
            (
                (
                    "load",
                    '.replace("", pd.NA)',
                    '.replace(to_replace=r".+", value=pd.NA, regex=True)',
                ),
            ),
            id="category-values-wiped",
        ),
        pytest.param(
            (
                (
                    "load",
                    'currency_order = ("EUR", "GBP", "MDL", "USD")',
                    'currency_order = ("USD", "MDL", "GBP", "EUR")',
                ),
            ),
            id="currency-category-order-reversed",
        ),
        pytest.param(
            (
                (
                    "load",
                    'status_order = ("approved", "declined", "pending", "refunded")',
                    'status_order = ("refunded", "pending", "declined", "approved")',
                ),
            ),
            id="status-category-order-reversed",
        ),
        pytest.param(
            (
                (
                    "load",
                    "if tuple(transactions.columns) != EXPECTED_COLUMNS:",
                    "if tuple(transactions.columns) != EXPECTED_COLUMNS and False:",
                ),
            ),
            id="schema-check-disabled",
        ),
        pytest.param(
            (
                (
                    "load",
                    "if not raw_fraud.isin(fraud_labels).all():",
                    "if not raw_fraud.isin(fraud_labels).all() and False:",
                ),
            ),
            id="fraud-label-check-disabled",
        ),
        pytest.param(
            (
                ("safe-counts", '"rows": len(transactions),', '"rows": 1000,'),
                (
                    "safe-counts",
                    '"fraud_rows": int(transactions["is_fraud"].sum()),',
                    '"fraud_rows": int('
                    '4 if True else transactions["is_fraud"].sum() / len(transactions)'
                    "),",
                ),
            ),
            id="hidden-fraud-prevalence-formula",
        ),
        pytest.param(
            (
                (
                    "load",
                    'fraud_labels = {"true": True, "false": False}',
                    'fraud_labels = {"true": False, "false": True}',
                ),
                ("safe-counts", '"rows": len(transactions),', '"rows": 1000,'),
                (
                    "safe-counts",
                    '"fraud_rows": int(transactions["is_fraud"].sum()),',
                    '"fraud_rows": int(len(transactions) - transactions["is_fraud"].sum()),',
                ),
            ),
            id="fraud-labels-inverted-and-count-masked",
        ),
    ],
)
def test_completed_cells_reject_semantic_and_colab_mutations(
    replacements: tuple[tuple[str, str, str], ...],
) -> None:
    notebook = copy.deepcopy(read_notebook())
    cells_by_id = {cast(str, cell.id): cell for cell in code_cells(notebook)}
    for cell_id, original, replacement in replacements:
        cell = cells_by_id[cell_id]
        source = cast(str, cell.source)
        assert original in source
        cell.source = source.replace(original, replacement, 1)

    with pytest.raises(AssertionError):
        assert_completed_cells_are_narrow_infrastructure(notebook)


def assert_notebook_is_clean_private_and_offline(notebook: NotebookNode) -> None:
    all_source = "\n".join(cast(str, cell.source) for cell in notebook.cells)
    assert "http://" not in all_source
    assert "https://" not in all_source
    assert SECRET_SIGNATURE.search(all_source) is None
    assert EMAIL_LITERAL.search(all_source) is None
    assert ABSOLUTE_LOCAL_PATH.search(all_source) is None
    assert all(name not in all_source.lower() for name in PRIVATE_FIELD_NAMES)

    for cell in code_cells(notebook):
        tree = parse_cell(cell)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module = node.names[0].name if isinstance(node, ast.Import) else node.module or ""
                assert module.split(".", maxsplit=1)[0] not in {
                    "httpx",
                    "requests",
                    "socket",
                    "urllib",
                }
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                value = node.value.strip()
                assert not PurePosixPath(value).anchor
                assert not PureWindowsPath(value).anchor
            if isinstance(node, (ast.BinOp, ast.JoinedStr)):
                folded = fold_static_string(node)
                if folded is not None:
                    assert SECRET_SIGNATURE.search(folded) is None
                    assert EMAIL_LITERAL.search(folded) is None
                    assert ABSOLUTE_LOCAL_PATH.search(folded) is None
                    assert all(name not in folded.lower() for name in PRIVATE_FIELD_NAMES)

        assert cell.execution_count is None
        assert cell.outputs == []
        assert len(json.dumps(cell.outputs, ensure_ascii=False).encode("utf-8")) < 20_000


def assert_notebook_safe_for_execution(notebook: NotebookNode) -> None:
    nbformat.validate(notebook)
    assert_exact_seed_path_and_colab_contract(notebook)
    assert_exact_exercise_contract(notebook)
    assert_completed_cells_are_narrow_infrastructure(notebook)
    assert_notebook_is_clean_private_and_offline(notebook)


def test_notebook_is_clean_small_private_data_free_and_offline() -> None:
    assert_notebook_is_clean_private_and_offline(read_notebook())


def test_kernel_environment_scrubs_secrets_and_forces_offline_proxies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-reach-kernel")
    monkeypatch.setenv("DATABASE_URL", "postgresql://secret.invalid/private")
    monkeypatch.setenv("HTTPS_PROXY", "https://ambient-proxy.invalid")
    monkeypatch.setenv("PYTHONPATH", "ambient-import-path")
    monkeypatch.setenv("SAFE_LOCALE", "kept")

    environment = isolated_kernel_environment(tmp_path)

    assert "OPENAI_API_KEY" not in environment
    assert "DATABASE_URL" not in environment
    assert "PYTHONPATH" not in environment
    assert environment["SAFE_LOCALE"] == "kept"
    assert environment["HTTP_PROXY"] == "http://127.0.0.1:9"
    assert environment["HTTPS_PROXY"] == "http://127.0.0.1:9"
    assert environment["ALL_PROXY"] == "http://127.0.0.1:9"
    assert environment["NO_PROXY"] == ""
    assert Path(environment["HOME"]).is_relative_to(tmp_path)
    assert Path(environment["JUPYTER_RUNTIME_DIR"]).is_relative_to(tmp_path)


def test_colab_fallback_uploads_missing_dataset_to_relative_path(tmp_path: Path) -> None:
    notebook = read_notebook()
    setup_source = next(
        cast(str, cell.source) for cell in code_cells(notebook) if cell.id == "setup"
    )
    uploaded_bytes = b"synthetic-upload-sentinel\n"
    bootstrap = f"""
import sys
import types

_uploaded_bytes = {uploaded_bytes!r}
_upload_calls = []

def _upload():
    _upload_calls.append("called")
    return {{"transactions.csv": _uploaded_bytes}}

_files = types.SimpleNamespace(upload=_upload)
_colab = types.ModuleType("google.colab")
_colab.files = _files
_google = types.ModuleType("google")
_google.__path__ = []
_google.colab = _colab
sys.modules["google"] = _google
sys.modules["google.colab"] = _colab
""".strip()
    verifier = """
assert _upload_calls == ["called"]
assert DATA_PATH == Path("datasets/transactions.csv")
assert DATA_PATH.read_bytes() == _uploaded_bytes
""".strip()
    simulation = nbformat.v4.new_notebook(  # type: ignore[no-untyped-call]
        cells=[
            nbformat.v4.new_code_cell(source=bootstrap),  # type: ignore[no-untyped-call]
            nbformat.v4.new_code_cell(source=setup_source),  # type: ignore[no-untyped-call]
            nbformat.v4.new_code_cell(source=verifier),  # type: ignore[no-untyped-call]
        ]
    )

    assert_notebook_safe_for_execution(notebook)
    NotebookClient(
        simulation,
        timeout=60,
        kernel_name="python3",
        allow_errors=False,
    ).execute(cwd=str(tmp_path), env=isolated_kernel_environment(tmp_path))

    assert (tmp_path / "datasets" / "transactions.csv").read_bytes() == uploaded_bytes


def test_unsafe_completed_cell_is_rejected_before_kernel_execution(tmp_path: Path) -> None:
    notebook = copy.deepcopy(read_notebook())
    setup_cell = next(cell for cell in code_cells(notebook) if cell.id == "setup")
    setup_cell.source = (
        f'{setup_cell.source}\nPath("probe-side-effect.txt").write_text('
        '"EXECUTED", encoding="utf-8")'
    )
    dataset_copy = tmp_path / "datasets" / "transactions.csv"
    dataset_copy.parent.mkdir(parents=True)
    dataset_copy.write_bytes((REPOSITORY_ROOT / "datasets" / "transactions.csv").read_bytes())

    with pytest.raises(AssertionError):
        execute_completed_notebook(notebook, cwd=tmp_path)

    assert not (tmp_path / "probe-side-effect.txt").exists()


def test_completed_notebook_executes_from_temporary_repo_copy(
    tmp_path: Path,
) -> None:
    notebook = read_notebook()
    dataset_copy = tmp_path / "datasets" / "transactions.csv"
    dataset_copy.parent.mkdir(parents=True)
    dataset_copy.write_bytes((REPOSITORY_ROOT / "datasets" / "transactions.csv").read_bytes())
    schema_verifier = """
assert tuple(transactions.columns) == (
    "id",
    "user_id",
    "amount",
    "currency",
    "merchant",
    "category",
    "timestamp",
    "status",
    "is_fraud",
)
assert transactions.shape == (1000, 9)
assert transactions.dtypes.astype(str).to_dict() == {
    "id": "string",
    "user_id": "string",
    "amount": "float64",
    "currency": "category",
    "merchant": "string",
    "category": "category",
    "timestamp": "datetime64[ns, UTC]",
    "status": "category",
    "is_fraud": "bool",
}
assert safe_counts == {
    "rows": 1000,
    "columns": 9,
    "fraud_rows": 4,
    "status_counts": {"approved": 874, "declined": 78, "pending": 31, "refunded": 17},
}
""".strip()
    semantic_verifier = """
import hashlib as _hashlib
import json as _json

_canonical_rows = [
    (
        str(row[0]),
        str(row[1]),
        format(float(row[2]), ".17g"),
        str(row[3]),
        str(row[4]),
        None if pd.isna(row[5]) else str(row[5]),
        row[6].isoformat(),
        str(row[7]),
        bool(row[8]),
    )
    for row in transactions.itertuples(index=False, name=None)
]
_payload = _json.dumps(
    _canonical_rows,
    ensure_ascii=True,
    separators=(",", ":"),
).encode("utf-8")
assert _hashlib.sha256(_payload).hexdigest() == __EXPECTED_DIGEST__
assert tuple(transactions["currency"].cat.categories) == ("EUR", "GBP", "MDL", "USD")
assert tuple(transactions["category"].cat.categories) == __EXPECTED_CATEGORIES__
assert tuple(transactions["status"].cat.categories) == (
    "approved",
    "declined",
    "pending",
    "refunded",
)
assert transactions["currency"].cat.ordered
assert transactions["category"].cat.ordered
assert transactions["status"].cat.ordered
assert random.random() == 0.6334896914538571
assert float(np.random.random()) == 0.368507245109836
""".strip()
    semantic_verifier = semantic_verifier.replace(
        "__EXPECTED_DIGEST__", repr(expected_transaction_digest())
    ).replace("__EXPECTED_CATEGORIES__", repr(expected_category_order()))
    executed = execute_completed_notebook(
        notebook,
        cwd=tmp_path,
        verifier_sources=(schema_verifier, semantic_verifier),
    )

    assert executed is not notebook
    output_cells = {cast(str, cell.id): cell for cell in code_cells(executed) if cell.outputs}
    assert set(output_cells) == {"inspect", "safe-counts"}

    inspect_outputs = output_cells["inspect"].outputs
    assert len(inspect_outputs) == 1
    assert inspect_outputs[0].output_type == "execute_result"
    assert ast.literal_eval(cast(str, inspect_outputs[0].data["text/plain"])) == {
        "shape": (1000, 9),
        "columns": (
            "id",
            "user_id",
            "amount",
            "currency",
            "merchant",
            "category",
            "timestamp",
            "status",
            "is_fraud",
        ),
        "dtypes": {
            "id": "string",
            "user_id": "string",
            "amount": "float64",
            "currency": "category",
            "merchant": "string",
            "category": "category",
            "timestamp": "datetime64[ns, UTC]",
            "status": "category",
            "is_fraud": "bool",
        },
    }

    safe_counts_cell = output_cells["safe-counts"]
    assert len(safe_counts_cell.outputs) == 1
    safe_output = safe_counts_cell.outputs[0]
    assert safe_output.output_type == "execute_result"
    assert ast.literal_eval(cast(str, safe_output.data["text/plain"])) == {
        "rows": 1000,
        "columns": 9,
        "fraud_rows": 4,
        "status_counts": {"approved": 874, "declined": 78, "pending": 31, "refunded": 17},
    }
    rendered_outputs = "\n".join(
        json.dumps(cell.outputs, ensure_ascii=False)
        for cell in code_cells(executed)
        if cell.outputs
    )
    assert len(rendered_outputs.encode("utf-8")) < 20_000
    assert re.search(r"\b[0-9a-f]{8}-[0-9a-f-]{27,}\b", rendered_outputs) is None
    assert re.search(r"\buser-\d+\b", rendered_outputs) is None
    assert "http://" not in rendered_outputs
    assert "https://" not in rendered_outputs
    assert SECRET_SIGNATURE.search(rendered_outputs) is None
    assert EMAIL_LITERAL.search(rendered_outputs) is None
    assert ABSOLUTE_LOCAL_PATH.search(rendered_outputs) is None
    assert all(name not in rendered_outputs.lower() for name in PRIVATE_FIELD_NAMES)
