# TriadCouncil: Comprehensive Engineering Handoff & Architecture Bible

> **Audience**: Any AI model (Claude, GPT, Gemini, DeepSeek), autonomous coding agent, or human engineer picking up this codebase.
> **Purpose**: Provide a complete, unambiguous mental model of TriadCouncil—its design philosophy, multi-agent LangGraph topology, provider matrix, human-in-the-loop safety boundaries, sandboxed execution runtime, and fullstack 3D Virtual AI Office HUD.

---

## 0. What is actually wired (read this first)

> [!IMPORTANT]
> Sections 1-11 below describe the intended architecture and include aspirational
> detail. This section states what the code does **today**. Where the two
> disagree, this section wins.

**Correct as written below:** the LangGraph topology, the five-phase flow, the
human `interrupt()` gate, the bounded QA repair cycle, the SHA-256 execution
bundle, and the spatial event bus.

**Differs from the sections below:**

| Claim elsewhere in this doc | Reality |
| :--- | :--- |
| Researcher uses Gemini 2.5 Flash with Google Search grounding | **Runs on Groq. There is no web search.** Citations are labelled unverified. |
| Senior Dev executes via the Antigravity SDK | Execution is **Docker only**, behind a `SandboxRunner` protocol. The Antigravity adapter is quarantined in `src/ai_team/_legacy/`. |
| Tournament mode: Junior 1 vs Junior 2 | Not wired. `junior_dev.py` / `senior_review.py` are quarantined. |
| Sandbox runs an approved shell command whitelist | Exact-string allowlist resolved to **argv with no shell**. `ls` and `cat` are no longer permitted. |
| Command whitelist matches approved prefixes | Prefix matching is gone; it accepted `...; rm -rf /`. |
| `/api/task`, `/api/runs/{id}/resume`, `/api/office/state`, `/api/office/clock` | Not real routes. See the API table in section 9. |
| Tests are "100% passing" | The suite was rewritten and has not been run end to end yet. |

**Additional guarantees now enforced in code, not prose:**

- The gate **fails closed**. Approval requires an explicit `y`/`yes`/`approve`;
  a malformed payload, a truthy `True`, an unexpected exception, or a missing
  `interrupt` import all abort. (`src/ai_team/graph/gate_decision.py`)
- `test_main.py` is **digest-locked** after the TDD node, re-verified by every
  downstream node, and the developer's output is filtered so it cannot write
  tests at all. (`src/ai_team/graph/contract_lock.py`)
- A test suite that **cannot fail** (for example `assertTrue(hasattr(main,
  '__name__'))`) is rejected and fails the run. It is never substituted in.
- QA **fails closed**. A provider outage yields `qa_passed=False`,
  `qa_skipped=True`, and a gate that reads `QA unavailable` — never PASS.
- No host execution exists. Docker missing means the run is refused.
- No host environment is forwarded into the container, so API keys are not
  visible to approved code.
- `success` requires approval **and** sandbox `exit_code == 0`.

**Also now enforced:**

- **Per-run tokens.** `POST /api/tasks/start` mints `secrets.token_urlsafe(32)`,
  returned once to the caller. Gate responses and downloads require it via
  `X-Run-Token` (or `?token=` for downloads, since a browser navigation cannot
  set a header), compared with `hmac.compare_digest`. The token is never logged
  and never broadcast on the WebSocket.
- **One behaviour owner.** All choreography lives in
  `ai_team.spatial.director.OfficeDirector`, an asyncio task with priority
  arbitration (`PIPELINE_CRITICAL > PROVIDER_STATE > SCHEDULED_BREAK >
  AMBIENT_IDLE`) and per-destination slot reservation. No `time.sleep()`
  remains on the graph thread, so animation cannot delay LLM work.
- **Provider state is visible.** `ai_team.providers.resilience` classifies
  failures into rate limit (wait, with a countdown in the HUD), quota exhausted
  (the agent walks out and the role is marked unavailable), auth failure, and
  hard error. Substitutions are named in the HUD and in the report.
- **One geometry source.** `frontend/src/components/office/OfficeGeometry.ts`
  owns furniture boxes and destination slots, with `findGeometryProblems()`
  asserting no slot sits inside furniture, no two slots share coordinates, and
  corridors keep clearance. It runs in dev and logs to the console.
- **Demand rendering.** The canvas uses `frameloop="demand"`, capped `dpr`,
  a once-baked shadow map, `ContactShadows frames={1}`, three lights instead of
  ten, and pauses while the tab is hidden. `?perf=1` shows real draw calls.

**Known gaps as of this handoff:**

- The test suite has never been executed; see [TESTING.md](TESTING.md).
- Tracks B2–B5 are unbuilt: no RED/GREEN theatre, no LangSmith tracing, no
  time-travel scrubber, no git worktree per run.
