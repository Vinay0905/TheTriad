"""ExecutionBundle construction, canonical hashing, and tamper detection."""

import hashlib
import json
from typing import Dict, List
from ai_team.domain.contracts import ExecutionBundle


class BundleTamperError(Exception):
    """Raised when an ExecutionBundle's contents do not match its computed digest."""


def compute_bundle_digest(
    task: str,
    assumptions: List[str],
    acceptance_criteria: List[str],
    source_files: Dict[str, str],
    test_files: Dict[str, str],
    declared_commands: List[str],
) -> str:
    """
    Compute a deterministic SHA-256 integrity digest for an execution bundle.
    Sorts dictionary keys and lists to ensure identical content produces identical hashes.
    """
    canonical_payload = {
        "task": task.strip(),
        "assumptions": sorted(assumptions),
        "acceptance_criteria": sorted(acceptance_criteria),
        "source_files": {k: source_files[k] for k in sorted(source_files.keys())},
        "test_files": {k: test_files[k] for k in sorted(test_files.keys())},
        "declared_commands": declared_commands,
    }

    serialized = json.dumps(canonical_payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def create_execution_bundle(
    task: str,
    assumptions: List[str],
    acceptance_criteria: List[str],
    source_files: Dict[str, str],
    test_files: Dict[str, str],
    declared_commands: List[str],
    workspace_path: str,
) -> ExecutionBundle:
    """Construct an ExecutionBundle with its computed canonical integrity digest."""
    digest = compute_bundle_digest(
        task=task,
        assumptions=assumptions,
        acceptance_criteria=acceptance_criteria,
        source_files=source_files,
        test_files=test_files,
        declared_commands=declared_commands,
    )

    return ExecutionBundle(
        task=task,
        assumptions=assumptions,
        acceptance_criteria=acceptance_criteria,
        source_files=source_files,
        test_files=test_files,
        declared_commands=declared_commands,
        workspace_path=workspace_path,
        bundle_digest=digest,
    )


def verify_bundle_integrity(bundle: ExecutionBundle) -> bool:
    """
    Verify that an ExecutionBundle has not drifted or been modified since hashing.
    Raises BundleTamperError if verification fails.
    """
    expected_digest = compute_bundle_digest(
        task=bundle.task,
        assumptions=bundle.assumptions,
        acceptance_criteria=bundle.acceptance_criteria,
        source_files=bundle.source_files,
        test_files=bundle.test_files,
        declared_commands=bundle.declared_commands,
    )

    if expected_digest != bundle.bundle_digest:
        raise BundleTamperError(
            f"Bundle integrity check failed! Expected {expected_digest}, found {bundle.bundle_digest}"
        )

    return True
