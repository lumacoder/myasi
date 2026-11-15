#!/usr/bin/env python3
"""myasi — 我的超级人工智能工具集（skills / MCP / CLI）管理器。

Users refer to skills by bare NAME only; ``skills/<name>/`` is internal storage.
Python 3.8+ standard library only. Works on Windows (py/python), Linux and macOS.
"""
import argparse
import base64
import difflib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

__version__ = "0.1.0"
DEFAULT_REPO = "lumacoder/myasi"
DEFAULT_REF = "main"
GITHUB_HOSTS = ("github.com", "api.github.com", "codeload.github.com", "raw.githubusercontent.com")
SHARED = "~/.agents/skills"
AGENT_DIRS = {  # Codex/pi/dsh/deepseek TUI all read ~/.agents/skills; Claude Code does not.
    "codex": SHARED, "pi": SHARED, "dsh": SHARED, "deepseek": SHARED,
    "claude": "~/.claude/skills",
}
LEGACY_DIRS = ["~/.codex/skills", "~/.pi/agent/skills", "~/.deepseek/skills", "~/.dsh/skills"]
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".git", ".DS_Store", "node_modules")
IS_WIN = os.name == "nt"


# ---------------------------------------------------------------- utilities
def die(msg, code=1):
    print("myasi: " + msg, file=sys.stderr)
    sys.exit(code)


def info(msg):
    print(msg)


def home():
    return Path(os.path.expanduser("~"))


def expand(p):
    return Path(os.path.expanduser(p))


def myasi_home():
    return Path(os.environ.get("MYASI_HOME") or (home() / ".myasi"))


def token():
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""


