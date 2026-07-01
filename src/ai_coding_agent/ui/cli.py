"""Command-line interface for the coding agent."""

import argparse
from pathlib import Path

from pydantic import ValidationError

from ai_coding_agent.core import AgentRequest


def main() -> int:
    """Run the command-line interface."""

    parser = argparse.ArgumentParser(description="Run the AI coding agent.")
    parser.add_argument("instruction")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--test-command", nargs="+")
    args = parser.parse_args()

    try:
        AgentRequest(
            instruction=args.instruction,
            repository_path=args.repo,
            test_command=tuple(args.test_command) if args.test_command else None,
        )
    except ValidationError as exc:
        print(str(exc))
        return 1

    print(
        "CLI request parsed. Provide a concrete LLM client through the Python API "
        "to execute patches."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
