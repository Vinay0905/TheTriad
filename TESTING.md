# Testing TriadCouncil on macOS

A walkthrough from a clean Mac to a completed run, including what the UI
should look like at each step so you can tell me where reality differs.

> **Read this first.** I wrote all of this code but ran none of it: this
> machine has no Python dependencies, no Node, and no Docker. `compileall`,
> the linters, an import-resolution audit (340 internal imports), and a
> numeric check of the office layout (31 slots, 30 routes) all pass, but
> nothing has executed. Expect a few first-run fixes. The section
> "If something breaks" at the end tells you what to send me.

---

## 1. Install the prerequisites

```bash
# Homebrew, if you don't already have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install python@3.12 node
brew install --cask docker
```

Then **launch Docker Desktop from Applications and wait for the whale icon in
the menu bar to stop animating.** The daemon must be running; the CLI alone is
not enough.

Verify all three:

```bash
python3 --version     # expect 3.11 or newer
node --version        # expect 18 or newer
docker version        # must print a "Server:" section, not just "Client:"
```

If `docker version` shows only a Client section, Docker Desktop is not running
yet. This matters: the pipeline **refuses to execute** rather than falling back
to running generated code on your Mac.

---

## 2. Get the project set up

```bash
cd /path/to/TheTriad

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

Build the sandbox image once. Approved code only ever runs inside this
container, never on your machine:

```bash
docker build -t triadcouncil-sandbox:py312 -f docker/sandbox.Dockerfile docker/
```

That takes a minute or two on first run. Confirm it exists:

```bash
docker image inspect triadcouncil-sandbox:py312 > /dev/null && echo "sandbox image OK"
```

Frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

---

## 3. API keys

```bash
cp .env.example .env
```

Then open `.env` and fill in the keys below. **You do not need all four.** Each
role degrades independently and says so rather than pretending: a missing
auditor reports "QA unavailable", and a missing developer provider reports that
no implementation was produced.

| Variable | Role | Where to get it | Notes |
| :--- | :--- | :--- | :--- |
| `GROQ_API_KEY` | Alex (developer), Elena (research), test contract | [console.groq.com/keys](https://console.groq.com/keys) | **Start here.** Free, instant, and covers the most roles. |
| `ZHIPUAI_QA_API_KEY` | Maya (QA auditor) | [bigmodel.cn](https://bigmodel.cn) | GLM-4-Flash is free. Needs a phone number. |
| `OPENROUTER_API_KEY` | David (manager) | [openrouter.ai/keys](https://openrouter.ai/keys) | Paid per token; a dollar goes a long way. |
| `GEMINI_API_KEY` | Developer fallback | [aistudio.google.com](https://aistudio.google.com/app/api-keys) | Free tier. Optional. |

**Minimum viable setup:** just `GROQ_API_KEY`. You will get a real frozen test
contract, a real implementation, real sandbox execution, and the gate. David's
RFC will fall back to labelled project defaults, and Maya will report
`QA UNAVAILABLE` at the gate. That is the system being honest, not broken.

**Recommended:** `GROQ_API_KEY` + `ZHIPUAI_QA_API_KEY`. That gives you a real
adversarial audit, so you can see `QA PASS` and the repair loop.

A useful optional tweak — a second Groq key so the test-contract author has its
own rate limit and does not compete with the developer:

```bash
GROQ_RESEARCHER_API_KEY=gsk_your_second_key
```

Keys are redacted from all logs, WebSocket frames, and reports, and **no host
environment is forwarded into the sandbox container**, so generated code cannot
read them.

---

## 4. Run the test suite first

This is the fastest way to find my mistakes before involving live models:

```bash
source .venv/bin/activate
python3 -m pytest -q
```

There are roughly 140 tests across eight files. They cover the gate failing
closed, a real `interrupt()` suspending and resuming, refusal leaving the
workspace empty, a tampered bundle being refused before any write, command
injection being rejected, Docker absence never invoking host Python, contract
modification being detected, a rate-limited auditor never rendering as a pass,
and the Director never double-booking a seat.

If some fail, that is the expected outcome of untested code. **Send me the
output and I will fix them** — do not work around them.

---

## 5. Try the CLI first

The CLI is the simplest path and exercises the whole pipeline:

```bash
python3 -m ai_team.cli "Write a function that converts a CSV string to a list of dicts with row validation"
```

### What you should see

Node-by-node progress, then a halt:

```
[TriadCouncil] Task: 'Write a function that converts...'
[TriadCouncil] Thread: thread_a1b2c3d4

--- Deliberation, research, frozen contract, implementation, audit ---
  - [Manager] Architectural RFC and acceptance criteria drafted
  - [Researcher] Dependency and concurrency audit complete
  - [TDD Engineer] Test contract authored and frozen
  - [Developer] Implementation drafted against the contract
  - [QA Auditor] Adversarial audit complete
  - [Preflight] ExecutionBundle locked with SHA-256 digest

==============================================================================
                 TRIADCOUNCIL HUMAN STEERING GATE (interrupt)
