"""Explicit CPU commands; no server, training or downloads on import."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..artifacts import file_sha256, json_bytes
from .app import create_app_from_config


def prepare_teacher(output: Path) -> Path:
    from ..part_a1.demo import run_demo

    run_demo(output)
    config = output / "service.json"
    config.write_bytes(
        json_bytes(
            {
                "bundle_root": str((output / "rules").resolve()),
                "expected_manifest_sha256": file_sha256(output / "rules" / "manifest.json"),
            }
        )
    )
    container = output / "container-service.json"
    container.write_bytes(
        json_bytes(
            {
                "bundle_root": "/bundle",
                "expected_manifest_sha256": file_sha256(output / "rules" / "manifest.json"),
            }
        )
    )
    return config


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare-teacher")
    prepare.add_argument("--output", required=True, type=Path)
    serve = commands.add_parser("serve")
    serve.add_argument("--config", required=True, type=Path)
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--trusted-local-artifact", action="store_true")
    args = parser.parse_args()
    if args.command == "prepare-teacher":
        print(prepare_teacher(args.output))
    else:
        import uvicorn

        app = create_app_from_config(
            args.config, trusted_local_artifact=args.trusted_local_artifact
        )
        uvicorn.run(app, host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
