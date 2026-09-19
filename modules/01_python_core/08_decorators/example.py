"""Time a document parser while retaining useful function metadata."""

from collections.abc import Callable
from functools import wraps


def timed[**P, T](function: Callable[P, T]) -> Callable[P, T]:
    @wraps(function)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
        result = function(*args, **kwargs)
        print(f"timed {function.__name__}")
        return result

    return wrapped


@timed
def parse_document(text: str) -> int:
    return len(text.split())


def main() -> None:
    print(parse_document("terms and conditions"))


if __name__ == "__main__":
    main()
