"""Completed teacher examples; the independent label-counting TODO lives elsewhere."""


def label_action(raw: str) -> str:
    label = raw.strip()
    if label == "":
        return "skip"
    elif len(label) > 6:
        return "review:long"
    else:
        return "keep:" + label.upper()


def trace_labels(labels: list[str]) -> list[tuple[str, str]]:
    trace = []
    for raw in labels:
        trace.append((raw, label_action(raw)))
    return trace


def countdown(start: int) -> list[int]:
    if type(start) is not int or start < 0:
        raise ValueError("start must be a nonnegative integer")
    remaining = start
    visited = []
    while remaining > 0:
        visited.append(remaining)
        remaining = remaining - 1
    return visited


def main() -> None:
    print("2 + 3 * 4 =", 2 + 3 * 4)
    print("range(1, 4) =", list(range(1, 4)))
    for raw, result in trace_labels([" oak ", "", "sequoia"]):
        print(f"{raw!r} -> {result}")
    print("countdown(3) =", countdown(3))
    action = label_action("pine")
    print("return is a value:", action)


if __name__ == "__main__":
    main()
