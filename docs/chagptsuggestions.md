# AI Team Planning Suggestions

## Executive recommendation

The project has a strong core idea: separate planning, research, drafting, review, and execution into explicit roles, then require a human decision before side effects occur. The main improvement needed is not adding more agents. It is making the plan more deterministic, auditable, and honest about what each stage guarantees.

The recommended direction is:

1. Build a small, reliable vertical slice first.
2. Make every role communicate through validated contracts.
3. Treat the human approval as approval of an immutable execution bundle.
4. Keep the Senior Dev execution backend behind a narrow adapter.
5. Add cyclic retries only after the single-pass path is proven.
6. Measure whether multiple agents improve outcomes before making the workflow more complex.

## 1. Clarify the product boundary

The current documents describe two related products:

- A multi-agent planning and code-review workflow.
- A governed coding agent that can write files and execute commands.

The second product is the riskier and more valuable part. The first can work with ordinary API clients; the second depends on tool permissions, workspace isolation, command policy, and reliable audit evidence.

The plan should explicitly define the MVP as:

> Given a natural-language task, produce a reviewed execution bundle, ask for approval, execute only that approved bundle in an isolated workspace, and report observed results.

This wording is better than promising that the agents “build software,” because it makes the evidence boundary clear: model output is a proposal; process output is verification.

## 2. Replace the current broad architecture with staged milestones

The proposed four-loop architecture is reasonable as a target design, but too much for the first implementation. Every loop introduces new failure modes, token cost, and state transitions before the basic safety contract has been proven.

### Recommended milestones

#### Milestone A: deterministic orchestration skeleton

Implement the state machine with fake providers and fixed fixture responses. Verify:

- every state transition;
- rejection at the human gate;
- no execution agent call after rejection;
- persistence of each transition;
- clean failure on malformed role output.

This milestone should run without any API keys.

#### Milestone B: provider adapters

Connect each role independently behind a common interface. Each adapter should expose one operation such as:

```text
Manager.plan(task) -> TaskPlan
Researcher.investigate(plan) -> ResearchFindings
JuniorDev.draft(plan, findings, contract) -> CodeDraft
SeniorDev.review(context) -> ReviewResult
SeniorDev.execute(bundle) -> ExecutionSummary
```

The orchestrator should not know whether a response came from OpenRouter, Groq, Gemini, or Antigravity.

#### Milestone C: one complete safe vertical slice

Use a deterministic task such as CSV-to-JSON conversion. Keep it deliberately boring:

- no network access;
- no package installation during execution;
- a fixed test command;
- a fresh run workspace;
- one execution attempt;
- no automatic repair yet.

This proves the real contract before adding orchestration sophistication.

#### Milestone D: bounded quality loops

Add one loop at a time:

1. Senior review revision.
2. Manager acceptance correction.
3. Sandbox repair.
4. Research follow-up.

Each loop should have its own budget, telemetry, and test coverage.

#### Milestone E: optimization and product polish

Only after the workflow is reliable should the project optimize latency, token usage, model routing, transcript compression, and user experience.

## 3. Make the execution bundle the central planning object

The design currently passes several independent payloads between roles. Add one explicit object that represents exactly what the user is approving.

```text
ExecutionBundle
├── task
├── assumptions
├── acceptance_criteria
├── source_files
├── test_files
├── declared_commands
├── workspace_policy
├── dependency_policy
├── risk_summary
└── bundle_digest
```

The bundle should be created only after review and preflight. The approval screen should display its digest. After the user enters `y`, the executor should verify that the bundle has not changed.

This solves several problems at once:

- The approved code cannot silently differ from the executed code.
- The command list is explicit rather than inferred from prose.
- The final report can identify exactly what was approved.
- Retries can be classified as either approved execution or a new proposal.

## 4. Strengthen the meaning of the human gate

The gate should be more than a yes/no prompt placed before an agent call. It should be a formal transition with a clear invariant:

> No state after `AWAITING_HUMAN_CONFIRMATION` may have write or command authority unless the recorded decision is affirmative and the approved bundle digest matches the execution bundle.

### Gate design

Before prompting, show:

- task summary;
- assumptions and unresolved risks;
- files to create or modify;
- complete file diff;
- tests to run;
- exact commands;
- workspace path;
- network and dependency policy;
- maximum execution time;
- approval digest.

