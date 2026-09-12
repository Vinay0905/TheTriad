# TriadCouncil: Architecture Decision Records (ADRs)

This document records the formal design decisions, alternatives considered, and trade-off evaluations governing the **TriadCouncil** architecture.

---

## ADR-001: Deliberative Council & Multi-Hypothesis Tournament Topology

### Status: Accepted

### Context
Single-path multi-agent pipelines (passing a task sequentially from agent 1 to agent 4) suffer from severe compounding error rates. If the initial planner makes an invalid assumption, or if the single code draft contains a fundamental flaw, subsequent stages merely optimize a broken concept.

### Decision
**Implement a Deliberative Council Topology with Multi-Hypothesis Tournament Drafting:**
1. **Council Deliberation & RFC**: The Manager posts an RFC which the Researcher (via live Google Search) and Senior Dev (via feasibility critique) challenge.
2. **Adversarial Red-Teaming**: The Council explicitly maps out failure modes (FMEA) and generates negative test cases before code generation.
3. **Dual-Hypothesis Tournament**: Junior Dev produces two competing implementations (Candidate A: Lean/StdLib vs. Candidate B: Modular/Robust). Senior Dev evaluates both against the TDD contract and synthesizes a hybrid solution.

### Rationale & Trade-offs
- *Anti-Fragility*: Exploring two orthogonal hypotheses prevents the team from getting trapped in a local minimum or single-model blind spot.
- *Shift-Left Failure Detection*: Red-teaming and live grounding uncover blockers during planning, rather than during runtime execution.
- *Cost / Latency Impact*: Groq generates 300–500 tokens/sec, meaning generating two candidate drafts in parallel adds less than 2 seconds of latency and negligible cost.

---

## ADR-002: Heterogeneous Model Specialization Across Council Roles

### Status: Accepted

### Context
Evaluating whether to standardize on a single provider (e.g. all Gemini or all Claude) vs. heterogeneous provider specialization.

### Decision
**Maintain strict provider heterogeneity mapped to functional strengths:**
- **Manager (OpenRouter)**: Frontier reasoning models (`claude-3.5-sonnet` / `deepseek-chat`) for synthesis, risk analysis, and customer reporting.
- **Researcher (Google GenAI)**: Gemini with native Google Search grounding for live web documentation and deprecation audits.
- **Junior Dev (Groq)**: High-speed LPU inference (`llama-3.1-8b-instant` / `llama-3.3-70b-versatile`) for rapid parallel candidate generation.
- **Senior Dev (Google Antigravity SDK)**: Gemini-powered coding agent with built-in capability gating and isolated workspace sandboxing.

### Rationale & Trade-offs
- *Avoids Monoculture Blindness*: Models from the same family frequently share systemic training set errors and stylistic biases. Cross-family review (e.g. Gemini reviewing Llama 3 code) surfaces bugs that homogeneous agents overlook.
- *Optimized Unit Economics*: Routine drafting uses low-cost, high-speed LPUs, reserving frontier reasoning and sandboxed execution for architectural decisions and verification.

---

## ADR-003: Contract-First TDD & Isolated Context Frames

### Status: Accepted

### Context
Multi-agent systems typically pass shared conversational transcripts between agents. This causes rapid context pollution, hallucinations, and token bloat.

### Decision
1. **Contract-First TDD**: Senior Dev locks `interfaces.py` and `test_suite.py` before any implementation code is authored. Junior Dev is prohibited from modifying tests.
2. **Isolated Context Frames**: Agents exchange schema-validated Pydantic payloads (`CouncilRFC`, `TDDContract`, `TournamentResult`, `ExecutionSummary`). Repair turns receive only the failing file, compiler traceback, and prior failure reason.

### Rationale & Trade-offs
- *Zero History Bleed*: Eliminates apologies, conversational pleasantries, and historical mistakes from accumulating in prompts.
- *Deterministic Ground Truth*: Test suite pass/fail status is the sole source of truth; models cannot "talk themselves into believing broken code works."

---

## ADR-004: Hierarchical Dual-Loop Resilience (Micro vs. Macro Loops)

### Status: Accepted

### Context
When code fails during runtime execution, systems either abort immediately or enter unconstrained retry loops that burn tokens without fixing root causes.

### Decision
**Adopt a Hierarchical Dual-Loop Architecture:**
1. **Micro-Loop (Local Sandbox Self-Healing)**:
   - Senior Dev iterates on syntax, imports, and failing unit tests within the sandbox.
   - Bounded to max **3 attempts**.
   - Enforces Monotonic Test Progress ($F_t \le F_{t-1}$) and AST Diff Cycle Detection.
2. **Macro-Loop (Architectural Back-Propagation)**:
   - If an unresolvable library incompatibility, OS roadblock, or structural design flaw is encountered, execution back-propagates to **Council Deliberation**.
   - The Council re-convenes with the post-mortem diagnostic to select alternative libraries or redesign interfaces.
   - Bounded to max **1 macro replan**, with re-presentation to the human steering gate.

### Rationale & Trade-offs
- *Real-World Developer Simulation*: Minor bugs are fixed locally in seconds; fundamental architectural dead-ends trigger team re-evaluation rather than stubborn, fruitless retries.
- *Transparency*: The human operator is kept informed of why a re-route occurred.

---

## ADR-005: Interactive Human Steering Gate (Beyond Binary Confirmation)

### Status: Accepted

### Context
`AGENTS.md` mandated a human confirmation gate before execution. A purely binary `[y/N]` prompt treats the human as a rubber stamp and forces a complete restart if the human wants a slight modification.

### Decision
**Upgrade the Confirmation Gate to an Interactive Steering Console:**
- `[y] Approve`: Commences sandboxed execution.
- `[n] Abort`: Clean, immediate termination with zero side effects.
- `[s] Steer with Guidance`: Allows the human to provide natural language constraints (e.g. *"Use pure stdlib, no pandas"*), routing immediately back into Council Deliberation.
- `[c] Compare Candidates`: Renders side-by-side diffs of Candidate A vs. Candidate B.

### Rationale & Trade-offs
- *Preserves Safety*: Execution remains 100% blocked until an explicit `y` is entered.
- *Empowers Human Agency*: The human can steer the architectural direction without having to kill the process and craft a whole new prompt.
