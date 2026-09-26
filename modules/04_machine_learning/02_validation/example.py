"""Expanding weather validation windows with a reserved future test period."""

import numpy as np
from sklearn.model_selection import TimeSeriesSplit


def weather_windows() -> tuple[list[tuple[list[int], list[int]]], list[int]]:
    development = np.arange(16)
    final_test = list(range(16, 20))
    splitter = TimeSeriesSplit(n_splits=3, test_size=3, gap=1)
    windows = [(train.tolist(), valid.tolist()) for train, valid in splitter.split(development)]
    return windows, final_test


def main() -> None:
    windows, final_test = weather_windows()
    for train, valid in windows:
        print(f"train days={train}; validation days={valid}")
    print(f"reserved final test days={final_test}")


if __name__ == "__main__":
    main()
