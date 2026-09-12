"""FastAPI server: WebSocket office hub plus the LangGraph run driver."""

import asyncio
import io
import time
import uuid
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional
from zipfile import ZipFile

from fastapi import BackgroundTasks, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ai_team.config import get_config
from ai_team.domain.contracts import (
    AgentMoveEvent,
    AgentStatusEvent,
    OfficeClockEvent,
    ProjectCompletedEvent,
    WhiteboardGateEvent,
)
from ai_team.execution.bundle import bundle_file_list
from ai_team.graph.builder import GATE_NODE, build_triad_graph
from ai_team.persistence.checkpointer import open_checkpointer
from ai_team.spatial.event_bus import get_event_bus
from ai_team.spatial.office_clock import OfficeClock

ACTIVE_RUNS: Dict[str, Dict[str, Any]] = {}
event_bus = get_event_bus()
config = get_config()
office_clock = OfficeClock()

# Set during lifespan startup. The graph must be built inside the checkpointer
# context, so it cannot be a module-level constant.
_graph = None


def get_graph():
    if _graph is None:
        raise HTTPException(
            status_code=503, detail="The council graph is not ready yet."
        )
    return _graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Hold the checkpointer open for the whole process lifetime.

    `SqliteSaver.from_conn_string()` is a context manager. Building the graph
    outside it, as the previous code did, meant the gate could not actually be
    resumed from a durable checkpoint.
    """
    global _graph

    event_bus.set_main_loop(asyncio.get_running_loop())
    clock_task = asyncio.create_task(broadcast_office_clock())

    with open_checkpointer(config.runs_dir / "checkpoints.db", durable=True) as saver:
        _graph = build_triad_graph(checkpointer=saver)
        print("  [Server] Durable SQLite checkpointer open; council graph compiled.")
        try:
            yield
        finally:
            _graph = None
            clock_task.cancel()
            try:
                await clock_task
            except asyncio.CancelledError:
                pass


app = FastAPI(title="TriadCouncil: Virtual AI Office Server", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


class StartTaskRequest(BaseModel):
    task: str


class GateResponseRequest(BaseModel):
    thread_id: str
    action: str  # "approve" | "abort" | "steer"; anything else aborts
    guidance: Optional[str] = None


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "TriadCouncil Virtual Office",
        "graph_ready": _graph is not None,
        "sandbox_backend": config.sandbox_backend,
    }


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
        await websocket.send_json(
            AgentStatusEvent(
                agent_id="manager",
                status_text="David: Standing by for user objective...",
                animation="Sit",
            ).model_dump()
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        event_bus.disconnect(websocket)


# ---------------------------------------------------------------------------
# Office choreography
#
# NOTE: this is still hardcoded against node names and still sleeps on the
# worker thread. Replacing it with a server-side OfficeDirector that owns
# arbitration and slot reservation is tracked as a separate change; it is left
# intact here so this pass stays focused on the safety path.
# ---------------------------------------------------------------------------


def _choreograph(node_name: str, pacing: Dict[str, float]) -> None:
    if node_name == "manager_rfc_node":
        pacing["manager_away_until"] = time.monotonic() + 7
        event_bus.dispatch(
            AgentStatusEvent(
                agent_id="manager",
                status_text="David: Taking a brief air break - reports will wait.",
                animation="Walk",
            )
        )
        event_bus.dispatch(
            AgentMoveEvent(
                agent_id="manager", from_node="desk_david", to_node="exit", action="Walk"
            )
        )
        event_bus.dispatch(
            AgentMoveEvent(
                agent_id="researcher",
                from_node="coffee_lounge",
                to_node="desk_elena",
                action="Walk",
            )
        )
        event_bus.dispatch(
            AgentStatusEvent(
                agent_id="researcher",
                status_text="Elena: Investigating technical approach & dependencies...",
                animation="Type",
            )
        )
    elif node_name == "researcher_audit_node":
        remaining = max(0.0, pacing.get("manager_away_until", 0.0) - time.monotonic())
        if remaining:
            event_bus.dispatch(
                AgentStatusEvent(
                    agent_id="researcher",
                    status_text="Elena: Research is ready - waiting for David to return.",
                    animation="Sit",
                )
            )
            time.sleep(remaining)

        event_bus.dispatch(
            AgentStatusEvent(
                agent_id="manager",
                status_text="David: Back from air break; ready for reports.",
                animation="Walk",
            )
        )
        event_bus.dispatch(
            AgentMoveEvent(
                agent_id="manager", from_node="exit", to_node="desk_david", action="Walk"
            )
        )
        time.sleep(2.5)
        event_bus.dispatch(
            AgentMoveEvent(
                agent_id="researcher",
                from_node="desk_elena",
                to_node="whiteboard",
                action="Walk",
            )
        )
        event_bus.dispatch(
            AgentStatusEvent(
                agent_id="researcher",
                status_text="Elena: Sharing verified research at the whiteboard...",
                animation="Walk",
            )
        )
        event_bus.dispatch(
            AgentStatusEvent(
                agent_id="developer",
                status_text="Alex: Translating research into a TDD contract...",
                animation="Type",
            )
        )
    elif node_name == "tdd_contract_node":
        event_bus.dispatch(
            AgentMoveEvent(
                agent_id="developer",
                from_node="whiteboard",
                to_node="desk_alex",
                action="Walk",
            )
        )
        event_bus.dispatch(
            AgentStatusEvent(
                agent_id="developer",
                status_text="Alex: Implementing main.py at dual screens...",
                animation="Type",
            )
        )
        event_bus.dispatch(
            AgentMoveEvent(
                agent_id="researcher",
                from_node="whiteboard",
                to_node="desk_elena",
                action="Walk",
            )
        )
        event_bus.dispatch(
            AgentStatusEvent(
                agent_id="researcher",
                status_text="Elena: Monitoring API specifications...",
                animation="Sit",
            )
        )
    elif node_name == "developer_node":
        event_bus.dispatch(
            AgentMoveEvent(
                agent_id="qa",
                from_node="desk_maya",
                to_node="desk_alex_review",
                action="Walk",
            )
        )
        event_bus.dispatch(
            AgentStatusEvent(
                agent_id="qa",
                status_text="Maya: Scrutinizing edge cases & race conditions...",
                animation="Type",
            )
        )
    elif node_name == "qa_audit_node":
        event_bus.dispatch(
            AgentMoveEvent(
                agent_id="qa",
                from_node="desk_alex_review",
                to_node="whiteboard_qa",
                action="Walk",
            )
        )
        event_bus.dispatch(
            AgentStatusEvent(
                agent_id="qa",
                status_text="Maya: Presenting QA findings for approval...",
                animation="Walk",
            )
        )
        event_bus.dispatch(
            AgentMoveEvent(
                agent_id="manager",
                from_node="desk_david",
                to_node="whiteboard_manager",
                action="Walk",
            )
        )
        event_bus.dispatch(
            AgentStatusEvent(
                agent_id="manager",
                status_text="David: Calling team to Whiteboard for approval...",
                animation="Sit",
            )
        )
    elif node_name == "sandbox_execution_node":
        event_bus.dispatch(
            AgentMoveEvent(
                agent_id="developer",
                from_node="whiteboard",
                to_node="desk_alex",
                action="Walk",
            )
        )
        event_bus.dispatch(
            AgentStatusEvent(
                agent_id="developer",
                status_text="Alex: Running the approved tests in the sandbox...",
                animation="Type",
            )
        )


def _broadcast_gate(thread_id: str, bundle: Dict[str, Any]) -> None:
    """Emit the single gate UI event.

    This lives here rather than in the gate node because `interrupt()` re-runs
    its node from the top on resume, so a dispatch inside the node fires again
    on every resume.
    """
    print(f"  [Server] Halted at the human gate for {thread_id}.")
    event_bus.dispatch(
        WhiteboardGateEvent(
            thread_id=thread_id,
            task=bundle.get("task", ""),
            code_preview=(bundle.get("source_files") or {}).get("main.py", ""),
            qa_report=bundle.get("qa_report") or "No auditor notes recorded.",
            bundle_digest=bundle.get("bundle_digest", ""),
            qa_status=bundle.get("qa_status", "UNAVAILABLE"),
            files=bundle_file_list(bundle),
            commands=bundle.get("declared_commands", []),
            gate_kind="EXECUTE",
        )
    )
    event_bus.dispatch(
        AgentStatusEvent(
            agent_id="manager",
            status_text="Waiting for human approval at the whiteboard...",
            animation="Sit",
        )
    )


def _broadcast_completion(thread_id: str, values: Dict[str, Any]) -> None:
    """Report the outcome, using real evidence only."""
    approval = values.get("approval_status")
    sandbox = values.get("sandbox_result") or {}
    exit_code = sandbox.get("exit_code")

    # Approval alone is not success. Tests must actually have passed.
    success = approval == "APPROVED" and exit_code == 0

    event_bus.dispatch(
        AgentMoveEvent(
            agent_id="qa", from_node="whiteboard", to_node="desk_maya", action="Walk"
        )
    )
    event_bus.dispatch(
        AgentStatusEvent(
            agent_id="manager",
            status_text="David: Delivering the outcome to BOSS room...",
            animation="Walk",
        )
    )
    event_bus.dispatch(
        AgentMoveEvent(
            agent_id="manager", from_node="whiteboard", to_node="boss_room", action="Walk"
        )
    )
    event_bus.dispatch(
        ProjectCompletedEvent(
            thread_id=thread_id,
            success=success,
            summary=values.get("final_status_report") or "No report was produced.",
            approval_status=approval,
            exit_code=exit_code,
            failing_tests_count=sandbox.get("failing_tests_count", 0),
            bundle_digest=(values.get("execution_bundle") or {}).get("bundle_digest"),
        )
    )

    run = ACTIVE_RUNS.get(thread_id)
    if run is not None:
        run["status"] = "COMPLETED" if success else "FAILED"
        run["approval_status"] = approval
        run["exit_code"] = exit_code


def _drive_graph(thread_id: str, task: str, resume: Optional[Dict[str, Any]] = None) -> None:
    """Advance the graph until it halts, then broadcast where it stopped.

    Used for both the initial run and every resume, so steering back into the
    council cannot be mistaken for delivery.
    """
    graph = get_graph()
    graph_config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 50,
    }
    pacing: Dict[str, float] = {}

    if resume is None:
        stream_input: Any = {"task_prompt": task}
    else:
        from langgraph.types import Command

        stream_input = Command(resume=resume)

    try:
        for event in graph.stream(stream_input, graph_config):
            for node_name in event:
                if node_name.startswith("__"):
                    continue
                print(f"  [Server] Node finished: {node_name}")
                _choreograph(node_name, pacing)

        snapshot = graph.get_state(graph_config)

        if snapshot.next and GATE_NODE in snapshot.next:
            bundle = snapshot.values.get("execution_bundle") or {}
            run = ACTIVE_RUNS.get(thread_id)
            if run is not None and bundle.get("workspace_path"):
                run["workspace_path"] = bundle["workspace_path"]
            _broadcast_gate(thread_id, bundle)
            return

        if snapshot.next:
            print(f"  [Server] Graph paused unexpectedly at {snapshot.next}.")
            return

        _broadcast_completion(thread_id, snapshot.values)
    except Exception as err:
        print(f"  [Server] Run {thread_id} failed: {err}")
        run = ACTIVE_RUNS.get(thread_id)
        if run is not None:
            run["status"] = "ERROR"
            run["error"] = str(err)


@app.post("/api/tasks/start")
async def start_task(request: StartTaskRequest, background_tasks: BackgroundTasks):
    get_graph()

    task = request.task.strip()
    if not task:
        raise HTTPException(status_code=400, detail="Task cannot be empty.")
    if clock_event().phase == "OFF_HOURS":
        raise HTTPException(
            status_code=409,
            detail="The office is closed. The team returns at 09:00 after off-hours.",
        )

    thread_id = f"thread_{uuid.uuid4().hex[:8]}"
    ACTIVE_RUNS[thread_id] = {"task": task, "status": "RUNNING"}

    event_bus.dispatch(
        AgentStatusEvent(
            agent_id="manager",
            status_text="David: Scoping objective & architectural requirements...",
            animation="Type",
        )
    )
    event_bus.dispatch(
        AgentMoveEvent(
            agent_id="manager", from_node="whiteboard", to_node="desk_david", action="Walk"
        )
    )
    event_bus.dispatch(
        AgentStatusEvent(
            agent_id="researcher",
            status_text="Elena: Preparing documentation search...",
            animation="Sit",
        )
    )

    background_tasks.add_task(_drive_graph, thread_id, task, None)

    return {"thread_id": thread_id, "task": task, "status": "STARTED"}


@app.post("/api/gate/respond")
async def respond_to_gate(request: GateResponseRequest, background_tasks: BackgroundTasks):
    graph = get_graph()
    thread_id = request.thread_id

    if thread_id not in ACTIVE_RUNS:
        raise HTTPException(status_code=404, detail="Unknown run.")

    graph_config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 50,
    }
    snapshot = graph.get_state(graph_config)
    if not snapshot.next or GATE_NODE not in snapshot.next:
        raise HTTPException(
            status_code=409, detail="No gate is currently awaiting a decision."
        )

    # The raw action is forwarded verbatim. The gate node owns interpretation
    # and fails closed on anything it does not recognise.
    resume_payload = {
        "action": request.action,
        "guidance": request.guidance or "",
    }

    background_tasks.add_task(
        _drive_graph, thread_id, ACTIVE_RUNS[thread_id].get("task", ""), resume_payload
    )

    return {"status": "RESUMED", "thread_id": thread_id}


@app.get("/api/runs/{thread_id}")
async def get_run(thread_id: str):
    run = ACTIVE_RUNS.get(thread_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Unknown run.")
    return {
        "thread_id": thread_id,
        "status": run.get("status"),
        "approval_status": run.get("approval_status"),
        "exit_code": run.get("exit_code"),
        "task": run.get("task"),
    }


@app.get("/api/runs/{thread_id}/download")
async def download_run_files(thread_id: str):
    """Stream the workspace for a specific run.

    There is deliberately no "newest run on disk" fallback: guessing meant an
    unknown thread id could be handed another run's files.
    """
    run = ACTIVE_RUNS.get(thread_id)
    if run is None or not run.get("workspace_path"):
        raise HTTPException(status_code=404, detail="No workspace for this run.")

    workspace = Path(run["workspace_path"])
    if not workspace.exists():
        raise HTTPException(status_code=404, detail="No workspace for this run.")

    buffer = io.BytesIO()
    with ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in workspace.rglob("*"):
            if "__pycache__" in file_path.parts or file_path.name.endswith(".pyc"):
                continue
            if file_path.is_file():
                archive.write(file_path, arcname=str(file_path.relative_to(workspace)))

    buffer.seek(0)
    safe_thread_id = thread_id.replace(" ", "_").replace("/", "_")
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": (
                f"attachment; filename=triadcouncil-{safe_thread_id}.zip"
            )
        },
    )


def main():
    import uvicorn

    src_dir = str(Path(__file__).resolve().parent.parent)
    uvicorn.run(
        "ai_team.server:app",
        host=config.server_host,
        port=config.server_port,
        app_dir=src_dir,
        # Off by default: the reloader runs a filesystem watcher for the life
        # of the process. Enable with AI_TEAM_SERVER_RELOAD=1 when developing.
        reload=config.server_reload,
        reload_dirs=[str(Path(src_dir) / "src")] if config.server_reload else None,
    )


if __name__ == "__main__":
    main()
