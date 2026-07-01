"""Main coding-agent orchestration."""

from ai_coding_agent.agents.prompts import build_fix_prompt, build_patch_prompt
from ai_coding_agent.core import AgentRequest, AgentResult, CommandResult, Patch
from ai_coding_agent.execution import CommandRunner
from ai_coding_agent.llm import LlmClient
from ai_coding_agent.repository import GitPatchApplier, RepositoryReader
from ai_coding_agent.storage import RunStore


class CodingAgent:
    """Coordinates repository reading, patch generation, execution, and storage."""

    def __init__(
        self,
        llm: LlmClient,
        repository_reader: RepositoryReader,
        patch_applier: GitPatchApplier,
        command_runner: CommandRunner,
        run_store: RunStore | None = None,
    ) -> None:
        self._llm = llm
        self._repository_reader = repository_reader
        self._patch_applier = patch_applier
        self._command_runner = command_runner
        self._run_store = run_store

    def run(self, request: AgentRequest) -> AgentResult:
        """Run the coding agent for one user instruction."""

        repository_path = request.repository_path.resolve()
        summary = self._repository_reader.summarize(repository_path)
        patch_text = self._llm.complete(build_patch_prompt(request, summary)).strip()
        self._patch_applier.apply(repository_path, Patch(diff=patch_text))

        test_result = None
        fix_attempts = 0
        if request.test_command is not None:
            test_result = self._command_runner.run(
                repository_path,
                request.test_command,
            )
            while (
                not test_result.succeeded
                and fix_attempts < request.max_fix_attempts
            ):
                fix_attempts += 1
                summary = self._repository_reader.summarize(repository_path)
                fix_text = self._llm.complete(
                    build_fix_prompt(request, summary, test_result)
                ).strip()
                self._patch_applier.apply(repository_path, Patch(diff=fix_text))
                test_result = self._command_runner.run(
                    repository_path,
                    request.test_command,
                )

        result = AgentResult(
            request=request,
            summary=self._summarize_result(test_result),
            patch_applied=True,
            test_result=test_result,
            fix_attempts=fix_attempts,
        )
        if self._run_store is not None:
            self._run_store.save(result)
        return result

    def _summarize_result(self, test_result: CommandResult | None) -> str:
        if test_result is None:
            return "Patch applied. No verification command was provided."
        if test_result.succeeded:
            return "Patch applied and verification passed."
        return "Patch applied, but verification failed."
