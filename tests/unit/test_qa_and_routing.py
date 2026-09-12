"""QA must fail closed, and routing must never send an unapproved run to the sandbox."""

import sys
import types

import pytest

from ai_team.graph.builder import route_gate, route_qa, route_tdd
from ai_team.graph.contract_lock import compute_test_digest
from ai_team.graph.nodes.developer import developer_node
from ai_team.graph.nodes.qa_audit import qa_audit_node

FROZEN_SUITE = (
    "import unittest\n"
    "from main import convert\n\n"
    "class TestConvert(unittest.TestCase):\n"
    "    def test_converts(self):\n"
    "        self.assertEqual(convert('a'), 'A')\n"
)

PROVIDER_ENV = (
    "OPENROUTER_API_KEY",
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
    "GROQ_RESEARCHER_API_KEY",
    "ZHIPUAI_API_KEY",
    "ZHIPUAI_QA_API_KEY",
    "ZHIPUAI_DEV_API_KEY",
)


@pytest.fixture
def no_providers(monkeypatch):
    for name in PROVIDER_ENV:
        monkeypatch.delenv(name, raising=False)


def _state(**overrides):
    state = {
        "task_prompt": "Uppercase a string",
        "tdd_contract": {"test_main.py": FROZEN_SUITE},
        "tdd_digest": compute_test_digest(FROZEN_SUITE),
        "tdd_locked": True,
        "tdd_status": "LOCKED",
        "synthesized_code": {"main.py": "def convert(v):\n    return v.upper()\n"},
        "repair_attempts": 0,
    }
    state.update(overrides)
    return state


def _fake_langchain_openai(monkeypatch, behaviour):
    """Install a stand-in `langchain_openai` module."""
    module = types.ModuleType("langchain_openai")

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            pass

        def invoke(self, _prompt):
            return behaviour()

    module.ChatOpenAI = FakeChatOpenAI
    monkeypatch.setitem(sys.modules, "langchain_openai", module)


class _Response:
    def __init__(self, content):
        self.content = content


# -- QA fails closed ----------------------------------------------------


def test_no_auditor_credentials_is_not_a_pass(no_providers):
    result = qa_audit_node(_state())

    assert result["qa_passed"] is False
    assert result["qa_skipped"] is True
    assert "QA unavailable" in result["qa_feedback"]


def test_rate_limited_auditor_is_not_a_pass(monkeypatch):
    """A 429 used to set qa_passed = True, so a quota error read as a pass."""
    monkeypatch.setenv("ZHIPUAI_QA_API_KEY", "test-key")

    def rate_limited():
        raise RuntimeError("Error code: 429 - rate limit exceeded (1305)")

    _fake_langchain_openai(monkeypatch, rate_limited)

    result = qa_audit_node(_state())

    assert result["qa_passed"] is False
    assert result["qa_skipped"] is True
    assert "unavailable" in result["qa_feedback"].lower()


def test_unavailable_auditor_does_not_consume_a_repair_attempt(monkeypatch):
    monkeypatch.setenv("ZHIPUAI_QA_API_KEY", "test-key")
    _fake_langchain_openai(
        monkeypatch, lambda: (_ for _ in ()).throw(RuntimeError("boom"))
    )

    result = qa_audit_node(_state(repair_attempts=1))
    assert result["repair_attempts"] == 1


def test_failing_audit_consumes_a_repair_attempt(monkeypatch):
    monkeypatch.setenv("ZHIPUAI_QA_API_KEY", "test-key")
    _fake_langchain_openai(
        monkeypatch,
        lambda: _Response("STATUS: FAIL\nREASON: Unbounded growth on empty input."),
    )

    result = qa_audit_node(_state(repair_attempts=0))

    assert result["qa_passed"] is False
    assert result["qa_skipped"] is False
    assert result["repair_attempts"] == 1
    assert "Unbounded growth" in result["qa_feedback"]


