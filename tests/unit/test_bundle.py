"""Unit tests for ExecutionBundle integrity hashing and tamper detection."""

import pytest
from ai_team.orchestration.bundle import (
    create_execution_bundle,
    compute_bundle_digest,
    verify_bundle_integrity,
    BundleTamperError,
)


def test_bundle_digest_is_deterministic():
    files1 = {"b.py": "print('b')", "a.py": "print('a')"}
    files2 = {"a.py": "print('a')", "b.py": "print('b')"}

    h1 = compute_bundle_digest(
        task="Test task",
        assumptions=["one", "two"],
        acceptance_criteria=["pass"],
        source_files=files1,
        test_files={"test.py": "assert True"},
        declared_commands=["pytest"],
    )

    h2 = compute_bundle_digest(
        task="Test task",
        assumptions=["two", "one"],  # Differently ordered assumptions
        acceptance_criteria=["pass"],
        source_files=files2,  # Differently ordered dictionary keys
        test_files={"test.py": "assert True"},
        declared_commands=["pytest"],
    )

    assert h1 == h2, "Digest must be independent of key insertion order"


def test_bundle_digest_changes_on_modification():
    base_args = dict(
        task="Task A",
        assumptions=["A"],
        acceptance_criteria=["Pass"],
        source_files={"main.py": "x = 1"},
        test_files={"test.py": "assert True"},
        declared_commands=["pytest"],
    )

    h1 = compute_bundle_digest(**base_args)

    # Modifying source code changes hash
    modified_args = dict(base_args)
    modified_args["source_files"] = {"main.py": "x = 2"}
    h2 = compute_bundle_digest(**modified_args)
    assert h1 != h2

    # Modifying commands changes hash
    cmd_args = dict(base_args)
    cmd_args["declared_commands"] = ["pytest -v"]
    h3 = compute_bundle_digest(**cmd_args)
    assert h1 != h3


def test_bundle_tamper_detection():
    bundle = create_execution_bundle(
        task="Task A",
        assumptions=["A"],
        acceptance_criteria=["Pass"],
        source_files={"main.py": "x = 1"},
        test_files={"test.py": "assert True"},
        declared_commands=["pytest"],
        workspace_path="/tmp/workspace",
    )

    # Intact bundle passes
    assert verify_bundle_integrity(bundle) is True

    # Tampered bundle (e.g. source file modified behind orchestrator's back)
    bundle.source_files["main.py"] = "x = 999"
    with pytest.raises(BundleTamperError):
        verify_bundle_integrity(bundle)
