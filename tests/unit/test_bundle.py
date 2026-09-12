"""ExecutionBundle integrity hashing and tamper detection.

Targets `ai_team.execution.bundle`, which is the single digest implementation
used by both preflight and the sandbox. There were previously two that hashed
different payloads, so the digest shown at the gate was not the one any test
verified.
"""

import pytest

from ai_team.execution.bundle import (
    BundleTamperError,
    build_bundle,
    bundle_file_list,
    compute_bundle_digest,
    digest_for_bundle,
    verify_bundle_integrity,
)

BASE = dict(
    task="Convert CSV to JSON",
    source_files={"main.py": "x = 1"},
    test_files={"test_main.py": "assert True"},
    declared_commands=["python3 -m unittest test_main.py"],
)


def test_digest_is_independent_of_key_order():
    first = compute_bundle_digest(
        task="Task",
        source_files={"b.py": "b", "a.py": "a"},
        test_files={"test_main.py": "t"},
        declared_commands=["python3 -m unittest test_main.py"],
    )
    second = compute_bundle_digest(
        task="Task",
        source_files={"a.py": "a", "b.py": "b"},
        test_files={"test_main.py": "t"},
        declared_commands=["python3 -m unittest test_main.py"],
    )
    assert first == second


def test_digest_ignores_surrounding_task_whitespace():
    assert compute_bundle_digest(**{**BASE, "task": "  Convert CSV to JSON  "}) == (
        compute_bundle_digest(**BASE)
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("task", "A different task"),
        ("source_files", {"main.py": "x = 2"}),
        ("source_files", {"main.py": "x = 1", "extra.py": ""}),
        ("test_files", {"test_main.py": "assert False"}),
        ("declared_commands", ["python3 -m pytest test_main.py"]),
        ("declared_commands", []),
    ],
)
def test_any_execution_relevant_change_changes_the_digest(field, value):
    assert compute_bundle_digest(**{**BASE, field: value}) != compute_bundle_digest(**BASE)


def test_command_order_is_significant():
    ordered = compute_bundle_digest(
        **{
            **BASE,
            "declared_commands": [
                "python3 -m unittest test_main.py",
                "python3 -m pytest test_main.py",
            ],
        }
    )
    reversed_order = compute_bundle_digest(
        **{
            **BASE,
            "declared_commands": [
                "python3 -m pytest test_main.py",
                "python3 -m unittest test_main.py",
            ],
        }
    )
    assert ordered != reversed_order


def test_build_bundle_attaches_a_verifiable_digest():
    bundle = build_bundle(
        **BASE, workspace_path="/tmp/ws", thread_id="thread_abc", qa_status="PASS"
    )
    assert bundle["bundle_digest"] == digest_for_bundle(bundle)
    assert verify_bundle_integrity(bundle) == bundle["bundle_digest"]
    assert bundle["thread_id"] == "thread_abc"
    assert bundle["qa_status"] == "PASS"


def test_commentary_does_not_affect_the_digest():
    """Editing prose must not invalidate an otherwise identical payload."""
    first = build_bundle(
        **BASE,
        workspace_path="/tmp/ws",
        thread_id="t",
        assumptions=["one"],
        acceptance_criteria=["a"],
    )
    second = build_bundle(
        **BASE,
        workspace_path="/tmp/ws",
        thread_id="t",
        assumptions=["completely different"],
        acceptance_criteria=["b"],
    )
    assert first["bundle_digest"] == second["bundle_digest"]


def test_tampering_with_source_after_approval_is_detected():
    bundle = build_bundle(**BASE, workspace_path="/tmp/ws", thread_id="t")

    # Simulates the payload changing between approval and execution.
    bundle["source_files"]["main.py"] = "import os; os.system('sh')"

    with pytest.raises(BundleTamperError):
        verify_bundle_integrity(bundle)


def test_tampering_with_commands_after_approval_is_detected():
    bundle = build_bundle(**BASE, workspace_path="/tmp/ws", thread_id="t")
    bundle["declared_commands"] = ["python3 -m unittest test_main.py; rm -rf /"]

    with pytest.raises(BundleTamperError):
        verify_bundle_integrity(bundle)


def test_a_bundle_without_a_digest_cannot_be_verified():
    with pytest.raises(BundleTamperError):
        verify_bundle_integrity({"task": "t", "source_files": {}, "test_files": {}})


def test_file_list_is_sorted_and_complete():
    bundle = build_bundle(
        task="t",
        source_files={"main.py": "", "helper.py": ""},
        test_files={"test_main.py": ""},
        declared_commands=[],
        workspace_path="/tmp/ws",
        thread_id="t",
    )
    assert bundle_file_list(bundle) == ["helper.py", "main.py", "test_main.py"]
