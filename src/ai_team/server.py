"""FastAPI ASGI Server with WebSocket Event Hub and LangGraph Task Execution."""

import asyncio
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langgraph.types import Command
from ai_team.config import get_config
from ai_team.domain.contracts import (
    AgentMoveEvent,
    AgentStatusEvent,
    WhiteboardGateEvent,
    TerminalLogEvent,
    ProjectCompletedEvent,
)
from ai_team.graph.builder import build_triad_graph
from ai_team.persistence.checkpointer import get_checkpointer
from ai_team.spatial.event_bus import get_event_bus

app = FastAPI(title="TriadCouncil 3D: Virtual AI Office Server")

# Allow Vite dev server CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active execution session state
ACTIVE_RUNS: Dict[str, Dict[str, Any]] = {}
event_bus = get_event_bus()
config = get_config()
checkpointer = get_checkpointer(config.runs_dir / "checkpoints.db")
triad_app = build_triad_graph(checkpointer=checkpointer)


class StartTaskRequest(BaseModel):
    task: str


class GateResponseRequest(BaseModel):
    thread_id: str
    action: str  # "approve", "abort", "steer"
    guidance: Optional[str] = None


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "TriadCouncil 3D Virtual Office"}


@app.websocket("/ws/office")
async def office_websocket(websocket: WebSocket):
    await event_bus.connect(websocket)
    try:
        # Initial greeting and status
        await websocket.send_json({
            "event_type": "AGENT_STATUS",
            "agent_id": "manager",
            "status_text": "Standing by for user objective...",
            "animation": "Sit",
            "timestamp": asyncio.get_event_loop().time(),
        })
        while True:
            # Client heartbeat
            await websocket.receive_text()
    except WebSocketDisconnect:
        event_bus.disconnect(websocket)


def run_pipeline_thread(thread_id: str, task: str):
    """Executes the LangGraph workflow up to the interrupt gate."""
    graph_config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 50,
    }
    initial_input = {"task_prompt": task}

    try:
        # 1. Stream events up to the interrupt
        for event in triad_app.stream(initial_input, graph_config):
            for node_name in event.keys():
                print(f"  [LangGraph Server] Node finished: {node_name}")
    except Exception as e:
        print(f"  [LangGraph Server Error] {e}")


@app.post("/api/tasks/start")
async def start_task(request: StartTaskRequest, background_tasks: BackgroundTasks):
    task = request.task.strip()
    if not task:
        raise HTTPException(status_code=400, detail="Task cannot be empty.")

    thread_id = f"thread_{uuid.uuid4().hex[:8]}"
    ACTIVE_RUNS[thread_id] = {
        "task": task,
        "status": "RUNNING",
    }

    # Broadcast initial movement & status
    await event_bus.broadcast(
        AgentStatusEvent(
            agent_id="manager",
            status_text="Decomposing objective into architecture RFC...",
            animation="Sit",
        )
    )
    await event_bus.broadcast(
        AgentMoveEvent(
            agent_id="manager",
            from_node="desk_manager",
            to_node="whiteboard",
            action="Walk",
        )
    )

    # Launch graph in background thread
    background_tasks.add_task(run_pipeline_thread, thread_id, task)

    return {
        "thread_id": thread_id,
        "task": task,
        "status": "STARTED",
    }


@app.post("/api/gate/respond")
async def respond_to_gate(request: GateResponseRequest, background_tasks: BackgroundTasks):
    thread_id = request.thread_id
    graph_config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 50,
    }

    snapshot = triad_app.get_state(graph_config)
    if not snapshot.next:
        raise HTTPException(status_code=400, detail="No active gate waiting for confirmation.")

    action = request.action.lower()
    resume_payload = {"action": action, "guidance": request.guidance or ""}
    resume_cmd = Command(resume=resume_payload)

    def resume_thread():
        try:
            for event in triad_app.stream(resume_cmd, graph_config):
                for node_name in event.keys():
                    print(f"  [LangGraph Server Post-Gate] Node finished: {node_name}")

            final_state = triad_app.get_state(graph_config)
            report = final_state.values.get("final_status_report", "Task completed.")
            success = final_state.values.get("approval_status") == "APPROVED"

            # Broadcast completion
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                event_bus.broadcast(
                    ProjectCompletedEvent(
                        thread_id=thread_id,
                        success=success,
                        summary=report,
                    )
                )
            )
        except Exception as e:
            print(f"  [Resume Error] {e}")

    background_tasks.add_task(resume_thread)

    return {"status": "RESUMED", "action": action}


def main():
    import uvicorn
    uvicorn.run(
        "ai_team.server:app",
        host=config.server_host,
        port=config.server_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
