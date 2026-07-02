# AI Coding Agent

A modular Python 3.12 AI coding agent for inspecting repositories, searching
source code, explaining project structure, generating patch diffs, applying
changes, running verification commands, and saving local run history.

This project is not a chatbot. It is a local coding-agent backend with FastAPI
endpoints, a custom HTML/CSS/JavaScript frontend, and a Gradio fallback UI.

## Demo

[Watch the project demo video](DEMO_VIDEO_URL)

Replace `DEMO_VIDEO_URL` with your uploaded video link, such as a Loom, YouTube,
Google Drive, or GitHub release asset URL.

## Features

- Custom web UI at `/app/`.
- Gradio fallback UI at `/ui/`.
- FastAPI backend with interactive docs at `/docs`.
- Repository summary endpoint for reading bounded source context.
- Repository search endpoint for finding files by path or content.
- Repository explanation endpoint powered by the configured LLM.
- Agent run endpoint for generating or applying unified diff patches.
- Manual patch mode using `patch_diff`.
- Groq LLM mode through Groq's OpenAI-compatible API.
- OpenAI-compatible fallback mode.
- Local command execution for verification commands such as `pytest`.
- Automatic fix attempts when verification fails.
- Patch repair retry flow for malformed LLM diffs.
- Git-backed patch application using `git apply --check --recount`.
- Failed patch debug output at `.agent/last_failed_patch.diff`.
- Local JSON run history at `.agent/runs.json`.
- Local repository activity history at `.agent/activity.json`.
- History view combining agent runs and repository actions.
- Clear history action through the frontend and API.
- Debug endpoints for import path and active LLM configuration.
- Pydantic v2 request and response models.
- Pytest test suite.

## Tech Stack

- Python 3.12+
- FastAPI
- Uvicorn
- Pydantic v2
- Gradio
- python-dotenv
- Vanilla HTML, CSS, and JavaScript
- Git patch application via the local `git` executable

## Project Structure

```text
src/ai_coding_agent/
  agents/        Agent orchestration and prompts
  api/           FastAPI app, request schemas, service helpers
  core/          Shared Pydantic models and errors
  execution/     Local command runner
  llm/           Manual, Groq, and OpenAI-compatible LLM clients
  repository/    Repository reader and Git patch applier
  storage/       JSON history stores
  ui/            Gradio UI, CLI, and history formatting
  web/static/    Custom HTML/CSS/JavaScript frontend
tests/           Pytest coverage
```

## Requirements

Use Python 3.12 or newer.

Install runtime dependencies:

```powershell
pip install -e .
```

Install runtime and test dependencies:

```powershell
pip install -e ".[dev]"
```

The project also expects `git` to be available on your `PATH` because patches
are applied with `git apply`.

## Environment Setup

Create a `.env` file in the project root. The app loads it automatically on
startup.

For Groq:

```env
GROQ_API_KEY=your-groq-key
GROQ_MODEL=openai/gpt-oss-120b
GROQ_BASE_URL=https://api.groq.com/openai/v1
AGENT_MAX_CONTEXT_CHARS=12000
AGENT_MAX_FILE_CHARS=3000
```

For OpenAI-compatible mode:

```env
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4.1-mini
OPENAI_BASE_URL=https://api.openai.com/v1
AGENT_MAX_CONTEXT_CHARS=12000
AGENT_MAX_FILE_CHARS=3000
```

If you provide a manual `patch_diff`, the agent uses that diff directly and does
not need an LLM key for that run.

## Running The App

Start the server:

```powershell
python -m uvicorn ai_coding_agent.api.app:create_app --factory --host 127.0.0.1 --port 8000 --reload
```

Open:

- Custom frontend: <http://127.0.0.1:8000/app/>
- Gradio fallback UI: <http://127.0.0.1:8000/ui/>
- API docs: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>

The root path `/` redirects to `/app/`.

## Frontend

The custom frontend supports:

