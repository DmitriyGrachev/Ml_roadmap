"""Student boundary for a one-shot, pull-driven batching iterator."""

from collections.abc import Iterable, Iterator


def iter_pages[T](source: Iterable[T], size: int) -> Iterator[tuple[T, ...]]:
    """Yield nonempty tuples of at most size items without reading ahead."""
    # TODO: validate size and batch the source lazily, retaining a partial last page.
    raise NotImplementedError("batch a one-shot stream")
