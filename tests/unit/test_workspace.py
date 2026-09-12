"""Unit tests for workspace management and path confinement."""

import pytest
from pathlib import Path
from ai_team.execution.workspace import (
    create_run_workspace,
    validate_path_confinement,
    write_bundle_files,
    PathConfinementError,
)


def test_create_run_workspace(tmp_path: Path):
    ws = create_run_workspace(tmp_path, "run_123")
    assert ws.exists()
    assert ws.name == "workspace"
    assert ws.parent.name == "run_123"


def test_path_confinement_allowed(tmp_path: Path):
    ws = create_run_workspace(tmp_path, "run_123")
    safe = validate_path_confinement(ws, "src/nested/app.py")
    assert str(safe).startswith(str(ws))


def test_path_confinement_prevents_escape(tmp_path: Path):
    ws = create_run_workspace(tmp_path, "run_123")
    with pytest.raises(PathConfinementError):
        validate_path_confinement(ws, "../../outside.py")


def test_write_bundle_files(tmp_path: Path):
    ws = create_run_workspace(tmp_path, "run_123")
    source = {"main.py": "print('hello')", "pkg/mod.py": "x = 10"}
    tests = {"test_main.py": "assert True"}

    created = write_bundle_files(ws, source, tests)
    assert len(created) == 3
    assert (ws / "main.py").read_text() == "print('hello')"
    assert (ws / "pkg" / "mod.py").read_text() == "x = 10"
    assert (ws / "test_main.py").read_text() == "assert True"