- No navmesh. Collision and occupancy are solved by corrected geometry, slot
  reservation, separation forces and obstacle resolution; `recast-navigation`
  was deliberately not added on an untested build.
- Elena still does not search the web.
- The run token lives in tab memory, so a refresh mid-run loses the ability to
  approve from the browser.

---

## 1. Executive Summary & Core Identity

**TriadCouncil** is an autonomous multi-agent software engineering system built natively on **LangGraph (0.2+)** and **FastAPI**, with a real-time **3D Virtual AI Office HUD** (React + TypeScript + Three.js/Canvas).

Unlike conventional multi-agent frameworks where conversational agents chat in an unconstrained circle until context explodes, TriadCouncil is architected as an **auditable software engineering department**:
- **Strict Role Specialization**: Five distinct roles (Manager, Researcher, TDD Engineer / Senior Dev, QA & Security Auditor, Junior Devs) mapped across **four heterogeneous frontier model families** (Anthropic/DeepSeek via OpenRouter, Google Gemini, Meta Llama via Groq, and ZhipuAI GLM-4-Flash).
- **Contract-First Test-Driven Development (TDD)**: The test suite and interfaces (`interfaces.py`, `test_main.py`) are locked *before* implementation code is written. Implementation agents are strictly forbidden from altering test files.
- **Bounded Iterative QA Cycles**: Automated AST syntax validation paired with adversarial QA code review (GLM-4-Flash). Failing code routes back to the Developer with explicit feedback, bounded to a maximum of **2 repair cycles**.
- **Immutable Human Confirmation Gate**: Code execution and filesystem writes are 100% blocked until an explicit human operator decision (`[y] Approve`, `[n] Abort`, `[s] Steer with Guidance`) is provided via the CLI or the interactive Whiteboard Modal in the 3D HUD.
- **Isolated Sandboxed Execution**: Approved code executes strictly inside `.runs/<run_id>/workspace/` with an enforced shell command whitelist and real test execution evidence.
- **Spatial 3D Virtual Office Simulation**: A live WebSocket event hub broadcasts agent movements, status animations (Thinking, Typing, Coffee breaks), whiteboard presentations, terminal logs, and a simulated workday clock to a full-bleed 3D office frontend.

---

## 2. System Architecture & Component Diagram

