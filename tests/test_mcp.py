"""`myasi mcp apply` output and --write merge for every client format, into a temp HOME."""
import json
import os
import sys
import unittest
from unittest import mock

from helpers import ROOT, Base, myasi

SERVERS = """servers:
  plain:
    command: npx
    args: ["-y", "pkg"]
    env:
      API_KEY: "${API_KEY}"
      MODE: fast
    clients: ["*"]
  remote:
    transport: http
    url: https://mcp.example.com/mcp
    headers:
      Authorization: "Bearer ${REMOTE_TOKEN}"
      X-Team: "${TEAM_ID}"
    clients: ["*"]
  codex-only:
    command: uvx
    args: [tool]
    clients: [codex]
    startup_timeout_sec: 30
  draft:
    command: TODO
    clients: ["*"]
    verified: false
"""


class McpApplyTest(Base):
    def setUp(self):
        super().setUp()
        self.f = self.tmp / "servers.yaml"
        self.f.write_text(SERVERS, encoding="utf-8")

    def apply(self, agent, *extra):
        return self.run_cli("mcp", "apply", "--agent", agent, "--file", str(self.f), "--source", str(ROOT), *extra)[0]

    def test_dry_run_writes_nothing(self):
        out = self.apply("all")
        for a in ("codex", "claude", "deepseek", "cursor", "gemini"):
            self.assertIn("## %s" % a, out)
        self.assertIn("skipped unverified: draft", out)
        self.assertIn("dry-run", out)
        self.assertEqual(sorted(os.listdir(str(self.home))), [])

    @unittest.skipIf(sys.version_info < (3, 11), "tomllib needs 3.11")
    def test_codex_toml_merge_idempotent(self):
        import tomllib
        cfg = self.home / ".codex" / "config.toml"
        cfg.parent.mkdir()
        cfg.write_text('model = "x"\n\n[mcp_servers.mine]\ncommand = "keep"\n', encoding="utf-8")
        self.apply("codex", "--write")
        self.apply("codex", "--write")
        text = cfg.read_text(encoding="utf-8")
        self.assertEqual(text.count(myasi.MARK_BEGIN), 1)
        d = tomllib.loads(text)
        self.assertEqual(d["model"], "x")
        self.assertEqual(d["mcp_servers"]["mine"], {"command": "keep"})
        self.assertEqual(d["mcp_servers"]["plain"]["env_vars"], ["API_KEY"])
        self.assertEqual(d["mcp_servers"]["plain"]["env"], {"MODE": "fast"})
        self.assertEqual(d["mcp_servers"]["remote"]["bearer_token_env_var"], "REMOTE_TOKEN")
        self.assertEqual(d["mcp_servers"]["remote"]["env_http_headers"], {"X-Team": "TEAM_ID"})
        self.assertEqual(d["mcp_servers"]["codex-only"]["startup_timeout_sec"], 30)
        self.assertNotIn("draft", d["mcp_servers"])
        self.assertNotIn("${", text)
        self.apply("codex", "--write", "--include-unverified")
        self.assertIn("draft", tomllib.loads(cfg.read_text(encoding="utf-8"))["mcp_servers"])

    def test_codex_refuses_unmanaged_clash_and_only_write(self):
        cfg = self.home / ".codex" / "config.toml"
        cfg.parent.mkdir()
        cfg.write_text('[mcp_servers.plain]\ncommand = "mine"\n', encoding="utf-8")
        self.run_cli("mcp", "apply", "--agent", "codex", "--write", "--file", str(self.f), "--source", str(ROOT), code=1)
        self.assertEqual(cfg.read_text(encoding="utf-8"), '[mcp_servers.plain]\ncommand = "mine"\n')
        self.run_cli("mcp", "apply", "--agent", "codex", "--write", "--only", "remote", "--file", str(self.f),
                     "--source", str(ROOT), code=1)

    def test_json_clients_merge(self):
        for agent, rel in (("deepseek", ".deepseek/mcp.json"), ("cursor", ".cursor/mcp.json"),
                           ("gemini", ".gemini/settings.json")):
            p = self.home / rel
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps({"theme": "dark", "mcpServers": {"mine": {"command": "keep"}}}), encoding="utf-8")
            self.apply(agent, "--write")
            d = json.loads(p.read_text(encoding="utf-8"))
            self.assertEqual(d["theme"], "dark")
            self.assertEqual(d["mcpServers"]["mine"], {"command": "keep"})
            self.assertEqual(set(d["mcpServers"]), {"mine", "plain", "remote"})
            env = d["mcpServers"]["plain"]["env"]
            remote = d["mcpServers"]["remote"]
            if agent == "cursor":
                self.assertEqual(env["API_KEY"], "${env:API_KEY}")
                self.assertEqual(remote["headers"]["Authorization"], "Bearer ${env:REMOTE_TOKEN}")
            else:
                self.assertEqual(env["API_KEY"], "${API_KEY}")
            if agent == "gemini":
                self.assertEqual(remote["httpUrl"], "https://mcp.example.com/mcp")
            else:
                self.assertEqual((remote["type"], remote["url"]), ("http", "https://mcp.example.com/mcp"))

    def test_json_creates_missing_file(self):
        self.apply("cursor", "--write")
        self.assertIn("plain", json.loads((self.home / ".cursor" / "mcp.json").read_text(encoding="utf-8"))["mcpServers"])

    def test_claude_commands_and_write(self):
        out = self.apply("claude", "--only", "plain")
        self.assertIn("claude mcp add-json plain '", out)
        self.assertIn('"type": "stdio"', out)
        self.assertIn("-s user", out)
        calls = []
        with mock.patch.object(myasi.shutil, "which", return_value="/usr/bin/claude"), \
                mock.patch.object(myasi.subprocess, "run",
                                  side_effect=lambda c, **k: calls.append(c) or mock.Mock(returncode=0, stderr="")):
            self.apply("claude", "--write")
        self.assertEqual([c[3] for c in calls], ["plain", "remote"])
        self.assertEqual(json.loads(calls[0][4])["env"], {"API_KEY": "${API_KEY}", "MODE": "fast"})
        with mock.patch.object(myasi.shutil, "which", return_value=None):
            self.run_cli("mcp", "apply", "--agent", "claude", "--write", "--file", str(self.f), "--source", str(ROOT),
                         code=1)

    def test_unverified_formats_print_only(self):
        for agent in ("dsh", "pi"):
            out = self.apply(agent, "--write")
            self.assertIn("not verified", out)
        self.assertEqual(sorted(os.listdir(str(self.home))), [])
        self.run_cli("mcp", "apply", "--agent", "vscode", "--file", str(self.f), "--source", str(ROOT), code=1)

    def test_repo_servers_yaml_renders(self):
        out, _ = self.run_cli("mcp", "apply", "--agent", "all", "--source", str(ROOT))
        self.assertIn("everything", out)
        out, _ = self.run_cli("mcp", "apply", "--agent", "codex", "--include-unverified", "--source", str(ROOT))
        self.assertIn('env_vars = ["EXAMPLE_API_KEY"]', out)
        self.assertIn('bearer_token_env_var = "EXAMPLE_TOKEN"', out)


if __name__ == "__main__":
    unittest.main()
