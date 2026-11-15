"""get / update / remove / list / search / info / sync / doctor / new against a local tree."""
import json
import os
import subprocess
import sys
from pathlib import Path

from helpers import ROOT, Base, myasi


class GetRemoveTest(Base):
    def test_get_by_bare_name_links_everywhere(self):
        out, _ = self.run_cli("get", "hello-myasi", "--source", str(ROOT))
        for d in (self.agents_dir, self.claude_dir):
            p = d / "hello-myasi"
            self.assertTrue(p.is_symlink(), p)
            self.assertTrue((p / "SKILL.md").is_file())
            self.assertEqual(p.resolve(), (ROOT / "skills" / "hello-myasi").resolve())
        rec = self.state()["installs"]["hello-myasi"]
        self.assertEqual(rec["kind"], "own")
        self.assertEqual(rec["path"], "skills/hello-myasi")
        self.assertEqual(rec["source_spec"], str(ROOT))
        self.assertEqual(rec["version"], "0.1.0")
        agents = {Path(t["path"]).parent.name and t["path"]: t["agents"] for t in rec["targets"]}
        self.assertEqual(agents[str(self.agents_dir / "hello-myasi")], ["codex", "deepseek", "dsh", "pi"])
        self.assertEqual(agents[str(self.claude_dir / "hello-myasi")], ["claude"])
        self.assertTrue(all(t["mode"] == "link" for t in rec["targets"]))

    def test_alias_resolves(self):
        out, _ = self.run_cli("get", "Hello", "--agent", "claude", "--source", str(ROOT))
        self.assertIn("alias of hello-myasi", out)
        self.assertTrue((self.claude_dir / "hello-myasi" / "SKILL.md").exists())
        self.assertFalse((self.claude_dir / "hello").exists())
        self.assertEqual(list(self.state()["installs"]), ["hello-myasi"])

    def test_unknown_name_suggests_and_installs_nothing(self):
        _, err = self.run_cli("get", "hello-myasi", "helo-myasi", "--source", str(ROOT), code=1)
        self.assertIn("unknown skill 'helo-myasi'", err)
        self.assertIn("closest: hello-myasi", err)
        self.assertFalse(self.agents_dir.exists())  # resolved before touching disk

    def test_agent_selection_and_copy(self):
        self.run_cli("get", "hello-myasi", "--agent", "codex", "--copy", "--source", str(ROOT))
        p = self.agents_dir / "hello-myasi"
        self.assertTrue(p.is_dir() and not p.is_symlink())
        self.assertFalse(self.claude_dir.exists())
        (rec,) = self.state()["installs"]["hello-myasi"]["targets"]
        self.assertEqual((rec["mode"], rec["agents"]), ("copy", ["codex"]))
        with self.assertRaises(SystemExit):
            myasi.agent_targets("codex,vscode")

    def test_shared_dir_keeps_agents(self):
        self.run_cli("get", "hello-myasi", "--agent", "codex", "--source", str(ROOT))
        self.run_cli("get", "hello-myasi", "--agent", "pi", "--source", str(ROOT))
        (t,) = self.state()["installs"]["hello-myasi"]["targets"]
        self.assertEqual(t["agents"], ["codex", "pi"])

    def test_env_agent_default(self):
        os.environ["MYASI_AGENT"] = "claude"
        self.run_cli("get", "hello-myasi", "--source", str(ROOT))
        self.assertTrue((self.claude_dir / "hello-myasi").exists())
        self.assertFalse(self.agents_dir.exists())

    def test_idempotent_get(self):
        self.run_cli("get", "hello-myasi", "--source", str(ROOT))
        first = self.state()
        self.run_cli("get", "hello-myasi", "--source", str(ROOT))
        second = self.state()
        strip = lambda s: {n: dict(r, updated_at="") for n, r in s["installs"].items()}  # noqa: E731
        self.assertEqual(strip(first), strip(second))
        self.assertEqual(sorted(os.listdir(str(self.agents_dir))), ["hello-myasi"])

    def test_link_then_copy_switches_mode(self):
        self.run_cli("get", "hello-myasi", "--agent", "claude", "--source", str(ROOT))
        self.run_cli("get", "hello-myasi", "--agent", "claude", "--copy", "--source", str(ROOT))
        p = self.claude_dir / "hello-myasi"
        self.assertFalse(p.is_symlink())
        self.assertTrue((p / "SKILL.md").exists())
        self.assertTrue((ROOT / "skills" / "hello-myasi" / "SKILL.md").exists())  # source untouched

    def test_unmanaged_dir_needs_force(self):
        d = self.claude_dir / "hello-myasi"
        d.mkdir(parents=True)
        (d / "mine.txt").write_text("user data")
        _, err = self.run_cli("get", "hello-myasi", "--agent", "claude", "--source", str(ROOT), code=1)
        self.assertIn("not installed by myasi", err)
        self.assertTrue((d / "mine.txt").exists())
        self.run_cli("get", "hello-myasi", "--agent", "claude", "--force", "--source", str(ROOT))
        self.assertTrue((d / "SKILL.md").exists())

    def test_partial_failure_keeps_state(self):
        (self.claude_dir / "myasi").mkdir(parents=True)  # unmanaged conflict on the 2nd name
        self.run_cli("get", "hello-myasi", "myasi", "--agent", "claude", "--source", str(ROOT), code=1)
        self.assertIn("hello-myasi", self.state()["installs"])  # first install still recorded
        self.run_cli("remove", "hello-myasi", "--source", str(ROOT))
        self.assertFalse(os.path.lexists(str(self.claude_dir / "hello-myasi")))

    def test_profile_get(self):
        self.run_cli("get", "--profile", "core,example", "--agent", "claude", "--source", str(ROOT))
        self.assertEqual(sorted(self.state()["installs"]), ["hello-myasi", "myasi"])
        self.run_cli("get", "--profile", "nope", "--source", str(ROOT), code=1)

    def test_remove_all_and_partial(self):
        self.run_cli("get", "hello-myasi", "--source", str(ROOT))
        self.run_cli("remove", "hello", "--agent", "claude", "--source", str(ROOT))  # alias + one agent
        self.assertFalse(os.path.lexists(str(self.claude_dir / "hello-myasi")))
        self.assertTrue((self.agents_dir / "hello-myasi").exists())
        self.assertEqual(len(self.state()["installs"]["hello-myasi"]["targets"]), 1)
        self.run_cli("remove", "hello-myasi", "--source", str(ROOT))
        self.assertFalse(os.path.lexists(str(self.agents_dir / "hello-myasi")))
        self.assertEqual(self.state()["installs"], {})
        self.assertTrue((ROOT / "skills" / "hello-myasi" / "SKILL.md").exists())  # never deletes the source
        out, _ = self.run_cli("remove", "hello-myasi", "--source", str(ROOT))
        self.assertIn("nothing to do", out)

    def test_remove_copy_skips_foreign_dir(self):
        self.run_cli("get", "hello-myasi", "--agent", "claude", "--copy", "--source", str(ROOT))
        p = self.claude_dir / "hello-myasi"
        (p / "SKILL.md").write_text("---\nname: other\ndescription: x\n---\nx\n")  # replaced by someone else
        out, _ = self.run_cli("remove", "hello-myasi", "--source", str(ROOT))
        self.assertIn("skipped", out)
        self.assertTrue(p.exists())


