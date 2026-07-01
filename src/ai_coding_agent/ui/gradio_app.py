"""Gradio interface for the coding agent."""

import shlex
from collections.abc import Callable
from pathlib import Path

import gradio as gr
from pydantic import ValidationError

from ai_coding_agent.agents import CodingAgent
from ai_coding_agent.core import AgentError, AgentRequest
from ai_coding_agent.repository import RepositoryReader
from ai_coding_agent.storage import RunStore

AgentFactory = Callable[[str | None], CodingAgent]


def create_gradio_app(
    agent_factory: AgentFactory,
    repository_reader: RepositoryReader,
    run_store: RunStore,
) -> gr.Blocks:
    """Create the Gradio UI connected to agent services."""

    with gr.Blocks(title="AI Coding Agent") as app:
        gr.Markdown("# AI Coding Agent")
        gr.Markdown("Inspect a repository, generate or apply a unified diff.")

        with gr.Tab("Run Agent"):
            repository_path = gr.Textbox(
                label="Repository path",
                value=str(Path.cwd()),
            )
            instruction = gr.Textbox(
                label="Instruction",
                lines=3,
                placeholder="Describe the code change you want.",
            )
            patch_diff = gr.Code(label="Unified diff patch", lines=14)
            test_command = gr.Textbox(
                label="Verification command",
                placeholder="pytest",
            )
            max_fix_attempts = gr.Slider(
                label="Max fix attempts",
                minimum=0,
                maximum=5,
                value=0,
                step=1,
            )
            run_button = gr.Button("Run", variant="primary")
            run_output = gr.JSON(label="Result")

        with gr.Tab("Repository"):
            repo_path_for_summary = gr.Textbox(
                label="Repository path",
                value=str(Path.cwd()),
            )
            query = gr.Textbox(label="Search query")
            summary_button = gr.Button("Summarize")
            search_button = gr.Button("Search")
            repository_output = gr.JSON(label="Repository output")

        with gr.Tab("History"):
            history_button = gr.Button("Refresh")
            history_output = gr.JSON(label="Runs")

        run_button.click(
            fn=lambda repo, text, diff, command, attempts: _run_agent(
                agent_factory,
                repo,
                text,
                diff,
                command,
                int(attempts),
            ),
            inputs=[
                repository_path,
                instruction,
                patch_diff,
                test_command,
                max_fix_attempts,
            ],
            outputs=run_output,
        )
        summary_button.click(
            fn=lambda repo: _summarize(repository_reader, repo),
            inputs=repo_path_for_summary,
            outputs=repository_output,
        )
        search_button.click(
            fn=lambda repo, text: _search(repository_reader, repo, text),
            inputs=[repo_path_for_summary, query],
            outputs=repository_output,
        )
        history_button.click(
            fn=lambda: [item.model_dump(mode="json") for item in run_store.list()],
            outputs=history_output,
        )

    return app


def _run_agent(
    agent_factory: AgentFactory,
    repository_path: str,
    instruction: str,
    patch_diff: str | None,
    test_command: str,
    max_fix_attempts: int,
) -> dict[str, object]:
    try:
        if not instruction.strip():
            return {"error": "Enter an instruction for the agent."}
        if not repository_path.strip():
            return {"error": "Enter a repository path."}
        command = tuple(shlex.split(test_command)) if test_command.strip() else None
        result = agent_factory(patch_diff).run(
            AgentRequest(
                instruction=instruction.strip(),
                repository_path=Path(repository_path),
                test_command=command,
                max_fix_attempts=max_fix_attempts,
            )
        )
        return result.model_dump(mode="json")
    except (AgentError, ValidationError, ValueError) as exc:
        return {"error": str(exc)}


def _summarize(reader: RepositoryReader, repository_path: str) -> dict[str, object]:
    try:
        return reader.summarize(Path(repository_path)).model_dump(mode="json")
    except (AgentError, ValueError) as exc:
        return {"error": str(exc)}


def _search(
    reader: RepositoryReader,
    repository_path: str,
    query: str,
) -> dict[str, object]:
    try:
        root = Path(repository_path).resolve()
        files = reader.search(root, query)
        return {
            "root": str(root),
            "files": [file.model_dump(mode="json") for file in files],
        }
    except (AgentError, ValueError) as exc:
        return {"error": str(exc)}