def write_lf(path, text):
    """Write UTF-8 with LF endings on every OS (Path.write_text(newline=) needs Python 3.10)."""
    with open(str(path), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def has_git():
    return shutil.which("git") is not None


# ---------------------------------------------------------------- YAML subset
# Supports: block maps/sequences, flow [..] {..}, quoted/plain scalars,
# block scalars (| |- > >-), comments. Enough for SKILL.md frontmatter and our
# config files; no anchors/tags/multi-docs.
def _indent(line):
    return len(line) - len(line.lstrip(" "))


def _strip_comment(s):
    q, skip = None, False
    for i, ch in enumerate(s):
        if skip:
            skip = False
        elif q:
            if q == '"' and ch == "\\":
                skip = True  # escaped char inside "..."
            elif ch == q and q == "'" and s[i + 1:i + 2] == "'":
                skip = True  # '' is an escaped quote inside '...'
            elif ch == q:
                q = None
        elif ch in "\"'" and (i == 0 or s[i - 1] in " [{,:"):
            q = ch
        elif ch == "#" and (i == 0 or s[i - 1] in " \t"):
            return s[:i].rstrip()
    return s


def _split_key(s):
    q = None
    for i, ch in enumerate(s):
        if q:
            if ch == q:
                q = None
        elif ch in "\"'" and i == 0:
            q = ch
        elif ch == ":" and (i + 1 == len(s) or s[i + 1] in " \t"):
            return _scalar(s[:i].strip()), s[i + 1:]
    return None, None


def _scalar(t):
    t = t.strip()
    if not t:
        return None
    if t[0] == '"' and t.endswith('"') and len(t) > 1:
        try:
            return json.loads(t)
        except ValueError:
            return t[1:-1]
    if t[0] == "'" and t.endswith("'") and len(t) > 1:
        return t[1:-1].replace("''", "'")
    low = t.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~"):
        return None
    if re.fullmatch(r"-?\d+", t):
        return int(t)
    if re.fullmatch(r"-?\d+\.\d+", t):
        return float(t)
    return t


def _flow(s, i=0):
    """Parse a flow value starting at s[i]; returns (value, next_index)."""
    while i < len(s) and s[i] == " ":
        i += 1
    if i < len(s) and s[i] in "[{":
        close = "]" if s[i] == "[" else "}"
        is_map = s[i] == "{"
        out = {} if is_map else []
        i += 1
        while True:
            while i < len(s) and s[i] in " ,":
                i += 1
            if i >= len(s):
                raise ValueError("unterminated flow collection")
            if s[i] == close:
                return out, i + 1
            if is_map:
                k, i = _flow_atom(s, i, stop=":")
                i += 1  # skip ':'
                v, i = _flow(s, i)
                out[_scalar(k)] = v
            else:
                v, i = _flow(s, i)
                out.append(v)
    atom, i = _flow_atom(s, i, stop=",]}")
    return _scalar(atom), i


def _flow_atom(s, i, stop):
    while i < len(s) and s[i] == " ":
        i += 1
    if i < len(s) and s[i] in "\"'":
        q = s[i]
        j = i + 1
        while j < len(s):
            if s[j] == "\\" and q == '"':
                j += 2
                continue
            if s[j] == q:
                if q == "'" and j + 1 < len(s) and s[j + 1] == "'":
                    j += 2
                    continue
                break
            j += 1
        return s[i:j + 1], j + 1
    j = i
    while j < len(s) and s[j] not in stop:
        j += 1
    return s[i:j].strip(), j


def _value(t):
    t = t.strip()
    if t and t[0] in "[{":
        v, _ = _flow(t)
        return v
    return _scalar(t)


class _Yaml:
    def __init__(self, text):
        self.L = text.replace("\t", "    ").splitlines()
        self.i = 0

    def skip(self):
        while self.i < len(self.L):
            s = self.L[self.i].strip()
            if s and not s.startswith("#"):
                break
            self.i += 1

    def parse(self):
        self.skip()
        if self.i >= len(self.L):
            return None
        return self.block(_indent(self.L[self.i]))

    def block(self, ind):
        s = self.L[self.i].strip()
        return self.seq(ind) if s == "-" or s.startswith("- ") else self.map(ind)

    def map(self, ind):
        d = {}
        while True:
            self.skip()
            if self.i >= len(self.L):
                break
            line = self.L[self.i]
            cur = _indent(line)
            if cur < ind:
                break
            content = _strip_comment(line.strip())
            if cur > ind or content == "-" or content.startswith("- "):
                if cur > ind:
                    raise ValueError("bad indentation at line %d: %r" % (self.i + 1, line))
                break
            k, rest = _split_key(content)
            if k is None:
                raise ValueError("expected 'key: value' at line %d: %r" % (self.i + 1, line))
            self.i += 1
            d[k] = self.after_key(rest, ind)
        return d

    def after_key(self, rest, ind):
        rest = rest.strip()
        if rest and rest[0] in "|>":
            return self.block_scalar(rest, ind)
        if rest:
            return _value(rest)
        self.skip()
        if self.i < len(self.L):
            nxt = self.L[self.i]
            n = _indent(nxt)
            if n > ind or (n == ind and (nxt.strip() == "-" or nxt.strip().startswith("- "))):
                return self.block(n)
        return None

    def seq(self, ind):
        out = []
        while True:
            self.skip()
            if self.i >= len(self.L):
                break
            line = self.L[self.i]
            cur = _indent(line)
            content = _strip_comment(line.strip())
            if cur != ind or not (content == "-" or content.startswith("- ")):
                break
            item = content[1:].strip()
            if not item:
                self.i += 1
                out.append(self.after_key("", ind))
                continue
            k, _ = _split_key(item) if item[:1] not in "[{\"'" else (None, None)
            if k is not None:
                new_ind = cur + len(content) - len(item)
                self.L[self.i] = " " * new_ind + item
                out.append(self.map(new_ind))
                continue
            self.i += 1
            out.append(_value(item))
        return out

    def block_scalar(self, head, ind):
        folded = head[0] == ">"
        chomp = head[1:2]
        lines = []
        bind = None
        while self.i < len(self.L):
            raw = self.L[self.i]
            if raw.strip() == "":
                lines.append("")
                self.i += 1
                continue
            n = _indent(raw)
            if n <= ind:
                break
            if bind is None:
                bind = n
            lines.append(raw[bind:])
            self.i += 1
        while lines and lines[-1] == "":
            lines.pop()
        if folded:
            text, prev_blank = "", True
            for ln in lines:
                if ln == "":
                    text += "\n"
                    prev_blank = True
                else:
                    text += ("" if prev_blank else " ") + ln
                    prev_blank = False
        else:
            text = "\n".join(lines)
        return text if chomp == "-" else text + "\n"


def parse_yaml(text):
    return _Yaml(text).parse()


def load_yaml(path):
    return parse_yaml(Path(path).read_text(encoding="utf-8")) or {}


def parse_frontmatter(text):
    """Return (frontmatter dict, body) of a SKILL.md."""
    text = text.lstrip("\ufeff")
    if not text.startswith("---"):
        return {}, text
    end = re.search(r"^---\s*$", text[3:], re.M)
    if not end:
        return {}, text
    fm = parse_yaml(text[3:3 + end.start()]) or {}
    return fm, text[3 + end.end():]


# ---------------------------------------------------------------- HTTP / auth
def http_get(url, accept=None):
    req = urllib.request.Request(url, headers={"User-Agent": "myasi/" + __version__})
    host = urllib.request.urlparse(url).hostname or ""
    if token() and host in GITHUB_HOSTS:
        req.add_header("Authorization", "Bearer " + token())
    if accept:
        req.add_header("Accept", accept)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        hint = " (private repo? set GITHUB_TOKEN or GH_TOKEN)" if e.code in (401, 403, 404) else ""
        die("HTTP %s for %s%s" % (e.code, url, hint))
    except urllib.error.URLError as e:
        die("network error for %s: %s" % (url, e.reason))


def git_env(url):
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    if token() and url.startswith("https://github.com/"):
        # Passed via env (not argv, not persisted in .git/config).
        cred = base64.b64encode(("x-access-token:" + token()).encode()).decode()
        n = int(env.get("GIT_CONFIG_COUNT", "0"))
        env["GIT_CONFIG_COUNT"] = str(n + 1)
        env["GIT_CONFIG_KEY_%d" % n] = "http.https://github.com/.extraheader"
        env["GIT_CONFIG_VALUE_%d" % n] = "AUTHORIZATION: basic " + cred
    return env


def git(args, cwd=None, url="", check=True):
    p = subprocess.run(["git"] + args, cwd=str(cwd) if cwd else None, env=git_env(url),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if check and p.returncode != 0:
        die("git %s failed: %s" % (" ".join(args[:3]), p.stderr.strip()[-400:]))
    return p


# ---------------------------------------------------------------- sources
def slug(s):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s).strip("_")[-80:]


class LocalSource:
    """A working tree on disk (e.g. a clone of the repo)."""
    kind = "local"

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.label = self.spec = str(self.root)
        self.ref = None

    def registry(self):
        f = self.root / "registry.json"
        if not f.exists():
            die("no registry.json in %s (run scripts/build_registry.py)" % self.root)
        return json.loads(f.read_text(encoding="utf-8"))

    def fetch(self, path):
        d = self.root / path
        if not (d / "SKILL.md").exists():
            die("missing %s/SKILL.md in local source" % path)
        return d

    def drop(self, path):
        pass

    def update(self):
        return False


class GitSource:
    """Partial clone + cone sparse-checkout: only registry/root files + requested skill dirs."""
    kind = "git"

    def __init__(self, url, ref=None):
        self.url, self.ref = url, ref
        self.spec = url
        self.label = url + ("@" + ref if ref else "")
        self.cache = myasi_home() / "cache" / slug(self.label)

    def ensure(self):
        if (self.cache / ".git").exists():
            return
        self.cache.parent.mkdir(parents=True, exist_ok=True)
        args = ["clone", "--quiet", "--depth", "1", "--filter=blob:none", "--sparse"]
        if self.ref:
            args += ["--branch", self.ref]
        p = git(args + [self.url, str(self.cache)], url=self.url, check=False)
        if p.returncode != 0:
            shutil.rmtree(self.cache, ignore_errors=True)
            die("git clone failed for %s: %s\n  private repo? use git credentials, or set GITHUB_TOKEN/GH_TOKEN"
                % (self.url, p.stderr.strip()[-300:]))

    def registry(self):
        self.ensure()
        f = self.cache / "registry.json"
        if not f.exists():
            die("%s has no registry.json at its root" % self.label)
        return json.loads(f.read_text(encoding="utf-8"))

    def sparse_list(self):
        p = git(["sparse-checkout", "list"], cwd=self.cache, check=False)
        return [x for x in p.stdout.split() if x]

    def fetch(self, path):
        self.ensure()
        if path not in self.sparse_list():
            git(["sparse-checkout", "add", path], cwd=self.cache, url=self.url)
        d = self.cache / path
        if not d.is_dir():
            die("%s not found in %s" % (path, self.label))
        return d

    def drop(self, path):
        if not (self.cache / ".git").exists():
            return
        keep = [x for x in self.sparse_list() if x != path]
        if not [x for x in keep if x.startswith("skills/")]:
            shutil.rmtree(str(self.cache), ignore_errors=True)  # nothing left: drop the cache (hygiene)
            return
        git(["sparse-checkout", "set"] + keep, cwd=self.cache, url=self.url)

    def update(self):
        self.ensure()
        before = git(["rev-parse", "HEAD"], cwd=self.cache).stdout.strip()
        git(["fetch", "--quiet", "--depth", "1", "--filter=blob:none", "origin", self.ref or "HEAD"],
            cwd=self.cache, url=self.url)
        git(["reset", "--quiet", "--hard", "FETCH_HEAD"], cwd=self.cache)
        return before != git(["rev-parse", "HEAD"], cwd=self.cache).stdout.strip()


class TarSource:
    """No git: codeload tarball, extracting only the requested directory."""
    kind = "tar"

    def __init__(self, repo, ref=None):
        self.repo, self.ref = repo, ref or DEFAULT_REF
        self.spec = repo
        self.label = "github:%s@%s (tarball)" % (repo, self.ref)
        self.cache = myasi_home() / "cache" / slug("tar_" + repo + "@" + self.ref)
        self._tar = None  # one download per run, however many skills are fetched

    def registry(self):
        if token():
            data = http_get("https://api.github.com/repos/%s/contents/registry.json?ref=%s" % (self.repo, self.ref),
                            accept="application/vnd.github.raw")
        else:
            data = http_get("https://raw.githubusercontent.com/%s/%s/registry.json" % (self.repo, self.ref))
        return json.loads(data.decode("utf-8"))

    def fetch(self, path):
        if self._tar is None:
            self._tar = self.download()
        data = self._tar
        dest = self.cache / path
        tmp = Path(tempfile.mkdtemp(prefix="myasi-"))
        try:
            with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
                found = False
                for m in tf.getmembers():
                    parts = m.name.split("/", 1)
                    if len(parts) < 2 or not (parts[1] == path or parts[1].startswith(path + "/")):
                        continue
                    if not (m.isfile() or m.isdir()) or ".." in Path(parts[1]).parts:
                        continue
                    found = True
                    out = tmp / parts[1]
                    if m.isdir():
                        out.mkdir(parents=True, exist_ok=True)
                    else:
                        out.parent.mkdir(parents=True, exist_ok=True)
                        out.write_bytes(tf.extractfile(m).read())
            if not found:
                die("%s not found in %s" % (path, self.label))
            if dest.exists():
                shutil.rmtree(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(tmp / path), str(dest))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return dest

    def download(self):
        return http_get("https://codeload.github.com/%s/tar.gz/%s" % (self.repo, self.ref))

    def drop(self, path):
        shutil.rmtree(self.cache / path, ignore_errors=True)
        if self.cache.exists() and not any(p.is_file() for p in self.cache.rglob("*")):
            shutil.rmtree(str(self.cache), ignore_errors=True)

    def update(self):
        self._tar = None
        return True  # re-download on next fetch


def script_repo_root():
    root = Path(__file__).resolve().parent.parent
    return root if (root / "registry.json").exists() and (root / "skills").is_dir() else None


def make_source(spec=None, ref=None):
    spec = spec or os.environ.get("MYASI_SOURCE") or ""
    ref = ref or os.environ.get("MYASI_REF") or None
    if not spec:
        root = script_repo_root()
        if root:
            return LocalSource(root)
        spec = os.environ.get("MYASI_REPO") or DEFAULT_REPO
    if spec.startswith("file://"):
        local = Path(urllib.request.url2pathname(spec[7:]))
        if (local / "registry.json").exists():
            return LocalSource(local)
        return GitSource(spec, ref)
    p = Path(os.path.expanduser(spec))
    if p.exists():
        if (p / "registry.json").exists():
            return LocalSource(p)
        if (p / "HEAD").exists() and (p / "objects").is_dir():  # bare repo
            return GitSource(p.resolve().as_uri(), ref)
        die("source %s is neither a working tree with registry.json nor a bare git repo" % p)
    m = re.fullmatch(r"(?:https://github\.com/)?([\w.-]+/[\w.-]+?)(?:\.git)?/?", spec)
    if m and not has_git():
        return TarSource(m.group(1), ref)
    if m:
        return GitSource("https://github.com/%s.git" % m.group(1), ref)
    if has_git():
        return GitSource(spec, ref)
    die("git not found and %s is not a GitHub repo; install git" % spec)


def source_for_external(ext):
    repo, ref = ext["repo"], ext.get("ref")
    if has_git():
        return GitSource("https://github.com/%s.git" % repo, ref)
    return TarSource(repo, ref)


# ---------------------------------------------------------------- registry
class Registry:
    def __init__(self, data):
        self.d = data
        self.skills = data.get("skills", {})
        self.external = data.get("external", {})
        self.aliases = data.get("aliases", {})

    def names(self):
        return sorted(set(self.skills) | set(self.external))

    def resolve(self, name, quiet=False):
        n = name.strip().lower()
        n = self.aliases.get(n, n)
        if n in self.skills:
            return n, dict(self.skills[n], kind="own")
        if n in self.external:
            return n, dict(self.external[n], kind="external")
        if quiet:
            return None, None
        close = difflib.get_close_matches(n, self.names() + list(self.aliases), n=3, cutoff=0.3)
        die("unknown skill %r. closest: %s  (try `myasi search %s`)" % (name, ", ".join(close) or "-", name))

    def profile(self, prof):
        p = self.d.get("profiles", {})
        if prof not in p:
            die("unknown profile %r; available: %s" % (prof, ", ".join(sorted(p))))
        return p[prof]


# ---------------------------------------------------------------- state
def state_path():
    return myasi_home() / "state.json"


def load_state():
    f = state_path()
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    return {"version": 1, "installs": {}}


def save_state(st):
    f = state_path()
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(f))