```
                              ┌──────────────────────────────────────────────────────────┐
                              │                 Human Operator / Client                   │
                              │           (CLI Terminal  OR  React 3D Office HUD)        │
                              └───────────────▲──────────────────────────┬───────────────┘
                                              │                          │
                                  State Stream│                          │ Task Prompt / Gate Action
                                  & Event Bus │                          │ (Approve / Steer / Abort)
                                              │                          ▼
┌─────────────────────────────────────────────┴──────────────────────────────────────────────────────────────┐
│                                             FASTAPI ASGI BACKEND SERVER                                    │
│                                                   (server.py)                                              │
│                                                                                                            │
│   ┌──────────────────────────┐   ┌───────────────────────────┐   ┌─────────────────────────────────────┐   │
│   │     OfficeClock (Sim)    │   │      Spatial EventBus     │   │      SQLite Checkpointer            │   │
│   │  Workday vs. Off-Hours   │   │  Broadcasts Moves, Status │   │    (.runs/checkpoints.db)           │   │
│   │  Day/Shift Transitions   │   │  Logs & Whiteboard Gates  │   │    Enables Graph Pause & Resume     │   │
│   └────────────┬─────────────┘   └─────────────▲─────────────┘   └──────────────────┬──────────────────┘   │
│                │                               │                                    │                      │
│                ▼                               │                                    ▼                      │
│   ┌────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                              LangGraph StateGraph Engine (builder.py)                              │   │
│   │                                                                                                    │   │
│   │  [START]                                                                                           │   │
│   │     │                                                                                              │   │
│   │     ▼                                                                                              │   │
│   │  1. manager_rfc_node ────────► 2. researcher_audit_node ────────► 3. tdd_contract_node             │   │
│   │     (OpenRouter / Claude)         (Gemini 2.5 Flash Grounding)        (Senior Dev Contract)        │   │
│   │                                                                               │                    │   │
│   │                                   ┌───────────────────────────────────────────┘                    │   │
│   │                                   ▼                                                                │   │
│   │                         4. developer_node (Alex) ◄────────┐ (Attempts < 2)                         │   │
│   │                            (Groq / Gemini)                │                                        │   │
│   │                                   │                       │                                        │   │
│   │                                   ▼                       │                                        │   │
│   │                         5. qa_audit_node (Maya) ──────────┘                                        │   │
│   │                            (GLM-4-Flash 30B MoE)                                                   │   │
│   │                                   │                                                                │   │
│   │                                   ▼ (Passed OR Attempts == 2)                                      │   │
│   │                         6. preflight_gate_node                                                     │   │
│   │                            (Locks ExecutionBundle & SHA-256 Digest)                                │   │
│   │                                   │                                                                │   │
│   │                                   ▼                                                                │   │
│   │                       ╔═════════════════════════════════╗                                          │   │
│   │                       ║ 7. human_steering_gate_node     ║                                          │   │
│   │                       ║    LangGraph interrupt()        ║                                          │   │
│   │                       ╚═══════════╤═════════════════════╝                                          │   │
│   │                                   │                                                                │   │
│   │               ┌───────────────────┼───────────────────┐                                            │   │
│   │        [Action: Steer]     [Action: Approve]   [Action: Abort]                                     │   │
│   │               │                   │                   │                                            │   │
│   │               ▼                   │                   ▼                                            │   │
│   │     (Back to Manager RFC)         │           (Clean Terminal Report)                              │   │
│   │                                   ▼                                                                │   │
│   │                         8. sandbox_execution_node                                                  │   │
│   │                            (Isolated Subprocess Workspace)                                         │   │
│   │                                   │                                                                │   │
│   │                                   ▼                                                                │   │
│   │                         9. manager_final_report_node ────────► [END]                               │   │
│   │                                                                                                    │   │
│   └────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. The 5 Council Roles & Model Specializations

To prevent single-model bias, systemic blindspots, and vendor lock-in, every role in the Council is deliberately assigned to the provider best suited to its operational constraints:

> [!WARNING]
> Three rows below are aspirational, not current. The **Researcher** runs on
> Groq with no web search; the **Senior Dev** executes via Docker, not
> Antigravity; and **Tournament Competitors** are not wired. See section 0.

| Role Name | Persona | Primary Provider / Model | Backend Integration | Core Responsibility | Economic Profile |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Manager** | **David** | **Anthropic Claude 3.5 Sonnet** (or DeepSeek Chat) via OpenRouter | `ChatOpenAI(base_url="https://openrouter.ai/api/v1")` | Decomposes task into requirements, authors architectural RFC, verifies preflight package, generates final delivery report. | Pay-as-you-go |
| **Researcher** | **Elena** | **Google Gemini 2.5 Flash** (Native Google Search Grounding) | `google-genai` SDK with `google_search` tool | Performs live web searches to detect deprecated APIs, breaking library changes, security advisories, and canonical docs. | **Free Tier** |
| **QA Auditor & Red-Teamer** | **Maya** | **ZhipuAI GLM-4-Flash** (30B MoE) | `ChatOpenAI(base_url="https://open.bigmodel.cn/api/paas/v4")` | Performs adversarial AST syntax checks, hunts for concurrency deadlocks, evaluates edge cases, writes negative tests, rejects fragile code. | **100% Permanently Free** |
| **Developer / Senior Dev** | **Alex** | **Groq LPU (Llama 3.3 70B / 3.1 8B)** or **Antigravity SDK (Gemini)** | `ChatGroq` / `Agent(LocalAgentConfig)` | Pre-Gate: Locks TDD interface and test suite, drafts implementation, repairs code based on QA feedback.<br>Post-Gate: Executes sandboxed tests. | Free Tier / Shared Gemini Key |
| **Tournament Competitors (Optional Mode)** | **Junior 1 vs. Junior 2** | **Groq (Llama 3.1 8B)** vs. **ZhipuAI (GLM-4-Flash)** | `ChatGroq` vs. `ChatOpenAI` | Synthesizes two competing codebases in parallel (Candidate A: Lean/StdLib vs. Candidate B: Modular/Defensive) for Senior Dev judging. | Free Tier / 100% Free |

### Critical Provider Environment Variables:
- `OPENROUTER_API_KEY`: Manager reasoning (`OPENROUTER_MODEL=anthropic/claude-3.5-sonnet`).
- `GEMINI_API_KEY`: Shared by Researcher (Search Grounding) and Antigravity SDK (`GEMINI_RESEARCHER_MODEL=gemini-2.5-flash`).
- `GROQ_API_KEY`: High-speed LPU code synthesis (`GROQ_MODEL=llama-3.3-70b-versatile` or `llama-3.1-8b-instant`).
- `ZHIPUAI_DEV_API_KEY` & `ZHIPUAI_QA_API_KEY` (or `ZHIPUAI_API_KEY`): Dedicated keys for GLM-4-Flash (`GLM_MODEL=glm-4-flash`).

---

## 4. State Schema & Lifecycle Contract

The entire multi-agent lifecycle is governed by a single strongly-typed state dictionary (`TriadCouncilState` in `src/ai_team/graph/state.py`), persisted across interrupts using SQLite (`SqliteSaver`):

```python
class TriadCouncilState(TypedDict, total=False):
    # --- Task & High-Level Metadata ---
    task_prompt: str                      # Original user objective
    triage_metadata: Optional[Dict[str, Any]] # Runtime flags (auto_allow_commands, prompt hooks)
    final_status_report: Optional[str]    # Executive closing report from Manager

    # --- Deliberative Council Phase ---
    manager_rfc: Optional[Dict[str, Any]]       # Architecture, assumptions, acceptance criteria
    researcher_audit: Optional[Dict[str, Any]]  # Verified search facts, citations, gotchas
    redteam_fmea: Optional[Dict[str, Any]]      # Failure modes, negative test requirements
    council_round: int                         # Iteration counter (incremented if steered)

    # --- TDD & Code Synthesis ---
    tdd_contract: Optional[Dict[str, str]]     # {"test_main.py": "..."} LOCKED before coding
    candidate_a: Optional[Dict[str, str]]      # Groq implementation draft
    candidate_b: Optional[Dict[str, str]]      # GLM-4-Flash implementation draft
    debate_verdict: Optional[str]              # Senior judge synthesis rationale
    synthesized_code: Optional[Dict[str, str]] # {"main.py": "...", "test_main.py": "..."}

    # --- Quality Assurance & Bounded Loops ---
    qa_passed: bool                            # True if AST valid and Maya approved
    qa_feedback: Optional[str]                 # Specific bug descriptions and failing lines
    repair_attempts: int                       # Current repair cycle count (max 2)

    # --- Human Steering Gate & Execution Bundle ---
    execution_bundle: Optional[Dict[str, Any]] # Complete preflight package (files, cmds, digest)
    approval_status: Optional[str]             # "PENDING" | "APPROVED" | "STEERED" | "ABORTED"
    human_feedback: Optional[str]              # Guidance string when operator chooses Steer

    # --- Sandboxed Execution & Evidence ---
    sandbox_result: Optional[Dict[str, Any]]   # exit_code, stdout, stderr, files_created
    last_failing_tests_count: int              # Extracted count of failing tests (0 if pass)
    patch_history_hashes: Annotated[List[str], operator.add] # Hash trail of applied patches
