"""Use built-in collection idioms for document-language metadata."""


def language_summary() -> tuple[list[str], dict[str, int]]:
    languages = ["en", "fr", "en", "de"]
    unique = sorted(set(languages))
    counts = {language: languages.count(language) for language in unique}
    return unique, counts


def main() -> None:
    unique, counts = language_summary()
    print(f"languages={unique}; counts={counts}")


if __name__ == "__main__":
    main()
