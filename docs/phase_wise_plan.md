# TriadCouncil 3D: Phase-Wise Development Plan

This document establishes the official development phases, scope boundaries, technical deliverables, and exit criteria for the **Visual Multi-Agent AI Office** simulation.

---

## Overview of Phases

```
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: MVP VERTICAL SLICE (Immediate Focus)                           │
│ • Single 3D Office Room (R3F + Three.js + Tailwind)                     │
│ • 4 Core Agents: Manager, Researcher, Developer, QA Auditor (GLM)       │
│ • Bounded QA Feedback Loop (Max 2 repair iterations)                    │
│ • Single Human Steering Gate at the Approval Boundary                   │
│ • Whitelisted Sandboxed Code Execution with Live Terminal Stream        │
│ • Static Waypoint Graph Navigation (No broken NavMeshes)                │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ Validated End-to-End Loop
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: COLLABORATIVE LIFE & INTERACTION                               │
│ • Conference Room Meetings with multi-agent group dialogue              │
│ • Direct User-to-Employee Chat ("Why did you choose this library?")     │
│ • Realistic Office Ambience ("Thinking..." badges, Rate-limit Coffee)   │
│ • Token Usage, Model Telemetry & Cost Dashboard                         │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ Production Hardening
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: EXPANSION & ADVANCED AUTONOMY                                  │
│ • Multi-Department Office Floor (Dev, Security, Design, Product)        │
│ • Docker Container Isolation for True Multi-Tenant Sandboxing           │
│ • Configurable Role Builder (Custom agents & system instructions)       │
│ • Long-Running Task Queues & Historical Replay Scrubbing                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: MVP Vertical Slice

### Objective
Prove the entire core value proposition end-to-end with zero synthetic fluff:
1. An objective is submitted.
2. 4 real LLM agents (OpenRouter, Gemini Search, Groq, GLM-4.7-Flash) perform real research, code authoring, and adversarial QA review with a strictly bounded cycle (max 2 retries).
3. The 3D virtual office visualizes character movements, typing, and status changes in real-time.
4. Execution stops at a single Human Gate at the Whiteboard.
5. On approval, real code is written and executed in `.runs/run_<id>/workspace` with unit tests streaming live terminal logs.

### Technical Deliverables

#### 1. Backend (`src/ai_team/`)
- **FastAPI Core (`server.py`)**:
  - REST endpoints: `POST /api/tasks/start`, `POST /api/gate/respond`, `GET /api/status`.
  - WebSocket hub: `ws://localhost:8000/ws/office` with heartbeat and event replaying.
- **Linear Orchestrator with Bounded Iteration (`orchestration/graph.py`)**:
  - Node 1: `manager_rfc_node` (OpenRouter Claude/DeepSeek).
  - Node 2: `researcher_audit_node` (Gemini 2.5 Flash with live Google Search).
  - Node 3: `developer_draft_node` (Groq / Gemini Flash).
  - Node 4: `qa_audit_node` (GLM-4.7-Flash, 100% Free).
  - Conditional Edge: If QA flags critical bugs and `repair_attempts < 2`, route back to Developer with specific failing assertions; otherwise advance to Gate.
  - Node 5: `human_steering_gate_node` (LangGraph `interrupt()`).
  - Node 6: `sandbox_exec_node` (Whitelisted local runner).
- **Append-Only Event Store (`persistence/events.py`)**:
  - SQLite table: `events(id INTEGER PRIMARY KEY, timestamp TEXT, event_type TEXT, payload JSON)`.
- **Spatial Action Translator (`spatial/translator.py`)**:
  - Maps agent state transitions to 3D waypoint destinations:
    - Manager: `desk_manager` (0, 0, -3), `whiteboard` (0, 0, -6).
    - Researcher: `desk_researcher` (-4, 0, -2).
    - Developer: `desk_developer` (4, 0, -2).
    - QA Auditor: `desk_qa` (4, 0, 1).
    - Break Lounge: `coffee_couch` (-4, 0, 3).

#### 2. Frontend (`frontend/`)
- **3D Canvas (`OfficeCanvas.tsx`)**:
  - React Three Fiber + Drei + Three.js.
  - Elevated isometric camera with smooth tweening.
  - Directional light with soft PCF shadows + warm ambient fill.
  - Modern office layout: 4 desks, monitors with screen glow, chairs, whiteboard, potted plants.
- **3D Character Controller (`AgentModel.tsx`)**:
  - Mixamo pre-rigged stylized humanoids.
  - Blended skeletal animations: `Idle`, `Walk`, `Sit`, `Type`, `Coffee`.
  - Static 2D Waypoint Navigator with linear A* interpolation.
  - Overhead status badges: `"Thinking..."`, `"Writing Code"`, `"Reviewing"`, `"Rate Limited ☕"`.
- **2D HUD & Dossier Panels (`hud/`)**:
  - Sidebar: Department & employee list with live status indicators.
  - Agent Dossier: Slide-out drawer when clicking an employee in 3D or sidebar.
  - Whiteboard Gate Modal: Renders when `interrupt()` triggers, showing code diffs with `[Approve]`, `[Abort]`, `[Steer]` buttons.
  - Terminal Dock: Collapsible bottom drawer streaming live stdout/stderr from test runs.

### Exit Criteria for Phase 1
- [ ] Submitting *"Build a thread-safe LRU Cache with TTL"* runs all 4 agents.
- [ ] Researcher Elena triggers real Google Search Grounding.
- [ ] QA Maya (GLM-4.7-Flash) audits code and executes max 2 repair turns if needed.
- [ ] 3D characters physically walk between desks and sit/type without clipping or sliding.
- [ ] Process halts at Whiteboard modal until user clicks `[Approve]`.
- [ ] Real `python3 -m unittest` executes in `.runs/run_<id>/workspace` and outputs genuine PASS/FAIL.

---

## Phase 2: Collaborative Life & Interaction

### Objective
Transform the office from a linear pipeline visualizer into a living, interactive virtual workplace.

### Technical Deliverables
- **Conference Room Group Meetings**:
  - Manager calls an architecture review meeting.
  - All 4 characters stand up, walk into the conference room, and sit around the table.
  - Multi-agent turn-taking generates a structured meeting transcript visible in the HUD.
- **Direct User-to-Employee Chat**:
  - Click any character (e.g. Alex the Developer) and ask: *"Why did you use `threading.RLock` instead of a primitive Lock?"*
  - Character looks up from computer, plays `Talk` gesture, and responds using active project working memory.
- **Office Ambience & Realistic Cooldowns**:
  - When an API returns HTTP 429 (rate limit), character powers down laptop, walks to the lounge, and sips coffee until the cooldown timer expires.
- **Token & Cost Telemetry Dock**:
  - Real-time tracking of tokens used, estimated cost per provider, and execution latency.

---

## Phase 3: Scaling & Enterprise Sandboxing

### Objective
Expand into multiple departments, advanced role customization, and multi-tenant security isolation.

### Technical Deliverables
- **Docker Container Sandboxing**:
  - Replace local subprocess execution with isolated Docker containers (`gVisor` / `cgroups` memory/CPU caps, zero network access).
- **Dynamic Role Builder**:
  - UI modal to hire new agents: define name, avatar, model provider, system prompt, and tool permissions.
- **Multi-Department Office Floors**:
  - Switch between Engineering, Security, Design, and Product zones.
- **Event Replay & Time Scrubbing**:
  - Rewind and fast-forward through previous project runs with exact 3D character replay.