==============================================================================
Task:       Write a function that converts a CSV string...
Thread:     thread_a1b2c3d4
Workspace:  .runs/thread_a1b2c3d4/workspace
Digest:     4f3c9a1e...
QA Status:  PASS
------------------------------------------------------------------------------
Files to be written:
  [+] main.py
  [+] test_main.py
------------------------------------------------------------------------------
Produced by:
  main.py: groq:llama-3.1-8b-instant
  manager_rfc: openrouter:anthropic/claude-3.5-sonnet
  qa_audit: zhipuai:glm-4-flash
  test_main.py: groq:openai/gpt-oss-120b
------------------------------------------------------------------------------
Implementation preview (main.py):
    def convert_csv(text): ...
------------------------------------------------------------------------------
Commands to be executed in the sandbox:
  $ python3 -m unittest test_main.py
==============================================================================

Enter decision ([y] Approve / [n] Abort / [s] Steer):
```

### Three things worth checking here

**Answer `n` first.** Then verify nothing was written:

```bash
ls .runs/thread_a1b2c3d4/workspace 2>/dev/null || echo "workspace never created - correct"
```

The report should say `ABORTED BY OPERATOR`, not a failure or a success.

**Then run it again and answer `y`.** You should see real container output:

```
--- Post-gate ---
  [Sandbox] Wrote 2 file(s) to /path/.runs/thread_.../workspace for digest 4f3c9a1e...
  [Sandbox/docker] $ python -m unittest -v test_main.py
  - [Sandbox] Approved code executed in isolation
  - [Manager] Final report compiled

# TriadCouncil Final Report: ...
**Outcome**: SUCCESS (exit code 0)
**Isolation Backend**: docker
```

Tests may genuinely fail (`FAILURE (exit code 1)`). That is a real result, not
a bug — it means the frozen contract caught a bad implementation, which is the
entire point.

**Then try `s`** with guidance like `use only the csv module from stdlib`. The
gate should **re-open** afterwards rather than reporting delivery.

### Prove the isolation is real

Stop Docker Desktop, then run again and approve. You should get a refusal, not
a run on your Mac:

```
**Outcome**: FAILURE (exit code 127)
Execution refused: Docker isolation is required but unavailable...
No code was run on the host.
```

---

## 6. Run the 3D office

Two terminals.

```bash
# Terminal 1
source .venv/bin/activate
python3 run_server.py
```

Expect:

```
  [Server] Durable SQLite checkpointer open; council graph compiled.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

It binds to **loopback only**. That is deliberate: this server exposes the
approval gate.

```bash
# Terminal 2
cd frontend
npm run dev
```

Open **http://localhost:5173**.

### What the office should look like before you do anything

- An isometric room: two bench desk pods in the middle (David and Elena north,
  Alex and Maya south), a whiteboard on the north wall, an espresso bar west, a
  round meeting table east, and a glass-partitioned BOSS room north-east.
- Four cone-shaped "meeple" characters sitting at their desks, each with a
  coloured floor ring when selected.
- **Top bar:** an objective input, `LINK: UP`, `ROLES: IDLE`, and
  `SANDBOX: READY` or `SANDBOX: UNAVAILABLE`.
- **Left panel:** the roster. **Right panel:** the dossier for the selected agent.
- **Bottom:** a collapsed terminal dock reading "No sandbox output".
- Clock pill showing `09:00 · D1`, advancing about one simulated hour every
  two and a half real minutes.

Three specific things to check, because they were all wrong before:

1. `ROLES: IDLE` at startup is **correct**. It used to say `NODES: 4/4 LIVE`
   unconditionally, which was a hardcoded string. It only shows counts once a
   run has actually called a provider.
2. `SANDBOX: UNAVAILABLE` means Docker is not running. It is reading real state.
3. The dossier has **no chat box**. It used to show invented agent replies on a
   timer. There is no backend channel to chat with a graph node.

### Ambient behaviour (watch for ~5 minutes)

Agents should periodically get up and move on their own, **including during a
live run**:

- Alex walks to the espresso bar roughly every two simulated hours.
- David steps out through the west door for air, and his desk stays empty
  until he returns.
- Maya walks over to stand *beside* Alex's desk to raise an edge case.
- Elena reads at the whiteboard.

This is chosen by need scoring rather than a fixed rotation, so the order
should not visibly repeat.

**Specifically look for these, since they were broken:**

- Two agents heading for the espresso bar should stand **side by side**, not
  merge into one body. There are two distinct slots there.
- Nobody should walk **through** a desk, the meeting table, or the pantry counter.
- Two agents meeting in a corridor should **veer around each other** rather
  than overlapping or jittering.
- Try dragging an agent onto a desk (only works when no run is active). It
  should **slide off** the furniture rather than sinking into it.

### Run a task

Type into the top bar:

```
Build a thread-safe LRU cache with TTL expiry
```

Click **Deploy council**. Expected sequence:

1. The button becomes "Council working..." with a spinner.
2. Agents move per pipeline stage: Elena to her desk, Alex to his, Maya over to
   Alex's desk for review, then Maya and David to **separate** whiteboard
   stations.
3. `ROLES` changes from `IDLE` to something like `3/3 OK`.
4. The **approval modal** opens.

