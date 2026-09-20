from __future__ import annotations

import ast
import json
import re
from collections.abc import Sequence
from pathlib import Path, PurePosixPath, PureWindowsPath
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
ABSOLUTE_LOCAL_PATH = re.compile(
    r"(?<![\w:/])(?:[A-Za-z]:[\\/][^\s\"'`]+|\\\\[^\s\"'`]+|"
    r"/(?!/)[A-Za-z0-9._~-]+(?:/[A-Za-z0-9._~-]+)*)"
)
SECRET_SIGNATURE = re.compile(
    r"\b(?:sk-(?:proj-)?[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|"
    r"gh[pousr]_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|"
    r"Bearer\s+[A-Za-z0-9._~+/-]{20,})\b"
)
EMAIL_LITERAL = re.compile(
    r"\b[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+\b"
)
CARD_CANDIDATE = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
SENSITIVE_NON_TOKEN_IDENTIFIER = re.compile(r"(?:^|_)(?:api_key|password|passwd|secret)(?:_|$)")
PRIVATE_FIELD_IDENTIFIER = re.compile(
    r"(?:^|_)(?:card_number|cardholder_name|cvv|pin|ssn|email|phone|iban|"
    r"account_number|customer_name|full_name|date_of_birth|dob)(?:_|$)"
)
SAFE_PROSE_CUE = re.compile(
    r"\b(?:warning|never|do not|don't|avoid|must not|should not|placeholder|training note)\b",
    re.IGNORECASE,
)
SAFE_PROSE_TARGET = re.compile(r"(?:^|_)(?:warning|message|instruction|note|prose)(?:_|$)")
SAFE_TOKEN_NEIGHBORS = {
    "average",
    "budget",
    "budgets",
    "completion",
    "count",
    "counts",
    "id",
    "ids",
    "input",
    "length",
    "lengths",
    "limit",
    "limits",
    "max",
    "min",
    "output",
    "prompt",
    "size",
    "sizes",
    "total",
    "usage",
}
PATH_CONSTRUCTORS = {"Path", "PurePath", "PurePosixPath", "PureWindowsPath"}
MAX_STATIC_STRING_LENGTH = 10_000
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


def normalize_identifier(value: str) -> str:
    with_camel_boundaries = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return re.sub(r"[^a-z0-9]+", "_", with_camel_boundaries.lower()).strip("_")


def is_sensitive_identifier(value: str) -> bool:
    normalized = normalize_identifier(value)
    if SENSITIVE_NON_TOKEN_IDENTIFIER.search(normalized):
        return True

    parts = normalized.split("_")
    for index, part in enumerate(parts):
        if part == "tokens":
            continue
        if part != "token":
            continue
        previous = parts[index - 1] if index > 0 else ""
        following = parts[index + 1] if index + 1 < len(parts) else ""
        if previous not in SAFE_TOKEN_NEIGHBORS and following not in SAFE_TOKEN_NEIGHBORS:
            return True
    return False


