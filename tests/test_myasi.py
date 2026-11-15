"""Stdlib unit tests: python -m unittest discover -s tests"""
import unittest

from helpers import myasi


class YamlTest(unittest.TestCase):
    def test_frontmatter_folded(self):
        fm, body = myasi.parse_frontmatter("---\nname: a-b\ndescription: >-\n  one\n  two\n---\n# body\n")
        self.assertEqual(fm, {"name": "a-b", "description": "one two"})
        self.assertIn("# body", body)

    def test_nested(self):
        y = myasi.parse_yaml(
            "servers:\n  x:\n    args: [\"-y\", pkg]  # c\n    env:\n      K: \"${K}\"\n"
            "    clients: [codex, claude]\n    ok: true\nlist:\n  - name: a\n    v: 1\n  - b\n"
            "lit: |\n  l1\n  l2\n")
        self.assertEqual(y["servers"]["x"], {"args": ["-y", "pkg"], "env": {"K": "${K}"},
                                             "clients": ["codex", "claude"], "ok": True})
        self.assertEqual(y["list"], [{"name": "a", "v": 1}, "b"])
        self.assertEqual(y["lit"], "l1\nl2\n")

    def test_empty_flow_and_comments(self):
        y = myasi.parse_yaml("# c\nsources: []  # none yet\nq: 'it''s # not a comment'\nn: ~\nb: no\n")
        self.assertEqual(y, {"sources": [], "q": "it's # not a comment", "n": None, "b": False})

    def test_only_comments(self):
        self.assertIsNone(myasi.parse_yaml("# just\n# comments\n"))

    def test_bad_indent_raises(self):
        with self.assertRaises(ValueError):
            myasi.parse_yaml("a: 1\n   b: 2\n")

    def test_frontmatter_bom_crlf_and_missing(self):
        fm, body = myasi.parse_frontmatter("\ufeff---\r\nname: x\r\ndescription: \"d: e\"\r\n---\r\nbody")
        self.assertEqual(fm, {"name": "x", "description": "d: e"})
        self.assertEqual(myasi.parse_frontmatter("no frontmatter"), ({}, "no frontmatter"))

    def test_flow_map_and_url_hash(self):
        y = myasi.parse_yaml("a: {k: v, n: [1, 2]}\nu: https://x.y/#frag\n")
        self.assertEqual(y, {"a": {"k": "v", "n": [1, 2]}, "u": "https://x.y/#frag"})


class McpTest(unittest.TestCase):
    def test_codex_env_forwarding(self):
        out = myasi.to_codex_toml({"ex": {"command": "npx", "args": ["-y", "example-mcp"],
                                          "env": {"EXAMPLE_API_KEY": "${EXAMPLE_API_KEY}", "MODE": "x"}}})
        self.assertIn('env_vars = ["EXAMPLE_API_KEY"]', out)
        self.assertIn('env = { "MODE" = "x" }', out)
        self.assertNotIn("${", out)

    def test_codex_renamed_env_warns(self):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            out = myasi.to_codex_toml({"ex": {"command": "c", "env": {"A": "${B}", "C": "x-${D}"}}})
        self.assertIn('env_vars = ["B"]', out)
        self.assertIn("renames a variable", buf.getvalue())
        self.assertIn("mixes text", buf.getvalue())

    def test_cursor_syntax(self):
        e = myasi.to_json_entry({"command": "c", "env": {"K": "${K}"}}, "cursor")
        self.assertEqual(e["env"]["K"], "${env:K}")


if __name__ == "__main__":
    unittest.main()
