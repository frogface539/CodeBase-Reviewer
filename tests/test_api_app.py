from pathlib import Path

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from ai_coding_agent.api.app import _build_llm, create_app
from ai_coding_agent.llm import OpenAiChatLlm


def test_api_health(tmp_path: Path) -> None:
    app = create_app(history_path=tmp_path / "runs.json")
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_summarizes_repository(tmp_path: Path) -> None:
    (tmp_path / "example.py").write_text("VALUE = 1\n", encoding="utf-8")
    app = create_app(history_path=tmp_path / "runs.json")
    client = TestClient(app)

    response = client.post(
        "/repositories/summary",
        json={"repository_path": str(tmp_path)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["root"] == str(tmp_path.resolve())
    assert body["files"][0]["path"] == "example.py"


def test_api_searches_repository(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text("class CodingAgent: pass\n", encoding="utf-8")
    app = create_app(history_path=tmp_path / "runs.json")
    client = TestClient(app)

    response = client.post(
        "/repositories/search",
        json={"repository_path": str(tmp_path), "query": "CodingAgent"},
    )

    assert response.status_code == 200
    assert response.json()["files"][0]["path"] == "agent.py"


def test_api_requires_patch_or_configured_llm(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = create_app(history_path=tmp_path / "runs.json")
    client = TestClient(app)

    response = client.post(
        "/agent/run",
        json={
            "repository_path": str(tmp_path),
            "instruction": "change it",
            "max_fix_attempts": 0,
        },
    )

    assert response.status_code == 400
    assert "Provide patch_diff" in response.json()["detail"]


def test_build_llm_uses_groq_when_configured(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    llm = _build_llm(None)

    assert isinstance(llm, OpenAiChatLlm)


def test_create_app_loads_dotenv(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    (tmp_path / ".env").write_text("GROQ_API_KEY=test-key\n", encoding="utf-8")

    create_app(history_path=tmp_path / "runs.json")
    llm = _build_llm(None)

    assert isinstance(llm, OpenAiChatLlm)
