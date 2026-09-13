"""FastAPI server: WebSocket office hub plus the LangGraph run driver.

Two responsibilities, kept apart on purpose:

- Driving the graph and reporting where it halted. Every halt is either the
  human gate (broadcast the gate) or the end (broadcast the outcome).
- Serving the office. All choreography belongs to the `OfficeDirector`, so
  this module emits semantic events and never sleeps for animation.

Access control is a per-run token. This is not multi-user auth; it stops a
stray browser tab from approving or downloading a run it did not start, on a
server bound to loopback.
"""

import asyncio
import hmac
import io
import secrets
import uuid
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional
from zipfile import ZipFile

from fastapi import (
    BackgroundTasks,
    FastAPI,
    Header,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ai_team.config import get_config
from ai_team.domain.contracts import (
    AgentStatusEvent,
    OfficeClockEvent,
    ProjectCompletedEvent,
    ProviderHealthEvent,
    WhiteboardGateEvent,
)
from ai_team.execution.bundle import bundle_file_list
from ai_team.execution.sandbox import sandbox_status
from ai_team.graph.builder import GATE_NODE, build_triad_graph
from ai_team.persistence.checkpointer import open_checkpointer
from ai_team.persistence.redaction import redact_secrets
from ai_team.providers.resilience import get_provider_health
from ai_team.spatial.director import get_director
from ai_team.spatial.event_bus import get_event_bus
from ai_team.spatial.office_clock import OfficeClock

ACTIVE_RUNS: Dict[str, Dict[str, Any]] = {}
event_bus = get_event_bus()
config = get_config()
office_clock = OfficeClock()
director = get_director(office_clock)

# Set during lifespan startup. The graph must be built inside the checkpointer
# context, so it cannot be a module-level constant.
_graph = None


def get_graph():
    if _graph is None:
        raise HTTPException(status_code=503, detail="The council graph is not ready yet.")
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
    tasks = [
        asyncio.create_task(broadcast_office_clock()),
        asyncio.create_task(director.run()),
    ]

    with open_checkpointer(config.runs_dir / "checkpoints.db", durable=True) as saver:
        _graph = build_triad_graph(checkpointer=saver)
        print("  [Server] Durable SQLite checkpointer open; council graph compiled.")
        try:
            yield
        finally:
            _graph = None
            for task in tasks:
                task.cancel()
            for task in tasks:
                try:
                    await task
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


# ---------------------------------------------------------------------------
# Run tokens
# ---------------------------------------------------------------------------


def _require_run(thread_id: str) -> Dict[str, Any]:
    run = ACTIVE_RUNS.get(thread_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Unknown run.")
    return run


def _authorize(thread_id: str, presented: Optional[str]) -> Dict[str, Any]:
    """Constant-time check that the caller started this run."""
    run = _require_run(thread_id)
    expected = run.get("run_token") or ""
    if not presented or not hmac.compare_digest(str(presented), expected):
        raise HTTPException(status_code=403, detail="Invalid or missing run token.")
    return run


# ---------------------------------------------------------------------------
# Clock and health broadcasting
# ---------------------------------------------------------------------------


def clock_event() -> OfficeClockEvent:
    snapshot = office_clock.snapshot()
    return OfficeClockEvent(
        phase=snapshot.phase,
        display_time=snapshot.display_time,
        day_number=snapshot.day_number,
        seconds_remaining=snapshot.seconds_remaining,
    )


def provider_health_event() -> ProviderHealthEvent:
    """Real backend health, replacing the old hardcoded 'NODES: 4/4 LIVE'."""
    available, _detail = sandbox_status()
    return ProviderHealthEvent(
        roles=get_provider_health().snapshot(),
        sandbox_available=available,
        sandbox_backend=config.sandbox_backend,
    )


async def broadcast_office_clock() -> None:
    """Keep all tabs in sync.

    Shift-change choreography belongs to the Director, so this only publishes
    time. The interval is deliberately coarse: the browser interpolates between
    ticks, and frequent timer wakeups are what stop a laptop CPU idling.
    """
    while True:
        event_bus.dispatch(clock_event())
        await asyncio.sleep(5)


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class StartTaskRequest(BaseModel):
    task: str


class GateResponseRequest(BaseModel):
    thread_id: str
    action: str  # "approve" | "abort" | "steer"; anything else aborts
    guidance: Optional[str] = None
    run_token: Optional[str] = None


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "TriadCouncil Virtual Office",
        "graph_ready": _graph is not None,
        "sandbox_backend": config.sandbox_backend,
    }


@app.get("/api/office/providers")
async def office_providers():
    """Live provider and sandbox availability, for honest HUD telemetry."""
    event = provider_health_event()
    _available, detail = sandbox_status()
    return {
        "roles": [role.model_dump() for role in event.roles],
        "sandbox_available": event.sandbox_available,
        "sandbox_backend": event.sandbox_backend,
        "sandbox_detail": detail,
    }


@app.websocket("/ws/office")
async def office_websocket(websocket: WebSocket):
    await event_bus.connect(websocket)
    try:
        await websocket.send_json(clock_event().model_dump())
        await websocket.send_json(provider_health_event().model_dump())
        await websocket.send_json(
            AgentStatusEvent(
                agent_id="manager",
                status_text="David: Standing by for an objective.",
                animation="Sit",
            ).model_dump()
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        event_bus.disconnect(websocket)
    except Exception as err:
        print(f"  [Server] WebSocket closed: {err}")
        event_bus.disconnect(websocket)


# ---------------------------------------------------------------------------
# Graph driver
# ---------------------------------------------------------------------------


def _broadcast_gate(thread_id: str, bundle: Dict[str, Any]) -> None:
    """Emit the single gate UI event.

    This lives here rather than in the gate node because `interrupt()` re-runs
    its node from the top on resume, so a dispatch inside the node fires again
    on every resume. The token is never included in this payload.
    """
    print(f"  [Server] Halted at the human gate for {thread_id}.")
    director.note_gate_open()
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


def _broadcast_completion(thread_id: str, values: Dict[str, Any]) -> None:
    """Report the outcome, using real evidence only."""
    approval = values.get("approval_status")
    sandbox = values.get("sandbox_result") or {}
    exit_code = sandbox.get("exit_code")

    # Approval alone is not success. The tests must actually have passed.
    success = approval == "APPROVED" and exit_code == 0

    director.note_run_finished()
    event_bus.dispatch(
        ProjectCompletedEvent(
            thread_id=thread_id,
            success=success,
            summary=redact_secrets(values.get("final_status_report") or "No report."),
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
    graph = _graph
    if graph is None:
        print("  [Server] Graph unavailable; run aborted.")
        return

    graph_config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}

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
                # Semantic only. The Director decides who moves, on its own
                # timeline, so animation never delays the pipeline.
                director.note_node_finished(node_name)

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
        director.note_run_finished()
        run = ACTIVE_RUNS.get(thread_id)
        if run is not None:
            run["status"] = "ERROR"
            run["error"] = redact_secrets(str(err))
        event_bus.dispatch(
            ProjectCompletedEvent(
                thread_id=thread_id,
                success=False,
                summary=(
                    "The run failed before completing.\n\n"
                    f"{redact_secrets(str(err))}"
                ),
                approval_status=None,
                exit_code=None,
            )
        )


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
    run_token = secrets.token_urlsafe(32)
    # Returned once, to the caller that started the run. Never logged and never
    # broadcast over the WebSocket.
    ACTIVE_RUNS[thread_id] = {
        "task": task,
        "status": "RUNNING",
        "run_token": run_token,
    }

    event_bus.dispatch(
        AgentStatusEvent(
            agent_id="manager",
            status_text="David: Scoping the objective and acceptance criteria...",
            animation="Type",
        )
    )

    background_tasks.add_task(_drive_graph, thread_id, task, None)

    return {
        "thread_id": thread_id,
        "task": task,
        "status": "STARTED",
        "run_token": run_token,
    }


@app.post("/api/gate/respond")
async def respond_to_gate(
    request: GateResponseRequest,
    background_tasks: BackgroundTasks,
    x_run_token: Optional[str] = Header(default=None, alias="X-Run-Token"),
):
    graph = get_graph()
    thread_id = request.thread_id

    _authorize(thread_id, x_run_token or request.run_token)

    graph_config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}
    snapshot = graph.get_state(graph_config)
    if not snapshot.next or GATE_NODE not in snapshot.next:
        raise HTTPException(status_code=409, detail="No gate is awaiting a decision.")

    # The raw action is forwarded verbatim. The gate node owns interpretation
    # and fails closed on anything it does not recognise.
    resume_payload = {"action": request.action, "guidance": request.guidance or ""}

    background_tasks.add_task(
        _drive_graph, thread_id, ACTIVE_RUNS[thread_id].get("task", ""), resume_payload
    )

    return {"status": "RESUMED", "thread_id": thread_id}


@app.get("/api/runs/{thread_id}")
async def get_run(
    thread_id: str,
    x_run_token: Optional[str] = Header(default=None, alias="X-Run-Token"),
    token: Optional[str] = Query(default=None),
):
    run = _authorize(thread_id, x_run_token or token)
    return {
        "thread_id": thread_id,
        "status": run.get("status"),
        "approval_status": run.get("approval_status"),
        "exit_code": run.get("exit_code"),
        "task": run.get("task"),
    }


@app.get("/api/runs/{thread_id}/download")
async def download_run_files(
    thread_id: str,
    x_run_token: Optional[str] = Header(default=None, alias="X-Run-Token"),
    token: Optional[str] = Query(default=None),
):
    """Stream the workspace for a specific run.

    The token may arrive as a query parameter because a browser download is a
    plain navigation and cannot set headers. There is deliberately no "newest
    run on disk" fallback: guessing meant an unknown thread id could be handed
    another run's files.
    """
    run = _authorize(thread_id, x_run_token or token)

    workspace_path = run.get("workspace_path")
    if not workspace_path:
        raise HTTPException(status_code=404, detail="No workspace for this run.")

    workspace = Path(workspace_path)
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
            "Content-Disposition": f"attachment; filename=triadcouncil-{safe_thread_id}.zip"
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
        # of the process.
        reload=config.server_reload,
        reload_dirs=[str(Path(src_dir) / "src")] if config.server_reload else None,
    )


if __name__ == "__main__":
    main()
