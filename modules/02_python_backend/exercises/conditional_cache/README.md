# Serve a conditional document

Difficulty: Medium · Estimated time: 35–55 minutes

## Prerequisites

Module 02 FastAPI response classes, headers, application factories, and TestClient.
Know UTF-8 encoding and the difference between a response body and its metadata.

## Requirements

Implement `create_app(document)` in `starter.py`. Accept a string representing a
public static document; each app serves its own document at `GET /document`.

- Compute the SHA-256 hexadecimal digest of the exact UTF-8 bytes. The strong
  ETag is the digest enclosed in double quotes. Do not use Python's `hash()`.
- Without a matching `If-None-Match` header, return HTTP 200 with the original
  UTF-8 text, a `text/plain` content type, and that `ETag` header.
- For conditional GET, split a provided header on commas and trim each token.
  A token matches if it is `*`, the quoted ETag, or `W/` followed by that ETag.
  If any token matches, return HTTP 304, no body bytes, and the same ETag.
- Nonmatching tokens return the normal 200 response. Unquoted hashes do not
  match. Header names are case-insensitive; ETag values are case-sensitive.
- Empty and Unicode documents are valid. Responses must be deterministic and
  independent across application instances.
- Scope is limited to this documented validator grammar and GET. Modification
  routes, range requests, dates, and cache-control policy are out of scope.

## Example

```text
GET /document                         -> 200, body abc
ETag: "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"

GET /document
If-None-Match: W/"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
                                      -> 304, empty body, same ETag
```

## Edge cases and optional hints

Try a weak validator, a list containing one matching validator, `*`, stale tags,
and empty content. `hashlib.sha256` and explicit FastAPI/Starlette response
classes help keep the body and status correct. A 304 must not serialize `null`.

## Run and done when

From the repository root:

```powershell
uv run pytest modules/02_python_backend/exercises/conditional_cache -q -rx
```

Edit only `starter.py`. Done when all tests pass with zero xfails, including
byte-empty conditional responses and independent application state.
