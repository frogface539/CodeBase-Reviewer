"""Patch application backed by Git."""

import re
import subprocess
from pathlib import Path

from ai_coding_agent.core import AgentError, Patch


class GitPatchApplier:
    """Applies unified diffs to a repository using `git apply`."""

    def apply(self, repository_path: Path, patch: Patch) -> None:
        """Apply a unified diff to the target repository."""

        root = repository_path.resolve()
        diff = self._prepare_diff(root, patch.diff)
        check = self._run(root, ["git", "apply", "--check", "--recount"], diff)
        if check.returncode != 0:
            self._write_failed_patch(root, diff)
            raise AgentError(self._format_patch_error(check.stderr, diff))

        applied = self._run(root, ["git", "apply", "--recount"], diff)
        if applied.returncode != 0:
            self._write_failed_patch(root, diff)
            raise AgentError(self._format_patch_error(applied.stderr, diff))

    def _prepare_diff(self, root: Path, diff: str) -> str:
        cleaned = self._extract_diff(diff)
        repaired = self._repair_missing_file_headers(cleaned)
        prefixed = self._repair_hunk_body_prefixes(repaired)
        normalized = self._normalize_src_layout_paths(root, prefixed)
        return self._remove_diff_hint_lines(normalized)

    def _extract_diff(self, diff: str) -> str:
        lines = [line.rstrip() for line in diff.strip().splitlines()]
        lines = [line for line in lines if not line.strip().startswith("```")]
        lines = self._filter_diff_hint_lines(lines)
        start = self._find_diff_start(lines)
        if start is None:
            return diff.strip() + "\n"
        return "\n".join(lines[start:]) + "\n"

    def _remove_diff_hint_lines(self, diff: str) -> str:
        lines = self._filter_diff_hint_lines(diff.splitlines())
        return "\n".join(lines) + ("\n" if diff.endswith("\n") else "")

    def _filter_diff_hint_lines(self, lines: list[str]) -> list[str]:
        return [line for line in lines if not self._is_diff_hint_line(line)]

    def _is_diff_hint_line(self, line: str) -> bool:
        return line.lstrip().startswith("?")

    def _find_diff_start(self, lines: list[str]) -> int | None:
        for index, line in enumerate(lines):
            if line.startswith(("diff --git ", "--- ")):
                return index
        return None

    def _repair_missing_file_headers(self, diff: str) -> str:
        lines = diff.splitlines()
        repaired: list[str] = []
        old_path: str | None = None
        new_path: str | None = None
        has_file_headers = False

        for line in lines:
            if line.startswith("diff --git "):
                old_path, new_path = self._parse_diff_git_paths(line)
                has_file_headers = False
                repaired.append(line)
                continue

            if line.startswith("--- "):
                has_file_headers = True
                repaired.append(line)
                continue

            if line.startswith("+++ "):
                has_file_headers = True
                repaired.append(line)
                continue

            if line.startswith("@@"):
                if old_path and new_path and not has_file_headers:
                    repaired.extend([f"--- {old_path}", f"+++ {new_path}"])
                    has_file_headers = True
                repaired.append(self._normalize_hunk_header(line))
                continue

            repaired.append(line)

        return "\n".join(repaired) + ("\n" if diff.endswith("\n") else "")

    def _parse_diff_git_paths(self, line: str) -> tuple[str | None, str | None]:
        parts = line.split()
        if len(parts) != 4:
            return None, None
        return parts[2], parts[3]

    def _normalize_hunk_header(self, line: str) -> str:
        if line.strip() == "@@":
            return "@@ -1 +1 @@"

        closing_index = line.find("@@", 2)
        if closing_index == -1:
            return line

        header_end = closing_index + 2
        suffix = line[header_end:].strip()
        if suffix == "" or suffix.startswith("?"):
            return line[:header_end]
        return line

    def _repair_hunk_body_prefixes(self, diff: str) -> str:
        lines = diff.splitlines()
        repaired: list[str] = []
        in_hunk = False

        for line in lines:
            if line.startswith(("diff --git ", "--- ", "+++ ")):
                in_hunk = False
                repaired.append(line)
                continue

            if line.startswith("@@"):
                in_hunk = True
                repaired.append(line)
                continue

            if in_hunk:
                repaired.append(self._repair_hunk_body_line(line))
                continue

            repaired.append(line)

        return "\n".join(repaired) + ("\n" if diff.endswith("\n") else "")

    def _repair_hunk_body_line(self, line: str) -> str:
        if line == "":
            return " "
        if line.startswith((" ", "+", "-", "\\")):
            return line
        return f" {line}"

    def _normalize_src_layout_paths(self, root: Path, diff: str) -> str:
        lines = diff.splitlines()
        normalized = [self._normalize_diff_line(root, line) for line in lines]
        trailing_newline = "\n" if diff.endswith("\n") else ""
        return "\n".join(normalized) + trailing_newline

    def _normalize_diff_line(self, root: Path, line: str) -> str:
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) == 4:
                return " ".join(
                    [
                        parts[0],
                        parts[1],
                        self._normalize_git_path(root, parts[2]),
                        self._normalize_git_path(root, parts[3]),
                    ]
                )
        if line.startswith("--- ") or line.startswith("+++ "):
            prefix, path = line[:4], line[4:]
            return f"{prefix}{self._normalize_git_path(root, path)}"
        return line

    def _normalize_git_path(self, root: Path, path: str) -> str:
        if path == "/dev/null":
            return path

        marker = ""
        raw_path = path
        if path.startswith(("a/", "b/")):
            marker = path[:2]
            raw_path = path[2:]

        if (root / raw_path).exists():
            return path

        src_path = Path("src") / raw_path
        if (root / src_path).exists():
            return f"{marker}{src_path.as_posix()}"

        return path

    def _run(
        self,
        cwd: Path,
        command: list[str],
        stdin: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=cwd,
            input=stdin,
            text=True,
            capture_output=True,
            check=False,
        )

    def _write_failed_patch(self, root: Path, diff: str) -> None:
        debug_dir = root / ".agent"
        debug_dir.mkdir(exist_ok=True)
        (debug_dir / "last_failed_patch.diff").write_text(diff, encoding="utf-8")

    def _format_patch_error(self, stderr: str, diff: str) -> str:
        message = stderr.strip() or "Patch did not apply cleanly."
        return f"{message}\n\nPrepared patch excerpt:\n{self._excerpt(diff, message)}"

    def _excerpt(self, diff: str, message: str) -> str:
        lines = diff.splitlines()
        line_number = self._extract_line_number(message)
        if line_number is None:
            start = 1
            end = min(len(lines), 12)
        else:
            start = max(1, line_number - 4)
            end = min(len(lines), line_number + 4)

        return "\n".join(
            f"{number}: {lines[number - 1]}"
            for number in range(start, end + 1)
        )

    def _extract_line_number(self, message: str) -> int | None:
        match = re.search(r"line (\d+)", message)
        if match is None:
            return None
        return int(match.group(1))