class UpdateTest(Base):
    def test_update_copy_from_recorded_source(self):
        tree = self.make_tree()
        self.run_cli("get", "hello-myasi", "--agent", "claude", "--copy", "--source", str(tree))
        sj = tree / "skills" / "hello-myasi" / "skill.json"
        meta = json.loads(sj.read_text(encoding="utf-8"))
        meta["version"] = "0.2.0"
        sj.write_text(json.dumps(meta), encoding="utf-8")
        (tree / "skills" / "hello-myasi" / "new.md").write_text("new file")
        self.rebuild(tree)
        out, _ = self.run_cli("update")  # no --source: uses the one recorded in state.json
        self.assertIn("0.1.0 -> 0.2.0", out)
        self.assertTrue((self.claude_dir / "hello-myasi" / "new.md").exists())
        self.assertEqual(self.state()["installs"]["hello-myasi"]["version"], "0.2.0")
        out, _ = self.run_cli("update", "hello-myasi")
        self.assertIn("up to date", out)

    def test_update_not_installed_and_vanished(self):
        tree = self.make_tree(extra_skills=["temp-skill"])
        out, _ = self.run_cli("update", "hello-myasi", "--source", str(tree))
        self.assertIn("not installed", out)
        self.run_cli("get", "temp-skill", "--agent", "claude", "--copy", "--source", str(tree))
        import shutil
        shutil.rmtree(str(tree / "skills" / "temp-skill"))
        self.rebuild(tree)
        out, _ = self.run_cli("update", "--source", str(tree))
        self.assertIn("no longer in the registry", out)


class ListSearchInfoTest(Base):
    def test_list_json_and_filters(self):
        out, _ = self.run_cli("list", "--json", "--source", str(ROOT))
        rows = {r["name"]: r for r in json.loads(out)}
        self.assertEqual(set(rows), {"myasi", "hello-myasi"})
        self.assertEqual(rows["hello-myasi"]["kind"], "own")
        out, _ = self.run_cli("list", "--tag", "example", "--json", "--source", str(ROOT))
        self.assertEqual([r["name"] for r in json.loads(out)], ["hello-myasi"])
        out, _ = self.run_cli("list", "--profile", "core", "--json", "--source", str(ROOT))
        self.assertEqual([r["name"] for r in json.loads(out)], ["myasi"])
        self.run_cli("get", "myasi", "--agent", "claude", "--source", str(ROOT))
        out, _ = self.run_cli("list", "--installed", "--source", str(ROOT))
        self.assertIn("myasi", out)
        self.assertIn("claude", out)
        self.assertIn("1 skill(s)", out)

    def test_search(self):
        out, _ = self.run_cli("search", "hello", "--source", str(ROOT))
        self.assertTrue(out.startswith("hello-myasi"))
        out, _ = self.run_cli("search", "示例", "--source", str(ROOT))
        self.assertIn("hello-myasi", out)
        out, _ = self.run_cli("search", "zzzzqqq", "--source", str(ROOT))
        self.assertIn("no match", out)

    def test_info(self):
        out, _ = self.run_cli("info", "hello", "--source", str(ROOT))
        d = json.loads(out)
        self.assertEqual((d["name"], d["aliases"], d["installed"]), ("hello-myasi", ["hello"], []))
        _, err = self.run_cli("info", "nothing-like-it", "--source", str(ROOT), code=1)
        self.assertIn("unknown skill", err)


