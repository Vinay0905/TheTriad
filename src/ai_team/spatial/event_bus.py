"""Thread-safe event bus broadcasting office and pipeline events to WebSockets."""

import asyncio
import json
import sqlite3
import threading
from pathlib import Path
from typing import List, Optional, Set

from fastapi import WebSocket

from ai_team.domain.contracts import OfficeEvent
from ai_team.persistence.redaction import redact_secrets

# High-frequency, low-value events. Persisting these opened a SQLite
# connection per frame and gave the audit log nothing useful.
_EPHEMERAL_EVENTS: Set[str] = {
    "OFFICE_CLOCK",
    "OFFICE_SCHEDULE_TICK",
    "AGENT_MOVE",
    "AGENT_STATUS",
    "PROVIDER_HEALTH",
}


class OfficeEventBus:
    """Manages connected clients and persists decision-relevant events."""

    def __init__(self, db_path: Optional[Path] = None):
        self.active_websockets: List[WebSocket] = []
        self.db_path = db_path or Path(".runs/events.db")
        self.main_loop: Optional[asyncio.AbstractEventLoop] = None
        self._db_lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # One long-lived connection instead of one per event. WAL keeps the
            # append from blocking readers.
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS office_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    event_type TEXT,
                    payload JSON
                )
                """
            )
            self._conn.commit()
        except Exception as err:
            print(f"[EventBus] Persistence unavailable, continuing in memory: {err}")
            self._conn = None

    def set_main_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self.main_loop = loop

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_websockets.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_websockets:
            self.active_websockets.remove(websocket)

    def dispatch(self, event: OfficeEvent) -> None:
        """Fire and forget from any thread, including LangGraph worker threads."""
        if self.main_loop and self.main_loop.is_running():
            asyncio.run_coroutine_threadsafe(self.broadcast(event), self.main_loop)
            return

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.broadcast(event))
            else:
                loop.run_until_complete(self.broadcast(event))
        except Exception as err:
            print(f"[EventBus] Dispatch skipped: {err}")

    def _persist(self, event: OfficeEvent, payload_json: str) -> None:
        if self._conn is None or event.event_type in _EPHEMERAL_EVENTS:
            return
        try:
            with self._db_lock:
                self._conn.execute(
                    "INSERT INTO office_events (timestamp, event_type, payload) VALUES (?, ?, ?)",
                    (event.timestamp, event.event_type, payload_json),
                )
                self._conn.commit()
        except Exception as err:
            print(f"[EventBus] Failed to log {event.event_type}: {err}")

    async def broadcast(self, event: OfficeEvent) -> None:
        """Persist where it matters, then fan out to every connected client."""
        # Redaction happens here so no path to a browser or a log can leak a
        # key, regardless of which node produced the event.
        payload_json = redact_secrets(json.dumps(event.model_dump()))

        self._persist(event, payload_json)

        disconnected = []
        for websocket in list(self.active_websockets):
            try:
                await websocket.send_text(payload_json)
            except Exception:
                disconnected.append(websocket)

        for dead in disconnected:
            self.disconnect(dead)


_event_bus: Optional[OfficeEventBus] = None


def get_event_bus() -> OfficeEventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = OfficeEventBus()
    return _event_bus
