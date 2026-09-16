"""Command-line interface for reproducible local and Colab runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import project_root
from .engine import create_synthetic_snapshot, run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Multi-Asset Market Risk Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Run the end-to-end risk pipeline.")
    run.add_argument("--config", default="config/model_config.yaml")
    run.add_argument("--data-mode", choices=["snapshot", "synthetic_demo", "live"], default=None)

    snapshot = subparsers.add_parser(
        "make-synthetic-snapshot", help="Create the watermarked artificial engineering snapshot."
    )
    snapshot.add_argument("--periods", type=int, default=520)
    snapshot.add_argument("--seed", type=int, default=42)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = project_root()
    if args.command == "make-synthetic-snapshot":
        result = create_synthetic_snapshot(root, args.periods, args.seed)
    else:
        config = Path(args.config)
        if not config.is_absolute():
            config = Path.cwd() / config
        result = run_pipeline(config, args.data_mode)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

