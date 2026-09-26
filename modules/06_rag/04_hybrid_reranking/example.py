"""Illustrative reranking changes order only within the supplied shortlist."""

from collections.abc import Mapping, Sequence


def rerank_shortlist(
    shortlist: Sequence[str], illustrative_scores: Mapping[str, float]
) -> tuple[str, ...]:
    return tuple(sorted(shortlist, key=lambda doc: (-illustrative_scores[doc], doc)))


def main() -> None:
    shortlist = ("garden-guide", "library-map", "trail-map")
    scores = {"garden-guide": 0.1, "library-map": 0.8, "trail-map": 0.6, "unretrieved": 0.99}
    print(rerank_shortlist(shortlist, scores))
    print("Fixed teaching scores; no trained reranker is used.")


if __name__ == "__main__":
    main()