class SyncTest(Base):
    def test_sync_profiles_prune_and_agent(self):
        tree = self.make_tree(extra_skills=["extra-one"])
        (tree / "profiles" / "clients.yaml").write_text(
            "clients:\n  codex:\n    profiles: [core]\n  claude:\n    profiles: [core]\n    extra: [extra-one]\n",
            encoding="utf-8")
        self.rebuild(tree)
        self.run_cli("sync", "--source", str(tree))
        self.assertTrue((self.agents_dir / "myasi").exists())
        self.assertTrue((self.claude_dir / "myasi").exists())
        self.assertTrue((self.claude_dir / "extra-one").exists())
        self.assertFalse((self.agents_dir / "extra-one").exists())
        before = self.state()
        self.run_cli("sync", "--source", str(tree))  # idempotent
        self.assertEqual(set(before["installs"]), set(self.state()["installs"]))
        # manual install + --prune removes what the profile no longer wants (only in synced dirs)
        self.run_cli("get", "hello-myasi", "--agent", "claude", "--source", str(tree))
        (tree / "profiles" / "clients.yaml").write_text(
            "clients:\n  codex:\n    profiles: [core]\n  claude:\n    profiles: [core]\n", encoding="utf-8")
        self.rebuild(tree)
        out, _ = self.run_cli("sync", "--agent", "claude", "--prune", "--source", str(tree))
        self.assertIn("pruned", out)
        self.assertFalse(os.path.lexists(str(self.claude_dir / "extra-one")))
        self.assertFalse(os.path.lexists(str(self.claude_dir / "hello-myasi")))
        self.assertTrue((self.agents_dir / "myasi").exists())
        self.assertNotIn("extra-one", self.state()["installs"])
        self.run_cli("sync", "--agent", "bogus", "--source", str(tree), code=1)


class DoctorTest(Base):
    def test_doctor_clean_broken_and_duplicates(self):
        self.run_cli("get", "hello-myasi", "--agent", "codex", "--source", str(ROOT))
        out, _ = self.run_cli("doctor", "--strict", "--source", str(ROOT))
        self.assertIn("all good", out)
        legacy = self.home / ".codex" / "skills" / "hello-myasi"
        legacy.mkdir(parents=True)
        os.symlink(str(self.tmp / "gone"), str(self.agents_dir / "dangling"))
        out, _ = self.run_cli("doctor", "--strict", "--source", str(ROOT), code=1)
        self.assertIn("visible twice", out)
        self.assertIn("broken link", out)
        self.run_cli("doctor", "--source", str(ROOT))  # non-strict still exits 0


class NewTest(Base):
    def test_new_scaffold_validates(self):
        tree = self.make_tree()
        self.run_cli("new", "my-tool", "-d", "当我说 my-tool 时使用", "--tags", "a,b", "--alias", "mt", "--dir", str(tree))
        d = tree / "skills" / "my-tool"
        self.assertTrue((d / "SKILL.md").exists() and (d / "agents" / "openai.yaml").exists())
        fm, _ = myasi.parse_frontmatter((d / "SKILL.md").read_text(encoding="utf-8"))
        self.assertEqual(fm, {"name": "my-tool", "description": "当我说 my-tool 时使用"})
        reg = json.loads((tree / "registry.json").read_text(encoding="utf-8"))
        self.assertEqual(reg["aliases"]["mt"], "my-tool")
        r = subprocess.run([sys.executable, str(tree / "scripts" / "validate.py")], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, universal_newlines=True)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.run_cli("get", "mt", "--agent", "claude", "--source", str(tree))
        self.assertTrue((self.claude_dir / "my-tool" / "SKILL.md").exists())
        self.run_cli("new", "my-tool", "--dir", str(tree), code=1)  # exists
        self.run_cli("new", "Bad_Name", "--dir", str(tree), code=1)
        self.run_cli("new", "x", "--dir", str(self.tmp), code=1)  # not a clone


class CliManifestTest(Base):
    def test_cli_dry_run_per_os(self):
        tree = self.make_tree()
        (tree / "cli" / "npm" / "global.txt").write_text("@scope/pkg  # comment\n# skip\n", encoding="utf-8")
        out, _ = self.run_cli("cli", "--os", "windows", "--source", str(tree))
        self.assertIn("winget import -i", out)
        self.assertIn("npm install -g @scope/pkg", out)
        self.assertIn("dry-run", out)
        out, _ = self.run_cli("cli", "--os", "macos", "--source", str(tree))
        self.assertIn("brew bundle", out)
        self.assertNotIn("winget", out)
