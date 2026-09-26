# Authorized vector search

Difficulty: Medium

Estimated time: 60–75 minutes. Prerequisites: vector geometry, typed records and sorting.

Implement `vector_search` for a local library/garden document index. Coordinates are
supplied synthetic values, not pretrained semantic embeddings or evidence of retrieval quality.

## Contract

- Query must be a nonempty one-dimensional sequence of finite numbers. Every document
  embedding must have the same dimension and finite values. Validate **all** documents,
  even unauthorized ones or when `top_k=0`, so index corruption is not silently hidden.
- Document IDs are unique nonblank strings. Preserve exact spelling. Every role name
  in document and requester role sets is a nonblank string. Empty role sets are valid.
- `top_k` is a nonnegative integer; reject booleans. Invalid input raises `ValueError`
  naming `query`, `embedding`/`dimension`, `document`, `role` or `top_k` as appropriate.
- A document is authorized only if its `allowed_roles` intersects requester `roles`.
  Empty document roles mean nobody has access. Public access must be modeled explicitly,
  for example by the role `public` being present on both sides.
- Select authorized documents **before top-k**, compute cosine similarity, then sort by
  descending score and ascending document ID for exact ties. Return immutable `VectorHit`
  records. Negative scores remain eligible; do not apply an undocumented score threshold.
- Define cosine involving any zero vector as `0.0`. Nonzero finite vectors, including
  very large/small magnitudes, must produce finite scores in `[-1, 1]`. Normalize safely
  before taking the dot product; avoid overflow/underflow from raw squared norms.
- Empty documents or no authorized documents return `()`. A large top-k returns all
  authorized documents. Preserve input data and deterministic results across input ordering.

Access to this exercise's records is already local/trusted; corrupt-index exceptions
are for a caller to handle without exposing private metadata in a public API response.

## Edge cases

An unauthorized best match, exact ties, zero vectors, negative similarity, no roles,
empty index, mismatched dimensions, NaN/infinity, duplicate IDs and extreme magnitudes.

## Run

```powershell
uv run pytest modules/06_rag/03_lexical_dense_retrieval/exercises/vector_search -q
```

Done when all tests pass and a restricted high-scoring document cannot displace an
eligible result from the returned top-k. The untouched starter remains expected-incomplete.
