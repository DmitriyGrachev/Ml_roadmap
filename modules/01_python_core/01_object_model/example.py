"""Show that object identity and value equality answer different questions."""


def compare_ticket_tags() -> tuple[bool, bool]:
    first = ["billing", "urgent"]
    second = ["billing", "urgent"]
    return first is second, first == second


def main() -> None:
    same_object, same_value = compare_ticket_tags()
    print(f"same object={same_object}; same value={same_value}")


if __name__ == "__main__":
    main()