# ---------------------------------------------------------------- install helpers
def agent_targets(agent_arg):
    agents = []
    for a in (agent_arg or os.environ.get("MYASI_AGENT") or "all").split(","):
        a = a.strip().lower()
        if a == "all":
            agents += list(AGENT_DIRS)
        elif a in AGENT_DIRS:
            agents.append(a)
        else:
            die("unknown agent %r (codex|claude|pi|dsh|deepseek|all)" % a)
    dirs = {}
    for a in agents:
        dirs.setdefault(str(expand(AGENT_DIRS[a])), []).append(a)
    return dirs  # {dir: [agents]}


def is_link(p):
    p = Path(p)
    if p.is_symlink():
        return True
    isj = getattr(os.path, "isjunction", None)
    if isj and isj(str(p)):
        return True
    if IS_WIN and p.exists():
        try:
            return bool(os.lstat(str(p)).st_file_attributes & 0x400)  # REPARSE_POINT
        except (AttributeError, OSError):
            return False
    return False


def make_link(src, dest):
    if IS_WIN:
        p = subprocess.run(["cmd", "/c", "mklink", "/J", str(dest), str(src)],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        return p.returncode == 0
    try:
        os.symlink(str(src), str(dest), target_is_directory=True)
        return True
    except OSError:
        return False


def remove_path(p, mode, name):
    p = Path(p)
    if not os.path.lexists(str(p)):
        return
    if is_link(p):
        try:
            os.unlink(str(p))
        except OSError:
            os.rmdir(str(p))  # Windows junction
        return
    fm, _ = parse_frontmatter((p / "SKILL.md").read_text(encoding="utf-8")) if (p / "SKILL.md").exists() else ({}, "")
    if mode == "copy" and fm.get("name") == name:
        shutil.rmtree(str(p))
    else:
        info("  ! skipped %s: not a myasi link/copy of %s" % (p, name))


def install_one(name, entry, src_dir, dirs, mode, st, force=False, label="", spec=""):
    rec = st["installs"].get(name, {"targets": []})
    managed = {t["path"]: t for t in rec["targets"]}
    for d, agents in dirs.items():
        dest = Path(d) / name
        Path(d).mkdir(parents=True, exist_ok=True)
        if os.path.lexists(str(dest)):
            if str(dest) in managed:
                remove_path(dest, managed[str(dest)]["mode"], name)
            elif force:
                info("  ! --force: replacing unmanaged %s" % dest)
                if is_link(dest):
                    remove_path(dest, "link", name)
                else:
                    shutil.rmtree(str(dest))
            else:
                die("%s exists and was not installed by myasi; remove it or pass --force" % dest)
        used = mode
        if mode == "link" and not make_link(src_dir, dest):
            info("  ! link failed, falling back to copy: %s" % dest)
            used = "copy"
        if used == "copy":
            shutil.copytree(str(src_dir), str(dest), ignore=IGNORE)
        prev = set(managed.get(str(dest), {}).get("agents", []))  # shared dir: keep earlier agents
        managed[str(dest)] = {"path": str(dest), "mode": used, "agents": sorted(prev | set(agents))}
        info("  + %-18s -> %s [%s] (%s)" % (name, dest, used, ",".join(agents)))
    rec.update({"targets": sorted(managed.values(), key=lambda t: t["path"]), "version": entry.get("version", ""),
                "kind": entry["kind"], "source": label, "path": entry["path"], "src_dir": str(src_dir),
                "source_spec": spec or rec.get("source_spec", ""),
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
    if entry["kind"] == "external":
        rec["repo"], rec["ref"] = entry["repo"], entry.get("ref")
    st["installs"][name] = rec


def ctx(args):
    src = make_source(getattr(args, "source", None), getattr(args, "ref", None))
    return src, Registry(src.registry())


def source_of(rec_or_entry, src):
    if rec_or_entry.get("kind") == "external":
        return source_for_external(rec_or_entry)
    return src


# ---------------------------------------------------------------- commands
def expand_names(args, reg):
    names = list(args.names or [])
    if getattr(args, "profile", None):
        for p in args.profile.split(","):
            names += reg.profile(p.strip())
    if getattr(args, "all", False):
        names += sorted(reg.skills)
    seen, out = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def resolve_all(reg, names):
    """Resolve every name before touching disk, so a typo never leaves a half-done install."""
    out = []
    for raw in names:
        name, entry = reg.resolve(raw)
        if raw.strip().lower() != name:
            info("  = %s is an alias of %s" % (raw, name))
        out.append((name, entry))
    return out


def cmd_get(args):
    src, reg = ctx(args)
    names = expand_names(args, reg)
    if not names:
        die("give a skill name, --profile or --all")
    dirs = agent_targets(args.agent)
    mode = "copy" if args.copy else "link"
    todo = resolve_all(reg, names)
    st = load_state()
    try:
        for name, entry in todo:
            s = source_of(entry, src)
            if entry["kind"] == "external" and not args.yes:
                info("  ? %s is third-party (%s/%s, license %s). Re-run with --yes to install, or: %s"
                     % (name, entry["repo"], entry["path"], entry.get("license") or "unknown", entry.get("install", "")))
                continue
            src_dir = s.fetch(entry["path"])
            install_one(name, entry, src_dir, dirs, mode, st, force=args.force, label=s.label, spec=s.spec)
    finally:
        save_state(st)  # also on die(): whatever was installed stays managed


def cached_registry(src):
    """Registry without network: local tree or an existing cache; None if neither."""
    if isinstance(src, GitSource) and not (src.cache / "registry.json").exists():
        return None
    if isinstance(src, TarSource):
        return None
    try:
        return Registry(src.registry())
    except SystemExit:
        return None


def cmd_remove(args):
    st = load_state()
    try:
        src = make_source(getattr(args, "source", None), getattr(args, "ref", None))
    except SystemExit:
        src = None
    reg = cached_registry(src) if src else None
    dirs = set(agent_targets(args.agent)) if args.agent else None
    try:
        for raw in args.names:
            name = (reg.resolve(raw, quiet=True)[0] if reg else None) or raw.strip().lower()
            rec = st["installs"].get(name)
            if not rec:
                info("  - %s: not installed by myasi (nothing to do)" % name)
                continue
            keep = []
            for t in rec["targets"]:
                if dirs is None or str(Path(t["path"]).parent) in dirs:
                    remove_path(t["path"], t["mode"], name)
                    info("  - %-18s x %s" % (name, t["path"]))
                else:
                    keep.append(t)
            if keep:
                rec["targets"] = keep
                continue
            del st["installs"][name]
            s = install_source(rec)
            if s is not None:
                s.drop(rec["path"])  # shrink the sparse checkout / tarball cache (never touches a local tree)
        if isinstance(src, GitSource) and not any(r.get("source_spec") == src.spec for r in st["installs"].values()):
            shutil.rmtree(str(src.cache), ignore_errors=True)  # registry-only clone is no longer needed
    finally:
        save_state(st)


def install_source(rec):
    """The source an install came from (recorded in state.json), without network access."""
    if rec.get("kind") == "external":
        return source_for_external(rec)
    spec = rec.get("source_spec")
    if not spec:
        return None
    try:
        return make_source(spec, rec.get("source_ref"))
    except SystemExit:
        return None


def cmd_update(args):
    explicit = getattr(args, "source", None) or os.environ.get("MYASI_SOURCE")
    st = load_state()
    names = args.names or sorted(st["installs"])
    groups = {}  # source spec -> [names]; each install updates from where it came from
    for raw in names:
        n = raw.strip().lower()
        rec = st["installs"].get(n)
        spec = "" if (explicit or not rec or rec.get("kind") == "external") else rec.get("source_spec", "")
        if spec and os.path.isabs(spec) and not os.path.exists(spec):
            info("  ! %s was installed from %s, which no longer exists; using the default source" % (n, spec))
            spec = ""
        groups.setdefault(spec, []).append(raw)
    try:
        for spec, group in sorted(groups.items()):
            src = make_source(spec or getattr(args, "source", None), getattr(args, "ref", None))
            updated = {src.label: src.update()}  # refresh first so the registry is current
            reg = Registry(src.registry())
            for raw in group:
                name, entry = reg.resolve(raw, quiet=True)
                rec = st["installs"].get(name or raw.strip().lower())
                if not rec:
                    info("  - %s: not installed; use `myasi get %s`" % (raw, raw))
                    continue
                if not entry:
                    info("  ! %s is no longer in the registry; `myasi remove %s` to clean up" % (raw, raw))
                    continue
                s = source_of(entry, src)
                if s.label not in updated:
                    updated[s.label] = s.update()
                src_dir = s.fetch(entry["path"])
                old = rec.get("version", "")
                for mode in sorted({t["mode"] for t in rec["targets"]}):
                    sub = {str(Path(t["path"]).parent): t["agents"] for t in rec["targets"] if t["mode"] == mode}
                    install_one(name, entry, src_dir, sub, mode, st, label=s.label, spec=s.spec)
                if old != entry.get("version", ""):
                    info("  ^ %s %s -> %s" % (name, old or "?", entry.get("version", "?")))
                else:
                    info("  = %s %s up to date" % (name, old or ""))
    finally:
        save_state(st)


def installed_marks(st, name):
    rec = st["installs"].get(name)
    return ",".join(sorted({a for t in rec["targets"] for a in t["agents"]})) if rec else ""


def cmd_list(args):
    src, reg = ctx(args)
    st = load_state()
    rows = []
    pick = set(reg.profile(args.profile)) if args.profile else None
    for n in reg.names():
        e = reg.skills.get(n) or reg.external.get(n)
        kind = "own" if n in reg.skills else "ext"
        if args.tag and args.tag not in e.get("tags", []):
            continue
        if pick is not None and n not in pick:
            continue
        if args.installed and not st["installs"].get(n):
            continue
        rows.append((n, kind, e.get("version", "-") or "-", installed_marks(st, n) or "-",
                     (e.get("description") or "").replace("\n", " ")))
    if args.json:
        print(json.dumps([dict(zip(("name", "kind", "version", "installed", "description"), r)) for r in rows],
                         ensure_ascii=False, indent=2))
        return
    info("source: %s" % src.label)
    w = max([len(r[0]) for r in rows] + [4])
    for n, kind, v, inst, desc in rows:
        info("%-*s  %-3s  %-7s  %-14s  %s" % (w, n, kind, v, inst, desc[:56] + ("…" if len(desc) > 56 else "")))
    info("%d skill(s)" % len(rows))


def cmd_search(args):
    _, reg = ctx(args)
    terms = [t.lower() for t in args.query if t.strip()]
    q = " ".join(terms)
    scored = []
    for n in reg.names():
        e = reg.skills.get(n) or reg.external.get(n)
        al = [a for a, t in reg.aliases.items() if t == n]
        desc = (e.get("description") or "").lower()
        tags = [t.lower() for t in e.get("tags", [])]
        s = 100 if q == n or q in al else 0
        for t in terms:
            s += 50 if t in n else 0
            s += 40 if any(t in a for a in al) else 0
            s += 30 if any(t in x for x in tags) else 0
            s += 10 if t in desc else 0
        s += int(20 * difflib.SequenceMatcher(None, q, n).ratio())
        if s > 12:
            scored.append((s, n, e))
    scored.sort(key=lambda x: (-x[0], x[1]))
    for _s, n, e in scored[: args.limit]:
        info("%-24s %s" % (n, (e.get("description") or "").replace("\n", " ")[:80]))
    if not scored:
        info("no match for %r" % q)


def cmd_info(args):
    _, reg = ctx(args)
    name, entry = reg.resolve(args.name)
    st = load_state()
    out = dict(entry)
    out["name"] = name
    out["aliases"] = sorted(a for a, t in reg.aliases.items() if t == name)
    out["installed"] = st["installs"].get(name, {}).get("targets", [])
    print(json.dumps(out, ensure_ascii=False, indent=2))


def cmd_sync(args):
    src, reg = ctx(args)
    clients = reg.d.get("clients", {})
    only = None
    if args.agent or os.environ.get("MYASI_AGENT"):
        only = {a for ds in agent_targets(args.agent).values() for a in ds}  # validates names
    want = {}  # dir -> {name: {agents}}
    for client, conf in sorted(clients.items()):
        if only is not None and client not in only:
            continue
        if client not in AGENT_DIRS:
            die("profiles/clients.yaml: unknown client %r" % client)
        d = str(expand(AGENT_DIRS[client]))
        want.setdefault(d, {})
        for prof in conf.get("profiles", []) or []:
            for n in reg.profile(prof):
                want[d].setdefault(n, set()).add(client)
        for n in conf.get("extra", []) or []:
            want[d].setdefault(n, set()).add(client)
    plan = {d: [(reg.resolve(raw)[0], reg.resolve(raw)[1], ags) for raw, ags in sorted(names.items())]
            for d, names in want.items()}  # resolve everything first
    st = load_state()
    mode = "copy" if args.copy else "link"
    try:
        for d, items in sorted(plan.items()):
            info("[%s]" % d)
            wanted = set()
            for name, entry, agents in items:
                wanted.add(name)  # a skipped third-party skill is still wanted: --prune keeps it
                if entry["kind"] == "external" and not args.yes:
                    info("  ? %s (third-party) skipped; pass --yes to include" % name)
                    continue
                s = source_of(entry, src)
                install_one(name, entry, s.fetch(entry["path"]), {d: sorted(agents)}, mode, st,
                            label=s.label, spec=s.spec)
            if args.prune:
                for name, rec in list(st["installs"].items()):
                    for t in list(rec["targets"]):
                        if str(Path(t["path"]).parent) == d and name not in wanted:
                            remove_path(t["path"], t["mode"], name)
                            rec["targets"].remove(t)
                            info("  - pruned %s" % t["path"])
                    if not rec["targets"]:
                        del st["installs"][name]
                        s = install_source(rec)
                        if s is not None:
                            s.drop(rec["path"])
    finally:
        save_state(st)
    info("sync done. MCP is separate: `myasi mcp apply --agent <agent>` (dry-run by default)")


# ---------------------------------------------------------------- MCP
ENV_REF = re.compile(r"^\$\{([A-Za-z_][A-Za-z0-9_]*)\}$")
MCP_AGENTS = ("codex", "claude", "deepseek", "cursor", "gemini", "dsh", "pi")
MARK_BEGIN = "# >>> managed-by: myasi (do not edit inside; edit mcp/servers.yaml)"
MARK_END = "# <<< managed-by: myasi"


def load_servers(src, path=None):
    if path:
        f = Path(path)
    elif isinstance(src, LocalSource):
        f = src.root / "mcp" / "servers.yaml"
    elif isinstance(src, GitSource):
        src.ensure()
        src.fetch("mcp")
        f = src.cache / "mcp" / "servers.yaml"
    else:
        data = http_get("https://raw.githubusercontent.com/%s/%s/mcp/servers.yaml" % (src.repo, src.ref))
        return parse_yaml(data.decode("utf-8")).get("servers", {})
    return load_yaml(f).get("servers", {})


def pick_servers(servers, agent, include_unverified):
    out, skipped = {}, []
    for name, s in sorted(servers.items()):
        clients = s.get("clients", ["*"])
        if "*" not in clients and agent not in clients:
            continue
        if s.get("verified") is False and not include_unverified:
            skipped.append(name)
            continue
        out[name] = s
    return out, skipped


def to_json_entry(s, agent):
    def conv(v):
        if agent == "cursor":
            return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", r"${env:\1}", v)
        return v
    if s.get("transport", "stdio") == "http":
        e = {"httpUrl": s["url"]} if agent == "gemini" else {"type": "http", "url": s["url"]}
        if s.get("headers"):
            e["headers"] = {k: conv(v) for k, v in s["headers"].items()}
        return e
    e = {"command": s["command"], "args": list(s.get("args", []))}
    if agent == "claude":
        e = dict({"type": "stdio"}, **e)
    if s.get("env"):
        e["env"] = {k: conv(str(v)) for k, v in s["env"].items()}
    return e


def toml_str(v):
    return json.dumps(v, ensure_ascii=False)


def to_codex_toml(servers):
    lines = [MARK_BEGIN]
    for name, s in servers.items():
        lines.append("[mcp_servers.%s]" % (name if re.fullmatch(r"[A-Za-z0-9_-]+", name) else toml_str(name)))
        if s.get("transport", "stdio") == "http":
            lines.append("url = %s" % toml_str(s["url"]))
            for hk, hv in (s.get("headers") or {}).items():
                m = re.fullmatch(r"Bearer \$\{([A-Za-z_][A-Za-z0-9_]*)\}", str(hv))
                if hk.lower() == "authorization" and m:
                    lines.append("bearer_token_env_var = %s" % toml_str(m.group(1)))
                elif ENV_REF.match(str(hv)):
                    lines.append("env_http_headers = { %s = %s }" % (toml_str(hk), toml_str(ENV_REF.match(hv).group(1))))
                else:
                    lines.append("http_headers = { %s = %s }" % (toml_str(hk), toml_str(hv)))
        else:
            lines.append("command = %s" % toml_str(s["command"]))
            lines.append("args = [%s]" % ", ".join(toml_str(str(a)) for a in s.get("args", [])))
            fwd, lit = [], {}
            for k, v in (s.get("env") or {}).items():
                m = ENV_REF.match(str(v))
                if m and m.group(1) == k:
                    fwd.append(k)
                elif m:
                    info("# ! %s: env %s=%s renames a variable; Codex can only forward same-name vars" % (name, k, v),)
                    fwd.append(m.group(1))
                elif "${" in str(v):
                    info("# ! %s: env %s mixes text and ${VAR}; not expressible in Codex, skipped" % (name, k))
                else:
                    lit[k] = str(v)
            if fwd:
                lines.append("env_vars = [%s]" % ", ".join(toml_str(x) for x in fwd))
            if lit:
                lines.append("env = { %s }" % ", ".join("%s = %s" % (toml_str(k), toml_str(v)) for k, v in lit.items()))
        if s.get("startup_timeout_sec"):
            lines.append("startup_timeout_sec = %s" % int(s["startup_timeout_sec"]))
        lines.append("")
    lines.append(MARK_END)
    return "\n".join(lines) + "\n"


def merge_codex(path, block, names):
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    pat = re.compile(re.escape(MARK_BEGIN) + r".*?" + re.escape(MARK_END) + r"\n?", re.S)
    outside = pat.sub("", text)
    clash = [n for n in names if re.search(r"^\[mcp_servers\.\"?%s\"?\]" % re.escape(n), outside, re.M)]
    if clash:
        die("%s already defines unmanaged [mcp_servers.%s]; remove those tables first (myasi never edits them)"
            % (path, ", ".join(clash)))
    new = (outside.rstrip("\n") + "\n\n" if outside.strip() else "") + block
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(new, encoding="utf-8")


def merge_json(path, servers_json, managed_key="mcpServers"):
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() and path.read_text(encoding="utf-8").strip() else {}
    data.setdefault(managed_key, {}).update(servers_json)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cmd_mcp(args):
    src = make_source(args.source, args.ref)
    servers = load_servers(src, args.file)
    agents = list(MCP_AGENTS[:5]) if args.agent == "all" else [a.strip().lower() for a in args.agent.split(",")]
    for agent in agents:
        if agent not in MCP_AGENTS:
            die("unknown agent %r for mcp (%s)" % (agent, "|".join(MCP_AGENTS)))
        sel, skipped = pick_servers(servers, agent, args.include_unverified)
        if args.only:
            sel = {k: v for k, v in sel.items() if k in args.only.split(",")}
        info("\n## %s — %d server(s)%s" % (agent, len(sel), "; skipped unverified: " + ", ".join(skipped) if skipped else ""))
        if agent == "codex":
            if args.write and args.only:
                die("--only is preview-only for codex; --write always rewrites the whole managed block")
            target = expand("~/.codex/config.toml")
            block = to_codex_toml(sel)
            info("# target: %s (only the managed block is replaced)" % target)
            print(block)
            if args.write:
                merge_codex(target, block, list(sel))
                info("# written %s" % target)
        elif agent == "claude":
            info("# target: Claude user scope via `claude mcp add-json` (${VAR} kept as-is, never expanded here)")
            cmds = [["claude", "mcp", "add-json", n, json.dumps(to_json_entry(s, agent), ensure_ascii=False), "-s", "user"]
                    for n, s in sel.items()]
            for c in cmds:
                print(" ".join(c[:4]) + " '" + c[4] + "' " + " ".join(c[5:]))
            if args.write:
                if not shutil.which("claude"):
                    die("`claude` not in PATH; run the commands above manually")
                for c in cmds:
                    r = subprocess.run(c, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                    info("# %s: %s" % (c[3], "ok" if r.returncode == 0 else r.stderr.strip()[:200]))
        elif agent in ("deepseek", "cursor", "gemini"):
            target = expand({"deepseek": "~/.deepseek/mcp.json", "cursor": "~/.cursor/mcp.json",
                             "gemini": "~/.gemini/settings.json"}[agent])
            js = {n: to_json_entry(s, agent) for n, s in sel.items()}
            info("# target: %s (merged into mcpServers; other keys kept)" % target)
            print(json.dumps({"mcpServers": js}, ensure_ascii=False, indent=2))
            if args.write:
                merge_json(target, js)
                info("# written %s" % target)
        else:
            info("# %s: MCP config format not verified yet (see docs/DESIGN.md). Neutral JSON below; nothing written." % agent)
            print(json.dumps({"mcpServers": {n: to_json_entry(s, agent) for n, s in sel.items()}}, ensure_ascii=False, indent=2))
    if not args.write:
        info("\n(dry-run: nothing written; add --write to apply)")


# ---------------------------------------------------------------- CLI manifests
def cmd_cli(args):
    src = make_source(args.source, args.ref)
    if not isinstance(src, LocalSource):
        if isinstance(src, GitSource):
            src.ensure()
            src.fetch("cli")
            root = src.cache
        else:
            die("`myasi cli` needs git or a local clone")
    else:
        root = src.root
    cmds = []
    target_os = args.os or ("windows" if IS_WIN else "macos" if sys.platform == "darwin" else "linux")
    if target_os == "windows":
        cmds.append(["winget", "import", "-i", str(root / "cli/windows/winget.json"), "--accept-package-agreements",
                     "--accept-source-agreements", "--ignore-unavailable"])
    elif target_os == "macos":
        cmds.append(["brew", "bundle", "--file", str(root / "cli/macos/Brewfile")])
    for rel, cmd in (("cli/npm/global.txt", ["npm", "install", "-g"]), ("cli/uv/tools.txt", ["uv", "tool", "install"])):
        f = root / rel
        for line in (f.read_text(encoding="utf-8").splitlines() if f.exists() else []):
            line = re.sub(r"(^|\s)#.*", "", line).strip()  # comments; keeps scoped names like @a/b
            if line:
                cmds.append(cmd + [line])
    for c in cmds:
        print(" ".join(c))
    if not cmds:
        info("(no CLI entries in cli/ manifests)")
    if args.run:
        for c in cmds:
            if not shutil.which(c[0]):
                info("! %s not found, skipped" % c[0])
                continue
            subprocess.run(c, shell=IS_WIN)
    else:
        info("(dry-run; add --run to execute)")


# ---------------------------------------------------------------- new (scaffold)
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SKILL_TEMPLATE = """---
name: {name}
description: {description}
---
# {name}

## 何时使用
- TODO：写清楚触发场景（description 也要写，agent 只靠它决定是否加载）。

## 步骤
1. TODO
2. TODO

## 注意
- 大文件（> 5MB）不要放进仓库；脚本放 scripts/，参考资料放 references/。
"""
OPENAI_YAML_TEMPLATE = """# Codex 界面元数据（可选）
interface:
  display_name: "{name}"
  short_description: "{short}"
policy:
  allow_implicit_invocation: true
"""


def repo_root_for_edit(args):
    for cand in (getattr(args, "dir", None), getattr(args, "source", None) or os.environ.get("MYASI_SOURCE"), None):
        if cand:
            p = Path(os.path.expanduser(cand))
            if (p / "registry.json").exists() and (p / "skills").is_dir():
                return p.resolve()
            die("%s is not a myasi working tree (needs registry.json and skills/)" % p)
    cwd = Path.cwd()
    for p in [cwd] + list(cwd.parents):
        if (p / "registry.json").exists() and (p / "skills").is_dir():
            return p
    root = script_repo_root()
    if root:
        return root
    die("run inside a clone of the myasi repo, or pass --dir <clone>")


def cmd_new(args):
    name = args.name.strip()
    if not NAME_RE.match(name) or len(name) > 64:
        die("name must be kebab-case (a-z, 0-9, -), <= 64 chars: %r" % name)
    root = repo_root_for_edit(args)
    d = root / "skills" / name
    if d.exists():
        die("%s already exists" % d)
    desc = " ".join((args.description or "TODO：一句话说明什么时候用这个 skill（<= 1024 字符）").split())
    if len(desc) > 1024:
        die("description is %d chars (> 1024)" % len(desc))
    (d / "agents").mkdir(parents=True)
    write_lf(d / "SKILL.md", SKILL_TEMPLATE.format(name=name, description=json.dumps(desc, ensure_ascii=False)))
    meta = {"version": "0.1.0", "tags": [t.strip() for t in (args.tags or "").split(",") if t.strip()],
            "aliases": [a.strip().lower() for a in (args.alias or "").split(",") if a.strip()],
            "clients": ["*"], "license": "MIT"}
    write_lf(d / "skill.json", json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
    short = desc[:60].replace('"', "'")
    write_lf(d / "agents" / "openai.yaml", OPENAI_YAML_TEMPLATE.format(name=name, short=short))
    info("created %s" % d)
    builder = root / "scripts" / "build_registry.py"
    if builder.exists() and not args.no_registry:
        r = subprocess.run([sys.executable, str(builder)], cwd=str(root))
        if r.returncode != 0:
            die("build_registry.py failed")
    info("next: edit %s, then\n  python scripts/build_registry.py && python scripts/validate.py\n"
         "  myasi get %s --source %s   # try it locally" % (d / "SKILL.md", name, root))


# ---------------------------------------------------------------- doctor
def cmd_doctor(args):
    problems = 0

    def ok(flag, msg):
        nonlocal problems
        problems += 0 if flag else 1
        info(("  ok   " if flag else "  WARN ") + msg)

    info("myasi %s  python %s  %s" % (__version__, sys.version.split()[0], sys.platform))
    ok(sys.version_info >= (3, 8), "python >= 3.8")
    ok(has_git(), "git in PATH (else tarball fallback is used)")
    info("  info token: %s" % ("GITHUB_TOKEN/GH_TOKEN set" if token() else "none (fine for public repos)"))
    try:
        src = make_source(args.source, args.ref)
        reg = Registry(src.registry())
        ok(True, "registry: %s (%d own, %d external)" % (src.label, len(reg.skills), len(reg.external)))
    except SystemExit:
        ok(False, "registry not reachable")
    st = load_state()
    for name, rec in sorted(st["installs"].items()):
        for t in rec["targets"]:
            p = Path(t["path"])
            ok(os.path.lexists(str(p)) and (p / "SKILL.md").exists(), "%s -> %s [%s]" % (name, p, t["mode"]))
    seen = {}
    for d in sorted({str(expand(x)) for x in list(AGENT_DIRS.values()) + LEGACY_DIRS}):
        if not os.path.isdir(d):
            continue
        for e in sorted(os.listdir(d)):
            p = Path(d) / e
            if e.startswith("."):
                continue
            if is_link(p) and not p.exists():
                ok(False, "broken link %s" % p)
            seen.setdefault(e, []).append(d)
    shared = str(expand(SHARED))
    for n, ds in sorted(seen.items()):
        dup = [d for d in ds if d != str(expand("~/.claude/skills"))]
        if len(dup) > 1 and shared in dup:
            ok(False, "%s is visible twice to ~/.agents readers: %s" % (n, ", ".join(dup)))
    info("doctor: %s" % ("all good" if not problems else "%d warning(s)" % problems))
    return 1 if problems and args.strict else 0


# ---------------------------------------------------------------- main
def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--source", help="repo (owner/name), git URL, file:// URL, bare repo or local clone; env MYASI_SOURCE")
    common.add_argument("--ref", help="branch/tag (default: repo default branch); env MYASI_REF")
    ap = argparse.ArgumentParser(prog="myasi", description="myasi — 按名管理 skills / MCP / CLI（我的超级人工智能）")
    ap.add_argument("--version", action="version", version="myasi " + __version__)
    sub = ap.add_subparsers(dest="cmd")
    ag = dict(help="codex|claude|pi|dsh|deepseek|all (comma list; default all)")

    p = sub.add_parser("get", parents=[common], help="install skill(s) by bare name")
    p.add_argument("names", nargs="*")
    p.add_argument("--agent", **ag)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--link", action="store_true", help="link to local cache (default)")
    g.add_argument("--copy", action="store_true", help="standalone copy")
    p.add_argument("--profile", help="comma list of profiles, e.g. core,video")
    p.add_argument("--all", action="store_true", help="all own skills (not recommended)")
    p.add_argument("--force", action="store_true", help="replace an existing unmanaged dir")
    p.add_argument("--yes", "-y", action="store_true", help="allow third-party (external) skills")
    p.set_defaults(fn=cmd_get)

    p = sub.add_parser("update", parents=[common], help="update installed skill(s)")
    p.add_argument("names", nargs="*")
    p.set_defaults(fn=cmd_update)

    p = sub.add_parser("remove", parents=[common], help="remove what myasi installed")
    p.add_argument("names", nargs="+")
    p.add_argument("--agent", help="only remove from these agents' dirs")
    p.set_defaults(fn=cmd_remove)

    p = sub.add_parser("list", parents=[common], help="list skills")
    p.add_argument("--tag")
    p.add_argument("--profile")
    p.add_argument("--installed", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_list)

    p = sub.add_parser("search", parents=[common], help="search name/alias/tag/description")
    p.add_argument("query", nargs="+")
    p.add_argument("--limit", type=int, default=5)
    p.set_defaults(fn=cmd_search)

    p = sub.add_parser("info", parents=[common], help="show one skill")
    p.add_argument("name")
    p.set_defaults(fn=cmd_info)

    p = sub.add_parser("sync", parents=[common], help="install per profiles/clients.yaml (idempotent)")
    p.add_argument("--agent", **ag)
    p.add_argument("--copy", action="store_true")
    p.add_argument("--prune", action="store_true", help="remove managed skills no longer wanted")
    p.add_argument("--yes", "-y", action="store_true", help="include third-party skills")
    p.set_defaults(fn=cmd_sync)

    p = sub.add_parser("mcp", parents=[common], help="MCP config from mcp/servers.yaml")
    msub = p.add_subparsers(dest="mcmd")
    pa = msub.add_parser("apply", parents=[common], help="print (default) or --write per-agent MCP config")
    pa.add_argument("--agent", default="all", help="|".join(MCP_AGENTS) + "|all")
    pa.add_argument("--write", action="store_true", help="merge into the agent's config (managed entries only)")
    pa.add_argument("--only", help="comma list of server names")
    pa.add_argument("--include-unverified", action="store_true")
    pa.add_argument("--file", help="servers.yaml path (default: from source)")
    pa.set_defaults(fn=cmd_mcp)

    p = sub.add_parser("cli", parents=[common], help="print/run CLI install commands from cli/ manifests")
    p.add_argument("--run", action="store_true")
    p.add_argument("--os", choices=["windows", "macos", "linux"])
    p.set_defaults(fn=cmd_cli)

    p = sub.add_parser("new", parents=[common], help="scaffold skills/<name>/ in a local clone and rebuild the registry")
    p.add_argument("name")
    p.add_argument("--description", "-d", help="when to use it (frontmatter description)")
    p.add_argument("--tags", help="comma list")
    p.add_argument("--alias", help="comma list of extra names (e.g. an old name)")
    p.add_argument("--dir", help="repo clone to write into (default: the clone containing cwd)")
    p.add_argument("--no-registry", action="store_true", help="do not run scripts/build_registry.py")
    p.set_defaults(fn=cmd_new)

    p = sub.add_parser("doctor", parents=[common], help="check installs, duplicates, broken links")
    p.add_argument("--strict", action="store_true")
    p.set_defaults(fn=cmd_doctor)

    args = ap.parse_args(argv)
    if not getattr(args, "fn", None):
        ap.print_help()
        return 0 if args.cmd is None else 2
    return args.fn(args) or 0


if __name__ == "__main__":
    sys.exit(main())
