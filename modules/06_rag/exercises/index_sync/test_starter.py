"""Revision comparisons for a local library index."""

# Error message wording is intentionally outside this exercise's contract.
# ruff: noqa: PT011
import pytest

from roadmap_tools.exercise import exercise_call

from .starter import Revision, SyncPlan, plan_index_sync

pytestmark = pytest.mark.student_exercise


def test_creates_updates_deletes_and_unchanged_are_disjoint_and_sorted() -> None:
    source = (Revision("z", "new"), Revision("a", "v1"), Revision("c", "v2"))
    indexed = (Revision("old", "v1"), Revision("c", "v1"), Revision("a", "v1"))
    assert exercise_call(plan_index_sync, source, indexed) == SyncPlan(
        (Revision("z", "new"),), (Revision("c", "v2"),), ("old",), ("a",)
    )


def test_revision_is_opaque_and_a_lower_looking_revision_still_updates() -> None:
    assert exercise_call(
        plan_index_sync, (Revision("a", "v1"),), (Revision("a", "v9"),)
    ) == SyncPlan((), (Revision("a", "v1"),), (), ())


def test_empty_source_deletes_every_indexed_document_in_id_order() -> None:
    assert exercise_call(plan_index_sync, (), (Revision("z", "x"), Revision("a", "x"))) == SyncPlan(
        (), (), ("a", "z"), ()
    )


def test_empty_index_creates_all_source_documents_in_id_order() -> None:
    assert exercise_call(plan_index_sync, (Revision("z", "x"), Revision("a", "x")), ()) == SyncPlan(
        (Revision("a", "x"), Revision("z", "x")), (), (), ()
    )


def test_empty_snapshots() -> None:
    assert exercise_call(plan_index_sync, (), ()) == SyncPlan((), (), (), ())


def test_exact_ids_and_revisions_are_preserved_and_inputs_do_not_change() -> None:
    source = (Revision(" doc ", " rev "),)
    assert exercise_call(plan_index_sync, source, ()) == SyncPlan(source, (), (), ())
    assert source == (Revision(" doc ", " rev "),)


@pytest.mark.parametrize(
    ("source", "indexed"),
    [
        ((Revision("a", "1"), Revision("a", "2")), ()),
        ((), (Revision("a", "1"), Revision("a", "1"))),
        ((Revision(" ", "1"),), ()),
        ((), (Revision("a", " "),)),
    ],
)
def test_invalid_revisions(source: tuple[Revision, ...], indexed: tuple[Revision, ...]) -> None:
    with pytest.raises(ValueError):
        exercise_call(plan_index_sync, source, indexed)
