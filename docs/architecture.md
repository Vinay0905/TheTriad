# TriadCouncil: LangGraph Multi-Agent Architecture

## 1. Executive Summary & Framework Foundation

**TriadCouncil** is implemented natively on **LangGraph (0.2+)** and **LangChain**. 

The system models a high-reliability software engineering department featuring **five distinct roles across four independent frontier model families** (Anthropic/DeepSeek on OpenRouter, Google Gemini, Meta Llama on Groq, and ZhipuAI GLM-4-Flash):
- **Cyclic StateGraph**: First-class support for multi-agent loops, tournament drafting, and back-propagation.
- **Dedicated QA & Security Red-Teamer (GLM-4-Flash)**: An independent adversarial agent that attacks plans for vulnerabilities, edge cases, and missing negative tests before code is written.
- **Cross-Model Tournament Duel (Groq vs. GLM-4-Flash)**: Two completely different model families draft competing implementations in parallel (Candidate A from Meta Llama vs. Candidate B from Zhipu GLM).
- **Checkpointer-Driven Human-in-the-Loop (`interrupt()`)**: State serialization (`SqliteSaver` / `MemorySaver`) that pauses execution right before side-effects, presenting an immutable **SHA-256 Integrity Digest** to the operator.
- **Google Antigravity Sandboxed Execution**: Verified runtime execution and evidence capture strictly inside an isolated workspace (`.runs/<run_id>/workspace/`).

---

## 2. Global LangGraph Topology

```mermaid
flowchart TD
    Start([START]) --> Triage["0. Task Triage Node"]

    %% Council Deliberation Subgraph
    subgraph CouncilDeliberation ["Phase 1: Deliberative Council & Adversarial Red-Teaming"]
        Triage --> ManagerRFC["1.1 Manager RFC Node (OpenRouter / Claude)"]
        ManagerRFC <-->|"Grounding Audit"| ResearcherAudit["1.2 Researcher Audit Node (Gemini + Grounding)"]
        ResearcherAudit --> RedTeamQA["1.3 Dedicated QA & Security Auditor (GLM-4-Flash Free)"]
    end

    %% TDD Contract
    RedTeamQA --> TDDContractNode["2. Senior Dev TDD Contract Node (interfaces + negative tests)"]

    %% Cross-Model Tournament
    subgraph CrossModelTournament ["Phase 3: Cross-Model Tournament Duel"]
        TDDContractNode --> JuniorDraftA["3.1 Candidate A: Groq (Meta Llama 3.1 8B)"]
        TDDContractNode --> JuniorDraftB["3.2 Candidate B: ZhipuAI (GLM-4-Flash 30B MoE)"]
        JuniorDraftA & JuniorDraftB --> SeniorJudge["3.3 Senior Dev Tournament Judge & Hybrid Synthesis Node"]
    end

    %% Pre-flight Gate
    SeniorJudge --> PreFlightGate["4. Manager Pre-Flight Quality Gate Node"]

    %% Human Steering Gate via LangGraph interrupt()
    PreFlightGate --> HumanGateNode{"5. Human Steering Gate Node<br/>interrupt(ExecutionBundle)"}

    %% Checkpointer Interrupt Responses
    HumanGateNode -->|"Command(action='abort')"| AbortNode["Clean Abort Node<br/>Zero Side Effects"]
    HumanGateNode -->|"Command(action='steer')"| ManagerRFC
    HumanGateNode -->|"Command(action='approve')"| SandboxExecNode["6. Isolated Antigravity Sandbox Node"]

    %% Sandbox Execution & Dual-Loop Healing
    subgraph ExecutionHealing ["Phase 6: Sandboxed Execution & Dual-Loop Healing"]
        SandboxExecNode --> RoutePostExec{"Route Post-Execution"}
        RoutePostExec -->|"Exit != 0 & Local Bug (Attempts < 3)"| MicroRepairNode["6.1 Senior Micro-Repair Node"]
        MicroRepairNode --> SandboxExecNode
        RoutePostExec -->|"Exit != 0 & Arch Blocker (Macro < 1)"| MacroReplanNode["6.2 Macro Escalation Node"]
        MacroReplanNode --> ManagerRFC
    end

    %% Reporting & Completion
    RoutePostExec -->|"Exit == 0 (All Tests Passed)"| FinalReportNode["7. Manager Final Report Node"]
    RoutePostExec -->|"Retries Exhausted / Cycle Detected"| ForensicNode["7. Forensic Incident Report Node"]
    ForensicNode --> FinalReportNode
    FinalReportNode --> End([END])
    AbortNode --> End
```

