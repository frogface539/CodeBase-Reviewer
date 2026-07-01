# AI Coding Agent

A modular Python 3.12 coding-agent project with repository inspection, patch
application, command execution, run history, FastAPI endpoints, and a Gradio UI.

## Run

Install the project into your virtual environment first:

```powershell
pip install -e .
```

Then start the server:

```powershell
python -m uvicorn ai_coding_agent.api.app:create_app --factory --host 127.0.0.1 --port 8000
```

Open:

- Gradio UI: http://127.0.0.1:8000/ui/
- API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

## LLM Configuration

The app can run in two modes:

- Paste a unified diff into the UI or send `patch_diff` to `POST /agent/run`.
- Set `GROQ_API_KEY` and leave `patch_diff` empty to let Groq generate the patch.
- Set `OPENAI_API_KEY` instead if you want to use OpenAI.

Create a `.env` file in the project root. You can copy `.env.example` and fill
in your key:

```env
GROQ_API_KEY=your-groq-key
GROQ_MODEL=openai/gpt-oss-120b
GROQ_BASE_URL=https://api.groq.com/openai/v1
AGENT_MAX_CONTEXT_CHARS=12000
AGENT_MAX_FILE_CHARS=3000
```

For OpenAI instead:

```env
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4.1-mini
OPENAI_BASE_URL=https://api.openai.com/v1
```

## Endpoints

- `GET /health`
- `POST /repositories/summary`
- `POST /repositories/search`
- `POST /agent/run`
- `GET /runs`

The app uses the same agent orchestration path for API and UI requests.
