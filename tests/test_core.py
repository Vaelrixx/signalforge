import hashlib
import json
import unittest

from signalforge.core import Snapshot, compare, normalize_html, normalize_json


def snap(kind, content):
    raw = json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return Snapshot("https://example.test", kind, content, digest, 200, "application/json" if kind == "json" else "text/html")


class CoreTests(unittest.TestCase):
    def test_html_normalization_removes_scripts_and_collapses_space(self):
        value = normalize_html("<html><head><title> Demo </title><script>x()</script></head><body>hello   world</body></html>")
        self.assertEqual(value, {"title": "Demo", "text": "Demo hello world"})

    def test_json_normalization_sorts_keys(self):
        self.assertEqual(list(normalize_json({"b": 1, "a": 2}).keys()), ["a", "b"])

    def test_json_diff_is_structured(self):
        old = snap("json", {"price": 10, "status": "ok"})
        new = snap("json", {"price": 12, "status": "ok", "plan": "pro"})
        event = compare(old, new)
        self.assertTrue(event.changed)
        paths = {item["path"] for item in event.details}
        self.assertIn("$.price", paths)
        self.assertIn("$.plan", paths)
        self.assertGreaterEqual(event.severity, 3)

    def test_same_snapshot_is_quiet(self):
        value = snap("json", {"status": "ok"})
        event = compare(value, value)
        self.assertFalse(event.changed)
        self.assertEqual(event.severity, 0)


if __name__ == "__main__":
    unittest.main()
