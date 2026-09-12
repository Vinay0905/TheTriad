"""Unit tests for LangGraph state schema and triage node."""

import pytest
from ai_team.graph.state import TriadCouncilState
from ai_team.graph.nodes.triage import task_triage_node


def test_triage_valid_prompt():
    state: TriadCouncilState = {"task_prompt": "Convert CSV to JSON"}
    result = task_triage_node(state)
    assert result["triage_metadata"]["status"] == "TRIAGED"
    assert result["council_round"] == 1
    assert result["micro_repair_count"] == 0


def test_triage_empty_prompt_fails():
    state: TriadCouncilState = {"task_prompt": "   "}
    with pytest.raises(ValueError):
        task_triage_node(state)
