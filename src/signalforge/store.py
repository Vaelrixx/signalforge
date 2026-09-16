from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .core import Snapshot


def load_snapshot(path: Path) -> Snapshot | None:
    if not path.exists():
        return None
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return Snapshot(**data)


def save_snapshot(path: Path, snapshot: Snapshot) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
