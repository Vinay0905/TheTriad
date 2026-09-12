# TriadCouncil

An auditable multi-agent TDD pipeline with a fail-closed human approval gate.

Four roles on four different model providers write a frozen test suite, implement
against it, audit the result, and then **stop**. Nothing is written to disk and
nothing is executed until a human approves a specific, hash-locked payload. On
approval, the code runs inside a locked-down Docker container and the pipeline
reports the real exit code.

The design goal is that the pipeline cannot lie to you. Every claim it makes is
either backed by evidence or reported as unavailable.

---

## What is actually wired

Only the compiled LangGraph graph in
[`src/ai_team/graph/builder.py`](src/ai_team/graph/builder.py) runs. It is the
single source of truth.

```
START
  -> manager_rfc_node          (OpenRouter)  architecture + acceptance criteria
  -> researcher_audit_node     (Groq)        dependency and concurrency audit
  -> tdd_contract_node         (Groq/OpenRouter) writes and FREEZES test_main.py
       |                                          invalid contract -> final report
  -> developer_node            (Groq -> Gemini -> OpenRouter) writes main.py only
  -> qa_audit_node             (ZhipuAI GLM) AST gate + adversarial review
       |  failed, budget left -> developer_node (max 2 repairs)
  -> preflight_gate_node                     packages bundle + SHA-256 digest
  -> human_steering_gate_node                LangGraph interrupt(); graph halts
       |  approve -> sandbox_execution_node  (Docker)
       |  steer   -> manager_rfc_node        (gate re-opens later)
       |  abort   -> final report            (nothing written, nothing run)
  -> manager_final_report_node
END
```

| Role | Provider | Responsibility |
| :--- | :--- | :--- |
| **David** (Manager) | OpenRouter | RFC, acceptance criteria, final report |
| **Elena** (Researcher) | Groq | Dependency / concurrency audit |
| **Alex** (Developer) | Groq, falling back to Gemini then OpenRouter | Frozen test contract, then `main.py` |
| **Maya** (QA) | ZhipuAI GLM-4-Flash | AST syntax gate + adversarial audit |

> **Note on the Researcher.** Elena runs on Groq and reasons from model
> knowledge. She does **not** perform live web search, and her references are
> labelled unverified. Earlier docs claimed Gemini Google Search grounding;
> that was never implemented. Wiring it is tracked as future work.

Not wired, kept for reference in [`src/ai_team/_legacy/`](src/ai_team/_legacy/):
the tournament nodes, the Antigravity adapter, an older approval state machine,
and an unused router module.

---

## The three guarantees

**1. The gate fails closed.** Approval requires an explicit `y` / `yes` /
`approve`. Every other input — a typo, a malformed payload, a truthy `True`, a
missing key, an unexpected exception, even a missing `interrupt` import —
resolves to abort. See
[`gate_decision.py`](src/ai_team/graph/gate_decision.py) and its tests.

**2. The test contract is frozen cryptographically.** `tdd_contract_node`
records a SHA-256 of `test_main.py`, and every node downstream re-verifies it
before acting. The developer node's output is filtered so it can only write
`main.py`. A suite that cannot fail — an existence check like
`assertTrue(hasattr(main, '__name__'))` — is rejected outright and fails the
run rather than being substituted. See
[`contract_lock.py`](src/ai_team/graph/contract_lock.py).

**3. Execution is isolated, or refused.** Approved code runs via
`docker run` with `--network=none`, `--read-only`, `--cap-drop ALL`,
`--security-opt no-new-privileges`, a non-root user, and bounded CPU, memory,
and pids. **No host environment is forwarded**, so no API key is visible to the
code being run. Commands are matched against an exact-string allowlist and
executed as argv with no shell. If Docker is missing, the run is refused — there
is no host fallback. See [`execution/sandbox/`](src/ai_team/execution/sandbox/).

There is no flag, config option, or "trusted mode" that skips the gate, and
none may be added.

---

## Setup

Requires Python 3.11+ and Docker.

