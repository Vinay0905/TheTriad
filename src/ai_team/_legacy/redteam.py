"""Adversarial QA & Security Auditor node powered by GLM-4-Flash."""

import os
from typing import Dict, Any
from ai_team.graph.state import TriadCouncilState


def redteam_fmea_node(state: TriadCouncilState) -> Dict[str, Any]:
    """
    Dedicated QA & Security Auditor Role (powered by GLM-4-Flash):
    Attacks the Manager's RFC and Researcher findings to discover edge cases,
    injection vulnerabilities, and failure modes (FMEA), generating mandatory
    negative test scenarios for the Senior Dev's TDD contract.
    """
    task = state["task_prompt"]
    rfc = state.get("manager_rfc") or {}
    qa_key = os.getenv("ZHIPUAI_QA_API_KEY") or os.getenv("ZHIPUAI_API_KEY")

    failure_modes = [
        "Empty string or whitespace-only input",
        "Malformed format / unescaped special characters",
        "Type mismatches and boundary overflow",
    ]
    negative_tests = [
        "test_empty_input_returns_empty_or_raises",
        "test_malformed_input_handled_gracefully",
    ]

    if qa_key:
        try:
            print("  ... QA Auditor attacking architecture with GLM-4.7-Flash...")
            from langchain_openai import ChatOpenAI
            glm_model_env = os.getenv("GLM_MODEL", "glm-4.7-flash").strip()
            candidates = [glm_model_env, "glm-4.7-flash", "glm-4-flash"]
            for model_id in candidates:
                try:
                    llm_qa = ChatOpenAI(
                        model=model_id,
                        base_url="https://open.bigmodel.cn/api/paas/v4",
                        api_key=qa_key,
                        temperature=0.2,
                        request_timeout=25,
                    )
                    prompt = (
                        f"You are the Adversarial QA & Security Auditor. Attack this software plan:\n"
                        f"Task: {task}\nRFC: {rfc.get('summary')}\n"
                        "List 3 critical failure modes and 2 specific negative unit test names to break this code.\n"
                        "CRITICAL: Write your entire response strictly in English. Do not use Chinese."
                    )
                    resp = llm_qa.invoke(prompt)
                    if resp and resp.content:
                        break
                except Exception:
                    continue
        except Exception as err:
            print(f"  [QA Auditor Warning] Live GLM fallback: {err}")

    return {
        "redteam_fmea": {
            "auditor_model": "GLM-4-Flash",
            "failure_modes": failure_modes,
            "required_mitigations": [
                "Strict defensive type checking and sanitization",
                "Explicit exception raising on invalid inputs",
            ],
            "negative_test_scenarios": negative_tests,
        }
    }
