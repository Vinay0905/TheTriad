"""FastAPI ASGI Server with WebSocket Event Hub and LangGraph Task Execution."""

import asyncio
import io
import os
import time
import uuid
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
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
    OfficeClockEvent,
)
from ai_team.graph.builder import build_triad_graph
from ai_team.persistence.checkpointer import get_checkpointer
from ai_team.spatial.event_bus import get_event_bus
from ai_team.spatial.office_clock import OfficeClock

app = FastAPI(title="TriadCouncil 3D: Virtual AI Office Server")

# Allow Vite dev server CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ACTIVE_RUNS: Dict[str, Dict[str, Any]] = {}
event_bus = get_event_bus()
config = get_config()
checkpointer = get_checkpointer(config.runs_dir / "checkpoints.db")
triad_app = build_triad_graph(checkpointer=checkpointer)
office_clock = OfficeClock()


def clock_event() -> OfficeClockEvent:
    snapshot = office_clock.snapshot()
    return OfficeClockEvent(
        phase=snapshot.phase,
        display_time=snapshot.display_time,
        day_number=snapshot.day_number,
        seconds_remaining=snapshot.seconds_remaining,
    )


async def broadcast_office_clock() -> None:
    """Keep all tabs in sync and announce shift changes once per transition."""
    previous_phase: Optional[str] = None
    while True:
        event = clock_event()
        event_bus.dispatch(event)

        if event.phase != previous_phase:
            if event.phase == "OFF_HOURS":
                for agent_id in ("manager", "researcher", "developer", "qa"):
                    event_bus.dispatch(
                        AgentStatusEvent(
                            agent_id=agent_id,
                            status_text="Clocking out for the day...",
                            animation="Walk",
                        )
                    )
                    event_bus.dispatch(
                        AgentMoveEvent(
                            agent_id=agent_id,
                            from_node="corridor_west",
                            to_node="exit",
                            action="Walk",
                        )
                    )
            elif previous_phase == "OFF_HOURS":
                for agent_id, desk in {
                    "manager": "desk_david",
                    "researcher": "desk_elena",
                    "developer": "desk_alex",
                    "qa": "desk_maya",
                }.items():
                    event_bus.dispatch(
                        AgentStatusEvent(
                            agent_id=agent_id,
                            status_text="Arriving for a new day...",
                            animation="Walk",
                        )
                    )
                    event_bus.dispatch(
                        AgentMoveEvent(
                            agent_id=agent_id,
                            from_node="exit",
                            to_node=desk,
                            action="Walk",
                        )
                    )

            previous_phase = event.phase

        await asyncio.sleep(1)


@app.on_event("startup")
async def startup_event():
    """Register the main async event loop with the event bus for cross-thread broadcasts."""
    event_bus.set_main_loop(asyncio.get_running_loop())
    asyncio.create_task(broadcast_office_clock())
    print("  ✓ [EventBus] Main async event loop registered for thread-safe cross-thread broadcasts.")


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
        initial_clock = clock_event()
        await websocket.send_json(initial_clock.model_dump())
        if initial_clock.phase == "OFF_HOURS":
            # A reloaded browser did not witness the original clock-out event;
            # give it the same exit choreography before hiding the team.
            for agent_id in ("manager", "researcher", "developer", "qa"):
                await websocket.send_json(
                    AgentStatusEvent(
                        agent_id=agent_id,
                        status_text="Clocked out for the day...",
                        animation="Walk",
                    ).model_dump()
                )
                await websocket.send_json(
                    AgentMoveEvent(
                        agent_id=agent_id,
                        from_node="corridor_west",
                        to_node="exit",
                        action="Walk",
                    ).model_dump()
                )
        # Initial greeting and status
        await websocket.send_json({
            "event_type": "AGENT_STATUS",
            "agent_id": "manager",
            "status_text": "David: Standing by for user objective...",
            "animation": "Sit",
            "timestamp": asyncio.get_event_loop().time(),
        })
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        event_bus.disconnect(websocket)