def stored_identifier_names(tree: ast.Module) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        name: str | None = None
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            name = node.id
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
            name = node.attr
        elif isinstance(node, (ast.arg, ast.keyword)):
            name = node.arg
        elif isinstance(node, ast.MatchMapping):
            name = node.rest
        elif isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)):
            name = node.name
        elif isinstance(node, ast.Import):
            names.extend(
                alias.asname or alias.name.split(".", maxsplit=1)[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            names.extend(alias.asname or alias.name for alias in node.names if alias.name != "*")
        if name is not None:
            names.append(name)
    return names


def parent_nodes(tree: ast.Module) -> dict[ast.AST, ast.AST]:
    return {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}


def assignment_target_names(node: ast.AST) -> list[str]:
    targets: Sequence[ast.AST]
    if isinstance(node, ast.Assign):
        targets = node.targets
    elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
        targets = [node.target]
    else:
        return []

    return [
        child.id for target in targets for child in ast.walk(target) if isinstance(child, ast.Name)
    ]


def static_format_number_exceeds_limit(value: str) -> bool:
    normalized = value.lstrip("0") or "0"
    maximum = str(MAX_STATIC_STRING_LENGTH)
    return len(normalized) > len(maximum) or (
        len(normalized) == len(maximum) and normalized > maximum
    )


def fold_static_formatted_value(value: ast.FormattedValue) -> str | None:
    if isinstance(value.value, ast.Constant) and isinstance(
        value.value.value, (str, int, float, bool, type(None))
    ):
        literal_value: object = value.value.value
    else:
        folded_string = fold_static_string(value.value)
        if folded_string is None:
            return None
        literal_value = folded_string

    if not isinstance(literal_value, (str, int, float, bool, type(None))):
        return None

    format_spec = ""
    if value.format_spec is not None:
        folded_format_spec = fold_static_string(value.format_spec)
        if folded_format_spec is None:
            return None
        format_spec = folded_format_spec
    if len(format_spec) > MAX_STATIC_STRING_LENGTH or any(
        static_format_number_exceeds_limit(number) for number in re.findall(r"\d+", format_spec)
    ):
        raise AssertionError("static format specification exceeds the analysis limit")

    if value.conversion == -1:
        converted = literal_value
    elif value.conversion == ord("s"):
        converted = str(literal_value)
    elif value.conversion == ord("r"):
        converted = repr(literal_value)
    elif value.conversion == ord("a"):
        converted = ascii(literal_value)
    else:
        return None
    try:
        part = format(converted, format_spec)
    except (TypeError, ValueError):
        return None
    if len(part) > MAX_STATIC_STRING_LENGTH:
        raise AssertionError("static formatted value exceeds the analysis limit")
    return part


def fold_static_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value

    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = fold_static_string(node.left)
        right = fold_static_string(node.right)
        if left is None or right is None:
            return None
        combined = left + right
        return combined if len(combined) <= MAX_STATIC_STRING_LENGTH else None

    if not isinstance(node, ast.JoinedStr):
        return None

    parts: list[str] = []
    total_length = 0
    for value in node.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            part = value.value
        elif isinstance(value, ast.FormattedValue):
            formatted = fold_static_formatted_value(value)
            if formatted is None:
                return None
            part = formatted
        else:
            return None
        parts.append(part)
        total_length += len(part)
        if total_length > MAX_STATIC_STRING_LENGTH:
            raise AssertionError("static f-string exceeds the analysis limit")
    return "".join(parts)


def guaranteed_static_string_prefix(node: ast.AST) -> str | None:
    folded = fold_static_string(node)
    if folded is not None:
        return folded

    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = fold_static_string(node.left)
        if left is None:
            return None
        right = guaranteed_static_string_prefix(node.right) or ""
        prefix = left + right
        return prefix if len(prefix) <= MAX_STATIC_STRING_LENGTH else None

    if not isinstance(node, ast.JoinedStr):
        return None

    parts: list[str] = []
    total_length = 0
    for value in node.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            part = value.value
        elif isinstance(value, ast.FormattedValue):
            formatted = fold_static_formatted_value(value)
            if formatted is None:
                break
            part = formatted
        else:
            break
        parts.append(part)
        total_length += len(part)
        if total_length > MAX_STATIC_STRING_LENGTH:
            return None
    return "".join(parts) or None


def imported_name_aliases(tree: ast.Module) -> dict[str, tuple[str, ...]]:
    aliases: dict[str, tuple[str, ...]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for imported in node.names:
                qualified = tuple(imported.name.split("."))
                bound_name = imported.asname or qualified[0]
                aliases[bound_name] = qualified if imported.asname else (qualified[0],)
        elif isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:
            module = tuple(node.module.split("."))
            for imported in node.names:
                if imported.name != "*":
                    aliases[imported.asname or imported.name] = (*module, imported.name)
    return aliases


def qualified_name(
    node: ast.AST,
    aliases: dict[str, tuple[str, ...]],
) -> tuple[str, ...] | None:
    if isinstance(node, ast.Name):
        return aliases.get(node.id, (node.id,))
    if isinstance(node, ast.Attribute):
        parent = qualified_name(node.value, aliases)
        if parent is not None:
            return (*parent, node.attr)
    return None


def is_statically_absolute_path_call(
    node: ast.Call,
    aliases: dict[str, tuple[str, ...]],
) -> bool:
    function_name = qualified_name(node.func, aliases)
    if function_name is None or node.keywords:
        return False

    is_path_constructor = function_name[-1] in PATH_CONSTRUCTORS and (
        len(function_name) == 1 or function_name[:-1] == ("pathlib",)
    )
    is_join = function_name in {
        ("os", "path", "join"),
        ("posixpath", "join"),
        ("ntpath", "join"),
    }
    if not is_path_constructor and not is_join:
        return False

    static_run: list[str] = []
    for argument in node.args:
        part = fold_static_string(argument)
        if part is None:
            prefix = guaranteed_static_string_prefix(argument)
            if prefix is not None:
                static_run.append(prefix)
                if (
                    PurePosixPath(*static_run).is_absolute()
                    or PureWindowsPath(*static_run).is_absolute()
                ):
                    return True
            static_run.clear()
            continue
        static_run.append(part)
        if PurePosixPath(*static_run).is_absolute() or PureWindowsPath(*static_run).is_absolute():
            return True
    return False


def is_safe_prose_literal(
    node: ast.AST,
    value: str,
    parents: dict[ast.AST, ast.AST],
) -> bool:
    if (
        SECRET_SIGNATURE.search(value)
        or EMAIL_LITERAL.search(value)
        or contains_luhn_card(value)
        or ABSOLUTE_LOCAL_PATH.search(value)
    ):
        return False

    current: ast.AST = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            return any(
                SAFE_PROSE_TARGET.search(normalize_identifier(name))
                for name in assignment_target_names(current)
            )
        if isinstance(current, ast.Call):
            function_name = ""
            if isinstance(current.func, ast.Name):
                function_name = current.func.id
            elif isinstance(current.func, ast.Attribute):
                function_name = current.func.attr
            if function_name in {"display", "print", "warn", "warning"}:
                return SAFE_PROSE_CUE.search(value) is not None
        if isinstance(current, ast.Expr):
            return SAFE_PROSE_CUE.search(value) is not None
        if isinstance(current, ast.stmt):
            break
    return False


def contains_luhn_card(value: str | int) -> bool:
    for candidate in CARD_CANDIDATE.findall(str(value)):
        digits = [int(character) for character in candidate if character.isdigit()]
        if not 13 <= len(digits) <= 19 or len(set(digits)) == 1:
            continue
        checksum = 0
        parity = len(digits) % 2
        for index, digit in enumerate(digits):
            if index % 2 == parity:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
        if checksum % 10 == 0:
            return True
    return False


def assert_static_string_is_safe(
    node: ast.AST,
    value: str,
    parents: dict[ast.AST, ast.AST],
) -> None:
    value = value.strip()
    if is_safe_prose_literal(node, value, parents):
        return
    normalized = normalize_identifier(value)
    assert not is_sensitive_identifier(normalized)
    assert PRIVATE_FIELD_IDENTIFIER.search(normalized) is None
    assert EMAIL_LITERAL.search(value) is None
    assert SECRET_SIGNATURE.search(value) is None
    assert not contains_luhn_card(value)
    assert ABSOLUTE_LOCAL_PATH.search(value) is None


def assert_executable_code_has_no_sensitive_content(
    tree: ast.Module,
    inherited_aliases: dict[str, tuple[str, ...]] | None = None,
) -> None:
    for name in stored_identifier_names(tree):
        assert not is_sensitive_identifier(name)

    parents = parent_nodes(tree)
    aliases = dict(inherited_aliases or {})
    aliases.update(imported_name_aliases(tree))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                continue
            if isinstance(node.value, int):
                assert not contains_luhn_card(node.value)
                continue
            if isinstance(node.value, str):
                assert_static_string_is_safe(node, node.value, parents)
            continue

        if isinstance(node, (ast.BinOp, ast.JoinedStr)):
            static_value = fold_static_string(node)
            if static_value is not None:
                assert_static_string_is_safe(node, static_value, parents)
            continue

        if isinstance(node, ast.Call):
            assert not is_statically_absolute_path_call(node, aliases)


def assert_no_sensitive_content(notebook: NotebookNode) -> None:
    aliases: dict[str, tuple[str, ...]] = {}
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        tree = parse_code_cell(cell)
        aliases.update(imported_name_aliases(tree))
        assert_executable_code_has_no_sensitive_content(tree, aliases)


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


@pytest.mark.parametrize(
    "unsafe_source",
    [
        'OPENAI_API_KEY = "placeholder"',
        "AZURE_OPENAI_API_KEY = load_from_vault()",
        "SESSION_TOKEN = object()",
        'ADMIN_PASSWORD_HINT = "placeholder"',
        'contacts = ["learner@example.test"]',
        'test_cards = ["4242 4242 4242 4242"]',
        'service_credential = "sk-proj-abcdefghijklmnopqrstuvwxyz0123456789"',
        'scratch = Path("/content/input.csv")',
        'scratch = Path("C:/Users/learner/input.csv")',
        'command = "cp /content/input.csv output.csv"',
        'command = "type C:/Users/learner/input.csv"',
        'customers = {"customer_email": ["redacted"]}',
    ],
)
def test_privacy_contract_rejects_sensitive_executable_code(unsafe_source: str) -> None:
    notebook = read_notebook("03_fraud_metrics.ipynb")
    notebook.cells[3].source += f"\n{unsafe_source}"

    with pytest.raises(AssertionError):
        assert_no_sensitive_content(notebook)


def test_privacy_contract_ignores_non_executable_prose_comments_and_warnings() -> None:
    notebook = read_notebook("03_fraud_metrics.ipynb")
    notebook.cells[0].source += (
        "\n\nTraining warning: never paste OPENAI_API_KEY, learner@example.test, "
        "4242 4242 4242 4242, or /content/input.csv into a notebook."
    )
    notebook.cells[3].source += (
        '\n# api_key = "sk-proj-abcdefghijklmnopqrstuvwxyz0123456789"\n'
        'warning = "Warning: do not store email addresses, card numbers, API keys, or paths."\n'
        'warning += " Use synthetic placeholders in training notebooks."\n'
        'print("Never store email addresses, API keys, tokens, or passwords in notebooks.")\n'
        "print(warning)"
    )

    assert_no_sensitive_content(notebook)


def test_privacy_contract_allows_benign_token_measurement_names() -> None:
    notebook = read_notebook("03_fraud_metrics.ipynb")
    notebook.cells[
        3
    ].source += (
        "\ntoken_counts = [128, 256]\nmodel_token_budget = 4_096\naverage_token_length = 4.2"
    )

    assert_no_sensitive_content(notebook)


@pytest.mark.parametrize(
    "unsafe_payload",
    [
        'payload = "never send learner@example.test"',
        'payload = "never store 4242 4242 4242 4242"',
        'payload = "never paste sk-proj-abcdefghijklmnopqrstuvwxyz0123456789"',
    ],
)
def test_warning_words_do_not_hide_sensitive_executable_payloads(unsafe_payload: str) -> None:
    notebook = read_notebook("03_fraud_metrics.ipynb")
    notebook.cells[3].source += f"\n{unsafe_payload}"

    with pytest.raises(AssertionError):
        assert_no_sensitive_content(notebook)


@pytest.mark.parametrize(
    "unsafe_warning",
    [
        'warning = "learner@example.test"',
        'warning = "4242 4242 4242 4242"',
        'warning = "sk-proj-abcdefghijklmnopqrstuvwxyz0123456789"',
        'warning = "/content/input.csv"',
    ],
)
def test_warning_target_does_not_hide_sensitive_literal_signatures(unsafe_warning: str) -> None:
    notebook = read_notebook("03_fraud_metrics.ipynb")
    notebook.cells[3].source += f"\n{unsafe_warning}"

    with pytest.raises(AssertionError):
        assert_no_sensitive_content(notebook)


@pytest.mark.parametrize(
    "unsafe_composition",
    [
        'service_credential = "sk-proj-" + "abcdefghijklmnopqrstuvwxyz0123456789"',
        'contact = "learner" + "@" + "example.test"',
        'test_card = "4242 4242 " + "4242 4242"',
        "service_credential = f\"sk-proj-{'abcdefghijklmnopqrstuvwxyz0123456789'}\"",
        "service_credential = f\"{'sk-proj-' + 'abcdefghijklmnopqrstuvwxyz0123456789'}\"",
        "contact = f\"{'learner':>7}@example.test\"",
        "contact = f\"{'learner'!s:>7}@example.test\"",
        "contact = f\"{('learn' + 'er'):>7}@example.test\"",
        "contact = f\"{('learn' + 'er')!s:>7}@example.test\"",
        "contact = f\"{'learner':>{7}}@example.test\"",
        'scratch = Path("/", "content", "private", "data.csv")',
        'scratch = PurePath("/", "content", "private", "data.csv")',
        'scratch = pathlib.PurePosixPath("/", "mnt", "data.csv")',
        'scratch = os.path.join("/", "private", "data.csv")',
        'scratch = Path("/", runtime_name)',
    ],
)
def test_privacy_contract_rejects_static_string_and_path_compositions(
    unsafe_composition: str,
) -> None:
    notebook = read_notebook("03_fraud_metrics.ipynb")
    notebook.cells[3].source += f"\n{unsafe_composition}"

    with pytest.raises(AssertionError):
        assert_no_sensitive_content(notebook)


@pytest.mark.parametrize(
    "unsafe_binding",
    [
        "try:\n    pass\nexcept Exception as OPENAI_API_KEY:\n    pass",
        "import os as OPENAI_API_KEY",
        "from os import environ as SESSION_TOKEN",
        "from settings import AZURE_OPENAI_API_KEY",
        "value = {}\nmatch value:\n    case {**SESSION_TOKEN}:\n        pass",
    ],
)
def test_privacy_contract_rejects_sensitive_import_and_exception_bindings(
    unsafe_binding: str,
) -> None:
    notebook = read_notebook("03_fraud_metrics.ipynb")
    notebook.cells[3].source += f"\n{unsafe_binding}"

    with pytest.raises(AssertionError):
        assert_no_sensitive_content(notebook)


def test_privacy_contract_accepts_relative_url_and_dynamic_compositions() -> None:
    notebook = read_notebook("03_fraud_metrics.ipynb")
    notebook.cells[3].source += (
        '\nrelative_path = Path("datasets", "transactions.csv")\n'
        'pure_relative_path = PurePath("datasets", "transactions.csv")\n'
        'joined_relative_path = os.path.join("datasets", "transactions.csv")\n'
        'dynamic_relative_path = Path("datasets", runtime_name)\n'
        'documentation_url = "https://" + "example.test/data.csv"\n'
        'credential_label = "sk-proj-" + runtime_suffix\n'
        'contact_label = f"{runtime_user:>7}@example.test"\n'
        "dynamic_format_label = f\"{'learner':{runtime_width}}@example.test\"\n"
        'numeric_label = f"{42:04d}"\n'
        'warning = "Never store " + "API keys or passwords in notebooks."\n'
        "try:\n"
        "    pass\n"
        "except Exception as error:\n"
        "    pass\n"
        "import os as operating_system"
    )

    assert_no_sensitive_content(notebook)


def test_privacy_contract_rejects_unbounded_static_format_specs() -> None:
    notebook = read_notebook("03_fraud_metrics.ipynb")
    oversized_width = "9" * 5_000
    notebook.cells[3].source += (
        "\ncontact_label = f\"{'learner':>" + oversized_width + '}@example.test"'
    )

    with pytest.raises(AssertionError):
        assert_no_sensitive_content(notebook)


@pytest.mark.parametrize(
    "unsafe_path",
    [
        'scratch = Path("C:", "\\\\Users", runtime_name)',
        'scratch = PureWindowsPath("C:", "\\\\Users", runtime_name)',
        'scratch = ntpath.join("C:", "\\\\Users", runtime_name)',
        'scratch = os.path.join("C:", "\\\\Users", runtime_name)',
        'scratch = Path("C:/" + runtime_name)',
        'scratch = PureWindowsPath(f"C:/{runtime_name}")',
        'scratch = ntpath.join("C:/" + runtime_name)',
        'scratch = os.path.join(f"C:/{runtime_name}")',
        'import pathlib as paths\nscratch = paths.Path("C:", "\\\\Users", runtime_name)',
        'from pathlib import Path as P\nscratch = P("C:", "\\\\Users", runtime_name)',
        "import ntpath as windows_paths\n"
        'scratch = windows_paths.join("C:", "\\\\Users", runtime_name)',
        'from ntpath import join as win_join\nscratch = win_join("C:", "\\\\Users", runtime_name)',
        "import os as operating_system\n"
        'scratch = operating_system.path.join("C:", "\\\\Users", runtime_name)',
        "from os.path import join as path_join\n"
        'scratch = path_join("C:", "\\\\Users", runtime_name)',
    ],
)
def test_privacy_contract_rejects_static_windows_roots_with_dynamic_tails_and_aliases(
    unsafe_path: str,
) -> None:
    notebook = read_notebook("03_fraud_metrics.ipynb")
    notebook.cells[3].source += f"\n{unsafe_path}"

    with pytest.raises(AssertionError):
        assert_no_sensitive_content(notebook)


def test_privacy_contract_accepts_relative_and_dynamic_aliased_paths() -> None:
    notebook = read_notebook("03_fraud_metrics.ipynb")
    notebook.cells[3].source += (
        "\nimport pathlib as paths\n"
        "from pathlib import Path as P\n"
        "import ntpath as windows_paths\n"
        "from ntpath import join as win_join\n"
        "import os as operating_system\n"
        "from os.path import join as path_join\n"
        'paths.Path("datasets", runtime_name)\n'
        'P(runtime_root, "transactions.csv")\n'
        'windows_paths.join("datasets", runtime_name)\n'
        'win_join(runtime_root, "transactions.csv")\n'
        'operating_system.path.join("datasets", runtime_name)\n'
        'path_join(runtime_root, "transactions.csv")\n'
        'drive_relative_path = Path("C:", runtime_name)\n'
        'unrelated_factory_path = paths_factory.Path("C:", "\\\\Users", runtime_name)'
    )

    assert_no_sensitive_content(notebook)


@pytest.mark.parametrize(
    ("import_source", "call_source"),
    [
        (
            "import pathlib as paths",
            'scratch = paths.Path("C:", "\\\\Users", runtime_name)',
        ),
        (
            "from pathlib import Path as P",
            'scratch = P("C:", "\\\\Users", runtime_name)',
        ),
        (
            "import ntpath as windows_paths",
            'scratch = windows_paths.join("C:", "\\\\Users", runtime_name)',
        ),
        (
            "from os.path import join as path_join",
            'scratch = path_join("C:", "\\\\Users", runtime_name)',
        ),
    ],
)
def test_privacy_contract_carries_import_aliases_across_code_cells(
    import_source: str,
    call_source: str,
) -> None:
    notebook = read_notebook("03_fraud_metrics.ipynb")
    notebook.cells[1].source += f"\n{import_source}"
    notebook.cells[3].source += f"\n{call_source}"

    with pytest.raises(AssertionError):
        assert_no_sensitive_content(notebook)


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
