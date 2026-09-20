"""Student boundary for a typed, parameterized retry decorator."""

from collections.abc import Callable
from functools import wraps


def retry[**P, R](
    *,
    attempts: int,
    retry_on: tuple[type[BaseException], ...],
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Retry a decorated operation for selected exception types only.

    Raise:
        ValueError: If ``attempts`` is not positive.
    """
    if attempts <= 0:
        raise ValueError("attempts must be positive")

    def decorate(operation: Callable[P, R]) -> Callable[P, R]:
        @wraps(operation)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            raise NotImplementedError("retry selected gateway failures")

        return wrapped

    return decorate
