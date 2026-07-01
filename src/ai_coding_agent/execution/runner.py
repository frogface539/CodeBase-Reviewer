"""Local command execution."""

import subprocess
from pathlib import Path

from ai_coding_agent.core import CommandResult


class CommandRunner:
    """Runs local commands with captured output."""

    def __init__(self, timeout_seconds: int = 120) -> None:
        self._timeout_seconds = timeout_seconds

    def run(self, cwd: Path, command: tuple[str, ...]) -> CommandResult:
        """Run a command in the given working directory."""

        try:
            completed = subprocess.run(
                command,
                cwd=cwd.resolve(),
                text=True,
                capture_output=True,
                timeout=self._timeout_seconds,
                check=False,
            )
            return CommandResult(
                command=command,
                return_code=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
        except subprocess.TimeoutExpired as exc:
            return CommandResult(
                command=command,
                return_code=124,
                stdout=exc.stdout or "",
                stderr=exc.stderr
                or f"Command timed out after {self._timeout_seconds}s.",
            )
