"""Groq chat completions settings."""

import os
from dataclasses import dataclass

from ai_coding_agent.llm.openai import OpenAiSettings


@dataclass(frozen=True)
class GroqSettings(OpenAiSettings):
    """Configuration for Groq's OpenAI-compatible chat completions endpoint."""

    model: str = "openai/gpt-oss-120b"
    base_url: str = "https://api.groq.com/openai/v1"
    provider_name: str = "Groq"

    @classmethod
    def from_env(cls) -> "GroqSettings | None":
        """Load Groq settings from environment variables when available."""

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None
        return cls(
            api_key=api_key,
            model=os.getenv("GROQ_MODEL", cls.model),
            base_url=os.getenv("GROQ_BASE_URL", cls.base_url).rstrip("/"),
            provider_name="Groq",
        )