```bash
pip install -r requirements.txt          # or: pip install -e ".[dev]"
cp .env.example .env                     # then fill in your keys

# Build the sandbox image once. Approved code runs here, never on the host.
docker build -t triadcouncil-sandbox:py312 -f docker/sandbox.Dockerfile docker/
```

### API keys

All four providers have a free tier. See
[KEYS_SETUP_GUIDE.md](KEYS_SETUP_GUIDE.md) for click-by-click instructions.

| Variable | Used by | Where to get it | Cost |
| :--- | :--- | :--- | :--- |
| `OPENROUTER_API_KEY` | Manager | [openrouter.ai/keys](https://openrouter.ai/keys) | Pay-as-you-go |
| `GROQ_API_KEY` | Developer, Researcher, TDD | [console.groq.com/keys](https://console.groq.com/keys) | Free tier |
| `ZHIPUAI_QA_API_KEY` | QA auditor | [bigmodel.cn](https://bigmodel.cn) | Free |
| `GEMINI_API_KEY` | Developer fallback | [aistudio.google.com](https://aistudio.google.com/app/api-keys) | Free tier |

Each role degrades independently. A missing key does not fabricate a result: a
missing auditor reports `QA unavailable`, and a missing developer provider
reports no implementation, which then fails QA.

---

## Running

### CLI

```bash
python3 -m ai_team.cli "Build a Python function that converts CSV to JSON with row validation"
```

The graph streams each node, then halts at the gate and prints the bundle: the
task, the digest, QA status, the files to be written, which model produced each
artifact, and the exact commands to be run. Then:

- `y` writes the files and runs the tests in Docker.
- `s` sends guidance back to the council; the gate re-opens afterwards.
- `n`, or anything unrecognized, aborts with nothing written.

Exit code is `0` only if the run was approved **and** the tests passed.

`--mock` clears all provider credentials to exercise the gate and routing
offline. It is not a demo mode: with no providers the contract cannot be
authored, so the run halts honestly before implementation.

### Web HUD

```bash
python3 run_server.py                    # binds 127.0.0.1:8000 by default
cd frontend && npm run dev               # http://localhost:5173
```

> **Frontend status.** The backend safety work landed ahead of the frontend.
> Per-run tokens are not yet plumbed through the UI, and the download endpoint's
> insecure "newest run on disk" fallback has been removed, so the TopBar
> download link returns 404 until that pass lands. The CLI is the fully wired
> path today.

---

## Tests

```bash
python3 -m pytest -q
```

The suite covers what the guarantees claim: the gate suspending and resuming
through a real `interrupt()`, refusal leaving the workspace empty, a tampered
bundle being refused before any write, command injection being rejected, Docker
absence never invoking host Python, contract modification being detected, and a
rate-limited auditor never rendering as a pass.

`tests/legacy/` covers the quarantined state machine and is excluded by default.

---

## Configuration

Beyond the keys above, everything is env-overridable; see
[`config.py`](src/ai_team/config.py). The ones that matter most:

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `AI_TEAM_SERVER_HOST` | `127.0.0.1` | Loopback by default; this is a single-operator cockpit |
| `AI_TEAM_SANDBOX` | `docker` | Isolation backend behind the `SandboxRunner` seam |
| `AI_TEAM_SANDBOX_IMAGE` | `triadcouncil-sandbox:py312` | Image approved code runs in |
| `AI_TEAM_SANDBOX_UID` | `65534:65534` | Container user; adjust if bind-mount writes fail |
| `AI_TEAM_EXECUTION_TIMEOUT_SECONDS` | `120` | Container is killed past this |
| `AI_TEAM_SERVER_RELOAD` | `0` | Uvicorn reloader off by default |

Model IDs drift, so they are never hardcoded inline — override
`OPENROUTER_MODEL`, `GROQ_MODEL`, `GLM_MODEL`, or
`GEMINI_RESEARCHER_MODEL` without touching code.

---

## Further reading

- [HANDOFF.md](HANDOFF.md) — architecture detail and the live API surface
- [AGENTS.md](AGENTS.md) — original project vision and hard constraints
