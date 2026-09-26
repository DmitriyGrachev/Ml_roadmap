"""A small provenance manifest without model serialization or loading."""

import hashlib
import json
import platform

import numpy as np
import sklearn


def sensor_manifest() -> dict[str, str | int]:
    source = b"sensor,temperature\nA,18.0\nB,21.0\n"
    return {
        "data_sha256": hashlib.sha256(source).hexdigest(),
        "data_source": "literal sensor fixture v1",
        "split": "predeclared sensors A=train, B=validation; demonstration only",
        "seed": 31,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scikit_learn": sklearn.__version__,
    }


def main() -> None:
    print(json.dumps(sensor_manifest(), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
