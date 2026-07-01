from pathlib import Path

from ai_coding_agent.repository import RepositoryReader


def test_repository_reader_ignores_binary_files(tmp_path: Path) -> None:
    source = tmp_path / "src" / "example.py"
    source.parent.mkdir()
    source.write_text("print('hello')\n", encoding="utf-8")
    (tmp_path / "image.bin").write_bytes(b"\x80\x81")

    summary = RepositoryReader().summarize(tmp_path)

    assert [file.path.as_posix() for file in summary.files] == ["src/example.py"]


def test_repository_reader_searches_paths_and_content(tmp_path: Path) -> None:
    source = tmp_path / "agent.py"
    source.write_text("class CodingAgent: pass\n", encoding="utf-8")

    matches = RepositoryReader().search(tmp_path, "codingagent")

    assert len(matches) == 1
    assert matches[0].path == Path("agent.py")


def test_repository_reader_ignores_generated_dependency_dirs(
    tmp_path: Path,
) -> None:
    source = tmp_path / "src" / "agent.py"
    generated = tmp_path / "work" / "packagetest" / "dependency.pth"
    source.parent.mkdir()
    generated.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    generated.write_text("should not be included\n", encoding="utf-8")

    summary = RepositoryReader().summarize(tmp_path)

    assert [file.path.as_posix() for file in summary.files] == ["src/agent.py"]


def test_repository_reader_ignores_env_files(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    secret = tmp_path / ".env"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    secret.write_text("GROQ_API_KEY=secret\n", encoding="utf-8")

    summary = RepositoryReader().summarize(tmp_path)

    assert [file.path.as_posix() for file in summary.files] == ["app.py"]
