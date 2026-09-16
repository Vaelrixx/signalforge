from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .core import compare, fetch_snapshot
from .store import load_snapshot, save_snapshot


def _state_path(root: Path, url: str) -> Path:
    key = hashlib.sha256(url.encode()).hexdigest()[:20]
    return root / f"{key}.json"


def main() -> None:
    parser = argparse.ArgumentParser(prog="signalforge", description="Structured web-change intelligence")
    parser.add_argument("url", help="HTTP/HTTPS URL to inspect")
    parser.add_argument("--state-dir", default=".signalforge", help="Snapshot state directory")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print event JSON")
    args = parser.parse_args()

    path = _state_path(Path(args.state_dir), args.url)
    previous = load_snapshot(path)
    current = fetch_snapshot(args.url)
    event = compare(previous, current)
    save_snapshot(path, current)

    print(json.dumps(event.to_dict(), ensure_ascii=False, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()
