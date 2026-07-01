"""LLM client protocol and prompt model."""

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class Prompt(BaseModel):
    """A structured prompt sent to an LLM."""

    system: str
    user: str = Field(min_length=1)

    model_config = ConfigDict(frozen=True)


class LlmClient(Protocol):
    """Protocol implemented by concrete LLM providers."""

    def complete(self, prompt: Prompt) -> str:
        """Return a text completion for the given prompt."""
