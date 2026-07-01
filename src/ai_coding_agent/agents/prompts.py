"""Prompt builders for the coding agent."""

import os

from ai_coding_agent.core import AgentRequest, CommandResult, RepositorySummary
from ai_coding_agent.llm import Prompt

MAX_CONTEXT_CHARS = 12_000
MAX_FILE_CHARS = 3_000


SYSTEM_PROMPT = """You are a senior Python software engineer.
Return only a unified diff patch. Do not include markdown fences.
Every file hunk must include diff --git, --- path, +++ path, and @@ headers.
Do not include ? marker lines, explanations, prose, or comments outside the diff.
Keep changes minimal, readable, and production quality."""


def build_patch_prompt(request: AgentRequest, summary: RepositorySummary) -> Prompt:
    """Build the initial patch-generation prompt."""

    files = _build_context(request.instruction, summary)
    return Prompt(
        system=SYSTEM_PROMPT,
        user=(
            f"Instruction:\n{request.instruction}\n\n"
            f"Repository files:\n{files}\n\n"
            "Generate a unified diff patch for the requested change."
        ),
    )


def build_fix_prompt(
    request: AgentRequest,
    summary: RepositorySummary,
    failure: CommandResult,
) -> Prompt:
    """Build a prompt for fixing a failed command after a patch."""

    files = _build_context(
        f"{request.instruction}\n{failure.stderr or failure.stdout}",
        summary,
    )
    return Prompt(
        system=SYSTEM_PROMPT,
        user=(
            f"Instruction:\n{request.instruction}\n\n"
            f"The verification command failed:\n{failure.stderr or failure.stdout}\n\n"
            f"Current repository files:\n{files}\n\n"
            "Generate a minimal unified diff patch that fixes the failure."
        ),
    )


def _build_context(query: str, summary: RepositorySummary) -> str:
    max_context_chars = _int_from_env("AGENT_MAX_CONTEXT_CHARS", MAX_CONTEXT_CHARS)
    max_file_chars = _int_from_env("AGENT_MAX_FILE_CHARS", MAX_FILE_CHARS)
    ranked_files = sorted(
        summary.files,
        key=lambda file: _score_file(query, file.path.as_posix(), file.content),
        reverse=True,
    )
    chunks: list[str] = []
    used_chars = 0

    for file in ranked_files:
        content = _truncate_content(file.content, max_file_chars)
        chunk = f"--- {file.path.as_posix()} ---\n{content}"
        if used_chars + len(chunk) > max_context_chars:
            remaining = max_context_chars - used_chars
            if remaining <= 500:
                break
            chunks.append(chunk[:remaining])
            break
        chunks.append(chunk)
        used_chars += len(chunk) + 2

    return "\n\n".join(chunks)


def _score_file(query: str, path: str, content: str) -> int:
    terms = {
        term.casefold()
        for term in query.replace("\\", " ").replace("/", " ").split()
        if len(term) >= 3
    }
    searchable_path = path.casefold()
    searchable_content = content.casefold()
    score = 0
    for term in terms:
        if term in searchable_path:
            score += 5
        if term in searchable_content:
            score += 1
    if path.endswith(".py"):
        score += 2
    return score


def _truncate_content(content: str, max_chars: int) -> str:
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + "\n... [truncated]"


def _int_from_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default
