"""Unit tests for AST syntax validation and truncated code repair."""

import pytest
from ai_team.utils import validate_python_syntax, repair_truncated_python_code
from ai_team.graph.nodes.qa_audit import qa_audit_node
from ai_team.graph.nodes.preflight import preflight_gate_node


def test_validate_python_syntax_valid():
    code = (
        "import unittest\n"
        "class TestApp(unittest.TestCase):\n"
        "    def test_ok(self):\n"
        "        self.assertTrue(True)\n"
    )
    is_valid, err = validate_python_syntax(code)
    assert is_valid is True
    assert err == ""


def test_validate_python_syntax_truncated():
    # Simulates the exact user bug where code was cut off at line 60
    broken_code = (
        "import unittest\n"
        "class TestApp(unittest.TestCase):\n"
        "    def test_ok(self):\n"
        "        self.assertTrue(True)\n"
        "    def test_broken(self):\n"
        "        self.assertIsInstance(html\n"
    )
    is_valid, err = validate_python_syntax(broken_code)
    assert is_valid is False
    assert "SyntaxError" in err


def test_repair_truncated_python_code():
    broken_code = (
        "import unittest\n"
        "class TestApp(unittest.TestCase):\n"
        "    def test_ok(self):\n"
        "        self.assertTrue(True)\n"
        "    def test_broken(self):\n"
        "        self.assertIsInstance(html\n"
    )
    healed = repair_truncated_python_code(broken_code)
    is_valid, err = validate_python_syntax(healed)
    assert is_valid is True
    assert "def test_ok" in healed
    assert "__main__" in healed


def test_qa_audit_catches_syntax_error():
    # When given broken main.py, QA Maya immediately catches it
    state = {
        "task_prompt": "build hello world",
        "synthesized_code": {
            "main.py": "def broken(\n",
            "test_main.py": "import unittest\nclass T(unittest.TestCase):\n    pass\n",
        },
        "repair_attempts": 0,
    }
    result = qa_audit_node(state)
    assert result["qa_passed"] is False
    assert "SyntaxError in main.py" in result["qa_feedback"]



def test_preflight_guarantees_valid_bundle():
    state = {
        "task_prompt": "build hello world",
        "synthesized_code": {
            "main.py": "def generate_html(): return '<h1>Hello</h1>'",
            "test_main.py": "import unittest\nclass T(unittest.TestCase):\n    def test_x(self): self.assertIsInstance(html\n",
        },
        "tdd_contract": {},
        "manager_rfc": {},
    }
    result = preflight_gate_node(state)
    bundle = result["execution_bundle"]
    test_code = bundle["test_files"]["test_main.py"]
    is_valid, _ = validate_python_syntax(test_code)
    assert is_valid is True
