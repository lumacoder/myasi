"""Fetching ONE skill without the whole repo: git partial clone + sparse checkout, and the tarball path."""
import os
import unittest
from pathlib import Path
from unittest import mock

from helpers import HAS_GIT, Base, git, myasi


def files_under(d):
    return sorted(str(p.relative_to(d)).replace("\\", "/") for p in Path(d).rglob("*")
                  if p.is_file() and ".git" not in p.relative_to(d).parts)


@unittest.skipUnless(HAS_GIT, "git not installed")
class GitSourceTest(Base):
    def setUp(self):
        super().setUp()
        self.tree = self.make_tree(extra_skills=["big-one", "big-two"])
        self.bare, self.url = self.make_bare(self.tree)
        os.environ["MYASI_SOURCE"] = self.url

    def cache(self):
        (c,) = [p for p in (self.home / ".myasi" / "cache").iterdir()]
        return c

    def test_only_requested_skill_is_checked_out(self):
        self.run_cli("get", "big-one", "--agent", "claude")
        c = self.cache()
        files = files_under(c)
        self.assertIn("skills/big-one/SKILL.md", files)
        self.assertFalse([f for f in files if f.startswith("skills/") and not f.startswith("skills/big-one/")], files)
        self.assertFalse([f for f in files if f.startswith(("mcp/", "cli/", "scripts/"))], files)
        self.assertIn("registry.json", files)  # cone mode keeps root files only
        link = self.claude_dir / "big-one"
        self.assertEqual(link.resolve(), (c / "skills" / "big-one").resolve())
        self.assertEqual(files_under(link), ["SKILL.md", "data.txt", "skill.json"])
        self.assertEqual(self.state()["installs"]["big-one"]["source_spec"], self.url)

    def test_second_skill_extends_sparse_set_and_remove_shrinks_it(self):
        self.run_cli("get", "big-one", "--agent", "claude")
        self.run_cli("get", "big-two", "--agent", "claude", "--copy")
        c = self.cache()
        self.assertTrue((c / "skills" / "big-two").is_dir())
        self.run_cli("remove", "big-two")
        self.assertFalse((c / "skills" / "big-two").exists())
        self.assertTrue((c / "skills" / "big-one" / "SKILL.md").exists())
        self.run_cli("remove", "big-one")
        self.assertFalse((self.home / ".myasi" / "cache").exists() and any((self.home / ".myasi" / "cache").iterdir()))

    def test_update_pulls_new_commit(self):
        self.run_cli("get", "big-one", "--agent", "claude", "--copy")
        self.add_skill(self.tree, "big-one", version="0.3.0", body="changed body")
        self.rebuild(self.tree)
        self.push_change(self.tree)
        os.environ.pop("MYASI_SOURCE")
        out, _ = self.run_cli("update")  # recorded source_spec
        self.assertIn("0.1.0 -> 0.3.0", out)
        self.assertIn("changed body", (self.claude_dir / "big-one" / "SKILL.md").read_text(encoding="utf-8"))

    def test_mcp_and_cli_from_git_source(self):
        out, _ = self.run_cli("mcp", "apply", "--agent", "codex")
        self.assertIn("[mcp_servers.everything]", out)
        out, _ = self.run_cli("cli", "--os", "linux")
        self.assertIn("dry-run", out)

    def test_ref_selection(self):
        git(self.tree, "checkout", "-qb", "dev")
        self.add_skill(self.tree, "dev-only")
        self.rebuild(self.tree)
        git(self.tree, "add", "-A")
        git(self.tree, "commit", "-qm", "dev")
        git(self.tree, "push", "-q", str(self.bare), "dev")
        self.run_cli("get", "dev-only", "--agent", "claude", code=1)  # not on main
        self.run_cli("get", "dev-only", "--agent", "claude", "--ref", "dev")
        self.assertTrue((self.claude_dir / "dev-only" / "SKILL.md").exists())

    def test_bare_repo_path_as_source(self):
        os.environ.pop("MYASI_SOURCE")
        self.run_cli("get", "big-two", "--agent", "claude", "--source", str(self.bare))
        self.assertTrue((self.claude_dir / "big-two" / "SKILL.md").exists())

    def test_clone_failure_message(self):
        os.environ["MYASI_SOURCE"] = (self.tmp / "missing.git").as_uri()
        _, err = self.run_cli("get", "big-one", code=1)
        self.assertIn("git clone failed", err)
        self.assertFalse((self.home / ".myasi" / "cache").exists() and any((self.home / ".myasi" / "cache").iterdir()))

    def test_mano_asi_from_bare_repo_and_devasi_alias(self):
        """Real example skill: get by alias from a local bare repo, only that skill dir is checked out."""
        os.environ.pop("MYASI_SOURCE", None)
        out, _ = self.run_cli("get", "devasi", "--agent", "claude", "--source", str(self.bare))
        self.assertIn("alias of mano-asi", out)
        self.assertTrue((self.claude_dir / "mano-asi" / "SKILL.md").exists())
        self.assertFalse((self.claude_dir / "devasi").exists())
        c = self.cache()
        files = files_under(c)
        skill_files = [f for f in files if f.startswith("skills/")]
        self.assertTrue(skill_files and all(f.startswith("skills/mano-asi/") for f in skill_files), files)
        self.assertIn("skills/mano-asi/SKILL.md", files)
        self.assertFalse([f for f in files if f.startswith(("skills/hello-myasi/", "skills/myasi/", "skills/big-"))], files)
        self.assertEqual(self.state()["installs"]["mano-asi"]["path"], "skills/mano-asi")


