"""The frozen test contract is the product's anti-cheat. These tests police it."""

import pytest

from ai_team.graph.contract_lock import (
    ContractBrokenError,
    assert_contract_unbroken,
    compute_test_digest,
    freeze_contract,
    frozen_test_source,
    validate_test_contract,
)

REAL_SUITE = """
import unittest
from main import convert_csv

class TestConvert(unittest.TestCase):
    def test_converts_a_row(self):
        self.assertEqual(convert_csv("a,b\\n1,2"), [{"a": "1", "b": "2"}])

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            convert_csv("")

if __name__ == '__main__':
    unittest.main()
"""

# The exact stub the old pipeline substituted whenever anything went wrong.
TAUTOLOGY_SUITE = """
import unittest
import main

class TestImplementation(unittest.TestCase):
    def test_basic_contract(self):
        self.assertTrue(hasattr(main, '__name__'))

if __name__ == '__main__':
    unittest.main()
"""


def _locked_state(suite: str = REAL_SUITE) -> dict:
    return dict(freeze_contract(suite, "from main import convert_csv"))


# -- digest and lock ----------------------------------------------------


def test_digest_is_byte_sensitive():
    assert compute_test_digest("a") != compute_test_digest("a ")
    assert compute_test_digest(REAL_SUITE) == compute_test_digest(REAL_SUITE)


def test_freeze_records_digest_and_sources():
    state = _locked_state()
    assert state["tdd_locked"] is True
    assert state["tdd_digest"] == compute_test_digest(REAL_SUITE)
    assert frozen_test_source(state) == REAL_SUITE


def test_unmodified_contract_passes():
    assert_contract_unbroken(_locked_state(), "a downstream node")


def test_rewriting_the_suite_is_detected():
    state = _locked_state()
    state["tdd_contract"]["test_main.py"] = TAUTOLOGY_SUITE

    with pytest.raises(ContractBrokenError):
        assert_contract_unbroken(state, "a downstream node")


def test_even_a_whitespace_edit_is_detected():
    state = _locked_state()
    state["tdd_contract"]["test_main.py"] = REAL_SUITE + "\n"

    with pytest.raises(ContractBrokenError):
        assert_contract_unbroken(state, "a downstream node")


def test_deleting_the_suite_is_detected():
    state = _locked_state()
    state["tdd_contract"] = {}

    with pytest.raises(ContractBrokenError):
        assert_contract_unbroken(state, "a downstream node")


def test_check_is_inert_before_the_contract_is_locked():
    """Safe to call anywhere, including before the TDD node has run."""
    assert_contract_unbroken({}, "an early node")
    assert_contract_unbroken({"tdd_contract": {"test_main.py": "anything"}}, "early")


# -- vacuity detection --------------------------------------------------


def test_real_suite_is_accepted():
    ok, reason = validate_test_contract(REAL_SUITE)
    assert ok, reason


def test_hasattr_tautology_is_rejected():
    ok, reason = validate_test_contract(TAUTOLOGY_SUITE)
    assert not ok
    assert "tautological" in reason


@pytest.mark.parametrize(
    "suite",
    [
        # assertTrue(True) cannot fail.
        """
import unittest
import main

class T(unittest.TestCase):
    def test_x(self):
        main.anything
        self.assertTrue(True)
""",
        # Asserting the module imported is not a behavioural assertion.
        """
import unittest
import main

class T(unittest.TestCase):
    def test_x(self):
        self.assertIsNotNone(main)
""",
        # Comparing constants cannot fail.
        """
import unittest
import main

class T(unittest.TestCase):
    def test_x(self):
        main.thing
        self.assertEqual(1, 1)
""",
    ],
)
def test_vacuous_assertions_are_rejected(suite):
    ok, _ = validate_test_contract(suite)
    assert not ok


def test_suite_using_locals_is_still_accepted():
    """A realistic suite assigns a result then asserts on it; that is fine."""
    suite = """
import unittest
from main import rate_limit

class T(unittest.TestCase):
    def test_allows_under_limit(self):
        result = rate_limit(1)
        self.assertEqual(result, True)
"""
    ok, reason = validate_test_contract(suite)
    assert ok, reason


def test_suite_that_never_imports_main_is_rejected():
    suite = """
import unittest

class T(unittest.TestCase):
    def test_x(self):
        self.assertEqual(2 + 2, 4)
"""
    ok, reason = validate_test_contract(suite)
    assert not ok
    assert "main" in reason


def test_syntax_error_is_rejected_not_repaired():
    ok, reason = validate_test_contract("import unittest\nclass T(:\n")
    assert not ok
    assert "syntax" in reason.lower()


def test_empty_suite_is_rejected():
    ok, _ = validate_test_contract("")
    assert not ok


def test_suite_with_no_test_methods_is_rejected():
    suite = """
import unittest
from main import thing

class T(unittest.TestCase):
    def helper(self):
        self.assertEqual(thing(), 1)
"""
    ok, reason = validate_test_contract(suite)
    assert not ok
    assert "no test methods" in reason
