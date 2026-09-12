"""Mechanical enforcement of the frozen TDD contract.

The premise of contract-first TDD is that the test suite is written before the
implementation and is then immutable. If a downstream node can rewrite the
tests to make broken code pass, the whole exercise is theatre.

So the lock is cryptographic rather than advisory: `tdd_contract_node` records
a digest of the test source, and every node downstream asserts the digest still
matches before doing anything. Nothing here depends on a model behaving well.
"""

import ast
import hashlib
from typing import Any, Dict, Optional, Set, Tuple

TEST_FILENAME = "test_main.py"
INTERFACES_FILENAME = "interfaces.py"

# Calls that merely prove a module exists. A suite made only of these passes
# against any implementation whatsoever, which is the cheat we are blocking.
_EXISTENCE_PROBES = frozenset({"hasattr", "dir"})


class ContractBrokenError(RuntimeError):
    """Raised when the frozen test suite no longer matches its recorded digest."""


class ContractInvalidError(ValueError):
    """Raised when a generated test suite is unparseable or vacuous."""


def compute_test_digest(test_source: str) -> str:
    """Digest the exact bytes of the test suite."""
    return hashlib.sha256((test_source or "").encode("utf-8")).hexdigest()


def frozen_test_source(state: Dict[str, Any]) -> str:
    """The authoritative test suite. Always read tests through this."""
    return (state.get("tdd_contract") or {}).get(TEST_FILENAME, "")


def freeze_contract(test_source: str, interfaces_source: str) -> Dict[str, Any]:
    """Build the state delta that locks the contract."""
    return {
        "tdd_contract": {
            INTERFACES_FILENAME: interfaces_source,
            TEST_FILENAME: test_source,
        },
        "tdd_digest": compute_test_digest(test_source),
        "tdd_locked": True,
    }


def assert_contract_unbroken(state: Dict[str, Any], where: str) -> None:
    """Verify the frozen suite is byte-identical to what was locked.

    A no-op before the contract is locked, so it is safe to call anywhere.
    """
    expected = state.get("tdd_digest")
    if not expected:
        return

    actual = compute_test_digest(frozen_test_source(state))
    if actual != expected:
        raise ContractBrokenError(
            f"Frozen test contract was modified before {where}. "
            f"Expected digest {expected[:12]}..., found {actual[:12]}.... "
            "Tests are immutable after the TDD node."
        )


def _main_symbols(tree: ast.AST) -> Set[str]:
    """Names the suite pulled out of `main`, plus `main` itself if imported."""
    symbols: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "main":
            for alias in node.names:
                symbols.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "main":
                    symbols.add(alias.asname or "main")
    return symbols


def _references_main(node: ast.AST, symbols: Set[str]) -> bool:
    """Whether a subtree actually touches the implementation under test."""
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id in symbols:
            return True
        if (
            isinstance(child, ast.Attribute)
            and isinstance(child.value, ast.Name)
            and child.value.id == "main"
        ):
            return True
    return False


def _assert_calls(node: ast.AST):
    for child in ast.walk(node):
        if (
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Attribute)
            and child.func.attr.startswith("assert")
        ):
            yield child


def _is_substantive_assert(call: ast.Call) -> bool:
    """An assertion that could actually fail against a wrong implementation."""
    args = list(call.args)
    if not args:
        return False

    # self.assertTrue(hasattr(main, '__name__')) and friends.
    for arg in args:
        if (
            isinstance(arg, ast.Call)
            and isinstance(arg.func, ast.Name)
            and arg.func.id in _EXISTENCE_PROBES
        ):
            return False

    # self.assertIsNotNone(main) - asserts the import worked, nothing more.
    if len(args) == 1 and isinstance(args[0], ast.Name) and args[0].id == "main":
        return False

    # self.assertTrue(True) / self.assertEqual(1, 1) - vacuous by construction.
    if all(isinstance(arg, ast.Constant) for arg in args):
        return False

    return True


def validate_test_contract(test_source: str) -> Tuple[bool, Optional[str]]:
    """Check that a generated suite is parseable and actually tests something.

    This is the analogue of "RED must fail for the right reason": a suite that
    cannot fail is not a contract, and must be rejected rather than silently
    replaced with a stub.
    """
    if not (test_source or "").strip():
        return False, "test suite is empty"

    try:
        tree = ast.parse(test_source)
    except SyntaxError as err:
        return False, f"test suite has a syntax error: {err}"

    symbols = _main_symbols(tree)
    if not symbols:
        return False, "test suite never imports the `main` module under test"

    test_methods = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test")
    ]
    if not test_methods:
        return False, "test suite declares no test methods"

    for method in test_methods:
        if not _references_main(method, symbols):
            continue
        if any(_is_substantive_assert(call) for call in _assert_calls(method)):
            return True, None

    return (
        False,
        "test suite is tautological: no test method makes an assertion that "
        "could fail against a wrong implementation",
    )