- Repository path input
- API and LLM status display
- Repository summary
- Repository search
- LLM-powered repository explanation with Markdown rendering
- Agent patch runs
- Optional verification command
- Configurable fix attempts
- History refresh
- Clear history
- Links to API docs and the Gradio fallback UI

## API Endpoints

### `GET /`

Redirects to the custom frontend at `/app/`.

### `GET /health`

Returns service health.

Response:

```json
{
  "status": "ok"
}
```

### `GET /debug/imports`

Returns the resolved import path for the installed `ai_coding_agent` package.
This helps confirm whether Uvicorn is running the local editable source or a
stale installed package.

Response:

```json
{
  "ai_coding_agent": "C:/path/to/src/ai_coding_agent/__init__.py"
}
```

### `GET /debug/llm`

Returns the active LLM provider, model, and base URL without exposing secrets.

Response:

```json
{
  "provider": "Groq",
  "model": "openai/gpt-oss-120b",
  "base_url": "https://api.groq.com/openai/v1"
}
```

### `POST /repositories/summary`

Reads text files under a repository and returns a compact source summary.
Ignored folders include `.git`, `.venv`, `.agent`, cache folders, build outputs,
`node_modules`, and egg-info folders. Environment files such as `.env` are also
ignored.

Request:

```json
{
  "repository_path": "C:/path/to/repository"
}
```

Response shape:

```json
{
  "root": "C:/path/to/repository",
  "files": [
    {
      "path": "src/example.py",
      "content": "file contents"
    }
  ]
}
```

### `POST /repositories/search`

Searches repository file paths and file contents.

Request:

```json
{
  "repository_path": "C:/path/to/repository",
  "query": "GitPatchApplier"
}
```

Response shape:

```json
{
  "root": "C:/path/to/repository",
  "files": [
    {
      "path": "src/ai_coding_agent/repository/patch.py",
      "content": "matching file contents"
    }
  ]
}
```

### `POST /repositories/explain`

Summarizes the repository, sends the summary and question to the configured LLM,
and returns a natural-language explanation. This is read-only and does not apply
patches.

Request:

```json
{
  "repository_path": "C:/path/to/repository",
  "question": "What is this repository about?"
}
```

Response:

```json
{
  "answer": "Markdown-formatted explanation from the LLM."
}
```

### `POST /agent/run`

Runs the coding agent for one instruction. The agent reads the repository,
generates or receives a patch, applies it, optionally runs a verification
command, and stores the result in history.

Request:

```json
{
  "repository_path": "C:/path/to/repository",
  "instruction": "Add input validation to the greeting function.",
  "patch_diff": null,
  "test_command": ["pytest"],
  "max_fix_attempts": 1
}
```

Manual patch request:

```json
{
  "repository_path": "C:/path/to/repository",
  "instruction": "Apply this patch.",
  "patch_diff": "diff --git a/example.py b/example.py\n--- a/example.py\n+++ b/example.py\n@@ -1 +1 @@\n-old\n+new\n",
  "test_command": null,
  "max_fix_attempts": 0
}
```

Response shape:

```json
{
  "request": {
    "instruction": "Add input validation to the greeting function.",
    "repository_path": "C:/path/to/repository",
    "test_command": ["pytest"],
    "max_fix_attempts": 1
  },
  "summary": "Patch applied and verification passed.",
  "patch_applied": true,
  "test_result": {
    "command": ["pytest"],
    "return_code": 0,
    "stdout": "...",
    "stderr": "..."
  },
  "fix_attempts": 0,
  "created_at": "2026-07-02T00:00:00Z"
}
```

### `GET /runs`

Returns persisted agent run history from `.agent/runs.json`.

### `GET /history`

Returns formatted Markdown history combining:

- Agent patch runs
- Repository summaries
- Repository searches
- Repository explanations

Response:

```json
{
  "markdown": "## History\n..."
}
```

### `DELETE /history`

Clears both agent run history and repository activity history.

Response:

```json
{
  "markdown": "No runs yet."
}
```

## Agent Workflow

