"""Provider protocols and implementations."""

from ai_team._legacy.providers.base import (
    ManagerProvider,
    ResearcherProvider,
    JuniorDevProvider,
    SeniorReviewerProvider,
    SeniorExecutorProvider,
)
from ai_team._legacy.providers.mocks import (
    MockManager,
    MockResearcher,
    MockJuniorDev,
    MockSeniorReviewer,
    MockSeniorExecutor,
)

__all__ = [
    "ManagerProvider",
    "ResearcherProvider",
    "JuniorDevProvider",
    "SeniorReviewerProvider",
    "SeniorExecutorProvider",
    "MockManager",
    "MockResearcher",
    "MockJuniorDev",
    "MockSeniorReviewer",
    "MockSeniorExecutor",
]