---

## 3. The 5 Roles & Heterogeneous Provider Allocations

| Role | Provider / Model Family | Backend Integration | Core Responsibility | Cost |
| :--- | :--- | :--- | :--- | :--- |
| **Manager** | **Anthropic / DeepSeek** via OpenRouter | `ChatOpenAI(base_url="https://openrouter.ai/api/v1")` | High-level scoping, RFC authoring, pre-flight gate, final status reporting. | Pay-as-you-go |
| **Researcher** | **Google Gemini 2.5 Flash** | `google-genai` with Search Grounding | Live web search grounding, API deprecation detection, verified documentation citations. | **Free Tier** |
| **QA & Security Red-Teamer** | **ZhipuAI GLM-4-Flash** (30B MoE) | `ChatOpenAI(base_url="https://open.bigmodel.cn/api/paas/v4")` | Adversarial FMEA audit, injection vulnerability checks, negative test scenario formulation. | **100% Free** |
| **Junior Dev 1** | **Meta Llama 3.1 8B** via Groq | `ChatGroq(model_name="llama-3.1-8b-instant")` | Ultra-fast synthesis of **Candidate A** (Lean / StdLib / Direct). | **Free Tier** |
| **Junior Dev 2 (Co-Dev)**| **ZhipuAI GLM-4-Flash** (30B MoE) | `ChatOpenAI(base_url="https://open.bigmodel.cn/api/paas/v4")` | Independent synthesis of **Candidate B** (Modular / Robust / Defensive). | **100% Free** |
| **Senior Dev** | **Google Antigravity SDK** (Gemini) | `Agent(LocalAgentConfig)` | Pre-Gate: TDD test contract authoring, tournament judge, hybrid code synthesis.<br>Post-Gate: Sandboxed file writer, test runner, micro-repair engineer. | Shared with Gemini Key |

---

## 4. Human-in-the-Loop Mechanics (`interrupt()` & Checkpointers)

LangGraph 0.2 replaces brittle manual CLI loops with native graph suspension:

### The Gate Node (`human_steering_gate_node`)
```python
from langgraph.types import interrupt, Command

def human_steering_gate_node(state: TriadCouncilState) -> Command:
    """Suspends the graph prior to any filesystem or command execution.
    Presents the SHA-256 integrity digest, file diffs, and declared commands.
    """
    bundle = state["execution_bundle"]
    
    user_decision = interrupt({
        "type": "CONFIRMATION_REQUIRED",
        "integrity_digest": bundle["bundle_digest"],
        "workspace_path": bundle["workspace_path"],
        "declared_files": list(bundle["source_files"].keys()) + list(bundle["test_files"].keys()),
        "declared_commands": bundle["declared_commands"],
        "options": ["[y] Approve", "[n] Abort", "[s] Steer with Guidance"]
    })
    
    action = user_decision.get("action", "abort").lower()
    
    if action in ["approve", "y"]:
        return Command(update={"approval_status": "APPROVED"}, goto="sandbox_execution_node")
    elif action in ["steer", "s"]:
        return Command(
            update={
                "approval_status": "STEERED",
                "human_feedback": user_decision.get("guidance", ""),
                "council_round": state.get("council_round", 0) + 1
            },
            goto="manager_rfc_node"
        )
    else:
        return Command(update={"approval_status": "ABORTED"}, goto="clean_abort_node")
```