```

---

## 5. The LangGraph Execution Pipeline (Node by Node)

### Node 1: `manager_rfc_node` (`src/ai_team/graph/nodes/manager.py`)
- **Agent**: David (Manager).
- **Behavior**: Analyzes the raw user prompt. Generates a structured Request for Comments (RFC) specifying:
  - Technical approach & architecture.
  - Hard assumptions & library boundaries.
  - Measurable Acceptance Criteria.
  - Research directives for Elena.
- **Office Event**: Dispatches `AgentMoveEvent(agent_id="manager", to_node="desk_david")` and status `"Drafting Architectural RFC..."`.

### Node 2: `researcher_audit_node` (`src/ai_team/graph/nodes/researcher.py`)
- **Agent**: Elena (Researcher).
- **Behavior**: Uses Google Gemini 2.5 Flash with native Google Search Grounding to audit the Manager's proposed libraries. Detects version incompatibilities, deprecated APIs, and known gotchas.
- **Fallback**: If Gemini API is unavailable, falls back gracefully to Groq OSS models or standard curated Python best practices.
- **Office Event**: Dispatches `AgentMoveEvent(agent_id="researcher", to_node="desk_elena")` and status `"Grounding architecture with live search..."`.

### Node 3: `tdd_contract_node` (`src/ai_team/graph/nodes/tdd_contract.py`)
- **Agent**: Alex (Senior Dev / TDD Engineer).
- **Behavior**: Authors the formal test contract (`test_main.py`) *before* implementation begins. The test suite includes:
  - Strict input validation tests.
  - Core happy path business logic tests.
  - Adversarial negative tests (malformed input, edge values, type mismatches).
- **Inviolable Rule**: This test suite is frozen. The downstream developer node cannot alter tests to make broken code pass.

### Node 4: `developer_node` (`src/ai_team/graph/nodes/developer.py`)
- **Agent**: Alex (Developer).
- **Initial Pass (`repair_attempts == 0`)**: Reads `task_prompt` and `tdd_contract`. Generates a complete, self-contained Python implementation in `main.py` using Groq LPU (Llama 3.3 70B) for instant generation.
- **Repair Pass (`repair_attempts > 0`)**: Ingests previous broken `main.py` along with Maya's explicit `qa_feedback`. Generates surgical repairs.
- **AST Sanitation**: Automatically runs `extract_python_code` and `repair_truncated_python_code` to seal unclosed docstrings or code fences.

### Node 5: `qa_audit_node` (`src/ai_team/graph/nodes/qa_audit.py`)
- **Agent**: Maya (QA Auditor & Security Red-Teamer).
- **Step 1: Automated AST Syntax Check**: Deterministically parses `main.py` and `test_main.py` with Python's `ast.parse()`. If syntax is broken and cannot be auto-repaired, rejects immediately without wasting LLM tokens.
- **Step 2: Adversarial Audit (GLM-4-Flash)**: Prompts GLM-4-Flash to inspect code for:
  - Resource leaks, unclosed file descriptors.
  - Thread safety & race conditions.
  - Incomplete edge case handling.
- **Step 3: Bounded Router (`route_qa` in `builder.py`)**:
  - If `qa_passed == False` AND `repair_attempts < 2`: Routes back to `developer_node`.
  - If `qa_passed == True` OR `repair_attempts >= 2`: Advances to `preflight_gate_node`.

### Node 6: `preflight_gate_node` (`src/ai_team/graph/nodes/preflight.py`)
- **Agent**: David (Manager Quality Gate).
- **Behavior**: Packages all verified assets into an immutable `ExecutionBundle`:
  - `source_files`: `{"main.py": "..."}`
  - `test_files`: `{"test_main.py": "..."}`
  - `declared_commands`: `["python3 -m unittest test_main.py"]`
  - `workspace_path`: `.runs/<thread_id>/workspace`
  - `bundle_digest`: SHA-256 integrity hash calculated deterministically over files and commands.

### Node 7: `human_steering_gate_node` (`src/ai_team/graph/nodes/human_gate.py`)
- **Behavior**: Calls LangGraph's native `interrupt({ ... })`. The entire graph halts execution.
- **Whiteboard Broadcast**: Dispatches `WhiteboardGateEvent` to the 3D HUD, popping open the interactive review modal showing the task, code preview, QA findings, and SHA-256 digest.
- **Operator Options**:
  1. **`[y] Approve`**: Resumes graph (`Command(resume={"action": "approve"})`) -> routes to `sandbox_execution_node`.
  2. **`[s] Steer with Guidance`**: Operator enters natural language guidance -> routes back to `manager_rfc_node` (increments `council_round`).
  3. **`[n] Abort`**: Clean cancellation with zero side effects -> routes to `manager_final_report_node`.

### Node 8: `sandbox_execution_node` (`src/ai_team/graph/nodes/sandbox_exec.py`)
- **Prerequisite**: Strict check: `state["approval_status"] == "APPROVED"`. Throws `PermissionError` if bypassed.
- **Filesystem Write**: Autonomously writes `main.py` and `test_main.py` into `.runs/<thread_id>/workspace/`.
- **Command Whitelist Validation**: Only approved commands (e.g. `python3 -m unittest`, `pytest`, `python3 main.py`) are permitted. Any unlisted command (e.g. `rm -rf`, `curl`) triggers a Policy Block (exit code 126).
- **Execution & Streaming**: Runs tests in a separate subprocess with a 60-second timeout. Standard output and error streams are captured and broadcast live in real-time via `TerminalLogEvent` to the web HUD.
- **Outcome Assessment**: Parses real exit codes and test failure counts (`failures=N`).

### Node 9: `manager_final_report_node` (`src/ai_team/graph/nodes/manager.py`)
- **Agent**: David (Manager).
- **Behavior**: Synthesizes the authentic runtime evidence, execution output, file list, and verification status into a professional delivery report.
- **Office Event**: Dispatches `ProjectCompletedEvent` and moves all agents back to their default desks.

---

## 6. The Human Confirmation Gate: Inviolable Security Rules

> [!CAUTION]
> **DO NOT TOUCH OR BYPASS THE HUMAN CONFIRMATION GATE.**
> The boundary between "planning/reviewing code in text" and "executing code in the environment" is the central security guarantee of this system.

1. **No Silent Execution**: Under no circumstances should code be executed, files written outside memory, or shell commands invoked without explicit operator approval.
2. **Deterministic Integrity Digest**: Every `ExecutionBundle` has a canonical SHA-256 hash computed over all source files, test files, and declared commands. If a single character changes, the hash invalidates.
3. **Dual-Channel Interface**:
   - **CLI**: Suspends execution and prompts: `Enter decision ([y] Approve / [n] Abort / [s] Steer):`.
   - **Web HUD**: Suspends graph, opens `WhiteboardGateModal` via WebSocket, and waits for POST `/api/runs/{thread_id}/resume`.

---

## 7. 3D Virtual AI Office Architecture & Frontend Stack

The system includes a fully reactive, spatial multi-agent virtual office visualization.

### Backend Infrastructure (`src/ai_team/server.py`):
- **FastAPI ASGI Application**: Hosts REST endpoints and WebSocket stream `/ws/office`.
- **Spatial Event Bus (`src/ai_team/spatial/event_bus.py`)**: Thread-safe in-memory publish/subscribe event hub using `asyncio.Queue` per active connection.
- **Office Clock (`src/ai_team/spatial/office_clock.py`)**: Realistic office shift simulation. Tracks `WORKDAY` vs. `OFF_HOURS`. When shifts end, agents automatically clock out and walk to the exit waypoint.

### WebSocket Event Protocol:
```typescript
type OfficeEvent =
  | { event_type: "AGENT_MOVE"; agent_id: string; from_node: string; to_node: string; action: string }
  | { event_type: "AGENT_STATUS"; agent_id: string; status_text: string; animation: "Idle"|"Walk"|"Sit"|"Type"|"Coffee" }
  | { event_type: "WHITEBOARD_GATE"; thread_id: string; task: string; code_preview: string; qa_report: string; bundle_digest: string }
  | { event_type: "TERMINAL_LOG"; stream: "stdout"|"stderr"; chunk: string }
  | { event_type: "PROJECT_COMPLETED"; thread_id: string; success: bool; summary: string }
  | { event_type: "OFFICE_CLOCK"; phase: "WORKDAY"|"OFF_HOURS"; display_time: string; day_number: number; seconds_remaining: number };
