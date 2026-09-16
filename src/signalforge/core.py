from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from difflib import unified_diff
from html.parser import HTMLParser
from typing import Any
from urllib.request import Request, urlopen


INTERESTING_TERMS = {
    "price": 3,
    "pricing": 3,
    "plan": 2,
    "deprecated": 4,
    "deprecation": 4,
    "breaking": 5,
    "outage": 5,
    "incident": 5,
    "security": 5,
    "available": 2,
    "unavailable": 4,
}


@dataclass(slots=True)
class Snapshot:
    url: str
    kind: str
    content: Any
    digest: str
    status_code: int
    content_type: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ChangeEvent:
    changed: bool
    kind: str
    severity: int
    summary: str
    details: Any
    previous_digest: str | None
    current_digest: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class _TextHTMLParser(HTMLParser):
    SKIP_TAGS = {"script", "style", "noscript", "template"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._title_depth = 0
        self.text_parts: list[str] = []
        self.title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
        if tag == "title":
            self._title_depth += 1

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title" and self._title_depth:
            self._title_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        cleaned = _clean_text(data)
        if not cleaned:
            return
        self.text_parts.append(cleaned)
        if self._title_depth:
            self.title_parts.append(cleaned)


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def normalize_html(html: str) -> dict[str, Any]:
    parser = _TextHTMLParser()
    parser.feed(html)
    return {
        "title": _clean_text(" ".join(parser.title_parts)),
        "text": _clean_text(" ".join(parser.text_parts)),
    }


def normalize_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: normalize_json(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [normalize_json(item) for item in value]
    return value


def fetch_snapshot(url: str, timeout: float = 20.0) -> Snapshot:
    request = Request(
        url,
        headers={"User-Agent": "SignalForge/0.1 (+https://github.com/Vaelrixx/signalforge)"},
    )
    with urlopen(request, timeout=timeout) as response:
        raw = response.read()
        status = getattr(response, "status", 200)
        final_url = response.geturl()
        content_type = response.headers.get_content_type().lower()
        charset = response.headers.get_content_charset() or "utf-8"

    text = raw.decode(charset, errors="replace")
    if content_type == "application/json" or content_type.endswith("+json"):
        kind = "json"
        content = normalize_json(json.loads(text))
    else:
        kind = "html"
        content = normalize_html(text)

    return Snapshot(
        url=final_url,
        kind=kind,
        content=content,
        digest=_digest(content),
        status_code=status,
        content_type=content_type,
    )


def _json_diff(old: Any, new: Any, path: str = "$") -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    if type(old) is not type(new):
        return [{"path": path, "type": "changed", "before": old, "after": new}]

    if isinstance(old, dict):
        for key in sorted(set(old) | set(new)):
            child = f"{path}.{key}"
            if key not in old:
                changes.append({"path": child, "type": "added", "after": new[key]})
            elif key not in new:
                changes.append({"path": child, "type": "removed", "before": old[key]})
            else:
                changes.extend(_json_diff(old[key], new[key], child))
        return changes

    if isinstance(old, list):
        if old != new:
            changes.append({"path": path, "type": "changed", "before": old, "after": new})
        return changes

    if old != new:
        changes.append({"path": path, "type": "changed", "before": old, "after": new})
    return changes


def _severity(text: str, change_count: int) -> int:
    score = 1 if change_count else 0
    lowered = text.lower()
    for term, weight in INTERESTING_TERMS.items():
        if term in lowered:
            score += weight
    if change_count >= 5:
        score += 1
    if change_count >= 20:
        score += 1
    return min(score, 10)


def compare(previous: Snapshot | None, current: Snapshot) -> ChangeEvent:
    if previous is None:
        return ChangeEvent(False, current.kind, 0, "Baseline captured", [], None, current.digest)

    if previous.digest == current.digest:
        return ChangeEvent(False, current.kind, 0, "No meaningful change", [], previous.digest, current.digest)

    if previous.kind != current.kind:
        details = [{"type": "content_type_changed", "before": previous.kind, "after": current.kind}]
        return ChangeEvent(True, current.kind, 8, "Content type changed", details, previous.digest, current.digest)

    if current.kind == "json":
        changes = _json_diff(previous.content, current.content)
        searchable = json.dumps(changes, ensure_ascii=False)
        return ChangeEvent(
            True,
            "json",
            _severity(searchable, len(changes)),
            f"{len(changes)} structured JSON change(s)",
            changes,
            previous.digest,
            current.digest,
        )

    old_text = previous.content.get("text", "")
    new_text = current.content.get("text", "")
    diff = list(unified_diff(old_text.splitlines(), new_text.splitlines(), fromfile="before", tofile="after", lineterm="", n=2))
    details = {
        "title_changed": previous.content.get("title") != current.content.get("title"),
        "before_title": previous.content.get("title", ""),
        "after_title": current.content.get("title", ""),
        "diff": diff[:120],
    }
    searchable = " ".join(diff) + " " + new_text[:5000]
    return ChangeEvent(True, "html", _severity(searchable, max(1, len(diff))), "HTML text changed", details, previous.digest, current.digest)
