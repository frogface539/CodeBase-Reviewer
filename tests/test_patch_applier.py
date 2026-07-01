from pathlib import Path
import subprocess

from ai_coding_agent.core import Patch
from ai_coding_agent.repository.patch import GitPatchApplier


def test_patch_applier_normalizes_src_layout_paths(tmp_path: Path) -> None:
    target = tmp_path / "src" / "ai_coding_agent" / "agents" / "coding.py"
    target.parent.mkdir(parents=True)
    target.write_text("VALUE = 1\n", encoding="utf-8")
    diff = "\n".join(
        [
            "diff --git a/ai_coding_agent/agents/coding.py "
            "b/ai_coding_agent/agents/coding.py",
            "--- a/ai_coding_agent/agents/coding.py",
            "+++ b/ai_coding_agent/agents/coding.py",
        ]
    )

    normalized = GitPatchApplier()._normalize_src_layout_paths(tmp_path, diff)

    assert "a/src/ai_coding_agent/agents/coding.py" in normalized
    assert "b/src/ai_coding_agent/agents/coding.py" in normalized


def test_patch_applier_repairs_missing_file_headers() -> None:
    diff = "\n".join(
        [
            "Here is the patch:",
            "```diff",
            "diff --git a/example.py b/example.py",
            "@@ -1 +1 @@?",
            "? ^",
            "-old",
            "+new",
            "```",
        ]
    )

    prepared = GitPatchApplier()._prepare_diff(Path.cwd(), diff)

    assert "Here is the patch" not in prepared
    assert "--- a/example.py" in prepared
    assert "+++ b/example.py" in prepared
    assert "@@ -1 +1 @@" in prepared
    assert "? ^" not in prepared


def test_patch_applier_removes_question_suffix_from_hunk_header() -> None:
    diff = "\n".join(
        [
            "diff --git a/example.py b/example.py",
            "--- a/example.py",
            "+++ b/example.py",
            "@@ -1 +1 @@ ?",
            "-old",
            "+new",
            "",
        ]
    )

    prepared = GitPatchApplier()._prepare_diff(Path.cwd(), diff)

    assert "@@ -1 +1 @@ ?" not in prepared
    assert "@@ -1 +1 @@" in prepared


def test_patch_applier_repairs_unprefixed_hunk_context() -> None:
    diff = "\n".join(
        [
            "diff --git a/example.py b/example.py",
            "--- a/example.py",
            "+++ b/example.py",
            "@@ -1,3 +1,3 @@",
            '"""Module docstring."""',
            "",
            "-old",
            "+new",
            "",
        ]
    )

    prepared = GitPatchApplier()._prepare_diff(Path.cwd(), diff)

    assert ' """Module docstring."""' in prepared
    assert "\n \n" in prepared


def test_patch_applier_repairs_bare_hunk_header() -> None:
    diff = "\n".join(
        [
            "diff --git a/example.py b/example.py",
            "--- a/example.py",
            "+++ b/example.py",
            "@@",
            "-old",
            "+new",
            "",
        ]
    )

    prepared = GitPatchApplier()._prepare_diff(Path.cwd(), diff)

    assert "@@ -1 +1 @@" in prepared


def test_patch_applier_recounts_bad_hunk_counts(tmp_path: Path) -> None:
    target = tmp_path / "example.py"
    target.write_text("old\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    diff = "\n".join(
        [
            "diff --git a/example.py b/example.py",
            "--- a/example.py",
            "+++ b/example.py",
            "@@ -1,5 +1,5 @@",
            "-old",
            "+new",
            "",
        ]
    )

    GitPatchApplier().apply(tmp_path, Patch(diff=diff))

    assert target.read_text(encoding="utf-8") == "new\n"