Accept only `y` or `yes` as approval. Treat all other inputs, EOF, blank input, and interrupted input as rejection.

### Important policy decision

Post-approval repairs need a separate rule. The safest default is:

- Repairs may edit files inside the already-approved workspace.
- Repairs may not add new commands, dependencies, external network access, or new file categories without returning to the human gate.

If the repair needs any of those things, the run becomes a new proposal and must stop for approval.

## 5. Separate proposal authority from execution authority

The system should make it impossible for a model prompt alone to grant capabilities. Capabilities must come from the orchestrator and the current state.

Recommended capability profiles:

| Phase | Read files | Write files | Run commands | Network |
|---|---:|---:|---:|---:|
| Planning | No | No | No | No |
| Research | No local writes | No | No | Search only through research adapter |
| Drafting | No | No | No | No |
| Review | Optional controlled reads | No | No | No |
| Preflight | No | No | No | No |
| Approved execution | Workspace only | Workspace only | Declared commands only | Disabled by default |
| Repair | Workspace only | Workspace only | Previously declared commands only | Disabled by default |

For pre-gate Senior Dev review, disabling irrelevant tools is preferable to merely denying calls at runtime. The model should not see tools it is never allowed to use.

## 6. Rework the role responsibilities

### Manager

The Manager should not be a generic “smart reviewer.” Its outputs should be deterministic planning artifacts:

- task interpretation;
- assumptions;
- acceptance criteria;
- scope exclusions;
- research questions;
- risk classification;
- approval recommendation.

The Manager should not approve based on confidence or prose quality. It should check criteria coverage and contract validity.

### Researcher

The Researcher should be invoked selectively. Not every task needs web research. Add a planning decision:

```text
research_required: true | false
research_reason: string
```

For local, deterministic tasks, unnecessary grounding adds latency and citation noise. For dependency, API, security, legal, current-product, or version-sensitive tasks, research should be mandatory.

Research findings should distinguish:

- verified fact;
- source interpretation;
- recommendation;
- unresolved uncertainty.

The Researcher must never be treated as an authority to execute commands. Retrieved pages and search results are untrusted input.

### Junior Dev

The Junior Dev should optimize for a useful first draft, not “production-ready” output. Its contract should require:

- source files only;
- implementation notes;
- known limitations;
- assumptions made;
- no claim that tests passed.

It should not generate or modify acceptance criteria. This keeps the junior role from redefining success to match its own implementation.

### Senior Dev

Split this role into two explicit capabilities:

- `SeniorReviewer`: read-only analysis and finalized proposal generation.
- `SeniorExecutor`: approved-bundle execution and evidence capture.

They may use the same model backend, but they should be different adapter methods, configurations, and state transitions. Avoid relying on the model to remember whether it is currently in review or execution mode.

### Final reporting

The final report should be generated from structured execution evidence first, with the Manager adding interpretation second. It should label each statement as one of:

- observed;
- model-reported;
- inferred;
- unresolved.

This prevents a model from turning an intended test command into a false statement that the test passed.

## 7. Improve the state machine

The existing state machine is a good conceptual start, but it should add explicit failure states and invariants.

### Suggested states

```text
RECEIVED
  -> PLANNING
  -> RESEARCHING or RESEARCH_SKIPPED
  -> CONTRACTING
  -> DRAFTING
  -> REVIEWING
  -> PREFLIGHT
  -> BUNDLE_LOCKED
  -> AWAITING_APPROVAL
  -> ABORTED or EXECUTING
  -> VERIFYING
  -> REPAIRING or REPORTING
  -> SUCCEEDED / FAILED / BLOCKED
```

Add these explicit terminal outcomes:

- `ABORTED`: human declined or input was not affirmative;
- `BLOCKED`: safe execution was impossible, such as sandbox unavailable;
- `FAILED`: approved execution ran and failed;
- `SUCCEEDED`: approved execution produced passing evidence;
- `INVALID`: an upstream contract could not be validated.

### State invariants

- No pre-approval state can write files or run commands.
- No execution can start without a locked bundle.
- Every transition has a timestamp, run ID, actor, input digest, and output snapshot.
- Every retry consumes a finite budget.
- A failed safety check cannot be converted into success by a model response.
- Any material bundle change invalidates approval.

## 8. Simplify the first retry strategy

The current plans contain several bounded loops, but bounds alone do not make retries safe. Define what each retry is allowed to change.