@unittest.skipUnless(HAS_GIT, "git not installed")
class ExternalSkillTest(Base):
    """Third-party entries: --yes gate; fetched from the upstream repo (redirected to a local bare repo)."""

    def test_external_needs_yes_and_fetches_one_dir(self):
        up = self.tmp / "upstream"
        up.mkdir()
        for n in ("ext-a", "ext-b"):
            self.add_skill(up, n)
        git(up, "init", "-q")
        git(up, "add", "-A")
        git(up, "commit", "-qm", "up")
        bare = self.tmp / "upstream.git"
        git(self.tmp, "clone", "-q", "--bare", str(up), str(bare))
        tree = self.make_tree(external=[{"name": "ext-a", "repo": "someone/skills", "path": "skills/ext-a",
                                         "ref": "main", "license": "MIT", "description": "third party"}])
        os.environ.update({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "url.%s.insteadOf" % bare.as_uri(),
                           "GIT_CONFIG_VALUE_0": "https://github.com/someone/skills.git"})
        out, _ = self.run_cli("get", "ext-a", "--agent", "claude", "--source", str(tree))
        self.assertIn("third-party", out)
        self.assertFalse((self.claude_dir / "ext-a").exists())
        self.run_cli("get", "ext-a", "--agent", "claude", "--yes", "--source", str(tree))
        self.assertTrue((self.claude_dir / "ext-a" / "SKILL.md").exists())
        rec = self.state()["installs"]["ext-a"]
        self.assertEqual((rec["kind"], rec["repo"]), ("external", "someone/skills"))
        caches = list((self.home / ".myasi" / "cache").iterdir())
        self.assertEqual(len(caches), 1)
        self.assertFalse((caches[0] / "skills" / "ext-b").exists())
        out, _ = self.run_cli("list", "--json", "--source", str(tree))
        self.assertIn('"kind": "ext"', out)
        self.run_cli("update", "ext-a", "--source", str(tree))
        self.run_cli("remove", "ext-a", "--source", str(tree))
        self.assertFalse(os.path.lexists(str(self.claude_dir / "ext-a")))
        self.assertEqual(list((self.home / ".myasi" / "cache").iterdir()), [])


