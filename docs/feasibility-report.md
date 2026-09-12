# AI Team Project Feasibility Report

## Executive conclusion

The project is technically feasible as a local CLI MVP, but it is not yet implementation-ready as specified. The orchestration concept, provider separation, typed hand-off contracts, bounded retries, persistence plan, and explicit human approval gate are all sound. The main feasibility risk is the Senior Dev execution boundary: the current documents assume an Antigravity API and sandbox behavior that must be verified against the installed SDK version before the pipeline can honestly claim governed execution.

**Recommendation: conditional go.** Build the MVP, but first make the runtime contract executable and conservative. Treat Antigravity as a version-pinned adapter, enable OS-level sandboxing explicitly, and test the approval boundary independently before connecting the full pipeline.

## Scope reviewed

This assessment reviewed `AGENTS.md` and:

- `docs/architecture.md`
- `docs/backends.md`
- `docs/decisions.md`
- `docs/state_machine.md`

The repository currently contains design documents only; there is no implementation to run or integration test. Consequently, this is an architecture and dependency feasibility assessment, not a passing MVP verification.

## Feasibility by capability

| Capability | Assessment | Evidence / implication |
|---|---|---|
| Four-role orchestration | Feasible | OpenRouter and Groq expose OpenAI-compatible endpoints; Gemini has an official Python SDK and grounding support. |
| Grounded research | Feasible with API drift risk | Google documents Google Search grounding and citation metadata, but the current examples use newer Interactions-style APIs than some project snippets. |
| Text-only pre-approval phases | Feasible | Antigravity defaults to read-only mode, and its capability model supports explicit tool allow/deny lists. |
| Human approval before mutation | Feasible, but must be tested as an invariant | The CLI can enforce this, but the agent must not receive write/command tools before approval and the post-approval call must be a separate state transition. |
| Sandboxed writes and tests | Feasible conditionally | Antigravity exposes file tools and command execution, but OS sandboxing is a separate `RunCommandConfig.enable_sandbox` setting and defaults to false in the current SDK types. |
| Bounded repair loops | Feasible in the orchestrator | Retry counts, patch hashes, and exit-code capture are ordinary deterministic control logic; they should not be delegated to model judgment. |
| Reproducible audit trail | Feasible | The `.runs/` layout is appropriate, provided secrets, prompts containing sensitive data, and untrusted generated files are handled deliberately. |
| Production-grade reliability | Not yet | Provider quotas, SDK preview churn, malformed structured output, timeouts, partial writes, and prompt-injection risks need explicit handling. |

## Findings that materially affect the design

### 1. The provider architecture is viable, but model IDs must be treated as live configuration