| Retry type | Allowed change | Requires new human approval? |
|---|---|---:|
| Parse retry | Output formatting only | No |
| Review revision | Proposed source/tests | Yes if bundle changes after approval; no before approval |
| Test repair | Approved workspace files | No, if commands and scope remain unchanged |
| Dependency change | Package files or install commands | Yes |
| Command change | Test/build/runtime commands | Yes |
| Network requirement | Any outbound access | Yes |

Do not use a generic “self-healing” loop. A model may interpret self-healing as permission to broaden scope, install tools, remove tests, or weaken assertions.

## 9. Make testing part of the plan, not an afterthought

The definition of done should be divided into deterministic tests and live integration tests.

### Deterministic unit tests

- schema validation;
- state transition guards;
- digest calculation;
- approval input handling;
- command manifest validation;
- path confinement;
- retry budgets;
- patch-cycle detection;
- redaction of secrets;
- persistence failure handling.

### Mocked orchestration tests

- happy path;
- researcher skipped;
- malformed Manager output;
- malformed Researcher citations;
- Junior output rejected by schema;
- Senior review blocking issue;
- preflight failure;
- human rejection;
- bundle tampering;
- executor timeout;
- failed repair budget;
- successful final report.

### Live smoke tests

Use opt-in tests that require API keys:

- one call per provider;
- one grounded research call;
- one read-only Antigravity session;
- one explicitly sandboxed command;
- one end-to-end CSV-to-JSON task.

Live tests should never run automatically as part of import, installation, or ordinary unit-test execution.

## 10. Treat persistence as an audit system

The proposed `.runs/` directory is useful, but define retention and redaction rules before implementing it.

Persist:

- run metadata;
- selected model IDs and package versions;
- state transitions;
- normalized role outputs;
- citations;
- bundle digest;
- human decision and timestamp;
- command, exit code, stdout, stderr;
- file manifest and final status.

Do not persist by default:

- API keys;
- the complete process environment;
- credentials embedded in generated text;
- unbounded raw provider responses;
- sensitive task data without an explicit policy.

Use atomic writes so an interrupted run leaves a readable partial audit rather than corrupt JSON. Add a schema version to every persisted record.

## 11. Add explicit operational budgets

The plan should define budgets before the first API call:

- maximum wall-clock duration;
- maximum provider calls per role;
- maximum total tokens;
- maximum sandbox attempts;
- maximum command duration;
- maximum generated file size;
- maximum output size stored in the audit trail;
- maximum workspace disk usage.

The orchestrator, not the model, should enforce these budgets. When a budget is exhausted, the run should become `BLOCKED` or `FAILED` with a clear reason.

## 12. Improve model and provider resilience

Model IDs should be configurable, but configuration alone is not enough. Add:

- startup validation against provider model lists where available;
- a display of active model IDs in the run metadata;
- provider-specific timeout and retry policies;
- exponential backoff for transient failures;
- no blind retries for authentication, policy, or malformed-request errors;
- a provider adapter contract that normalizes text, structured output, citations, and usage.

Do not let a provider fallback silently change the role’s expected behavior. Record every fallback in the audit trail and include it in the final report.

## 13. Reduce prompt and context risk

Flattened summaries are preferable to an unrestricted transcript, but the summaries should be structured and loss-aware. Add a compact context envelope:

```text
ContextEnvelope
├── task_id
├── source_stage
├── schema_version
├── facts
├── decisions
├── unresolved_questions
├── prohibited_assumptions
└── source_digest
```

Every downstream role should know what it is allowed to rely on. For example, Researcher findings should not be silently converted into requirements, and Junior implementation notes should not be treated as test evidence.

For long tasks, preserve the full artifacts on disk but pass only the relevant structured subset to the next role.

## 14. Add security planning before feature expansion

The system is an execution agent, so its threat model matters more than ordinary CLI tooling.

Plan for:

- prompt injection in user tasks, repository files, and web pages;
- malicious generated shell commands;
- path traversal and symlink escape;
- environment-variable exfiltration;
- network access from generated programs;
- dependency-install attacks;
- denial of service through huge files or infinite processes;
- secrets accidentally copied into `.runs/`;
- model attempts to disable or rewrite tests.

The minimum safe default is:

