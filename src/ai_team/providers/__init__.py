"""Provider resilience.

The older provider protocol classes and mock implementations moved to
`ai_team._legacy.providers`: they described a four-role design that the
compiled graph no longer uses, and the mock runner executed commands on the
host with `shell=True`.

What lives here now is the layer that makes free-tier reality survivable
without lying about it.
"""

from ai_team.providers.resilience import (
    AllProvidersUnavailableError,
    InvalidModelOutput,
    ProviderOutcome,
    RoleProvider,
    announce_recoveries,
    call_with_office_presence,
    classify_provider_error,
    get_provider_health,
)

__all__ = [
    "AllProvidersUnavailableError",
    "InvalidModelOutput",
    "ProviderOutcome",
    "RoleProvider",
    "announce_recoveries",
    "call_with_office_presence",
    "classify_provider_error",
    "get_provider_health",
]
