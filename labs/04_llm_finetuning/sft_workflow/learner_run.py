"""Manual learner project entrypoint; no implicit downloads or training on import."""

import argparse
from pathlib import Path
from typing import Any


def run_project(base: Path, tokenizer: Path, data: Path, output: Path, max_steps: int) -> Any:
    """Write your independent runner using starter boundaries and the evidence schema.

    Load only explicitly supplied local snapshots with local_files_only=True and
    trust_remote_code=False. Compare base/improved_prompt/LoRA on one heldout set,
    save actual predictions, adapter, dataset, splits, runner source and hashes.
    Return an evidence manifest; fail on errors rather than writing success.
    """
    raise NotImplementedError("Implement independent pretrained SFT experiment and evidence")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base", "tokenizer", "data", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--max-steps", type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.max_steps <= 100:
        parser.error("--max-steps must be 1..100 for this bounded learner project")
    if not args.base.is_dir() or not args.tokenizer.is_dir() or not args.data.is_file():
        parser.error("base/tokenizer/data must exist locally; download separately")
    if args.output.exists():
        parser.error("--output must name a NEW directory")
    run_project(
        args.base.resolve(),
        args.tokenizer.resolve(),
        args.data.resolve(),
        args.output,
        args.max_steps,
    )


if __name__ == "__main__":
    main()
