"""Buffer circular de logs para a interface Web."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List


@dataclass
class LogBuffer:
    max_entries: int = 200
    _entries: List[dict] = field(default_factory=list)

    def append(self, log_type: str, message: str) -> None:
        self._entries.append(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "type": log_type,
                "message": message,
            }
        )
        overflow = len(self._entries) - self.max_entries
        if overflow > 0:
            del self._entries[:overflow]

    def snapshot(self, limit: int | None = None) -> list[dict]:
        if limit is None:
            return list(self._entries)
        return list(self._entries[-limit:])

    def clear(self) -> None:
        self._entries.clear()