1. The agent reads repository context with `RepositoryReader`.
2. It builds a patch prompt from the user instruction and repository summary.
3. It gets a patch from either:
   - `ManualPatchLlm` when `patch_diff` is provided.
   - Groq when `GROQ_API_KEY` is configured.
   - OpenAI-compatible settings when `OPENAI_API_KEY` is configured.
4. `GitPatchApplier` extracts and normalizes the diff.
5. The patch is checked with `git apply --check --recount`.
6. The patch is applied with `git apply --recount`.
7. If a verification command is provided, `CommandRunner` executes it locally.
8. If verification fails and fix attempts remain, the agent asks the LLM for a
   fix patch and retries.
9. The final result is saved to local JSON history.

## Patch Handling

The patch applier is designed to handle common LLM diff problems:

- Markdown code fences around diffs
- Extra prose before the diff
- Diff hint lines beginning with `?`
- Missing file headers after `diff --git`
- Bare or malformed hunk headers
- Missing hunk body prefixes
- Source-layout path mismatches, such as `package/file.py` vs `src/package/file.py`

If a patch still fails, the prepared patch is written to:

```text
.agent/last_failed_patch.diff
```

The API error also includes a numbered excerpt near the failing line.

## History Storage

History is local to the project directory:

```text
.agent/runs.json
.agent/activity.json
```

Use the History panel in the custom frontend or Gradio UI to refresh or clear
history. You can also clear history with:

```powershell
Invoke-RestMethod -Method Delete -Uri http://127.0.0.1:8000/history
```

## CLI Commands

The package exposes these console scripts:

```powershell
ai-coding-agent
ai-coding-agent-server
```

The most common development command is still the explicit Uvicorn command:

```powershell
python -m uvicorn ai_coding_agent.api.app:create_app --factory --host 127.0.0.1 --port 8000 --reload
```

## Testing

Run the test suite:

```powershell
pytest
```

Run a compile check:

```powershell
python -m compileall -q src tests
```

Useful manual tests:

- Open `/health` and confirm `{"status":"ok"}`.
- Open `/debug/imports` and confirm it points to `src/ai_coding_agent`.
- Open `/debug/llm` and confirm it shows Groq or OpenAI settings.
- Use Repository Summary on the project path.
- Use Repository Search with terms like `GitPatchApplier`, `AgentRequest`, or
  `history`.
- Use Repository Explain with `What is this repository about?`.
- Run the agent with a manual diff and no test command.
- Run the agent with `pytest` as the verification command.
- Refresh History and confirm repository actions and agent runs appear.
- Clear History and confirm the history output resets.

## Troubleshooting

### `GET /` shows 404

The current app redirects `/` to `/app/`. If you still see a 404, restart the
server and open:

```text
http://127.0.0.1:8000/app/
```

### The server runs stale code

Open:

```text
http://127.0.0.1:8000/debug/imports
```

It should point to:

```text
.../src/ai_coding_agent/__init__.py
```

If it points into `.venv/Lib/site-packages`, reinstall editable mode:

```powershell
pip install -e .
```

### Groq rate-limit errors

Groq can be free and still enforce token-per-minute and token-per-day limits.
Reduce repository context, wait for the reset window, use a smaller request, or
switch models/accounts according to your Groq plan.

### Groq error code 1010

Check:

```env
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=openai/gpt-oss-120b
```

Also confirm `GROQ_API_KEY` is valid.

### Patch does not apply

Check:

```text
.agent/last_failed_patch.diff
```

Then compare the file paths and context lines in the patch with your current
working tree.

### Permission denied for editable install files

Delete broken temporary install output in the `work` folder if needed, then run:

```powershell
pip install -e .
```

Make sure no old server process is holding files open.

## Notes

- The app intentionally keeps state local in `.agent`.
- Repository reading skips common dependency, cache, build, Git, virtualenv, and
  environment-secret files.
- LLM requests are generated from bounded repository context to reduce token
  usage.
- The custom frontend is the primary UI; Gradio remains available as a fallback.
