"""Print a few stable facts useful when checking a Python environment."""

import sys


def environment_facts() -> dict[str, str]:
    return {"implementation": sys.implementation.name, "major_version": str(sys.version_info.major)}


def main() -> None:
    facts = environment_facts()
    print(f"{facts['implementation']} {facts['major_version']}")


if __name__ == "__main__":
    main()
