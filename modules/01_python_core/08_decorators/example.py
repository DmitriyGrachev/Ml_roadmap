"""Log a function boundary while retaining useful callable metadata."""

import logging
import sys
from collections.abc import Callable
from functools import wraps


def log_calls[**P, T](*, logger: logging.Logger) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorate(function: Callable[P, T]) -> Callable[P, T]:
        @wraps(function)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
            logger.info("starting %s", function.__name__)
            try:
                return function(*args, **kwargs)
            finally:
                logger.info("finished %s", function.__name__)

        return wrapped

    return decorate


lesson_logger = logging.getLogger("python_core.decorators")


@log_calls(logger=lesson_logger)
def normalize_labels(labels: list[str]) -> str:
    return ", ".join(label.strip().lower() for label in labels)


def main() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    previous_level = lesson_logger.level
    previous_propagate = lesson_logger.propagate
    lesson_logger.addHandler(handler)
    lesson_logger.setLevel(logging.INFO)
    lesson_logger.propagate = False
    try:
        print(normalize_labels([" Billing ", "URGENT"]))
    finally:
        lesson_logger.removeHandler(handler)
        lesson_logger.setLevel(previous_level)
        lesson_logger.propagate = previous_propagate


if __name__ == "__main__":
    main()
