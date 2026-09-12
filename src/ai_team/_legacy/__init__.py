"""Quarantined code. Not part of the live system.

Everything here predates or sits outside the compiled LangGraph graph in
`ai_team.graph.builder`:

- `orchestration/` is a second, independent approval state machine. Having two
  implementations of the confirmation gate is exactly the split-brain problem
  that let tests pass while the live path misbehaved, so it is no longer
  imported anywhere.
- `routers.py` references nodes that were never wired (`clean_abort_node`,
  `senior_micro_repair_node`, `macro_escalation_node`). The live routers are in
  `ai_team.graph.builder`.
- `junior_dev.py`, `senior_review.py`, `redteam.py` are tournament-mode nodes,
  not registered in the graph.
- `antigravity_dev.py` is the Antigravity SDK adapter, unused by the live
  execution path. If it is ever revived it must still read `GEMINI_API_KEY`.

Nothing in `ai_team` imports this package. It is retained for reference only;
do not add imports from live code.
"""
