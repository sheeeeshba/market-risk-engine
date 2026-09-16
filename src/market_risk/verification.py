"""Evidence manifest helpers for reproducibility gates."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path


def workspace_tree_hash(root: str | Path) -> str:
    """Hash source, tests, configuration, templates, and documentation."""

    root = Path(root)
    ignored_parts = {
        ".git",
        ".mplconfig",
        ".mypy_cache",
        ".venv",
        ".uv-cache",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        "build",
        "dist",
    }
    ignored_roots = {root / "outputs", root / "reports" / "generated"}
    digest = hashlib.sha256()
    files = []
    for path in root.rglob("*"):
        if (
            not path.is_file()
            or ignored_parts.intersection(path.parts)
            or any(part.endswith(".egg-info") for part in path.parts)
        ):
            continue
        if any(path == ignored or ignored in path.parents for ignored in ignored_roots):
            continue
        files.append(path)
    for path in sorted(files):
        digest.update(str(path.relative_to(root)).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _git_commit(root: Path) -> str | None:
    """Return the current commit when the project is inside a Git worktree."""

    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def _portable_paths(paths: Iterable[str], root: Path) -> list[str]:
    portable: list[str] = []
    for value in paths:
        path = Path(value)
        if path.is_absolute():
            try:
                portable.append(str(path.relative_to(root)))
                continue
            except ValueError:
                pass
        portable.append(str(path))
    return portable


def record_gate(
    manifest_path: str | Path,
    gate: str,
    command: str,
    exit_status: int,
    project_root: str | Path,
    configuration_hash: str,
    input_snapshot_id: str,
    verified_output_paths: Iterable[str],
) -> None:
    """Append or replace one gate record in the verification manifest."""

    target = Path(manifest_path)
    if target.exists():
        manifest = json.loads(target.read_text(encoding="utf-8"))
    else:
        manifest = {"schema_version": 1, "gates": {}}
    manifest["gates"][gate] = {
        "command": command,
        "utc_timestamp": datetime.now(timezone.utc).isoformat(),
        "exit_status": int(exit_status),
        "git_commit": _git_commit(Path(project_root)),
        "workspace_tree_hash": workspace_tree_hash(project_root),
        "configuration_hash": configuration_hash,
        "input_snapshot_id": input_snapshot_id,
        "verified_output_paths": _portable_paths(verified_output_paths, Path(project_root)),
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
