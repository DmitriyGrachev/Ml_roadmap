"""Use a fresh real in-memory SQLite database for every repository scenario."""

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine

from roadmap_tools.exercise import exercise_call

from .starter import Equipment, EquipmentRepository

pytestmark = pytest.mark.student_exercise


@pytest.fixture
def engine() -> Iterator[Engine]:
    database = create_engine("sqlite+pysqlite:///:memory:")
    yield database
    database.dispose()


def test_empty_repository(engine: Engine) -> None:
    assert exercise_call(EquipmentRepository(engine).list_all) == []


def test_database_is_the_record_source(engine: Engine) -> None:
    repository = EquipmentRepository(engine)
    exercise_call(repository.add, Equipment("A1", "Tripod"))
    with engine.begin() as connection:
        assert connection.execute(select(repository.table.c.name)).scalar_one() == "Tripod"
        connection.execute(repository.table.insert().values(serial="Z2", name="Camera"))
    assert exercise_call(repository.list_all) == [
        Equipment("A1", "Tripod"),
        Equipment("Z2", "Camera"),
    ]


def test_add_commits_and_new_repository_reads_sorted_records(engine: Engine) -> None:
    repository = EquipmentRepository(engine)
    exercise_call(repository.add, Equipment("Z2", "Camera"))
    exercise_call(repository.add, Equipment("A1", "Tripod"))
    assert exercise_call(EquipmentRepository(engine).list_all) == [
        Equipment("A1", "Tripod"),
        Equipment("Z2", "Camera"),
    ]


def test_duplicate_serial_is_value_error_and_preserves_first_record(engine: Engine) -> None:
    repository = EquipmentRepository(engine)
    exercise_call(repository.add, Equipment("A1", "Camera"))
    with pytest.raises(ValueError, match="serial"):
        exercise_call(repository.add, Equipment("A1", "Replacement"))
    exercise_call(repository.add, Equipment("A2", "Lens"))
    assert exercise_call(repository.list_all) == [
        Equipment("A1", "Camera"),
        Equipment("A2", "Lens"),
    ]


def test_quotes_are_data_and_result_list_is_detached(engine: Engine) -> None:
    repository = EquipmentRepository(engine)
    item = Equipment("O'7", "Artist's camera; DROP TABLE equipment;")
    exercise_call(repository.add, item)
    first = exercise_call(repository.list_all)
    assert first == [item]
    first.clear()
    assert exercise_call(repository.list_all) == [item]


@pytest.mark.parametrize(
    "item",
    [
        Equipment("", "Lens"),
        Equipment(" ", "Lens"),
        Equipment(" A1", "Lens"),
        Equipment("A1", ""),
        Equipment("A1", "  "),
        Equipment("A1", "Lens "),
    ],
)
def test_invalid_text_does_not_insert(engine: Engine, item: Equipment) -> None:
    repository = EquipmentRepository(engine)
    with pytest.raises(ValueError, match="equipment"):
        exercise_call(repository.add, item)
    assert exercise_call(repository.list_all) == []


def test_different_engines_have_independent_data(engine: Engine) -> None:
    repository = EquipmentRepository(engine)
    exercise_call(repository.add, Equipment("A1", "Lens"))
    other = create_engine("sqlite+pysqlite:///:memory:")
    try:
        assert exercise_call(EquipmentRepository(other).list_all) == []
    finally:
        other.dispose()