```

### Frontend Stack (`frontend/`):
- **Framework**: React 18 with TypeScript, bundled by Vite.
- **Styling**: Tailwind CSS with custom HUD dark theme, Lucide icons.
- **State Management**: Zustand store (`frontend/src/store/officeStore.ts`) tracking agent positions, terminal logs, whiteboard modals, clock state, and active runs.
- **3D / 2D Canvas (`frontend/src/components/office/OfficeCanvas.tsx`)**:
  - Renders an isometric floor plan with designated zones: Manager Suite, Research Lab, Dev Bullpen, QA Desk, Conference Room, Breakroom, and Whiteboard.
  - Agents navigate dynamically along a pre-computed waypoint graph (`WaypointGraph.ts`).
  - Animated characters with distinct avatars, status indicators, and stateful speech bubbles.

---

## 8. Complete Project File Directory Structure

```
TriadCouncil/
├── AGENTS.md                   # Original project vision & constraints specification
├── KEYS_SETUP_GUIDE.md         # Step-by-step guide for acquiring free/paid API keys
├── README.md                   # High-level repo summary & quickstart commands
├── requirements.txt            # Python dependencies (LangGraph, FastAPI, etc.)
├── run_dev.py                  # Single-command launcher (Backend + frontend guidance)
├── run_server.py               # Standalone FastAPI server launcher (uvicorn)
├── .env.example                # Canonical template for all environment variables
│
├── docker/
│   └── sandbox.Dockerfile      # python:3.12-slim + pinned pytest; execution image
├── pyproject.toml              # Package metadata, deps, pytest config
│
├── docs/                       # Architectural records & specifications
│   ├── architecture.md         # Detailed LangGraph topology & node specifications
│   ├── backends.md             # Model evaluation & provider trade-offs
│   ├── decisions.md            # Architectural Decision Records (ADRs 001-005)
│   ├── state_machine.md        # State transition formalisms
│   └── phase_wise_plan.md      # Roadmap and development milestones
│
├── src/ai_team/                # Core Python backend package
│   ├── config.py               # Immutable AppConfig dataclass reading .env
│   ├── server.py               # FastAPI server, REST routes, WebSocket hub, ZIP export
│   ├── cli.py                  # CLI entrypoint for running tasks in terminal
│   ├── utils.py                # Code extraction, AST syntax validation, auto-repair
│   │
│   ├── domain/                 # Domain models & Pydantic contracts
│   │   ├── contracts.py        # TaskPlan, ExecutionBundle, OfficeEvent definitions
│   │   ├── budgets.py          # Operational resource ceilings (tokens, time, calls)
│   │   └── states.py           # State enum and terminal status classifications
│   │
│   ├── graph/                  # LangGraph StateGraph engine (the only pipeline)
│   │   ├── state.py            # TriadCouncilState TypedDict schema
│   │   ├── builder.py          # StateGraph wiring, edges, and the live routers
│   │   ├── gate_decision.py    # Fail-closed parsing of operator decisions
│   │   ├── contract_lock.py    # Test digest lock + vacuous-suite detection
│   │   └── nodes/              # StateGraph node implementations
│   │       ├── manager.py      # RFC formulation & final reporting
│   │       ├── researcher.py   # Groq dependency audit (NOT search-grounded)
│   │       ├── tdd_contract.py # Authors and freezes test_main.py
│   │       ├── developer.py    # Alex implementation; may only write main.py
│   │       ├── qa_audit.py     # Maya AST check & adversarial GLM audit
│   │       ├── preflight.py    # Bundle packaging & SHA-256 digest
│   │       ├── human_gate.py   # LangGraph interrupt() gate, side-effect free
│   │       └── sandbox_exec.py # Verify digest, write files, delegate to runner
│   │
│   ├── execution/              # Sandbox & workspace management
│   │   ├── bundle.py           # THE canonical digest: build / verify / compare
│   │   ├── workspace.py        # Path-confined atomic writes
│   │   ├── mock_sandbox.py     # Offline runner; not selectable as a backend
│   │   └── sandbox/            # Isolation backends behind one protocol
│   │       ├── base.py         # SandboxRunner protocol, SandboxResult, exit codes
│   │       ├── allowlist.py    # Exact-match command -> argv table
│   │       └── docker_runner.py# Locked-down `docker run`; refuses if unavailable
│   │
│   ├── _legacy/                # QUARANTINED. Not imported by live code.
│   │   ├── orchestration/      # Older parallel approval FSM
│   │   ├── routers.py          # References nodes that were never wired
│   │   ├── junior_dev.py       # Tournament mode
│   │   ├── senior_review.py    # Tournament judging
│   │   ├── redteam.py          # Standalone FMEA node
│   │   └── antigravity_dev.py  # Antigravity SDK adapter
│   │
│   ├── persistence/            # SQLite checkpoints & secret masking
│   │   ├── checkpointer.py     # SqliteSaver factory for graph suspension/resumption
│   │   ├── redaction.py        # Regex-based API key & credential masking in logs
│   │   └── runs.py             # Metadata logging and run manifest writer
│   │
│   ├── providers/              # LLM wrapper classes & client adapters
│   │   ├── antigravity_dev.py  # Google Antigravity SDK Agent adapter
│   │   ├── base.py             # Abstract base class for providers
│   │   └── mocks.py            # Offline synthetic mock responses for zero-cost tests
│   │
│   └── spatial/                # 3D Office simulation components
│       ├── event_bus.py        # Async WebSocket event broadcaster
│       ├── office_clock.py     # Simulated office workday clock & shift transitions
│       └── waypoints.py        # Spatial coordinates (desks, whiteboard, breakroom)
│
├── frontend/                   # 3D Virtual Office Web Client (React + Vite + TS)
│   ├── package.json            # Node dependencies (Lucide, Tailwind, Zustand)
│   ├── vite.config.ts          # Vite build config with backend proxy
│   ├── src/
│   │   ├── App.tsx             # Main layout, HUD dock, modals, canvas mount
│   │   ├── store/              # Zustand global state (officeStore.ts)
│   │   ├── hooks/              # useOfficeSocket.ts (WebSocket reconnection & dispatch)
│   │   ├── types/              # TypeScript mirror of Python event contracts
│   │   └── components/
│   │       ├── hud/            # TopBar, Sidebar, TerminalDock, WhiteboardGateModal, DeliveryReportModal
│   │       └── office/         # OfficeCanvas, AgentCharacter, WaypointGraph, OfficeLife
│   │
│   └── dist/                   # Production-compiled static frontend bundle
│
└── tests/
    ├── unit/                   # Gate decisions, contract lock, allowlist, digest,
    │                           #   docker argv, QA fail-closed, routing
    ├── integration/            # Real interrupt() suspend/resume through a
    │                           #   compiled graph with a checkpointer
    └── legacy/                 # Quarantined FSM tests; excluded by pytest.ini
