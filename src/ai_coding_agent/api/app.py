"""FastAPI application for the coding agent."""

from collections.abc import Callable
from pathlib import Path

import ai_coding_agent
import gradio as gr
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from ai_coding_agent.agents import CodingAgent
from ai_coding_agent.agents.prompts import build_explanation_prompt
from ai_coding_agent.api.schemas import (
    AgentRunRequest,
    RepositoryExplainRequest,
    RepositoryRequest,
    RepositorySearchRequest,
)
from ai_coding_agent.core import (
    AgentError,
    AgentRequest,
    AgentResult,
    RepositorySummary,
)
from ai_coding_agent.execution import CommandRunner
from ai_coding_agent.llm import (
    GroqSettings,
    LlmClient,
    ManualPatchLlm,
    OpenAiChatLlm,
    OpenAiSettings,
)
from ai_coding_agent.repository import GitPatchApplier, RepositoryReader
from ai_coding_agent.storage import JsonActivityStore, JsonRunStore
from ai_coding_agent.ui.gradio_app import create_gradio_app


def create_app(history_path: Path | None = None) -> FastAPI:
    """Create the FastAPI application and mount the Gradio UI."""

    load_dotenv(Path.cwd() / ".env")
    app = FastAPI(title="AI Coding Agent", version="0.1.0")
    reader = RepositoryReader()
    runner = CommandRunner()
    patch_applier = GitPatchApplier()
    store = JsonRunStore(history_path or Path(".agent") / "runs.json")
    activity_store = JsonActivityStore(Path(".agent") / "activity.json")

    def build_agent(patch_diff: str | None = None) -> CodingAgent:
        return CodingAgent(
            llm=_build_llm(patch_diff),
            repository_reader=reader,
            patch_applier=patch_applier,
            command_runner=runner,
            run_store=store,
        )

    app.state.repository_reader = reader
    app.state.run_store = store
    app.state.activity_store = activity_store
    app.state.agent_factory = build_agent

    @app.get("/health")
    def health() -> dict[str, str]:
        """Return service health."""

        return {"status": "ok"}

    @app.get("/debug/imports")
    def debug_imports() -> dict[str, str]:
        """Return import paths for debugging local editable installs."""

        return {"ai_coding_agent": str(Path(ai_coding_agent.__file__).resolve())}

    @app.get("/debug/llm")
    def debug_llm() -> dict[str, str]:
        """Return active LLM configuration without exposing secrets."""

        return _debug_llm_config()

    @app.post("/repositories/summary")
    def summarize_repository(request: RepositoryRequest) -> RepositorySummary:
        """Return a compact repository summary."""

        return _handle_errors(lambda: reader.summarize(request.repository_path))

    @app.post("/repositories/search")
    def search_repository(request: RepositorySearchRequest) -> RepositorySummary:
        """Return repository files matching a query."""

        def search() -> RepositorySummary:
            root = request.repository_path.resolve()
            return RepositorySummary(
                root=root,
                files=reader.search(root, request.query),
            )

        return _handle_errors(search)

    @app.post("/repositories/explain")
    def explain_repository(request: RepositoryExplainRequest) -> dict[str, str]:
        """Return a read-only natural-language repository explanation."""

        def explain() -> dict[str, str]:
            summary = reader.summarize(request.repository_path)
            answer = _build_llm(None).complete(
                build_explanation_prompt(request.question, summary)
            )
            return {"answer": answer}

        return _handle_errors(explain)

    @app.post("/agent/run")
    def run_agent(request: AgentRunRequest) -> AgentResult:
        """Apply a patch, optionally run verification, and persist the result."""

        def run() -> AgentResult:
            agent = build_agent(request.patch_diff)
            return agent.run(
                AgentRequest(
                    instruction=request.instruction,
                    repository_path=request.repository_path,
                    test_command=(
                        tuple(request.test_command) if request.test_command else None
                    ),
                    max_fix_attempts=request.max_fix_attempts,
                )
            )

        return _handle_errors(run)

    @app.get("/runs")
    def list_runs() -> list[AgentResult]:
        """Return persisted agent run history."""

        return _handle_errors(store.list)

    return gr.mount_gradio_app(
        app,
        create_gradio_app(
            build_agent,
            lambda: _build_llm(None),
            reader,
            store,
            activity_store,
        ),
        path="/ui",
    )


def main() -> None:
    """Run the FastAPI and Gradio application."""

    uvicorn.run("ai_coding_agent.api.app:create_app", factory=True, reload=False)


def _handle_errors(action: Callable[[], object]) -> object:
    try:
        return action()
    except AgentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _build_llm(patch_diff: str | None) -> LlmClient:
    if patch_diff and patch_diff.strip():
        return ManualPatchLlm(patch_diff.strip())

    groq_settings = GroqSettings.from_env()
    if groq_settings is not None:
        return OpenAiChatLlm(groq_settings)

    settings = OpenAiSettings.from_env()
    if settings is None:
        raise AgentError(
            "Provide patch_diff or set GROQ_API_KEY or OPENAI_API_KEY to generate "
            "patches with an LLM."
        )
    return OpenAiChatLlm(settings)


def _debug_llm_config() -> dict[str, str]:
    groq_settings = GroqSettings.from_env()
    if groq_settings is not None:
        return {
            "provider": "Groq",
            "model": groq_settings.model,
            "base_url": groq_settings.base_url,
        }

    settings = OpenAiSettings.from_env()
    if settings is not None:
        return {
            "provider": "OpenAI",
            "model": settings.model,
            "base_url": settings.base_url,
        }

    return {"provider": "none", "model": "", "base_url": ""}


if __name__ == "__main__":
    main()
