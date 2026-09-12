"""Checkpointer factory for durable LangGraph state persistence.

`SqliteSaver.from_conn_string()` returns a *context manager*, not a saver. The
previous implementation returned it directly and the graph was compiled with
that object, so durable resume never actually worked. Callers must now enter
the context and keep it open for as long as the graph is in use, which is why
this exposes `open_sqlite_checkpointer()` rather than a bare factory.
"""

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional


class CheckpointerUnavailableError(RuntimeError):
    """Raised when durable persistence was required but could not be opened."""


def _memory_saver():
    from langgraph.checkpoint.memory import MemorySaver

    return MemorySaver()


@contextmanager
def open_sqlite_checkpointer(db_path: Optional[Path] = None) -> Iterator[object]:
    """Open a durable SQLite checkpointer for the lifetime of the context.

    The human gate suspends the graph and resumes it from a checkpoint, so
    persistence is the mechanism that makes approval durable across a restart.
    A failure to open it is therefore fatal rather than something to downgrade
    silently.
    """
    path = Path(db_path) if db_path else Path(".runs") / "checkpoints.db"
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
    except ImportError as err:
        raise CheckpointerUnavailableError(
            "langgraph-checkpoint-sqlite is not installed, so runs cannot be "
            "resumed after a restart. Install it, or run the CLI with --mock "
            "to use in-memory checkpoints."
        ) from err

    # `check_same_thread=False` matters because the graph is driven from a
    # worker thread while FastAPI serves the gate response on the event loop.
    with SqliteSaver.from_conn_string(str(path)) as saver:
        yield saver


@contextmanager
def open_memory_checkpointer() -> Iterator[object]:
    """In-memory checkpoints. Resumable within one process only."""
    yield _memory_saver()


@contextmanager
def open_checkpointer(
    db_path: Optional[Path] = None, *, durable: bool = True
) -> Iterator[object]:
    """Open the appropriate checkpointer as a context manager."""
    if durable:
        with open_sqlite_checkpointer(db_path) as saver:
            yield saver
    else:
        with open_memory_checkpointer() as saver:
            yield saver


def get_checkpointer(db_path: Optional[Path] = None):
    """Deprecated. Retained only to fail loudly rather than silently misbehave.

    It is impossible to return a correctly-managed SQLite saver from a plain
    function, so callers must migrate to `open_checkpointer()`.
    """
    raise CheckpointerUnavailableError(
        "get_checkpointer() is unsafe: SqliteSaver.from_conn_string() is a "
        "context manager and must stay open for the life of the graph. Use "
        "open_checkpointer(db_path, durable=...) instead."
    )