```

---

## 9. REST API & WebSocket Endpoint Reference

The backend runs on `http://localhost:8000`:

These are the routes that actually exist in [`src/ai_team/server.py`](src/ai_team/server.py). The server binds **`127.0.0.1:8000`** by default.

| Endpoint | Method | Payload / Params | Description |
| :--- | :--- | :--- | :--- |
| `/api/health` | `GET` | None | Service status, whether the graph is compiled, and the active sandbox backend. |
| `/api/office/providers` | `GET` | None | Live per-role provider state and sandbox availability. This is the HUD's real telemetry source. |
| `/api/tasks/start` | `POST` | `{"task": "Build a CSV parser"}` | Starts a run. Returns `{"thread_id", "task", "status", "run_token"}`. The token is issued **once**. 409 during off-hours. |
| `/api/gate/respond` | `POST` | `{"thread_id", "action", "guidance"}` + `X-Run-Token` | Resumes the suspended graph. `action` is forwarded verbatim; the gate node interprets it and **fails closed** on anything unrecognized. 403 bad token, 404 unknown run, 409 if no gate is waiting. |
| `/api/runs/{thread_id}` | `GET` | `X-Run-Token` or `?token=` | Status, approval status, and sandbox exit code. |
| `/api/runs/{thread_id}/download` | `GET` | `X-Run-Token` or `?token=` | Streams a ZIP of that run's workspace. 404 if unknown — there is deliberately **no** fallback to another run's files. |
| `/ws/office` | `WebSocket` | N/A | Broadcasts all spatial and pipeline events. Never carries secrets or run tokens. |

