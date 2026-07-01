from pathlib import Path

from ai_coding_agent.agents.prompts import MAX_CONTEXT_CHARS, build_patch_prompt
from ai_coding_agent.core import AgentRequest, FileSnapshot, RepositorySummary


def test_patch_prompt_limits_repository_context(tmp_path: Path) -> None:
    summary = RepositorySummary(
        root=tmp_path,
        files=[
            FileSnapshot(path=Path("large.py"), content="x = 1\n" * 20_000),
            FileSnapshot(path=Path("small.py"), content="def target(): pass\n"),
        ],
    )
    request = AgentRequest(
        instruction="change target",
        repository_path=tmp_path,
    )

    prompt = build_patch_prompt(request, summary)

    assert len(prompt.user) < MAX_CONTEXT_CHARS + 1_000
    assert "... [truncated]" in prompt.user
