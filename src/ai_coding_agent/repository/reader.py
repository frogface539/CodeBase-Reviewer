"""Repository reading utilities."""

from collections.abc import Iterable
from pathlib import Path

from ai_coding_agent.core import FileSnapshot, RepositorySummary


class RepositoryReader:
    """Reads bounded source context from a repository."""

    def __init__(
        self,
        ignored_dirs: Iterable[str] | None = None,
        ignored_names: Iterable[str] | None = None,
        max_file_bytes: int = 80_000,
    ) -> None:
        self._ignored_dirs = set(
            ignored_dirs
            or {
                ".agent",
                ".git",
                ".mypy_cache",
                ".pytest_cache",
                ".ruff_cache",
                ".venv",
                "__pycache__",
                "build",
                "dist",
                "node_modules",
                "packagetest",
                "pydeps",
                "rundeps",
                "testdeps",
            }
        )
        self._ignored_names = set(
            ignored_names
            or {
                ".env",
                ".env.local",
                ".env.production",
                ".env.test",
            }
        )
        self._max_file_bytes = max_file_bytes

    def summarize(self, root: Path) -> RepositorySummary:
        """Return readable source files under the repository root."""

        resolved_root = root.resolve()
        files = [
            FileSnapshot(path=path.relative_to(resolved_root), content=content)
            for path, content in self._iter_text_files(resolved_root)
        ]
        return RepositorySummary(root=resolved_root, files=files)

    def search(self, root: Path, query: str) -> list[FileSnapshot]:
        """Return files whose path or contents contain the query text."""

        normalized_query = query.casefold()
        summary = self.summarize(root)
        return [
            file
            for file in summary.files
            if normalized_query in file.path.as_posix().casefold()
            or normalized_query in file.content.casefold()
        ]

    def _iter_text_files(self, root: Path) -> Iterable[tuple[Path, str]]:
        for path in sorted(root.rglob("*")):
            if not path.is_file() or self._is_ignored(path, root):
                continue
            try:
                if path.stat().st_size > self._max_file_bytes:
                    continue
                yield path, path.read_text(encoding="utf-8")
            except (OSError, PermissionError, UnicodeDecodeError):
                continue

    def _is_ignored(self, path: Path, root: Path) -> bool:
        relative_parts = path.relative_to(root).parts
        return path.name in self._ignored_names or any(
            part in self._ignored_dirs for part in relative_parts
        )