def test_passing_audit_does_not_consume_a_repair_attempt(monkeypatch):
    """Incrementing on success used to miscount the bounded loop."""
    monkeypatch.setenv("ZHIPUAI_QA_API_KEY", "test-key")
    _fake_langchain_openai(
        monkeypatch, lambda: _Response("STATUS: PASS\nSUMMARY: Looks correct.")
    )

    result = qa_audit_node(_state(repair_attempts=1))

    assert result["qa_passed"] is True
    assert result["repair_attempts"] == 1


def test_empty_implementation_fails_qa(no_providers):
    result = qa_audit_node(_state(synthesized_code={"main.py": "   "}))
    assert result["qa_passed"] is False
    assert "empty" in result["qa_feedback"].lower()


def test_broken_implementation_fails_qa(no_providers):
    result = qa_audit_node(_state(synthesized_code={"main.py": "def convert(:\n"}))
    assert result["qa_passed"] is False
    assert "syntax" in result["qa_feedback"].lower()


def test_invalid_contract_fails_qa(no_providers):
    result = qa_audit_node(
        _state(tdd_status="INVALID", tdd_failure_reason="no provider produced a suite")
    )
    assert result["qa_passed"] is False
    assert "no provider produced a suite" in result["qa_feedback"]


@pytest.mark.parametrize(
    "behaviour",
    [
        lambda: _Response("STATUS: PASS\nSUMMARY: fine"),
        lambda: _Response("STATUS: FAIL\nREASON: broken"),
    ],
)
def test_qa_never_returns_the_contract(monkeypatch, behaviour):
    """Rewriting tdd_contract here is what destroyed the frozen contract."""
    monkeypatch.setenv("ZHIPUAI_QA_API_KEY", "test-key")
    _fake_langchain_openai(monkeypatch, behaviour)

    result = qa_audit_node(_state())
    assert "tdd_contract" not in result


# -- developer cannot touch the contract --------------------------------


def test_developer_copies_the_frozen_suite_verbatim(no_providers):
    result = developer_node(_state())
    assert result["synthesized_code"]["test_main.py"] == FROZEN_SUITE


def test_developer_reports_failure_instead_of_a_stub(no_providers):
    """There used to be a generate_html() Hello World fallback here."""
    result = developer_node(_state())

    assert result["synthesized_code"]["main.py"] == ""
    assert "generate_html" not in str(result)
    assert "Hello world" not in str(result)
    assert result["provider_attribution"]["main.py"] == "none"


# -- routing ------------------------------------------------------------


def test_unapproved_states_never_route_to_the_sandbox():
    for status in (None, "", "PENDING", "ABORTED", "STEERED", "approved", "UNKNOWN"):
        assert route_gate({"approval_status": status}) != "sandbox_execution_node"

    assert route_gate({}) == "manager_final_report_node"


def test_only_exact_approval_routes_to_the_sandbox():
    assert route_gate({"approval_status": "APPROVED"}) == "sandbox_execution_node"


def test_steered_returns_to_the_council():
    assert route_gate({"approval_status": "STEERED"}) == "manager_rfc_node"


def test_failed_audit_within_budget_returns_to_the_developer():
    assert route_qa({"qa_passed": False, "repair_attempts": 0}) == "developer_node"
    assert route_qa({"qa_passed": False, "repair_attempts": 1}) == "developer_node"


def test_exhausted_budget_advances_to_the_gate_still_failing():
    assert route_qa({"qa_passed": False, "repair_attempts": 2}) == "preflight_gate_node"


def test_unavailable_auditor_advances_without_burning_repairs():
    state = {"qa_passed": False, "qa_skipped": True, "repair_attempts": 0}
    assert route_qa(state) == "preflight_gate_node"


def test_passing_audit_advances_to_the_gate():
    assert route_qa({"qa_passed": True, "repair_attempts": 0}) == "preflight_gate_node"


def test_missing_qa_result_is_treated_as_failure():
    """An absent verdict must not be optimistically read as a pass."""
    assert route_qa({"repair_attempts": 0}) == "developer_node"


def test_invalid_contract_ends_the_run():
    assert route_tdd({"tdd_status": "INVALID"}) == "manager_final_report_node"


def test_locked_contract_proceeds_to_implementation():
    assert route_tdd({"tdd_status": "LOCKED"}) == "developer_node"
