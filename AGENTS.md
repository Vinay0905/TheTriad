# AGENTS.md

> [!IMPORTANT]
> **Status: this file is the original project vision, not a description of the
> current code.** The system was rebuilt on LangGraph with five roles, a frozen
> TDD contract, and Docker-based isolation. Two things in particular have
> changed: the Senior Dev executes approved code in a **Docker container**, not
> the Antigravity SDK sandbox; and the pipeline is a compiled `StateGraph`, not
> the linear four-role FSM sketched below.
>
> For what is actually wired, read **[HANDOFF.md](HANDOFF.md) section 0** and
> **[README.md](README.md)**.
>
> The "Do not touch" section at the bottom of this file **still applies in
> full** and is enforced in code. The confirmation gate is non-negotiable.

## What this project is

**AI Team** is a small multi-agent system that simulates a software team of
four roles — Manager, Researcher, Senior Dev, Junior Dev — each backed by a
different LLM API, working together on one task at a time in a fixed
pipeline with a human confirmation gate before any code is actually run.

The point isn't to have four chatbots talk in a circle. It's to give each
role the backend best suited to what that role actually needs to do, and to
keep a hard line between "the team is discussing/drafting code" and "the
team is executing code for real."

This file is the shared brief. Any AI assistant (Claude, ChatGPT, Gemini,
etc.) reading this should come away understanding the goal, the
architecture, the constraints, and what's still undecided — enough to
usefully contribute a design opinion, a chunk of code, or a review, without
needing the full conversation history that produced this doc.

## Goal

Build a CLI pipeline where a person hands the team a task in natural
language, and:

1. The team collectively produces a reviewed, finalized plan of action +
   draft code — entirely in text, no execution.
2. The person explicitly approves.
3. Only then does the Senior Dev role actually write files and run/test
   code, in a real sandboxed environment, and report the true output.

Nothing gets executed without a human in the loop.

## Architecture

| Role       | Backend                      | Responsibility | Can execute code? |
|------------|-------------------------------|-----------------|---------------------|
| Manager    | OpenRouter (strong general model) | Breaks the task into a plan, delegates, reviews, writes the final report. Pure judgment, no tools. | No |
| Researcher | Gemini API (free tier), Google Search grounding enabled | Gathers real, current facts/docs/gotchas relevant to the task before the devs start. | No |
| Junior Dev | Groq (fast/cheap model) | Writes a first-pass implementation as text/code. Expected to be rough — the Senior Dev is there to catch problems. | No |
| Senior Dev | **Antigravity SDK** (`google-antigravity`, powered by Gemini) | Reviews and finalizes the Junior Dev's draft. **Then**, after human approval, re-invoked with full capabilities to actually write files and execute code in its sandbox, and report real results. | Only after human confirmation |

### Why this split

- **Manager and Researcher never need tools** — they need reasoning and
  facts, respectively. Cheap/fast general-purpose APIs are the right fit.
- **Researcher specifically uses Gemini's Google Search grounding tool**
  so its output is based on live results, not model memory.
- **Junior Dev uses Groq** for cheap, fast iteration — it's meant to
  produce a rough draft quickly, not a polished final answer.
- **Senior Dev uses the Antigravity SDK** because it's the only backend in
  this stack that is both a capable coding model (Gemini) *and* ships with
  a real, governable execution sandbox with a built-in read-only vs.
  full-capability mode. That maps directly onto the "draft in text, execute
  after approval" requirement without extra scaffolding.

### The confirmation gate (non-negotiable)

The Antigravity `Agent` defaults to **read-only mode** — it can reason about
and rewrite code but cannot touch a filesystem or run anything. Full tool
and sandbox access only turns on when the caller explicitly passes
`capabilities=CapabilitiesConfig()`.

The pipeline uses this directly as the safety boundary:

- **Draft/review phase** → Senior Dev agent instantiated with default
  (read-only) capabilities.
- **Execute phase** → a *separate* agent call, only reachable after an
  explicit `y` at a CLI prompt, instantiated *with*
  `capabilities=CapabilitiesConfig()`.

Any future change to this project (automation, scheduling, removing the
prompt, batch mode, etc.) **must preserve an explicit human approval step
before the execute-phase call.** This is a hard constraint, not a
style preference — see "Do not touch" below.

