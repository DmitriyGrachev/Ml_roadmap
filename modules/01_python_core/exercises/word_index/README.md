# Build a word index

Difficulty: Beginner · Estimated time: 25–40 minutes

## Prerequisites

Module 01 lessons 02 (collections), 03 (functions), and 09 (pytest).
Practice dictionaries, sets, deterministic sorting, and input validation.

## Requirements

Implement `build_word_index(documents)` in `starter.py`.

- Accept a mapping from document IDs to text. IDs must be nonempty strings with
  no leading/trailing whitespace; text must be a string. Raise `ValueError` for
  invalid entries, even if other entries are valid; the message includes `document`.
- Define a word as a maximal run of ASCII letters `A-Z` or `a-z`. Lowercase words;
  punctuation, digits, underscores, and non-ASCII characters are separators.
- Return a new dictionary whose keys appear in alphabetical order. Each value is
  a tuple of unique document IDs in lexicographic order. A word repeated within
  one document contributes that ID once.
- Empty mappings and documents without words are valid. Do not change the input;
  repeated calls must return independent, equal results.

## Example

```python
build_word_index({"z": "Rain, SUN!", "a": "sun rain-cloud"})
# {"cloud": ("a",), "rain": ("a", "z"), "sun": ("a", "z")}
```

## Edge cases and optional hints

Try repeated words, an empty document, and `room42_blue`. This is a deliberately
ASCII tokenizer, not a natural-language search engine. A regular expression can
find words; sets can represent document membership before the final sort.

## Run and done when

From the repository root:

```powershell
uv run pytest modules/01_python_core/exercises/word_index -q -rx
```

Edit only `starter.py`. Done when all tests pass with zero xfails and you can
explain why counting occurrences would produce the wrong index.
