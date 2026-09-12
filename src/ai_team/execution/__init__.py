"""Execution, workspace confinement, and sandbox isolation."""

from ai_team.execution.bundle import (
    BundleTamperError,
    build_bundle,
    bundle_file_list,
    compute_bundle_digest,
    verify_bundle_integrity,
)
from ai_team.execution.workspace import (
    PathConfinementError,
    create_run_workspace,
    validate_path_confinement,
    write_bundle_files,
)

# NOTE: `MockSandboxRunner` used to be exported here. It executed declared
# commands on the host with `shell=True`, so merely importing this package made
# a host-execution path reachable. It is quarantined in `ai_team._legacy` and
# is deliberately not re-exported. The only supported way to run code is
# `ai_team.execution.sandbox.get_sandbox_runner()`.

__all__ = [
    "BundleTamperError",
    "PathConfinementError",
    "build_bundle",
    "bundle_file_list",
    "compute_bundle_digest",
    "create_run_workspace",
    "validate_path_confinement",
    "verify_bundle_integrity",
    "write_bundle_files",
]
