from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Memory:
    id: int
    text: str
    vector: list[float] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "vector": self.vector,
            "created_at": self.created_at.isoformat(),
        }