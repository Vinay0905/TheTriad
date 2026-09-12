"""Junior Dev dual-candidate drafting node using Groq and GLM-4-Flash."""

import os
from typing import Dict, Any
from ai_team.graph.state import TriadCouncilState


def junior_draft_node(state: TriadCouncilState) -> Dict[str, Any]:
    """
    Tournament Drafting:
    - Junior Dev 1 (Groq / Meta Llama 3.1 8B): Synthesizes Candidate A (Lean / StdLib / Direct).
    - Junior Dev 2 (ZhipuAI / GLM-4-Flash): Synthesizes Candidate B (Modular / Robust / Defensive).
    Two independent model families compete head-to-head on the same TDD contract!
    """
    task = state["task_prompt"]
    contract = state.get("tdd_contract") or {}
    test_code = contract.get("test_main.py", "")
    groq_key = os.getenv("GROQ_API_KEY")
    glm_key = os.getenv("ZHIPUAI_DEV_API_KEY") or os.getenv("ZHIPUAI_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    cand_a_code = f"'''Candidate A implementation for: {task}'''\n# Implement module to satisfy tests\n"
    cand_b_code = f"'''Candidate B implementation for: {task}'''\n# Implement module to satisfy tests\n"

    # 1. Candidate A (Groq / Qwen 27B) - Lean & Fast
    if groq_key:
        try:
            print("  ... Junior Dev 1 (Groq) drafting Candidate A...")
            from langchain_groq import ChatGroq
            groq_model_name = os.getenv("GROQ_MODEL", "qwen/qwen3.6-27b").strip()
            llm_groq = ChatGroq(
                model_name=groq_model_name,
                groq_api_key=groq_key,
                temperature=0.3,
                max_tokens=600,
                request_timeout=20,
            )
            prompt_a = (
                f"You are Junior Developer 1. Write the Python implementation for `main.py` to accomplish this task:\n"
                f"{task}\n\n"
                f"Unit Test Suite Contract that your code MUST satisfy:\n"
                f"{test_code}\n\n"
                "Focus on a clean, minimal-dependency standard-library solution with high throughput.\n"
                "Return ONLY executable Python code for `main.py`."
            )
            resp_a = llm_groq.invoke(prompt_a)
            clean_a = extract_python_code(resp_a.content)
            if clean_a:
                cand_a_code = clean_a
        except Exception as err:
            print(f"  [Junior Dev 1 Notice] Groq notice: {err}")

    # 2. Candidate B (GLM-4.7-Flash / OpenRouter) - Defensive & Robust
    candidate_b_generated = False
    if glm_key:
        try:
            print("  ... Junior Dev 2 (GLM-4.7-Flash) drafting Candidate B...")
            from langchain_openai import ChatOpenAI
            llm_glm = ChatOpenAI(
                model="glm-4.7-flash",
                base_url="https://open.bigmodel.cn/api/paas/v4",
                api_key=glm_key,
                temperature=0.3,
                max_tokens=600,
                request_timeout=15,
            )
            prompt_b = (
                f"You are Junior Developer 2. Write the Python implementation for `main.py` to accomplish this task:\n"
                f"{task}\n\n"
                f"Unit Test Suite Contract that your code MUST satisfy:\n"
                f"{test_code}\n\n"
                "Focus on strict defensive type checking, robust exception safety, and edge-case handling.\n"
                "Return ONLY executable Python code for `main.py`."
            )
            resp_b = llm_glm.invoke(prompt_b)
            clean_b = extract_python_code(resp_b.content)
            if clean_b:
                cand_b_code = clean_b
                candidate_b_generated = True
        except Exception as err:
            print(f"  [Junior Dev 2 Notice] GLM notice: {err}")

    # Fast secondary fallback for Candidate B if GLM is throttled
    if not candidate_b_generated and openrouter_key:
        try:
            print("  ... Junior Dev 2 drafting Candidate B via secondary provider...")
            from langchain_openai import ChatOpenAI
            llm_fallback = ChatOpenAI(
                model=os.getenv("OPENROUTER_MODEL", "nex-agi/nex-n2.5-mini:free"),
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_key,
                temperature=0.4,
                max_tokens=600,
                request_timeout=20,
            )
            prompt_b = (
                f"You are Junior Developer 2. Write an alternative, defensive Python implementation for `main.py` to accomplish:\n"
                f"{task}\n\n"
                f"Unit Test Suite Contract:\n{test_code}\n\n"
                "Return ONLY executable Python code for `main.py`."
            )
            resp_b = llm_fallback.invoke(prompt_b)
            clean_b = extract_python_code(resp_b.content)
            if clean_b:
                cand_b_code = clean_b
        except Exception as err:
            print(f"  [Junior Dev 2 Notice] Secondary provider notice: {err}")

    return {
        "candidate_a": {"main.py": cand_a_code},
        "candidate_b": {"main.py": cand_b_code},
    }
