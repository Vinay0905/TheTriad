"""Run persistence, audit trail management, and atomic artifact storage."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel
from ai_team.persistence.redaction import sanitize_dict


class RunPersistence:
    """Manages atomic disk persistence and audit logs under .runs/<run_id>/."""

    def __init__(self, runs_dir: Path, run_id: str):
        self.run_dir = (runs_dir / run_id).resolve()
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.events_file = self.run_dir / "events.jsonl"

    def log_event(self, from_state: str, to_state: str, payload: Optional[Dict[str, Any]] = None) -> None:
        """Append an immutable state transition event."""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from_state": from_state,
            "to_state": to_state,
            "payload": sanitize_dict(payload or {}),
        }
        with open(self.events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    def save_artifact(self, filename: str, data: Any) -> Path:
        """Atomically write an artifact JSON or markdown file."""
        target_path = self.run_dir / filename
        temp_path = self.run_dir / f"{filename}.tmp"

        if isinstance(data, BaseModel):
            content = data.model_dump_json(indent=2)
        elif isinstance(data, (dict, list)):
            content = json.dumps(sanitize_dict(data), indent=2)
        else:
            content = str(data)

        temp_path.write_text(content, encoding="utf-8")
        temp_path.replace(target_path)
        return target_path