def run_pipeline_thread(thread_id: str, task: str):
    """Executes the LangGraph workflow up to the interrupt gate, driving real-time office choreographies."""
    graph_config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 50,
    }
    initial_input = {"task_prompt": task}
    manager_away_until: Optional[float] = None

    try:
        for event in triad_app.stream(initial_input, graph_config):
            for node_name in event.keys():
                print(f"  [LangGraph Server] Node finished: {node_name}")

                # Real Office Choreography based on pipeline progression
                if node_name == "manager_rfc_node":
                    # David has scoped the work and takes a short, bounded air
                    # break. A completed research hand-off waits for him.
                    manager_away_until = time.monotonic() + 7
                    event_bus.dispatch(
                        AgentStatusEvent(
                            agent_id="manager",
                            status_text="David: Taking a brief air break — reports will wait.",
                            animation="Walk",
                        )
                    )
                    event_bus.dispatch(
                        AgentMoveEvent(
                            agent_id="manager",
                            from_node="desk_david",
                            to_node="exit",
                            action="Walk",
                        )
                    )
                    event_bus.dispatch(
                        AgentMoveEvent(agent_id="researcher", from_node="coffee_lounge", to_node="desk_elena", action="Walk")
                    )
                    event_bus.dispatch(
                        AgentStatusEvent(agent_id="researcher", status_text="Elena: Investigating technical approach & dependencies...", animation="Type")
                    )
                elif node_name == "researcher_audit_node":
                    # The report is ready, but the team does not pretend it was
                    # delivered while the manager is away.
                    remaining_away = max(0.0, (manager_away_until or 0.0) - time.monotonic())
                    if remaining_away:
                        event_bus.dispatch(
                            AgentStatusEvent(
                                agent_id="researcher",
                                status_text="Elena: Research is ready — waiting for David to return.",
                                animation="Sit",
                            )
                        )
                        time.sleep(remaining_away)

                    event_bus.dispatch(
                        AgentStatusEvent(
                            agent_id="manager",
                            status_text="David: Back from air break; ready for reports.",
                            animation="Walk",
                        )
                    )
                    event_bus.dispatch(
                        AgentMoveEvent(
                            agent_id="manager",
                            from_node="exit",
                            to_node="desk_david",
                            action="Walk",
                        )
                    )
                    time.sleep(2.5)
                    # Research is shared at the whiteboard before implementation.
                    event_bus.dispatch(
                        AgentMoveEvent(agent_id="researcher", from_node="desk_elena", to_node="whiteboard", action="Walk")
                    )
                    event_bus.dispatch(
                        AgentStatusEvent(agent_id="researcher", status_text="Elena: Sharing verified research at the whiteboard...", animation="Walk")
                    )
                    event_bus.dispatch(
                        AgentStatusEvent(agent_id="developer", status_text="Alex: Translating research into a TDD contract...", animation="Type")
                    )
                elif node_name == "tdd_contract_node":
                    # Contract is ready; Alex returns to a focused build session.
                    event_bus.dispatch(
                        AgentMoveEvent(agent_id="developer", from_node="whiteboard", to_node="desk_alex", action="Walk")
                    )
                    event_bus.dispatch(
                        AgentStatusEvent(agent_id="developer", status_text="Alex: Implementing main.py at dual screens...", animation="Type")
                    )
                    event_bus.dispatch(
                        AgentMoveEvent(agent_id="researcher", from_node="whiteboard", to_node="desk_elena", action="Walk")
                    )
                    event_bus.dispatch(
                        AgentStatusEvent(agent_id="researcher", status_text="Elena: Monitoring API specifications...", animation="Sit")
                    )
                elif node_name == "developer_node":
                    # QA review is a deliberate hand-off from build to audit (stands beside Alex at desk_alex_review).
                    event_bus.dispatch(
                        AgentMoveEvent(agent_id="qa", from_node="desk_maya", to_node="desk_alex_review", action="Walk")
                    )
                    event_bus.dispatch(
                        AgentStatusEvent(agent_id="qa", status_text="Maya: Scrutinizing edge cases & race conditions...", animation="Type")
                    )
                elif node_name == "qa_audit_node":
                    # QA findings and the manager meet at the approval board at distinct non-overlapping spots.
                    event_bus.dispatch(
                        AgentMoveEvent(agent_id="qa", from_node="desk_alex_review", to_node="whiteboard_qa", action="Walk")
                    )
                    event_bus.dispatch(
                        AgentStatusEvent(agent_id="qa", status_text="Maya: Presenting QA findings for approval...", animation="Walk")
                    )
                    event_bus.dispatch(
                        AgentMoveEvent(agent_id="manager", from_node="desk_david", to_node="whiteboard_manager", action="Walk")
                    )
                    event_bus.dispatch(
                        AgentStatusEvent(agent_id="manager", status_text="David: Calling team to Whiteboard for approval...", animation="Sit")
                    )

        # 2. Check state after stream reaches __interrupt__
        snapshot = triad_app.get_state(graph_config)
        if snapshot.next:
            bundle = snapshot.values.get("execution_bundle", {})
            if thread_id in ACTIVE_RUNS and "workspace_path" in bundle:
                ACTIVE_RUNS[thread_id]["workspace_path"] = bundle["workspace_path"]
            qa_feedback = snapshot.values.get("qa_feedback", "Verified all constraints.")
            code_preview = bundle.get("source_files", {}).get("main.py", "")
            digest = bundle.get("bundle_digest", "")

            print(f"\n  [LangGraph Server] ⏸️ Halted at Human Steering Gate interrupt for thread: {thread_id}")
            print(f"  [LangGraph Server] Dispatching Whiteboard Gate Modal to 3D Office...")

            # Broadcast the Whiteboard Gate modal event
            event_bus.dispatch(
                WhiteboardGateEvent(
                    thread_id=thread_id,
                    task=task,
                    code_preview=code_preview,
                    qa_report=qa_feedback,
                    bundle_digest=digest,
                )
            )
            event_bus.dispatch(
                AgentStatusEvent(
                    agent_id="manager",
                    status_text="Waiting for human approval at Whiteboard...",
                    animation="Sit",
                )
            )
    except Exception as e:
        print(f"  [LangGraph Server Error] {e}")


