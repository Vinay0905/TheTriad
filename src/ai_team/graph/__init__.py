"""LangGraph multi-agent orchestration package.

The compiled graph in `builder` is the only pipeline. Its routers live there
too; the previously exported `route_human_gate` / `route_post_execution` came
from an unwired module and are now quarantined in `ai_team._legacy.routers`.
"""

from ai_team.graph.builder import GATE_NODE, build_triad_graph, route_gate, route_qa, route_tdd
from ai_team.graph.gate_decision import parse_gate_decision
from ai_team.graph.state import TriadCouncilState

__all__ = [
    "GATE_NODE",
    "TriadCouncilState",
    "build_triad_graph",
    "parse_gate_decision",
    "route_gate",
    "route_qa",
    "route_tdd",
]
