from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .models import Memory
from .vectors import embed


class Store:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.items: list[Memory] = self._read()

    def _read(self) -> list[Memory]:
        if not self.path.exists():
            return []

        out: list[Memory] = []
        for row in json.loads(self.path.read_text()):
            out.append(
                Memory(
                    id=row["id"],
                    text=row["text"],
                    vector=row.get("vector", []),
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
            )
        return out

    def save(self) -> None:
        rows = [m.to_dict() for m in self.items]
        self.path.write_text(json.dumps(rows, indent=2))

    def all(self) -> list[Memory]:
        return list(self.items)

    def remember(self, text: str) -> Memory:
        clean = text.strip()
        if not clean:
            raise ValueError("cannot remember nothing")

        for m in self.items:
            if m.text.lower() == clean.lower():
                return m

        m = Memory(id=len(self.items) + 1, text=clean, vector=embed([clean])[0])
        self.items.append(m)
        self.save()
        return m

    def reset(self) -> None:
        self.items.clear()
        self.save()

    def ensure_vectors(self) -> None:
        missing = [m for m in self.items if not m.vector]
        if not missing:
            return
        for m, vector in zip(missing, embed([m.text for m in missing])):
            m.vector = vector
        self.save()