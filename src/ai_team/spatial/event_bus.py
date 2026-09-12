"""Asynchronous Event Bus broadcasting spatial and state events to connected WebSockets."""

import json
import sqlite3
import time
from pathlib import Path
from typing import List, Optional
from fastapi import WebSocket
from ai_team.domain.contracts import OfficeEvent


class OfficeEventBus:
    """Manages connected 3D clients and persists events to an append-only SQLite log."""

    def __init__(self, db_path: Optional[Path] = None):
        self.active_websockets: List[WebSocket] = []
        self.db_path = db_path or Path(".runs/events.db")
        self._init_db()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS office_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    event_type TEXT,
                    payload JSON
                )
                """
            )

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_websockets.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_websockets:
            self.active_websockets.remove(websocket)

    async def broadcast(self, event: OfficeEvent):
        """Persist to SQLite and broadcast JSON to all connected browser clients."""
        payload_dict = event.model_dump()
        payload_json = json.dumps(payload_dict)

        # 1. Append-only persistence
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO office_events (timestamp, event_type, payload) VALUES (?, ?, ?)",
                    (event.timestamp, event.event_type, payload_json),
                )
        except Exception as e:
            print(f"[EventBus Error] Failed to log event to SQLite: {e}")

        # 2. WebSocket fan-out
        disconnected = []
        for ws in self.active_websockets:
            try:
                await ws.send_text(payload_json)
            except Exception:
                disconnected.append(ws)

        for dead_ws in disconnected:
            self.disconnect(dead_ws)


# Global singleton event bus
_event_bus: Optional[OfficeEventBus] = None


def get_event_bus() -> OfficeEventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = OfficeEventBus()
    return _event_bus
