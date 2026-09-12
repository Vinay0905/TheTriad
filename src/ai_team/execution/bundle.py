"""Canonical ExecutionBundle hashing, used by both preflight and the sandbox.

There used to be two different digest implementations that hashed different
payloads, so the value shown to the operator at the gate was not the value any
test verified. This module is now the single source of truth: preflight
computes the digest, and the sandbox recomputes it and refuses to write
anything on a mismatch.

The digest covers exactly the inputs that determine what lands on disk and
what runs. Commentary like assumptions and acceptance criteria is excluded on
purpose, so editing prose cannot invalidate an otherwise identical payload.
"""

import hashlib
import json
from typing import Any, Dict, List, Mapping, Sequence


class BundleTamperError(Exception):
    """Raised when a bundle's contents do not match its recorded digest."""


def compute_bundle_digest(
    task: str,
    source_files: Mapping[str, str],
    test_files: Mapping[str, str],
    declared_commands: Sequence[str],
) -> str:
    """Deterministic SHA-256 over the execution-relevant payload."""
    canonical: Dict[str, Any] = {
        "task": (task or "").strip(),
        "source_files": {key: source_files[key] for key in sorted(source_files)},
        "test_files": {key: test_files[key] for key in sorted(test_files)},
        "declared_commands": list(declared_commands),
    }
    serialized = json.dumps(canonical, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def digest_for_bundle(bundle: Mapping[str, Any]) -> str:
    """Recompute the digest of an existing bundle mapping."""
    return compute_bundle_digest(
        task=bundle.get("task", ""),
        source_files=bundle.get("source_files") or {},
        test_files=bundle.get("test_files") or {},
        declared_commands=bundle.get("declared_commands") or [],
    )


def verify_bundle_integrity(bundle: Mapping[str, Any]) -> str:
    """Confirm a bundle still hashes to its recorded digest.

    Raises `BundleTamperError` on mismatch. Callers must treat that as a hard
    stop: the operator approved a specific payload, and this is no longer it.
    """
    recorded = bundle.get("bundle_digest")
    if not recorded:
        raise BundleTamperError("Bundle has no recorded digest to verify against.")

    actual = digest_for_bundle(bundle)
    if actual != recorded:
        raise BundleTamperError(
            "Bundle integrity check failed: the approved payload has changed. "
            f"Approved digest {recorded[:12]}..., current {actual[:12]}...."
        )
    return actual


def build_bundle(
    task: str,
    source_files: Mapping[str, str],
    test_files: Mapping[str, str],
    declared_commands: Sequence[str],
    workspace_path: str,
    thread_id: str,
    **extra: Any,
) -> Dict[str, Any]:
    """Assemble a bundle with its digest already attached."""
    bundle: Dict[str, Any] = {
        "task": task,
        "thread_id": thread_id,
        "source_files": dict(source_files),
        "test_files": dict(test_files),
        "declared_commands": list(declared_commands),
        "workspace_path": workspace_path,
    }
    bundle.update(extra)
    bundle["bundle_digest"] = compute_bundle_digest(
        task=task,
        source_files=source_files,
        test_files=test_files,
        declared_commands=declared_commands,
    )
    return bundle


def bundle_file_list(bundle: Mapping[str, Any]) -> List[str]:
    return sorted(
        list((bundle.get("source_files") or {}).keys())
        + list((bundle.get("test_files") or {}).keys())
    )
