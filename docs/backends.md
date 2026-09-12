# LangChain & LangGraph Provider Integrations

This document defines the exact LangChain and LangGraph integrations for all providers across the TriadCouncil system.

---

## 1. Manager: OpenRouter via `ChatOpenAI`

The Manager uses the standard LangChain `ChatOpenAI` wrapper pointed at the OpenRouter base URL:

```python
import os
from langchain_openai import ChatOpenAI

def get_manager_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        temperature=0.2,
        default_headers={
            "HTTP-Referer": "https://github.com/triadcouncil",
            "X-Title": "TriadCouncil Multi-Agent",
        },
    )
```

---

## 2. Researcher: Google Gemini with Search Grounding via `google-genai`

Gemini 2.5 Flash native search grounding is wrapped into a LangGraph node function, extracting `grounding_metadata` and URLs directly:

```python
import os
from google import genai
from google.genai import types

def researcher_audit_node(state: dict) -> dict:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    prompt = f"Audit package dependencies and APIs for: {state['task_prompt']}"
    
    response = client.models.generate_content(
        model=os.getenv("GEMINI_RESEARCHER_MODEL", "gemini-2.5-flash"),
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=1.0,
        ),
    )
    
    citations = []
    if response.candidates and response.candidates[0].grounding_metadata:
        metadata = response.candidates[0].grounding_metadata
        if metadata.grounding_chunks:
            for chunk in metadata.grounding_chunks:
                if chunk.web:
                    citations.append({"title": chunk.web.title, "url": chunk.web.uri})
                    
    return {
        "researcher_audit": {
            "findings": response.text,
            "citations": citations,
        }
    }
```

---

## 3. QA & Security Auditor and Junior Dev 2: ZhipuAI GLM-4-Flash (100% Free)

Zhipu AI exposes an OpenAI-compatible endpoint at `https://open.bigmodel.cn/api/paas/v4`. We use separate API keys for the QA Auditor and Junior Dev 2 to isolate rate limits:

```python
import os
from langchain_openai import ChatOpenAI

def get_glm_qa_model() -> ChatOpenAI:
    """Dedicated Adversarial QA & Security Auditor model."""
    key = os.getenv("ZHIPUAI_QA_API_KEY") or os.getenv("ZHIPUAI_API_KEY")
    return ChatOpenAI(
        model=os.getenv("GLM_MODEL", "glm-4-flash"),
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=key,
        temperature=0.2,
    )

def get_glm_dev_model() -> ChatOpenAI:
    """Junior Dev 2 (Candidate B author in the Cross-Model Tournament)."""
    key = os.getenv("ZHIPUAI_DEV_API_KEY") or os.getenv("ZHIPUAI_API_KEY")
    return ChatOpenAI(
        model=os.getenv("GLM_MODEL", "glm-4-flash"),
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=key,
        temperature=0.3,
    )
```

---

## 4. Junior Dev 1: Groq via `ChatGroq`

The Junior Dev 1 leverages Groq's LPUs for sub-second drafting of **Candidate A**:

```python
import os
from langchain_groq import ChatGroq

def get_junior_dev_groq_model() -> ChatGroq:
    return ChatGroq(
        model_name=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        groq_api_key=os.environ.get("GROQ_API_KEY"),
        temperature=0.3,
    )
```

---

## 5. Senior Dev: Google Antigravity SDK as LangGraph Nodes

The Senior Dev acts in two distinct LangGraph node modes:

### A. Pre-Gate Review Node (`senior_review_node`)
Instantiated with read-only policies. It evaluates the tournament candidates (A and B), authors the TDD contract, and generates the hybrid code.

```python
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.hooks import policy

async def senior_review_node(state: dict) -> dict:
    config = LocalAgentConfig(
        system_instructions="You are a Senior Software Engineer performing strict code review and tournament judging.",
        policies=[
            policy.deny("run_command"),
            policy.deny("create_file"),
            policy.deny("edit_file"),
            policy.allow("view_file"),
        ]
    )
    async with Agent(config=config) as agent:
        response = await agent.chat(...)
        return {"synthesized_code": ...}
```

### B. Post-Gate Sandboxed Execution Node (`sandbox_execution_node`)
Instantiated only downstream of the `human_steering_gate_node`, with full `CapabilitiesConfig()` and workspace confinement:

```python
from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig
from google.antigravity.hooks import policy

async def sandbox_execution_node(state: dict) -> dict:
    workspace_path = state["execution_bundle"]["workspace_path"]
    config = LocalAgentConfig(
        workspaces=[workspace_path],
        capabilities=CapabilitiesConfig(),
        policies=[
            policy.workspace_only([workspace_path]),
            policy.allow_all(),
        ]
    )
    async with Agent(config=config) as agent:
        response = await agent.chat(...)
        return {"sandbox_result": ...}
```
