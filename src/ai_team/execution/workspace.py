"""Isolated run workspace management with strict path confinement."""

from pathlib import Path
from typing import Dict, List


class PathConfinementError(Exception):
    """Raised when a file operation attempts to escape the isolated workspace."""


def create_run_workspace(runs_dir: Path, run_id: str) -> Path:
    """Create and return a dedicated, isolated workspace directory for a run."""
    workspace = (runs_dir / run_id / "workspace").resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def validate_path_confinement(workspace: Path, relative_or_absolute_path: str) -> Path:
    """
    Ensure the target path resolves strictly inside the designated workspace.
    Guards against directory traversal (e.g. '../') and symlink escapes.
    """
    workspace_resolved = workspace.resolve()
    target = (workspace_resolved / relative_or_absolute_path).resolve()

    try:
        target.relative_to(workspace_resolved)
    except ValueError:
        raise PathConfinementError(
            f"Access denied: '{relative_or_absolute_path}' escapes workspace '{workspace_resolved}'"
        )

    return target


def write_bundle_files(
    workspace: Path, source_files: Dict[str, str], test_files: Dict[str, str]
) -> List[str]:
    """
    Write all source and test files to the workspace with path confinement validation.
    Returns the list of relative file paths created.
    """
    created_paths = []
    all_files = {**source_files, **test_files}

    for rel_path_str, content in all_files.items():
        safe_path = validate_path_confinement(workspace, rel_path_str)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(content, encoding="utf-8")
        created_paths.append(rel_path_str)

    return created_paths
