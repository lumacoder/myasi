"""Shared fixtures: throwaway HOME, in-process CLI runner, fixture repos (tree, bare git, tarball)."""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import myasi  # noqa: E402

HAS_GIT = shutil.which("git") is not None
REPO_FILES = ["registry.json", "skills", "profiles", "catalog", "mcp", "cli", "scripts", ".claude-plugin"]


def git(cwd, *args):
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")
    subprocess.run(["git", "-c", "init.defaultBranch=main", "-c", "core.autocrlf=false"] + list(args), cwd=str(cwd),
                   env=env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class Base(unittest.TestCase):
    """Every test gets its own HOME / MYASI_HOME and cleans up after itself."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="myasi-test-")).resolve()
        self.addCleanup(shutil.rmtree, str(self.tmp), ignore_errors=True)  # runs even if setUp fails later
        self.home = self.tmp / "home"
        self.home.mkdir()
        env = {"HOME": str(self.home), "USERPROFILE": str(self.home), "MYASI_HOME": str(self.home / ".myasi"),
               "PYTHONDONTWRITEBYTECODE": "1", "GIT_TERMINAL_PROMPT": "0"}
        for k in ("MYASI_SOURCE", "MYASI_REF", "MYASI_AGENT", "MYASI_REPO", "GITHUB_TOKEN", "GH_TOKEN"):
            env[k] = ""
        self.env = mock.patch.dict(os.environ, env)
        self.env.start()
        self.addCleanup(self.env.stop)
        for k in ("MYASI_SOURCE", "MYASI_REF", "MYASI_AGENT", "MYASI_REPO", "GITHUB_TOKEN", "GH_TOKEN"):
            os.environ.pop(k, None)

    # -- running the CLI in-process
    def run_cli(self, *argv, code=0):
        out, err = io.StringIO(), io.StringIO()
        rc = 0
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                rc = myasi.main(list(argv)) or 0
            except SystemExit as e:
                rc = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
        if code is not None:
            self.assertEqual(rc, code, "myasi %s\nstdout:\n%s\nstderr:\n%s" % (" ".join(argv), out.getvalue(), err.getvalue()))
        return out.getvalue(), err.getvalue()

    def state(self):
        f = self.home / ".myasi" / "state.json"
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"installs": {}}

    @property
    def agents_dir(self):
        return self.home / ".agents" / "skills"

    @property
    def claude_dir(self):
        return self.home / ".claude" / "skills"

    # -- fixture repos
    def make_tree(self, name="tree", extra_skills=(), external=None):
        """A copy of this repo (registry, skills, scripts...) plus optional extra skills; registry rebuilt."""
        t = self.tmp / name
        t.mkdir()
        for f in REPO_FILES:
            src = ROOT / f
            if src.is_dir():
                shutil.copytree(str(src), str(t / f), ignore=shutil.ignore_patterns("__pycache__"))
            elif src.exists():
                shutil.copy2(str(src), str(t / f))
        for s in extra_skills:
            self.add_skill(t, s)
        if external:
            lines = ["sources:"]
            for e in external:
                lines.append("  - name: %s" % e["name"])
                for k in ("repo", "path", "ref", "license", "description"):
                    if e.get(k):
                        lines.append("    %s: %s" % (k, e[k]))
            (t / "catalog" / "external.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.rebuild(t)
        return t

    def add_skill(self, tree, name, version="0.1.0", body="body", aliases=()):
        d = Path(tree) / "skills" / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text("---\nname: %s\ndescription: fixture skill %s\n---\n%s\n" % (name, name, body),
                                    encoding="utf-8")
        (d / "skill.json").write_text(json.dumps({"version": version, "tags": ["fixture"], "aliases": list(aliases)}),
                                      encoding="utf-8")
        (d / "data.txt").write_text("payload of " + name, encoding="utf-8")

    def rebuild(self, tree):
        subprocess.run([sys.executable, str(Path(tree) / "scripts" / "build_registry.py")], check=True,
                       stdout=subprocess.DEVNULL, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))

    def make_bare(self, tree):
        """Commit `tree` and publish it as a bare repo; returns (bare_path, file:// url)."""
        git(tree, "init", "-q")
        git(tree, "add", "-A")
        git(tree, "commit", "-qm", "fixture")
        bare = self.tmp / (Path(tree).name + ".git")
        git(self.tmp, "clone", "-q", "--bare", str(tree), str(bare))
        git(bare, "config", "uploadpack.allowFilter", "true")
        return bare, bare.as_uri()

    def push_change(self, tree, msg="change"):
        git(tree, "add", "-A")
        git(tree, "commit", "-qm", msg)
        git(tree, "push", "-q", str(self.tmp / (Path(tree).name + ".git")), "HEAD:main")

    def make_tarball(self, tree, top="myasi-main", evil=False):
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tf:
            tf.add(str(tree), arcname=top)
            if evil:
                data = b"pwned"
                ti = tarfile.TarInfo(top + "/skills/hello-myasi/../../../escape.txt")
                ti.size = len(data)
                tf.addfile(ti, io.BytesIO(data))
                ln = tarfile.TarInfo(top + "/skills/hello-myasi/link")
                ln.type, ln.linkname = tarfile.SYMTYPE, "/etc/passwd"
                tf.addfile(ln)
        return buf.getvalue()
