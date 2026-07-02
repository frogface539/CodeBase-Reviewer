"""HTTP request models for the FastAPI application."""

from pathlib import Path

from pydantic import BaseModel, Field


class RepositoryRequest(BaseModel):
    """Request body for repository-level operations."""

    repository_path: Path


class RepositorySearchRequest(RepositoryRequest):
    """Request body for searching repository text."""

    query: str = Field(min_length=1)


class RepositoryExplainRequest(RepositoryRequest):
    """Request body for read-only repository explanations."""

    question: str = Field(default="What is this repository about?", min_length=1)


class AgentRunRequest(RepositoryRequest):
    """Request body for running the coding agent from HTTP."""

    instruction: str = Field(min_length=1)
    patch_diff: str | None = None
    test_command: list[str] | None = None
    max_fix_attempts: int = Field(default=1, ge=0, le=5)
