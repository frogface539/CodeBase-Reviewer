"""OpenAI-compatible chat completions client."""

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

from ai_coding_agent.core import AgentError
from ai_coding_agent.llm.client import Prompt


@dataclass(frozen=True)
class OpenAiSettings:
    """Configuration for an OpenAI-compatible chat completions endpoint."""

    api_key: str
    model: str = "gpt-4.1-mini"
    base_url: str = "https://api.openai.com/v1"
    timeout_seconds: int = 120
    provider_name: str = "OpenAI-compatible provider"

    @classmethod
    def from_env(cls) -> "OpenAiSettings | None":
        """Load settings from environment variables when available."""

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        return cls(
            api_key=api_key,
            model=os.getenv("OPENAI_MODEL", cls.model),
            base_url=os.getenv("OPENAI_BASE_URL", cls.base_url).rstrip("/"),
            provider_name="OpenAI",
        )


class OpenAiChatLlm:
    """LLM client using an OpenAI-compatible chat completions API."""

    def __init__(self, settings: OpenAiSettings) -> None:
        self._settings = settings

    def complete(self, prompt: Prompt) -> str:
        """Return a text completion for the given prompt."""

        payload = {
            "model": self._settings.model,
            "messages": [
                {"role": "system", "content": prompt.system},
                {"role": "user", "content": prompt.user},
            ],
            "temperature": 0,
        }
        request = urllib.request.Request(
            f"{self._settings.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self._settings.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "ai-coding-agent/0.1.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self._settings.timeout_seconds,
            ) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise AgentError(self._format_error(detail)) from exc
        except urllib.error.URLError as exc:
            raise AgentError(self._format_error(str(exc.reason))) from exc

        return self._extract_text(body)

    def _extract_text(self, body: dict[str, object]) -> str:
        choices = body.get("choices")
        if not isinstance(choices, list) or not choices:
            raise AgentError("LLM response did not include choices.")
        first = choices[0]
        if not isinstance(first, dict):
            raise AgentError("LLM response choice was malformed.")
        message = first.get("message")
        if not isinstance(message, dict):
            raise AgentError("LLM response message was malformed.")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise AgentError("LLM response did not include patch content.")
        return content

    def _format_error(self, detail: str) -> str:
        if "1010" in detail:
            return (
                f"{self._settings.provider_name} rejected the request with code 1010. "
                "Check that the API key, base URL, and model are correct. If this is "
                "Groq, make sure GROQ_BASE_URL is https://api.groq.com/openai/v1."
            )
        return f"LLM request failed: {detail}"
