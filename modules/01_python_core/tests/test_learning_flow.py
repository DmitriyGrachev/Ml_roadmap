"""Curriculum contracts for the complete Module 01 learning flow."""

from __future__ import annotations

import ast
import re
from collections import Counter
from pathlib import Path

import pytest

MODULE_ROOT = Path(__file__).parents[1]
LESSONS = (
    "00_environment",
    "01_object_model",
    "02_collections",
    "03_functions",
    "04_typing",
    "05_data_modeling",
    "06_exceptions_io",
    "07_iterators_generators",
    "08_decorators",
    "09_testing",
    "10_asyncio",
)
SHARED_HEADINGS = (
    "Goal",
    "Java mental model",
    "Python model",
    "Key concepts",
    "Example",
    "Exercises",
    "Self-check",
    "Done when",
)

FIRST_SPRINT_CODING = (
    "02_collections/exercises/detect_duplicates/README.md",
    "02_collections/exercises/group_by_user/README.md",
    "02_collections/exercises/provider_frequency/README.md",
    "02_collections/exercises/sort_payments/README.md",
    "02_collections/exercises/filter_project_events/README.md",
    "02_collections/exercises/slice_windows/README.md",
    "02_collections/exercises/unpack_settlements/README.md",
    "03_functions/exercises/configurable_filter/README.md",
    "03_functions/exercises/combine_responses/README.md",
    "04_typing/exercises/payment_processor_protocol/README.md",
)
DEBUGGING_PRACTICE = (
    "03_functions/debugging/mutable_defaults/README.md",
    "07_iterators_generators/debugging/iterator_exhaustion/README.md",
)
CODE_REVIEW_PRACTICE = (
    "02_collections/code_review/java_shaped_grouping/README.md",
    "03_functions/code_review/stateful_report/README.md",
)
MINI_FEATURES = ("mini_features/transaction_report/README.md",)
LATER_EXERCISES = (
    "05_data_modeling/exercises/payment_model/README.md",
    "06_exceptions_io/exercises/json_export/README.md",
    "07_iterators_generators/exercises/stream_transactions/README.md",
    "08_decorators/exercises/retry_gateway/README.md",
    "09_testing/exercises/mock_provider/README.md",
    "10_asyncio/exercises/fetch_quotes/README.md",
)
NEUTRAL_EXERCISES = (
    "exercises/calendar_intervals/README.md",
    "exercises/word_index/README.md",
    "exercises/paged_stream/README.md",
    "exercises/bounded_fetch/README.md",
    "exercises/interview_patterns/README.md",
)
ALL_PRACTICE = (
    FIRST_SPRINT_CODING
    + DEBUGGING_PRACTICE
    + CODE_REVIEW_PRACTICE
    + MINI_FEATURES
    + LATER_EXERCISES
    + NEUTRAL_EXERCISES
)
LESSON_PRACTICE = {
    "00_environment": (),
    "01_object_model": (),
    "02_collections": (
        *FIRST_SPRINT_CODING[:7],
        CODE_REVIEW_PRACTICE[0],
        MINI_FEATURES[0],
    ),
    "03_functions": (
        *FIRST_SPRINT_CODING[7:9],
        DEBUGGING_PRACTICE[0],
        CODE_REVIEW_PRACTICE[1],
    ),
    "04_typing": (FIRST_SPRINT_CODING[9],),
    "05_data_modeling": (LATER_EXERCISES[0],),
    "06_exceptions_io": (LATER_EXERCISES[1],),
    "07_iterators_generators": (DEBUGGING_PRACTICE[1], LATER_EXERCISES[2]),
    "08_decorators": (LATER_EXERCISES[3],),
    "09_testing": (LATER_EXERCISES[4],),
    "10_asyncio": (LATER_EXERCISES[5],),
}


def read_lesson(lesson: str) -> str:
    return (MODULE_ROOT / lesson / "README.md").read_text(encoding="utf-8")


def markdown_targets(markdown: str) -> list[str]:
    return re.findall(r"\[[^\]]+\]\(([^)]+)\)", markdown)


def exercise_section(markdown: str) -> str:
    return markdown.split("## Exercises\n", 1)[1].split("\n## Self-check", 1)[0]


def module_relative_target(readme: Path, target: str) -> str:
    path_text = target.split("#", 1)[0]
    resolved = (readme.parent / path_text).resolve()
    return resolved.relative_to(MODULE_ROOT.resolve()).as_posix()


@pytest.mark.parametrize("lesson", LESSONS)
def test_lessons_keep_shared_headings_and_five_to_ten_self_checks(lesson: str) -> None:
    markdown = read_lesson(lesson)

    assert tuple(re.findall(r"^## (.+)$", markdown, flags=re.MULTILINE)) == SHARED_HEADINGS
    self_check = markdown.split("## Self-check\n", 1)[1].split("\n## Done when", 1)[0]
    questions = re.findall(r"^\d+\. ", self_check, flags=re.MULTILINE)
    assert 5 <= len(questions) <= 10


