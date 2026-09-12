"""Checkpointer factory for durable LangGraph state persistence."""

from pathlib import Path
from typing import Optional


def get_checkpointer(db_path: Optional[Path] = None):
    """
    Instantiate a LangGraph checkpointer.
    Prefers durable SqliteSaver; falls back to in-memory MemorySaver if sqlite module unavailable.
    """
    if db_path is None:
        db_path = Path(".runs") / "checkpoints.db"

    db_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
        return SqliteSaver.from_conn_string(str(db_path))
    except (ImportError, Exception):
        try:
            from langgraph.checkpoint.memory import MemorySaver
            return MemorySaver()
        except ImportError:
            return None
