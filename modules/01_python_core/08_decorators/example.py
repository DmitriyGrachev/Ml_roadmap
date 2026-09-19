"""Time a document parser while retaining useful function metadata."""

from collections.abc import Callable
from functools import wraps
from time import perf_counter

type Clock = Callable[[], float]
type Reporter = Callable[[str], None]


def timed[**P, T](
    *, clock: Clock = perf_counter, reporter: Reporter = print
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorate(function: Callable[P, T]) -> Callable[P, T]:
        @wraps(function)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
            started_at = clock()
            result = function(*args, **kwargs)
            elapsed = clock() - started_at
            reporter(f"{function.__name__} took {elapsed:.3f}s")
            return result

        return wrapped

    return decorate


@timed()
def parse_document(text: str) -> int:
    return len(text.split())


def main() -> None:
    print(parse_document("terms and conditions"))


if __name__ == "__main__":
    main()
