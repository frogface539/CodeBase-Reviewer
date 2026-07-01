"""Manual patch provider for local UI and API workflows."""

from ai_coding_agent.llm.client import Prompt


class ManualPatchLlm:
    """Returns a caller-supplied unified diff through the LLM protocol."""

    def __init__(self, patch_diff: str) -> None:
        self._patch_diff = patch_diff

    def complete(self, prompt: Prompt) -> str:
        """Return the configured patch diff."""

        return self._patch_diff
