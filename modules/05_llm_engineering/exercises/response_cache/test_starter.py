"""A pure version-aware cache with injected time."""

# Error message wording is intentionally outside this exercise's contract.
# ruff: noqa: PT011
import pytest

from roadmap_tools.exercise import exercise_call

from .starter import CacheEntry, CacheKey, CacheResult, cache_response

pytestmark = pytest.mark.student_exercise

KEY = CacheKey("hours?", "local-model", "v1")


def test_fresh_hit_preserves_expiry_instead_of_sliding_it() -> None:
    entry = CacheEntry(KEY, "Nine", 12.0)
    assert exercise_call(cache_response, (entry,), KEY, now=11.0, ttl=20.0) == CacheResult(
        (entry,), "Nine", True
    )


def test_exact_expiry_is_a_miss_and_all_expired_entries_are_pruned() -> None:
    other = CacheEntry(CacheKey("map?", "local-model", "v1"), "Map", 9.0)
    assert exercise_call(
        cache_response, (CacheEntry(KEY, "Nine", 10.0), other), KEY, now=10.0, ttl=1.0
    ) == CacheResult((), None, False)


@pytest.mark.parametrize(
    "requested",
    [
        CacheKey("hours?", "local-model", "v2"),
        CacheKey("hours?", "other-model", "v1"),
        CacheKey("Hours?", "local-model", "v1"),
    ],
)
def test_every_key_component_is_exact_and_version_sensitive(requested: CacheKey) -> None:
    entry = CacheEntry(KEY, "Nine", 12.0)
    assert exercise_call(cache_response, (entry,), requested, now=10.0, ttl=1.0) == CacheResult(
        (entry,), None, False
    )


def test_write_replaces_key_and_appends_after_other_fresh_entries() -> None:
    other = CacheEntry(CacheKey("map?", "local-model", "v1"), "Map", 15.0)
    entries = (CacheEntry(KEY, "Old", 20.0), other)
    assert exercise_call(
        cache_response, entries, KEY, now=10.0, ttl=2.0, response="New"
    ) == CacheResult((other, CacheEntry(KEY, "New", 12.0)), "New", False)
    assert entries[0].response == "Old"


def test_empty_string_is_a_write_and_can_be_a_hit() -> None:
    write = exercise_call(cache_response, (), KEY, now=0.0, ttl=1.0, response="")
    assert write == CacheResult((CacheEntry(KEY, "", 1.0),), "", False)
    assert exercise_call(cache_response, write.entries, KEY, now=0.5, ttl=1.0).hit is True


def test_miss_does_not_insert_an_entry() -> None:
    assert exercise_call(cache_response, (), KEY, now=1.0, ttl=1.0) == CacheResult((), None, False)


@pytest.mark.parametrize(("now", "ttl"), [(-1.0, 1.0), (1.0, 0.0), (float("nan"), 1.0)])
def test_invalid_clock_or_ttl(now: float, ttl: float) -> None:
    with pytest.raises(ValueError):
        exercise_call(cache_response, (), KEY, now=now, ttl=ttl)


def test_duplicate_keys_are_invalid_even_if_one_entry_expired() -> None:
    with pytest.raises(ValueError):
        exercise_call(
            cache_response,
            (CacheEntry(KEY, "A", 1.0), CacheEntry(KEY, "B", 2.0)),
            KEY,
            now=3.0,
            ttl=1.0,
        )


def test_blank_key_component_is_invalid() -> None:
    with pytest.raises(ValueError):
        exercise_call(cache_response, (), CacheKey(" ", "m", "v"), now=0.0, ttl=1.0)


def test_nonfinite_expiry_is_invalid() -> None:
    with pytest.raises(ValueError):
        exercise_call(cache_response, (CacheEntry(KEY, "A", float("inf")),), KEY, now=0.0, ttl=1.0)
