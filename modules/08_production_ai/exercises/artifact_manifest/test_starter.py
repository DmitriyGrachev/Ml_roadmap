"""Validate versioned names and content hashes on caller-supplied byte snapshots."""

# ruff: noqa: PT011 -- The public contract specifies exception classes, not message text.

from hashlib import sha256

import pytest

from roadmap_tools import exercise_call

from .starter import ArtifactEntry, ArtifactManifest, validate_manifest

ABC_HASH = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
EMPTY_HASH = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_checks_bytes_and_returns_sorted_paths_without_mutating_snapshots() -> None:
    manifest = ArtifactManifest(
        1,
        "library-v2",
        (ArtifactEntry("z/prompt.txt", ABC_HASH), ArtifactEntry("a/index.bin", EMPTY_HASH)),
    )
    snapshots = {"z/prompt.txt": b"abc", "a/index.bin": b"", "unused.bin": b"unused"}
    assert exercise_call(validate_manifest, manifest, snapshots) == ("a/index.bin", "z/prompt.txt")
    assert snapshots == {"z/prompt.txt": b"abc", "a/index.bin": b"", "unused.bin": b"unused"}
    assert manifest.entries[0].path == "z/prompt.txt"


def test_missing_artifact_raises_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        exercise_call(
            validate_manifest, ArtifactManifest(1, "v1", (ArtifactEntry("a", ABC_HASH),)), {}
        )


def test_content_mismatch_is_rejected_even_when_length_matches() -> None:
    with pytest.raises(ValueError):
        exercise_call(
            validate_manifest,
            ArtifactManifest(1, "v1", (ArtifactEntry("a", ABC_HASH),)),
            {"a": b"abd"},
        )


@pytest.mark.parametrize(
    "path",
    ["/a", "../a", "a/../b", "a//b", "a/./b", "C:/a", "a\\b", "a/", "a.", ".hidden", "a name", ""],
)
def test_rejects_noncanonical_relative_keys(path: str) -> None:
    with pytest.raises(ValueError):
        exercise_call(
            validate_manifest,
            ArtifactManifest(1, "v1", (ArtifactEntry(path, ABC_HASH),)),
            {path: b"abc"},
        )


@pytest.mark.parametrize("digest", [ABC_HASH.upper(), "0" * 63, "g" * 64, "", " " + ABC_HASH])
def test_requires_canonical_sha256_text(digest: str) -> None:
    with pytest.raises(ValueError):
        exercise_call(
            validate_manifest,
            ArtifactManifest(1, "v1", (ArtifactEntry("a", digest),)),
            {"a": b"abc"},
        )


def test_rejects_duplicate_paths_even_if_digests_agree() -> None:
    with pytest.raises(ValueError):
        exercise_call(
            validate_manifest,
            ArtifactManifest(1, "v1", (ArtifactEntry("a", ABC_HASH),) * 2),
            {"a": b"abc"},
        )


@pytest.mark.parametrize("version", [0, 2, True])
def test_rejects_unknown_or_boolean_schema_version(version: int) -> None:
    with pytest.raises(ValueError):
        exercise_call(
            validate_manifest,
            ArtifactManifest(version, "v1", (ArtifactEntry("a", ABC_HASH),)),
            {"a": b"abc"},
        )


@pytest.mark.parametrize("release", ["", " v1", "v1 ", "x" * 81])
def test_release_identifier_is_required_and_bounded(release: str) -> None:
    with pytest.raises(ValueError):
        exercise_call(
            validate_manifest,
            ArtifactManifest(1, release, (ArtifactEntry("a", ABC_HASH),)),
            {"a": b"abc"},
        )


def test_rejects_empty_manifest() -> None:
    with pytest.raises(ValueError):
        exercise_call(validate_manifest, ArtifactManifest(1, "v1", ()), {})


def test_rejects_too_many_entries_before_content_lookup() -> None:
    entries = tuple(ArtifactEntry(f"item-{number}", ABC_HASH) for number in range(101))
    with pytest.raises(ValueError):
        exercise_call(validate_manifest, ArtifactManifest(1, "v1", entries), {})


def test_rejects_path_over_length_limit() -> None:
    path = "a" * 241
    with pytest.raises(ValueError):
        exercise_call(
            validate_manifest,
            ArtifactManifest(1, "v1", (ArtifactEntry(path, ABC_HASH),)),
            {path: b"abc"},
        )


def test_validates_all_metadata_before_reading_missing_content() -> None:
    manifest = ArtifactManifest(
        1, "v1", (ArtifactEntry("missing", ABC_HASH), ArtifactEntry("../invalid", ABC_HASH))
    )
    with pytest.raises(ValueError):
        exercise_call(validate_manifest, manifest, {})


def test_binary_payload_is_hashed_without_interpreting_it() -> None:
    payload = b"\x80\x04not-a-safe-object\x00\xff"
    manifest = ArtifactManifest(
        1, "v1", (ArtifactEntry("museum.bin", sha256(payload).hexdigest()),)
    )
    assert exercise_call(validate_manifest, manifest, {"museum.bin": payload}) == ("museum.bin",)
