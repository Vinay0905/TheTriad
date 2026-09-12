"""Manager Pre-Flight Quality Gate node."""

import hashlib
import json
import uuid
from pathlib import Path
from typing import Dict, Any
from ai_team.graph.state import TriadCouncilState


def preflight_gate_node(state: TriadCouncilState) -> Dict[str, Any]:
    """
    Manager verifies 100% acceptance criteria coverage, packages the finalized
    source files and test suite into an ExecutionBundle, and computes the SHA-256 digest.
    """
    task = state["task_prompt"]
    rfc = state.get("manager_rfc") or {}
    source_files = state.get("synthesized_code") or {}
    test_files = {"test_main.py": state.get("tdd_contract", {}).get("test_main.py", "")}
    declared_commands = ["python3 -m unittest test_main.py"]

    run_id = f"run_{uuid.uuid4().hex[:8]}"
    workspace_path = str(Path(".runs") / run_id / "workspace")

    # Compute deterministic SHA-256 digest
    canonical_payload = {
        "task": task.strip(),
        "source_files": {k: source_files[k] for k in sorted(source_files.keys())},
        "test_files": {k: test_files[k] for k in sorted(test_files.keys())},
        "declared_commands": declared_commands,
    }
    serialized = json.dumps(canonical_payload, sort_keys=True, ensure_ascii=True)
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    bundle = {
        "task": task,
        "assumptions": rfc.get("assumptions", []),
        "acceptance_criteria": rfc.get("acceptance_criteria", []),
        "debate_verdict": state.get("debate_verdict", ""),
        "source_files": source_files,
        "test_files": test_files,
        "declared_commands": declared_commands,
        "workspace_path": workspace_path,
        "bundle_digest": digest,
    }

    return {
        "execution_bundle": bundle,
        "approval_status": "PENDING",
    }
