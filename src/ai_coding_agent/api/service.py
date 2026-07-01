"""Application service for the coding agent."""

from pathlib import Path
from typing import Protocol

from ai_coding_agent.core import AgentRequest, AgentResult


class AgentRunner(Protocol):
    """Protocol for objects that can execute an agent request."""

    def run(self, request: AgentRequest) -> AgentResult:
        """Run one agent request."""


class AgentService:
    """Small API facade over the coding agent."""

    def __init__(self, agent: AgentRunner) -> None:
        self._agent = agent

    def run(
        self,
        instruction: str,
        repository_path: Path,
        test_command: tuple[str, ...] | None = None,
        max_fix_attempts: int = 1,
    ) -> AgentResult:
        """Run the agent using plain Python values."""

        request = AgentRequest(
            instruction=instruction,
            repository_path=repository_path,
            test_command=test_command,
            max_fix_attempts=max_fix_attempts,
        )
        return self._agent.run(request)
