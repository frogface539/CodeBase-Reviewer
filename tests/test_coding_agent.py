from pathlib import Path

from ai_coding_agent.agents import CodingAgent
from ai_coding_agent.core import AgentRequest, CommandResult, Patch
from ai_coding_agent.execution import CommandRunner
from ai_coding_agent.llm import Prompt
from ai_coding_agent.repository import GitPatchApplier, RepositoryReader


class StaticLlm:
    def __init__(self, response: str) -> None:
        self.response = response
        self.prompts: list[Prompt] = []

    def complete(self, prompt: Prompt) -> str:
        self.prompts.append(prompt)
        return self.response


class RecordingPatchApplier(GitPatchApplier):
    def __init__(self) -> None:
        self.patch: Patch | None = None

    def apply(self, repository_path: Path, patch: Patch) -> None:
        self.patch = patch


class PassingRunner(CommandRunner):
    def run(self, cwd: Path, command: tuple[str, ...]) -> CommandResult:
        return CommandResult(command=command, return_code=0)


def test_coding_agent_generates_patch_and_runs_verification(tmp_path: Path) -> None:
    (tmp_path / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
    llm = StaticLlm("diff --git a/module.py b/module.py\n")
    patch_applier = RecordingPatchApplier()
    agent = CodingAgent(
        llm=llm,
        repository_reader=RepositoryReader(),
        patch_applier=patch_applier,
        command_runner=PassingRunner(),
    )

    result = agent.run(
        AgentRequest(
            instruction="change value",
            repository_path=tmp_path,
            test_command=("pytest",),
        )
    )

    assert result.summary == "Patch applied and verification passed."
    assert result.patch_applied is True
    assert patch_applier.patch == Patch(diff="diff --git a/module.py b/module.py")
    assert len(llm.prompts) == 1