OpenRouter documents an OpenAI-compatible API and a models endpoint, so the Manager adapter is practical and can retain the proposed `OpenAI(base_url=...)` approach. OpenRouter also describes model aliases and a catalog API, which supports the project convention of environment-configurable model IDs rather than inline constants. [OpenRouter quickstart](https://openrouter.ai/docs/quickstart), [OpenRouter models](https://openrouter.ai/docs/guides/overview/models)

Groq likewise documents the OpenAI-compatible base URL and model-listing endpoint. However, the project’s example defaults `llama-3.1-8b-instant` and `llama-3.3-70b-versatile` are scheduled for shutdown on August 16, 2026 according to Groq’s deprecation page. Since the current date is September 11, 2026, those defaults should be considered unavailable unless an enterprise exception applies. Replace them with a current configured default, such as `openai/gpt-oss-20b`, and verify the live model list at startup or in a diagnostic command. [Groq OpenAI compatibility](https://console.groq.com/docs/openai), [Groq deprecations](https://console.groq.com/docs/deprecations), [Groq models](https://console.groq.com/docs/models)

The same issue applies to the OpenRouter example `anthropic/claude-3.5-sonnet`: it should be a configuration example, not a guaranteed current default. A startup configuration report should print the selected model IDs without printing API keys.

### 2. Google Search grounding is available, but the integration should target the current SDK surface

Google’s current documentation describes Google Search grounding as a first-party tool that produces grounded responses with annotations and search-call/result steps. This supports the Researcher role and the requirement to preserve citations. [Google Search grounding](https://ai.google.dev/gemini-api/docs/google-search)

The project’s `google-genai` direction is correct, but the exact example in `docs/backends.md` should be treated as provisional. Google’s migration documentation shows a move toward the `google.genai` client and newer interaction patterns. Implement a small adapter that normalizes the response into `{text, citations, queries}` and add a fixture-based parser test; do not let the rest of the pipeline depend on raw Gemini response objects. [Gemini SDK migration](https://ai.google.dev/gemini-api/docs/migrate)

Gemini model names also drift. The deprecation page currently lists `gemini-2.5-flash` as available without a shutdown date, while `gemini-2.0-flash` has a June 1, 2026 shutdown date. The researcher default should therefore not be `gemini-2.0-flash`; keep the model configurable and validate it during setup. [Gemini deprecations](https://ai.google.dev/gemini-api/docs/deprecations)

### 3. Antigravity is the differentiator and the largest implementation risk

The official Antigravity SDK repository confirms the important high-level premise: install from PyPI because platform-specific wheels include a compiled runtime, set `GEMINI_API_KEY`, and use read-only defaults unless `CapabilitiesConfig()` is supplied. [Antigravity SDK README](https://github.com/google-antigravity/antigravity-sdk-python)

The project documents a policy API with `LocalAgentConfig`, `policy.allow_all()`, and `policy.workspace_only()`. These names and semantics must be checked against the exact installed release instead of copied from a design sketch. The current public SDK types explicitly distinguish tool exposure from policy rejection: `enabled_tools` / `disabled_tools` remove tools from the model context, while policies reject calls at runtime. For the pre-gate agent, disabling write and command tools is the stronger default because it prevents the model from attempting them at all. [Antigravity SDK types](https://github.com/google-antigravity/antigravity-sdk-python/blob/main/google/antigravity/types.py)

Most importantly, the current SDK type documentation says command execution has an `enable_sandbox` option and that it defaults to `False`. Therefore, the proposed post-gate configuration is not sufficient if it only passes `CapabilitiesConfig()` and a workspace policy. The execution adapter must explicitly configure the command runner for OS-level sandboxing, verify that the platform supports it, and fail closed if it cannot. A workspace allowlist is useful, but it is not equivalent to process isolation.

### 4. The human gate is conceptually strong, but the documents currently overstate what it proves

The gate proves that a human typed `y`; it does not by itself prove that the approved diff is exactly what gets written, that the command list is complete, or that a generated command cannot escape the intended workspace. The implementation should bind approval to a digest of the finalized artifact:

```text
finalized_plan + source_files + test_files + declared_commands
        -> approval_digest
human approves digest D
        -> execution call receives exactly artifact D
```

The execution phase should reject any artifact mutation after approval unless it creates a new digest and returns to the gate. This is the strongest way to preserve the project’s non-negotiable safety rule while still allowing bounded post-gate repairs.

### 5. The cyclic architecture is valuable, but too ambitious for the first integration milestone

The four loops are internally coherent, and the state machine has useful explicit bounds. However, implementing all loops before proving one happy path will multiply failure modes: malformed Pydantic output, provider retries, citation parsing, SDK tool events, partial writes, command timeouts, and repair-loop semantics will be difficult to localize.

For the MVP, use one pass for planning, one grounded research call, one draft, one read-only review, one preflight result, the approval gate, and one execution attempt. Add repair and revision loops only after the basic audit trail and safety tests pass. The state machine can retain the future states, but the first implementation should make their budgets configurable internally and fixed to one where possible.

## Primary risks and mitigations

| Risk | Severity | Mitigation |
|---|---:|---|
| Antigravity preview/API changes | High | Pin the package; isolate all imports/configuration in `antigravity_dev.py`; add an SDK smoke test using the installed wheel. |
| “Full capabilities” without OS sandboxing | Critical | Set `enable_sandbox=True`; use workspace-only policy; fail closed when unavailable; test path traversal and command escape cases. |
| Deprecated model defaults | High | Replace stale Groq defaults; validate model IDs; expose all IDs through environment variables. |
| Approval bypass through stale or mutated artifacts | Critical | Hash the approved artifact and verify the same hash at execution start. |
| LLM-generated shell commands are unsafe | Critical | Show commands before approval; allow only commands from an explicit command manifest; impose timeout, environment filtering, and workspace confinement. |
| Prompt injection in task files or web results | High | Treat all retrieved text and repository files as untrusted data; keep tool permissions outside model control; never let research citations authorize execution. |
| Partial writes after execution failure | Medium | Execute in a per-run workspace; record created/modified files; use atomic writes where practical; do not silently copy results into the user project. |
| Structured output failure | Medium | Validate every role response with Pydantic; retry parsing with a bounded repair prompt; stop with a diagnostic instead of guessing. |
| Cost/latency from four providers and loops | Medium | Add per-run budgets, timeouts, and token accounting; defer cyclic loops until the single-pass path is reliable. |

## Recommended implementation order

1. **Configuration and diagnostics:** model IDs, API-key presence checks, package versions, timeout settings, and a provider connectivity check that never executes generated code.
2. **Typed contracts:** implement the Pydantic payloads from `docs/architecture.md`; validate and serialize every boundary.
3. **Provider adapters:** Manager, Researcher, Junior, and Antigravity read-only adapters, each with mocked unit tests and a live opt-in smoke test.
4. **Approval artifact:** render the final plan, diff, tests, commands, and approval digest. Confirm that `N`, EOF, blank input, and unexpected input produce no writes and no commands.
5. **Execution adapter:** create a fresh per-run workspace; explicitly enable OS-level sandboxing; restrict tools and paths; capture stdout, stderr, exit code, and file manifest.
6. **Persistence:** write `.runs/` records with redaction and atomic JSON writes. Never persist API keys or unrestricted environment dumps.
7. **One end-to-end fixture:** use a deterministic CSV-to-JSON task with no network dependency. Test approval rejection and approval success as separate integration tests.
8. **Only then add loops:** enable bounded research revision, code review revision, preflight rerouting, and post-gate repair one at a time.

## Minimum acceptance tests before calling the MVP feasible

- With missing keys, the CLI reports exactly which role is unavailable and performs no partial run.
- A mocked full pipeline reaches the gate with a stable approval digest.
- Any input other than `y`/`yes` exits without creating the target source files and without invoking the execution agent.
- Changing one byte of the approved source or command manifest invalidates the digest and prevents execution.
- The pre-gate Antigravity agent cannot call `create_file`, `edit_file`, or `run_command`.
- The post-gate agent can only write inside a fresh run workspace.
- Sandbox mode is explicitly enabled and a startup assertion fails if the SDK reports it unavailable.
- A command timeout returns a failed `ExecutionSummary`, not a success.
- A failing test records the exact command, exit code, stdout, stderr, and attempt number.
- A repair loop stops at its bound and detects repeated patch hashes.
- The final report distinguishes model claims from observed process output.

## Final verdict

The project is a good **engineering prototype** and a credible basis for a governed coding-agent CLI. It is not yet safe to describe as a real sandboxed execution system until the Antigravity adapter proves explicit OS-level sandboxing and the approval-to-artifact binding is implemented. The best next milestone is a narrow, test-heavy vertical slice—not the full cyclic architecture: Manager → Researcher → Junior → read-only Senior → digest-bound approval → one sandboxed execution → persisted report.

If that slice passes the acceptance tests above, the remaining loops are incremental orchestration work. If it cannot pass them, the project should replace or wrap the execution backend before investing further in multi-agent prompt design.

## Sources

1. [Google Antigravity SDK repository and README](https://github.com/google-antigravity/antigravity-sdk-python)
2. [Google Antigravity SDK type definitions](https://github.com/google-antigravity/antigravity-sdk-python/blob/main/google/antigravity/types.py)
3. [Google Gemini API: Grounding with Google Search](https://ai.google.dev/gemini-api/docs/google-search)
4. [Google Gemini API: SDK migration guide](https://ai.google.dev/gemini-api/docs/migrate)
5. [Google Gemini API: deprecations](https://ai.google.dev/gemini-api/docs/deprecations)
6. [OpenRouter quickstart](https://openrouter.ai/docs/quickstart)
7. [OpenRouter model catalog](https://openrouter.ai/docs/guides/overview/models)
8. [Groq OpenAI compatibility](https://console.groq.com/docs/openai)
9. [Groq model deprecations](https://console.groq.com/docs/deprecations)
10. [Groq supported models](https://console.groq.com/docs/models)
