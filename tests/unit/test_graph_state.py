"""Unit tests for LangGraph state schema and manager RFC node."""

import pytest
from ai_team.graph.state import TriadCouncilState
from ai_team.graph.nodes.manager import manager_rfc_node


def test_manager_rfc_valid_prompt():
    state: TriadCouncilState = {"task_prompt": "Convert CSV to JSON"}
    result = manager_rfc_node(state)
    assert "manager_rfc" in result
    assert len(result["manager_rfc"]["acceptance_criteria"]) > 0


def test_manager_rfc_incorporates_feedback():
    state: TriadCouncilState = {
        "task_prompt": "Convert CSV to JSON",
        "human_feedback": "Ensure strict RFC4180 compliance",
    }
    result = manager_rfc_node(state)
    assert "manager_rfc" in result

