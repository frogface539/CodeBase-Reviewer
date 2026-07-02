"""Persistent run history storage."""

import json
from pathlib import Path
from typing import Protocol

from pydantic import TypeAdapter

from ai_coding_agent.core import ActivityRecord, AgentResult


class RunStore(Protocol):
    """Protocol for persisting agent run results."""

    def save(self, result: AgentResult) -> None:
        """Persist one agent result."""

    def list(self) -> list[AgentResult]:
        """Return all persisted agent results."""

    def clear(self) -> None:
        """Remove all persisted agent results."""


class JsonRunStore:
    """Stores agent results in a local JSON file."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._adapter = TypeAdapter(list[AgentResult])

    def save(self, result: AgentResult) -> None:
        """Append an agent result to the JSON history file."""

        items = self.list()
        items.append(result)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(
                [item.model_dump(mode="json") for item in items],
                indent=2,
            ),
            encoding="utf-8",
        )

    def list(self) -> list[AgentResult]:
        """Return all stored agent results."""

        if not self._path.exists():
            return []
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        return self._adapter.validate_python(raw)

    def clear(self) -> None:
        """Remove all stored agent results."""

        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text("[]", encoding="utf-8")


class ActivityStore(Protocol):
    """Protocol for persisting read-only UI activity."""

    def save(self, record: ActivityRecord) -> None:
        """Persist one activity record."""

    def list(self) -> list[ActivityRecord]:
        """Return all persisted activity records."""

    def clear(self) -> None:
        """Remove all persisted activity records."""


class JsonActivityStore:
    """Stores read-only UI activity in a local JSON file."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._adapter = TypeAdapter(list[ActivityRecord])

    def save(self, record: ActivityRecord) -> None:
        """Append an activity record to the JSON history file."""

        items = self.list()
        items.append(record)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(
                [item.model_dump(mode="json") for item in items],
                indent=2,
            ),
            encoding="utf-8",
        )

    def list(self) -> list[ActivityRecord]:
        """Return all stored activity records."""

        if not self._path.exists():
            return []
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        return self._adapter.validate_python(raw)

    def clear(self) -> None:
        """Remove all stored activity records."""

        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text("[]", encoding="utf-8")
