from pathlib import Path

from ai_coding_agent.api import AgentService
from ai_coding_agent.core import AgentRequest, AgentResult


class RecordingAgent:
    def __init__(self) -> None:
        self.request: AgentRequest | None = None

    def run(self, request: AgentRequest) -> AgentResult:
        self.request = request
        return AgentResult(
            request=request,
            summary="ok",
            patch_applied=True,
        )


def test_agent_service_builds_request(tmp_path: Path) -> None:
    agent = RecordingAgent()
    service = AgentService(agent)

    result = service.run("change it", tmp_path, ("pytest",), max_fix_attempts=2)

    assert result.summary == "ok"
    assert agent.request == AgentRequest(
        instruction="change it",
        repository_path=tmp_path,
        test_command=("pytest",),
        max_fix_attempts=2,
    )
