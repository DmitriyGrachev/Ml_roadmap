# Check a library artifact manifest

Difficulty: Medium. Estimated time: 40–65 minutes.

Prerequisites: mappings, regular expressions, bytes, `hashlib`, and
[01 — Serving](../../01_serving_contracts/README.md) and
[02 — Releases](../../02_releases_evaluation/README.md).

A library search release lists its prompt and index artifacts. Check the versioned manifest
against caller-supplied local byte snapshots before another component considers loading them.
This function never reads a filesystem, unpickles data, imports artifacts, or opens a network.

## Contract

Implement `validate_manifest(manifest, snapshots)` using the supplied record types.

1. The schema version is the integer `1`, excluding boolean `True`. `release_id` has
   1–80 characters, with no leading or trailing whitespace. Entries number 1–100.
2. Each path is a unique, case-sensitive relative key of at most 240 characters.
   Components are separated by a single `/`. Each component matches
   `[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*` in full. Thus absolute paths, drive prefixes,
   backslashes, empty components, `.`/`..`, leading/trailing dots, and spaces are invalid.
   Do not normalize a rejected path into an accepted one. These are portable manifest
   keys, not proof that a similarly named native filesystem path is safe to open.
3. Each SHA-256 digest is exactly 64 lowercase hexadecimal characters (`0-9`, `a-f`).
   Duplicate paths are invalid even when their digests agree.
4. Validate **all** metadata before checking snapshots. Invalid metadata raises `ValueError`.
   Then process entries in declaration order: a missing snapshot raises `FileNotFoundError`;
   a mismatched SHA-256 digest raises `ValueError`. Hash the actual bytes with `hashlib`.
   Other inputs use the declared types; error message wording is not prescribed.
5. Unlisted snapshots are ignored. On success, return the manifest paths as a tuple sorted
   lexicographically. Do not mutate the manifest or mapping or interpret artifact contents.

## Example

The bytes `b"abc"` have SHA-256
`ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad`.
A schema-1 manifest listing `prompts/catalog.txt` with this digest and a matching snapshot
returns `("prompts/catalog.txt",)`. Replacing the bytes with `b"abd"` must fail.

## TODO boundary and run

Implement `validate_manifest`; data shapes are provided, validation and hashing are not.

```powershell
uv run pytest modules/08_production_ai/exercises/artifact_manifest -q -rx
```

Optional hints: distinguish structural checks from content checks. Match the entire path
component and digest; a prefix match can accept a trailing invalid character.

Done when the focused tests pass with zero xfails and you can explain the limits: hashes
check consistency with a manifest, not publisher identity or artifact trustworthiness.
An attacker who changes both content and manifest can still pass. No sandbox, signature,
symlink protection, native filename guarantee, or safe-deserialization guarantee is provided.
