"""Trace names, shared lists, rebinding, copying, and missing versus empty values."""


def compare_ticket_tags() -> tuple[bool, bool]:
    first = ["billing", "urgent"]
    second = ["billing", "urgent"]
    return first is second, first == second


def main() -> None:
    same_object, same_value = compare_ticket_tags()
    print(f"same object={same_object}; same value={same_value}")

    # Steps 1-4 match the four diagrams in theory.md; L1/L2/L3 are diagram labels.
    labels = ["draft"]
    alias = labels
    print("1:", labels, alias, labels is alias)

    alias.append("review")
    print("2:", labels, alias, labels is alias)

    alias = ["archived"]
    print("3:", labels, alias, labels is alias)

    copied = labels.copy()
    print("4:", copied, copied is labels, copied == labels)

    copied.append("done")
    print("5:", labels, copied)

    missing = None
    empty: list[str] = []
    present = ["draft"]
    text = "False"
    print("missing:", missing is None, bool(missing))
    print("empty:", empty is None, bool(empty))
    print("present:", present is None, bool(present))
    print("text:", text is None, bool(text))


if __name__ == "__main__":
    main()
