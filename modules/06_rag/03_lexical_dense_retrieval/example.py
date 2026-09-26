"""Lexical corpus mechanics plus explicitly synthetic vector geometry."""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def lexical_scores(query: str) -> tuple[float, ...]:
    corpus = ["Library lends local maps.", "Garden grows herbs.", "Trail map shows a lake."]
    vectorizer = TfidfVectorizer()
    documents = vectorizer.fit_transform(corpus)
    scores = cosine_similarity(vectorizer.transform([query]), documents)[0]
    return tuple(float(score) for score in scores)


def synthetic_geometry() -> float:
    # These chosen coordinates are not a language model's embeddings.
    return float(cosine_similarity(np.array([[1.0, 2.0]]), np.array([[10.0, 20.0]]))[0, 0])


def main() -> None:
    print(
        {
            "library_query": lexical_scores("library maps"),
            "unknown_query": lexical_scores("volcano"),
        }
    )
    print({"synthetic_same_direction": synthetic_geometry()})


if __name__ == "__main__":
    main()