def test_object_model_contrasts_dynamic_typing_and_python_conventions_with_java() -> None:
    markdown = read_lesson("01_object_model").lower()
    java_model = markdown.split("## java mental model", 1)[1].split("## python model", 1)[0]

    assert "static typing" in java_model
    assert "dynamically typed" in markdown
    assert "runtime" in markdown
    assert "conventions" in markdown
    assert "pythonic" in markdown


def test_functions_explain_collection_and_forwarding_semantics_of_variadic_arguments() -> None:
    markdown = read_lesson("03_functions")
    compact = " ".join(markdown.split())

    assert re.search(r"`\*args`[^.]*tuple", compact)
    assert re.search(r"`\*\*kwargs`[^.]*dict", compact)
    assert "unpack" in compact.lower()
    assert "forward" in compact.lower()


def test_exception_example_defines_raises_and_catches_its_custom_exception() -> None:
    source = (MODULE_ROOT / "06_exceptions_io" / "example.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    custom_exceptions = {
        node.name
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and any(isinstance(base, ast.Name) and base.id.endswith("Error") for base in node.bases)
    }
    raised_names = {
        node.exc.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Raise)
        and isinstance(node.exc, ast.Call)
        and isinstance(node.exc.func, ast.Name)
    }
    caught_names = {
        handler.type.id
        for handler in (node for node in ast.walk(tree) if isinstance(node, ast.ExceptHandler))
        if isinstance(handler.type, ast.Name)
    }

    assert custom_exceptions
    assert custom_exceptions <= raised_names
    assert custom_exceptions <= caught_names


def test_exceptions_lesson_teaches_the_custom_exception_flow_explicitly() -> None:
    markdown = read_lesson("06_exceptions_io").lower()

    assert "custom exception" in markdown
    assert "raise" in markdown
    assert "except" in markdown


def test_async_lesson_pins_the_event_loop_model_and_parallelism_boundary() -> None:
    markdown = read_lesson("10_asyncio").lower()

    for concept in (
        "coroutine",
        "async",
        "await",
        "event loop",
        "gather",
        "thread",
        "cpu parallelism",
    ):
        assert concept in markdown


def test_module_practice_map_has_the_exact_complete_inventory_once() -> None:
    assert len(FIRST_SPRINT_CODING) == 10
    assert len(DEBUGGING_PRACTICE) == 2
    assert len(CODE_REVIEW_PRACTICE) == 2
    assert len(MINI_FEATURES) == 1
    assert len(LATER_EXERCISES) == 6
    assert len(NEUTRAL_EXERCISES) == 5
    assert len(set(ALL_PRACTICE)) == 26

    discovered = {
        path.relative_to(MODULE_ROOT).as_posix()
        for path in MODULE_ROOT.rglob("README.md")
        if any(
            part in {"exercises", "debugging", "code_review", "mini_features"}
            for part in path.parts
        )
    }
    assert discovered == set(ALL_PRACTICE)

    module_readme = MODULE_ROOT / "README.md"
    linked = Counter(
        module_relative_target(module_readme, target)
        for target in markdown_targets(module_readme.read_text(encoding="utf-8"))
        if module_relative_target(module_readme, target) in ALL_PRACTICE
    )
    assert linked == Counter({path: 1 for path in ALL_PRACTICE})


@pytest.mark.parametrize("lesson", LESSONS)
def test_each_exercises_section_links_its_lesson_specific_practice(lesson: str) -> None:
    readme = MODULE_ROOT / lesson / "README.md"
    section = exercise_section(readme.read_text(encoding="utf-8"))
    links = markdown_targets(section)
    linked_practice = {
        module_relative_target(readme, target)
        for target in links
        if module_relative_target(readme, target) in ALL_PRACTICE
    }

    assert links, f"{lesson} needs actionable linked navigation"
    assert linked_practice == set(LESSON_PRACTICE[lesson])


def test_all_module_and_lesson_markdown_links_resolve() -> None:
    readmes = [
        MODULE_ROOT / "README.md",
        *(MODULE_ROOT / lesson / "README.md" for lesson in LESSONS),
    ]

    for readme in readmes:
        for target in markdown_targets(readme.read_text(encoding="utf-8")):
            assert "://" not in target
            path_text = target.split("#", 1)[0]
            assert path_text, f"use a file-qualified link in {readme}"
            assert (readme.parent / path_text).is_file(), f"broken link {target!r} in {readme}"


def test_navigation_has_no_stale_placeholders_or_solution_hints() -> None:
    stale = re.compile(
        r"\b(?:later|next|future)\s+(?:tasks?|exercises?|practice|coding task)\b|"
        r"\bexercises?\s+(?:arrive|follow|will be added)\b",
        flags=re.IGNORECASE,
    )
    sections = [(MODULE_ROOT / "README.md").read_text(encoding="utf-8")]
    sections.extend(exercise_section(read_lesson(lesson)) for lesson in LESSONS)

    for section in sections:
        assert stale.search(section) is None
        assert "solution" not in section.lower()
        assert "hint" not in section.lower()
        assert "```" not in section