### The approval modal

It should show, top to bottom:

- Header: `HUMAN APPROVAL GATE` and "Nothing has been written or run".
- Your objective.
- **QA status** as a coloured card: green `PASS`, red `FAIL`, or amber
  `UNAVAILABLE` with "The auditor could not be reached. This is not a pass."
- The **SHA-256 bundle digest**.
- Maya's auditor notes.
- **Files to be written** (`+ main.py`, `+ test_main.py`) and **commands to be
  executed** (`$ python3 -m unittest test_main.py`).
- A preview of `main.py`.
- A guidance field.
- Three buttons: **Abort · write nothing**, **Steer the council** (disabled
  until you type guidance), **Approve · run in sandbox**.

Accessibility checks: focus should land on **Abort** when it opens, Tab should
cycle within the modal, and **Escape should do nothing at all**. That last one
is intentional — a stray keypress must not resolve a security decision.

### After approving

- The terminal dock at the bottom auto-expands and streams **real** container
  output (`test_convert ... ok`, `Ran 3 tests in 0.002s`, `OK`).
- David walks into the BOSS room.
- After a few seconds the **delivery modal** opens showing four evidence
  tiles — Approval, Exit code, Failing tests, Digest — then the full report and
  a **Download workspace (.zip)** button.

The headline should be one of three states, never a fabricated percentage:

| What happened | Headline |
| :--- | :--- |
| Approved, tests passed | `TESTS PASSED IN THE SANDBOX` · `EXIT 0` |
| Approved, tests failed | `TESTS FAILED IN THE SANDBOX` · `EXIT 1` |
| You aborted | `RUN ABORTED — NOTHING WAS EXECUTED` |

An aborted run shows "No workspace was written, so there is nothing to
download" instead of a download button.

---

## 7. Optional: watch the free-tier behaviour

This is the part I am most curious about, and the hardest to trigger on demand.

Groq's free tier rate-limits quickly. Fire several runs in a row and watch for:

- **Rate limited:** the agent stays at their desk with an amber nameplate
  reading `rate limited · 18s`, counting down. The dossier shows attempt
  *n* of 3. The run continues after the wait.
- **Quota exhausted:** the agent **walks out of the west door**, their body
  disappears, and a placard appears on their empty desk reading
  `Alex · out` with an expected return time.
- **Covered by a substitute:** if you have `GEMINI_API_KEY` set and Groq's
  quota dies, the placard reads `covered by gemini:gemini-2.5-flash`, and the
  final report's "Which model produced what" table names the substitute.

That last one is the point: failover is never silent. If a different model
wrote your code, the report says so.

To force the quota path without waiting, put a deliberately invalid key in
`.env` — you should get `AUTH_FAILED` in the top bar rather than a silent
fallback.

---

## 8. Optional: check the performance fix

Your MacBook was heating up. Open the office with the perf overlay:

```
http://localhost:5173/?perf=1
```

A panel appears bottom-left with draw calls, triangles, and frame time.

**What to look for:**

- With nobody moving, **fps should read 0**. That is correct: the office now
  renders on demand instead of continuously. This is the single biggest change.
- While agents walk, fps rises and settles back to 0 when they stop.
- Switch to another browser tab for a minute, then check Activity Monitor —
  the Chrome Helper (GPU) process should be near idle.

For a real comparison, run the same check on the old build
(`git stash` this work, or check out the previous commit) and note the numbers.
I would rather you measure it than take my word for it.

---

## 9. If something breaks

Please send me whichever of these is relevant:

- **Python traceback** from Terminal 1, in full.
- **Browser console errors** (Cmd-Option-J). In particular, anything starting
  with `[OfficeGeometry] layout problems:` — that is a self-check I added, and
  it means a destination or corridor is misplaced.
- **`npm run build` output**, since I could not typecheck the frontend here:
  ```bash
  cd frontend && npm run build
  ```
  This is the most likely place to find my mistakes.
- **`python3 -m pytest -q` output** if any test fails.
- A screenshot if something looks wrong rather than errors.

### Things I already know are not finished

- **Tracks B2–B5 are not built:** no RED/GREEN theatre, no LangSmith tracing,
  no time-travel checkpoint scrubber, no git-worktree-per-run.
- **No navmesh.** I fixed the collision, occupancy, and phasing problems with
  corrected geometry, slot reservation, separation, and obstacle resolution,
  all of which I could verify numerically. I deliberately did **not** add the
  `recast-navigation` WASM dependency, because an async-initialising navmesh I
  cannot run risks a blank office, and pathing aesthetics were not worth that
  on an untested build. Paths are smoothed by string-pulling instead, which
  gets most of the visual benefit.
- **The meeting table is unused** by the current pipeline. The seats and routes
  exist and are validated, but no stage sends anyone there yet.
- **Elena does not search the web.** She runs on Groq and reasons from model
  knowledge; her citations are labelled unverified. Real Gemini Search
  grounding is not wired.
- **One browser tab per run.** The run token is held in memory by the tab that
  started the run, so a second tab cannot approve or download it. Refreshing
  mid-run loses the token, and you will have to abort from the CLI or restart.