class TarSourceTest(Base):
    """No git on the machine: registry from raw.githubusercontent, skill dir from the codeload tarball."""

    def setUp(self):
        super().setUp()
        self.tree = self.make_tree(extra_skills=["big-one"])
        self.calls = []

    def fake_http(self, tarball):
        def http_get(url, accept=None):
            self.calls.append(url)
            if url.endswith("/registry.json") or "contents/registry.json" in url:
                return (self.tree / "registry.json").read_bytes()
            if "codeload.github.com" in url:
                return tarball
            if url.endswith("mcp/servers.yaml"):
                return (self.tree / "mcp" / "servers.yaml").read_bytes()
            raise AssertionError("unexpected url " + url)
        return http_get

    def test_tarball_extracts_only_requested_dir(self):
        tb = self.make_tarball(self.tree, evil=True)
        with mock.patch.object(myasi, "has_git", return_value=False), \
                mock.patch.object(myasi, "http_get", self.fake_http(tb)):
            src = myasi.make_source("someone/myasi")
            self.assertIsInstance(src, myasi.TarSource)
            self.run_cli("get", "big-one", "hello-myasi", "--agent", "claude", "--copy", "--source", "someone/myasi")
        self.assertEqual(len([u for u in self.calls if "codeload" in u]), 1)  # one download for two skills
        self.assertTrue((self.claude_dir / "big-one" / "data.txt").exists())
        cache = self.home / ".myasi" / "cache"
        (c,) = list(cache.iterdir())
        self.assertEqual(sorted(os.listdir(str(c / "skills"))), ["big-one", "hello-myasi"])
        self.assertFalse((c / "mcp").exists())
        self.assertFalse((c / "skills" / "hello-myasi" / "link").exists())  # symlink member skipped
        self.assertFalse(list(self.tmp.rglob("escape.txt")))  # path traversal member skipped
        with mock.patch.object(myasi, "has_git", return_value=False):
            self.run_cli("remove", "big-one", "hello-myasi", "--source", "someone/myasi")
        self.assertFalse(cache.exists() and any(cache.iterdir()))

    def test_tarball_missing_dir(self):
        tb = self.make_tarball(self.tree)
        with mock.patch.object(myasi, "has_git", return_value=False), \
                mock.patch.object(myasi, "http_get", self.fake_http(tb)):
            src = myasi.make_source("https://github.com/someone/myasi.git", "main")
            with self.assertRaises(SystemExit):
                src.fetch("skills/not-there")

    def test_token_uses_api_for_registry(self):
        os.environ["GITHUB_TOKEN"] = "dummy-value-for-test"
        tb = self.make_tarball(self.tree)
        with mock.patch.object(myasi, "has_git", return_value=False), \
                mock.patch.object(myasi, "http_get", self.fake_http(tb)):
            myasi.make_source("someone/myasi").registry()
        self.assertTrue(self.calls[0].startswith("https://api.github.com/repos/someone/myasi/contents/registry.json"))

    def test_git_env_passes_token_without_argv(self):
        os.environ["GITHUB_TOKEN"] = "dummy-value-for-test"
        for k in ("GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0"):
            os.environ.pop(k, None)
        env = myasi.git_env("https://github.com/someone/myasi.git")
        self.assertEqual(env["GIT_CONFIG_KEY_0"], "http.https://github.com/.extraheader")
        self.assertFalse("GIT_CONFIG_KEY_0" in myasi.git_env("file:///tmp/x.git"), "token header leaked to non-GitHub URL")
        os.environ.update({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.quotePath", "GIT_CONFIG_VALUE_0": "false"})
        env = myasi.git_env("https://github.com/someone/myasi.git")  # appends after existing env config
        self.assertEqual((env["GIT_CONFIG_COUNT"], env["GIT_CONFIG_KEY_0"]), ("2", "core.quotePath"))
        self.assertEqual(env["GIT_CONFIG_KEY_1"], "http.https://github.com/.extraheader")
        req = []
        with mock.patch.object(myasi.urllib.request, "urlopen", side_effect=lambda r, timeout: req.append(r) or
                               mock.MagicMock(__enter__=lambda s: mock.Mock(read=lambda: b"{}"))):
            myasi.http_get("https://example.com/x")
            myasi.http_get("https://raw.githubusercontent.com/a/b/main/x")
        self.assertIsNone(req[0].get_header("Authorization"))  # token never sent to other hosts
        self.assertEqual(req[1].get_header("Authorization"), "Bearer dummy-value-for-test")


class MakeSourceTest(Base):
    def test_kinds(self):
        tree = self.make_tree()
        self.assertIsInstance(myasi.make_source(str(tree)), myasi.LocalSource)
        self.assertIsInstance(myasi.make_source(tree.as_uri()), myasi.LocalSource)
        with mock.patch.object(myasi, "has_git", return_value=True):
            s = myasi.make_source("owner/repo", "v1")
            self.assertIsInstance(s, myasi.GitSource)
            self.assertEqual((s.url, s.ref), ("https://github.com/owner/repo.git", "v1"))
        with self.assertRaises(SystemExit):
            myasi.make_source(str(self.tmp))  # neither tree nor bare repo