- fresh workspace per run;
- no host-project writes until successful completion is explicitly copied or reviewed;
- no network during execution;
- no dependency installation unless declared and approved;
- filtered environment;
- command allowlist or command manifest;
- process timeout and resource limits;
- symlink and path validation;
- fail closed if the sandbox cannot be confirmed.

## 15. Reconsider TDD contract generation

The architecture proposes that the Senior Dev creates interfaces and tests before the Junior Dev implements them. This is useful, but it creates a subtle risk: the tests become an unapproved interpretation of the user’s request.

Improve the order:

1. Manager defines acceptance criteria in plain language.
2. Senior Dev translates them into a test contract.
3. Manager checks that the test contract covers the criteria.
4. Only then does Junior Dev implement.

The Manager should not need to inspect every line of test code, but it should receive a coverage matrix:

| Acceptance criterion | Test ID | Covered? | Notes |
|---|---|---:|---|
| Converts valid CSV | `test_valid_csv` | Yes | Main path |
| Handles empty input | `test_empty_csv` | Yes | Defined behavior |
| Rejects malformed rows | `test_bad_row` | Yes | Error contract |

This makes “100% acceptance criteria coverage” measurable rather than rhetorical.

## 16. Define what success means for arbitrary tasks

“Exit code 0” is necessary but not sufficient. A program can exit successfully while producing the wrong result or no result.

The execution contract should include:

- commands;
- expected exit codes;
- expected artifacts;
- assertions over output where practical;
- test count and pass count;
- file manifest;
- optional domain-specific validation.

The final status should distinguish:

- process success;
- test success;
- artifact validation success;
- acceptance-criteria coverage.

## 17. Recommended project structure

When implementation begins, organize around boundaries rather than provider names:

```text
src/ai_team/
├── domain/
│   ├── contracts.py
│   ├── states.py
│   └── policies.py
├── orchestration/
│   ├── state_machine.py
│   ├── budgets.py
│   └── approval.py
├── providers/
│   ├── manager.py
│   ├── researcher.py
│   ├── junior_dev.py
│   └── antigravity_dev.py
├── execution/
│   ├── workspace.py
│   ├── command_manifest.py
│   ├── sandbox.py
│   └── evidence.py
├── persistence/
│   ├── runs.py
│   └── redaction.py
└── cli.py
```

The most important boundary is `execution/`. No provider adapter should be able to bypass its workspace, command, timeout, and evidence controls.

## 18. Decisions that should be made now

Resolve these before implementation:

1. Does execution modify the user’s project directly, or only a fresh run workspace?
2. Are network access and package installation ever allowed?
3. Can a post-approval repair change tests, or only source files?
4. What exact artifact changes require a new approval?
5. Which tasks are in MVP scope: local scripts only, or existing repositories too?
6. Is the Researcher mandatory for every task or conditional?
7. What happens when the sandbox backend is unavailable?
8. How long are `.runs/` artifacts retained?
9. What is the maximum per-run cost and duration?
10. Does the system report partial success, or only success/failure/blocked?

The most important answer is the first one. Directly modifying the user’s project substantially increases the safety and rollback burden. A per-run workspace should be the MVP default.

## 19. Suggested revised definition of done

The MVP is complete when:

- all role adapters can be mocked independently;
- live provider calls are isolated behind configuration;
- every role response is schema-validated;
- the pipeline reaches a stable execution bundle;
- the approval prompt displays the exact bundle digest;
- rejection performs no writes and never invokes the executor;
- approval invokes only the executor with the matching digest;
- execution is confined to a fresh workspace with verified sandboxing;
- commands, exit codes, outputs, and file changes are recorded;
- failures are reported as failures or blocked runs, never inferred successes;
- the CSV-to-JSON fixture passes end to end;
- the same fixture proves the rejection path;
- stale model IDs and unavailable providers produce actionable diagnostics;
- the README explains setup, permissions, limitations, and safety boundaries.

Automatic repair, multiple revision loops, transcript optimization, and provider failover should be explicitly outside the first MVP unless the vertical slice is already reliable.

## Final assessment

The project should proceed, but the plan should become narrower and more contract-driven. The strongest differentiator is not that four models collaborate; it is that the system can show a person exactly what will happen, obtain explicit approval, execute within a verified boundary, and prove what actually happened.

Prioritize that evidence chain over additional role complexity. Once it is reliable, the proposed research loop, review loop, and repair loop become valuable extensions. Before that point, they mainly increase the number of places where the system can appear intelligent without being trustworthy.