## Pipeline / flow

```
1. Manager       -> plan (task broken into steps + what "done" looks like)
2. Researcher    -> grounded findings relevant to the plan
3. Junior Dev    -> draft code (text only)
4. Senior Dev    -> review + finalized code (text only, Antigravity read-only)
5. Manager       -> summary + risk flag
   --- human approves: y/N ---
6. Senior Dev    -> real execution in sandbox (Antigravity, full capabilities)
7. Manager       -> final status report
```

Currently a straight linear pipeline — no role can send work backward (e.g.
Manager rejecting a plan and looping the Researcher again). See Roadmap.

## Environment / setup

Required API keys (env vars):

- `GROQ_API_KEY` — https://console.groq.com
- `OPENROUTER_API_KEY` — https://openrouter.ai/keys
- `GEMINI_API_KEY` — https://aistudio.google.com/apikey
  (this single key is used by **both** the Researcher's Gemini API calls
  **and** the Antigravity SDK — no separate Antigravity key exists)

Install: `pip install -r requirements.txt`
(pulls `openai`, `google-genai`, and `google-antigravity` — the latter
includes a compiled runtime binary, so it must be installed via PyPI, not
just cloned from source)

Run: `python orchestrator.py "task description"`

## Conventions

- Each role's system prompt should stay short and role-scoped — don't let
  the Manager's prompt drift into writing code, don't let the Junior Dev's
  prompt drift into final decision-making.
- Model IDs for all three providers (Groq, OpenRouter, Gemini) drift over
  time. Never hardcode a model ID as a magic string inline — always go
  through config so it can be overridden by env var without a code change.
- Keep inter-role context as flattened text summaries, not raw API
  response objects, so any backend can be swapped without reshaping every
  other role's input.
- Antigravity SDK is new and its API surface may shift between `0.x`
  releases — treat `antigravity_dev.py` as the one place that needs
  re-checking against the SDK's own `examples/` folder if something breaks,
  rather than assuming the rest of the pipeline is at fault.

## Open questions / not yet decided

These are genuinely undecided — if you're an AI or person picking this up,
useful next contribution is often an opinion on one of these rather than
new code:

1. **Revision loops.** Should the Manager be able to reject the Senior
   Dev's plan and send it back to Junior Dev / Researcher, rather than the
   current strictly linear flow?
2. **Junior Dev as a second Antigravity agent.** Right now Junior Dev is
   Groq-only text. Should it instead be a second Antigravity agent
   (read-only) so it can "ask" the Senior Dev to run things, making the
   junior/senior dynamic feel more literal? Tradeoff: extra latency/cost
   vs. more realistic role separation.
3. **Shared transcript vs. flattened summaries.** Currently each role only
   sees a condensed text summary of prior steps. Worth switching to a full
   running transcript for richer context, at the cost of longer prompts?
4. **Logging/persistence.** Nothing is currently saved between runs. Do we
   want each run's transcript + execution result written to disk (and if
   so, where, and in what format) for later review?
5. **Failure handling.** If the Senior Dev's real execution phase fails
   (error, timeout, sandbox limit), does the pipeline retry automatically,
   hand back to Junior Dev, or just report failure to the Manager and stop?

## Definition of done (for the current MVP)

- [ ] All four roles callable independently with their own backend.
- [ ] Full pipeline runs end-to-end on a simple test task (e.g. "write a
      function that converts CSV to JSON") without manual intervention
      except the single y/N confirmation.
- [ ] Confirming `N` cleanly stops the pipeline with nothing executed.
- [ ] Confirming `y` results in real sandbox execution with genuine
      pass/fail output, not a hallucinated "it works."
- [ ] README accurately reflects setup steps for someone with none of the
      three API keys yet.

## Do not touch

- **The confirmation gate.** Do not add a flag, config option, or
  "trusted mode" that skips the human `y/N` prompt before real code
  execution. If automation is ever needed, it should require a separate,
  clearly-labeled opt-in path — not a modification of the default gate.
- **Which env var the Antigravity SDK reads.** It must remain
  `GEMINI_API_KEY` — this is fixed by the SDK itself, not a project choice.