Removed: `/api/task`, `/api/runs/{id}/resume`, `/api/office/state`,
`/api/office/clock`, and `/api/runs/download/latest`. The last of those
returned the newest workspace on disk, so any caller could obtain another run's
files.

---

## 10. Operational Guidelines: How to Run & Verify

### 1. Environment Configuration
Ensure `.env` exists in the project root with the appropriate keys:
```bash
cp .env.example .env
```
*(At minimum, `OPENROUTER_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, and `ZHIPUAI_DEV_API_KEY` should be populated. For offline testing, use the mock flags).*

### 2. Build the sandbox image (once)
Approved code runs only inside this container, never on the host:
```bash
docker build -t triadcouncil-sandbox:py312 -f docker/sandbox.Dockerfile docker/
```

### 3. Run the test suite
```bash
python3 -m pytest -q
```
The suite exercises the guarantees directly: real `interrupt()` suspend/resume,
refusal leaving the workspace empty, tampered bundles refused before any write,
command injection rejected, Docker absence never invoking host Python, contract
modification detected, and a rate-limited auditor never rendering as a pass.

`tests/legacy/` covers the quarantined orchestration FSM and is excluded from
the default run via `pytest.ini`.

### 3. Run via Headless CLI
```bash
# Live mode (calls real LLMs and executes approved code in sandbox)
python3 -m ai_team.cli "Build a Python function that converts CSV to JSON with row validation"

# Offline simulated mock mode (zero API calls, tests full LangGraph gate suspension)
python3 -m ai_team.cli --mock "Build a rate limiter"
```

### 4. Run the Fullstack 3D Virtual Office
```bash
# Terminal 1: Start Backend
python3 run_server.py

# Terminal 2: Start Frontend
cd frontend && npm run dev
```
Open your browser at `http://localhost:5173`. Enter a prompt in the top HUD bar, watch agents walk to the whiteboard and debate, review code in the Whiteboard Gate modal, and download the verified ZIP bundle upon completion.

---

## 11. Known Gotchas & Design Rules for Future AI Maintainers

1. **Antigravity SDK Key Convention**: The Google Antigravity SDK reads `GEMINI_API_KEY`. Never rename this environment variable to `ANTIGRAVITY_API_KEY`. (The adapter itself is quarantined in `src/ai_team/_legacy/`, but the constraint stands if it is ever revived.)
2. **`interrupt()` re-runs its node from the top on resume.** This is the single most common source of bugs here. A side effect placed *before* `interrupt()` fires again on every resume — which is exactly why the Whiteboard gate event was moved out of `human_gate.py` and into the server, after `stream()` halts. Keep the gate node side-effect free.
3. **`SqliteSaver.from_conn_string()` returns a context manager, not a saver.** Compiling the graph with the un-entered object silently breaks durable resume. Use `open_checkpointer()` and build the graph *inside* the context; the server does this in its FastAPI `lifespan`.
4. **Never repair or substitute a test file.** `utils.repair_truncated_python_code()` is for *implementation* code that was truncated mid-generation. Applying it, or any fallback, to `test_main.py` breaks the digest lock and destroys the contract. An invalid test suite must fail the run.
5. **Command allowlisting is exact-match, not prefix-match.** Prefix matching accepted `python3 -m unittest test_main.py; rm -rf /`. Add new commands as whole-string keys in `execution/sandbox/allowlist.py`, mapped to an argv list. Never reintroduce `shell=True`.
6. **No host environment reaches the container.** Only `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`, and `PYTHONPATH` are set. Do not add `-e` passthroughs; approved code must not be able to read provider keys.
7. **Failing closed is the rule everywhere.** A provider outage must never render as a pass, an approval, or a success. If a role is unavailable, say so and let the human decide.
8. **No Infinite QA Loops**: The repair cycle is bounded by `MAX_QA_REPAIR_CYCLES = 2`. Note that `repair_attempts` increments **only on a failed audit** — incrementing on success miscounted the budget. An *unavailable* auditor consumes no attempts, because there is no feedback to repair against.
9. **Never add a gate bypass.** No `--yes`, no trusted mode, no config option, no "skip if CI". If automation is ever needed it must be a separate, clearly-labelled binary, not a flag on the default path.
