# TriadCouncil: Comprehensive Engineering Handoff & Architecture Bible

> **Audience**: Any AI model (Claude, GPT, Gemini, DeepSeek), autonomous coding agent, or human engineer picking up this codebase.
> **Purpose**: Provide a complete, unambiguous mental model of TriadCouncil—its design philosophy, multi-agent LangGraph topology, provider matrix, human-in-the-loop safety boundaries, sandboxed execution runtime, and fullstack 3D Virtual AI Office HUD.

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
│   ├── graph/                  # LangGraph StateGraph engine
│   │   ├── state.py            # TriadCouncilState TypedDict schema
│   │   ├── builder.py          # StateGraph wiring, nodes, edges, conditional routers
│   │   └── nodes/              # StateGraph node implementations
│   │       ├── manager.py      # RFC formulation & final reporting
│   │       ├── researcher.py   # Gemini live search grounding
│   │       ├── tdd_contract.py # Frozen test harness authoring
│   │       ├── developer.py    # Alex implementation & iterative QA repair
│   │       ├── qa_audit.py     # Maya AST check & adversarial GLM-4-Flash audit
│   │       ├── preflight.py    # Bundle locking & SHA-256 digest creation
│   │       ├── human_gate.py   # LangGraph native interrupt() gate
│   │       ├── sandbox_exec.py # Subprocess file writing & command runner
│   │       ├── junior_dev.py   # Tournament candidate drafting
│   │       ├── senior_review.py# Tournament judging & hybrid code synthesis
│   │       └── redteam.py      # Dedicated adversarial FMEA authoring
│   │
│   ├── execution/              # Sandbox & Workspace management
│   │   ├── workspace.py        # Safe atomic file writes in .runs/<run_id>/workspace/
│   │   └── mock_sandbox.py     # Deterministic offline mock sandbox runner
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
└── tests/                      # Automated test suite (Unit & Integration)
    ├── unit/                   # Fast isolated unit tests (contracts, budgets, syntax)
    └── integration/            # Full LangGraph interrupt & mock pipeline integration tests
```

---

## 9. REST API & WebSocket Endpoint Reference

The backend runs on `http://localhost:8000`:

| Endpoint | Method | Payload / Params | Description |
| :--- | :--- | :--- | :--- |
| `/api/task` | `POST` | `{"task": "Build a CSV parser"}` | Initiates a new LangGraph pipeline run in background. Returns `{"run_id": "thread_..."}`. |
| `/api/runs/{run_id}/resume` | `POST` | `{"action": "approve" \| "steer" \| "abort", "guidance": "..."}` | Resumes a suspended graph from its exact SQLite checkpoint at the Human Gate. |
| `/api/runs/{run_id}` | `GET` | None | Returns the current state, approval status, and output of a specific run. |
| `/api/runs/{run_id}/download` | `GET` | None | Streams a **ZIP archive** containing all workspace files (`main.py`, `test_main.py`, manifests). |
| `/api/office/state` | `GET` | None | Returns active agents, desk assignments, and current simulated clock phase. |
| `/api/office/clock` | `GET` | None | Returns live snapshot of the simulated workday clock. |
| `/ws/office` | `WebSocket` | N/A | Full duplex persistent stream broadcasting all spatial and pipeline events. |

---

## 10. Operational Guidelines: How to Run & Verify

### 1. Environment Configuration
Ensure `.env` exists in the project root with the appropriate keys:
```bash
cp .env.example .env
```
*(At minimum, `OPENROUTER_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, and `ZHIPUAI_DEV_API_KEY` should be populated. For offline testing, use the mock flags).*

### 2. Run Automated Test Suite
The project maintains a 100% passing test suite across contracts, syntax guards, budgets, and LangGraph interrupt flows:
```bash
python3 -m pytest tests/ -v
```

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

1. **Antigravity SDK Key Convention**: The Google Antigravity SDK reads `GEMINI_API_KEY`. Never rename this environment variable to `ANTIGRAVITY_API_KEY`.
2. **LangGraph 0.2 `interrupt()` Behavior**:
   - The graph suspension relies on `langgraph.types.interrupt`.
   - When running under pytest, mock the interrupt or pass a custom `Command(resume=...)` to prevent blocking the test runner.
3. **AST Syntax Healing**: LLMs occasionally emit truncated code due to token limits. Always use `utils.repair_truncated_python_code()` before failing on a syntax check; it automatically appends missing quotes, parentheses, and indentation blocks.
4. **Command Whitelist Enforcement**: Never allow arbitrary shell commands in `sandbox_exec.py`. All commands must match approved prefixes (`python3 -m unittest`, `pytest`, `python3 main.py`).
5. **No Infinite QA Loops**: The QA repair cycle between Alex and Maya is strictly bounded by `MAX_QA_REPAIR_CYCLES = 2`. If Maya rejects the code twice, the system must not loop forever; it must package the current state and escalate directly to the Human Gate with Maya's audit notes.
