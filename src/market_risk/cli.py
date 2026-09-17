"""Command-line interface for reproducible local and Colab runs."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
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

    app = subparsers.add_parser("app", help="Launch the interactive Streamlit dashboard.")
    app.add_argument("--port", type=int, default=8501)
    app.add_argument("--address", default="localhost")
    app.add_argument("--no-browser", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = project_root()
    if args.command == "app":
        app_path = Path.cwd() / "streamlit_app.py"
        if not app_path.is_file():
            app_path = root / "streamlit_app.py"
        command = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(app_path),
            "--server.address",
            args.address,
            "--server.port",
            str(args.port),
        ]
        if args.no_browser:
            command.extend(["--server.headless", "true"])
        return subprocess.call(command)
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