@app.post("/api/tasks/start")
async def start_task(request: StartTaskRequest, background_tasks: BackgroundTasks):
    task = request.task.strip()
    if not task:
        raise HTTPException(status_code=400, detail="Task cannot be empty.")
    if clock_event().phase == "OFF_HOURS":
        raise HTTPException(
            status_code=409,
            detail="The office is closed. The team returns at 09:00 after off-hours.",
        )

    thread_id = f"thread_{uuid.uuid4().hex[:8]}"
    ACTIVE_RUNS[thread_id] = {
        "task": task,
        "status": "RUNNING",
    }

    # Broadcast initial movement & status: Manager scopes at desk
    event_bus.dispatch(
        AgentStatusEvent(
            agent_id="manager",
            status_text="David: Scoping objective & architectural requirements...",
            animation="Type",
        )
    )
    event_bus.dispatch(
        AgentMoveEvent(
            agent_id="manager",
            from_node="whiteboard",
            to_node="desk_david",
            action="Walk",
        )
    )
    event_bus.dispatch(
        AgentStatusEvent(
            agent_id="researcher",
            status_text="Elena: Preparing documentation search...",
            animation="Sit",
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
            # Let office know approval was granted!
            if action in ["approve", "y", "yes"]:
                event_bus.dispatch(
                    AgentMoveEvent(agent_id="developer", from_node="whiteboard", to_node="desk_alex", action="Walk")
                )
                event_bus.dispatch(
                    AgentStatusEvent(agent_id="developer", status_text="Alex: Executing code in sandbox & running tests...", animation="Type")
                )

            for event in triad_app.stream(resume_cmd, graph_config):
                for node_name in event.keys():
                    print(f"  [LangGraph Server Post-Gate] Node finished: {node_name}")

            final_state = triad_app.get_state(graph_config)
            report = final_state.values.get("final_status_report", "Task completed.")
            success = final_state.values.get("approval_status") == "APPROVED"

            # David announces completion and team returns to workstations
            event_bus.dispatch(
                AgentStatusEvent(agent_id="manager", status_text="David: Project delivery complete!", animation="Sit")
            )
            event_bus.dispatch(
                AgentMoveEvent(agent_id="manager", from_node="whiteboard", to_node="desk_david", action="Walk")
            )
            event_bus.dispatch(
                AgentMoveEvent(agent_id="qa", from_node="whiteboard", to_node="desk_maya", action="Walk")
            )
            event_bus.dispatch(
                ProjectCompletedEvent(
                    thread_id=thread_id,
                    success=success,
                    summary=report,
                )
            )
        except Exception as e:
            print(f"  [Resume Error] {e}")

    background_tasks.add_task(resume_thread)

    return {"status": "RESUMED", "action": action}


@app.get("/api/runs/{thread_id}/download")
async def download_run_files(thread_id: str):
    """Packages all synthesized project source and test files into a zip archive for offline inspection."""
    workspace: Optional[Path] = None
    if thread_id in ACTIVE_RUNS and "workspace_path" in ACTIVE_RUNS[thread_id]:
        ws_path = Path(ACTIVE_RUNS[thread_id]["workspace_path"])
        if ws_path.exists():
            workspace = ws_path

    if not workspace:
        # Fallback to newest run directory in .runs
        runs_dir = Path(".runs")
        if runs_dir.exists():
            run_dirs = sorted(
                [d for d in runs_dir.iterdir() if d.is_dir() and d.name.startswith("run_")],
                key=lambda d: d.stat().st_mtime,
                reverse=True,
            )
            for r in run_dirs:
                ws = r / "workspace"
                if ws.exists() and any(ws.glob("*.py")):
                    workspace = ws
                    break

    if not workspace or not workspace.exists():
        raise HTTPException(status_code=404, detail="Project files not found for this run.")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in workspace.rglob("*"):
            if "__pycache__" in file_path.parts or file_path.name.endswith(".pyc"):
                continue
            if file_path.is_file():
                arcname = file_path.relative_to(workspace)
                zf.write(file_path, arcname=str(arcname))

    zip_buffer.seek(0)
    safe_thread_id = thread_id.replace(" ", "_")
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=triadcouncil-project-{safe_thread_id}.zip"},
    )


@app.get("/api/runs/download/latest")
async def download_latest_run_files():
    """Download the most recently executed project files."""
    return await download_run_files("latest")


def main():
    import uvicorn
    src_dir = str(Path(__file__).resolve().parent.parent)
    uvicorn.run(
        "ai_team.server:app",
        host=config.server_host,
        port=config.server_port,
        app_dir=src_dir,
        reload=True,
        reload_dirs=[str(Path(src_dir) / "src")],
    )


if __name__ == "__main__":
    main()
