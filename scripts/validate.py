#!/usr/bin/env python3
"""Repository checks: skills frontmatter, unique names/aliases, registry freshness,
size limits, forbidden files, MCP placeholders, and a secrets regex scan.
Usage: python scripts/validate.py      (exit 1 on any error)
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from myasi import ENV_REF, load_yaml, parse_frontmatter  # noqa: E402
import build_registry  # noqa: E402

KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_SKILL_BYTES = 5 * 1024 * 1024
FORBIDDEN = re.compile(r"(^|/)(node_modules|dist|__pycache__|\.venv)(/|$)|\.(zip|pyc|7z|rar)$|(^|/)\.env$")
SECRETS = [
    ("GitHub token", re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{60,}")),
    ("OpenAI-style key", re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{24,}")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("Private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Assigned secret", re.compile(
        r"(?i)\b[\w-]*(?:api[_-]?key|secret|token|passwd|password)\b[\"']?\s*[:=]\s*[\"']"
        r"(?!\$\{)(?!<)(?!TODO)[A-Za-z0-9_\-+/=.]{16,}[\"']")),
]
errors = []


def err(msg):
    errors.append(msg)


def repo_files():
    try:
        out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=str(ROOT),
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True).stdout
        files = [f for f in out.decode("utf-8").split("\0") if f]
        return [f for f in files if (ROOT / f).is_file()]
    except (OSError, subprocess.CalledProcessError):
        return [str(p.relative_to(ROOT)).replace("\\", "/") for p in ROOT.rglob("*")
                if p.is_file() and ".git" not in p.parts]


def check_skills():
    names = {}
    for d in sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir()):
        f = d / "SKILL.md"
        if not f.is_file():
            err("skills/%s: missing SKILL.md" % d.name)
            continue
        try:
            fm, body = parse_frontmatter(f.read_text(encoding="utf-8"))
        except ValueError as e:
            err("skills/%s: bad frontmatter: %s" % (d.name, e))
            continue
        name, desc = fm.get("name"), str(fm.get("description") or "").strip()
        if name != d.name:
            err("skills/%s: frontmatter name %r must equal folder name" % (d.name, name))
        if not KEBAB.match(d.name) or len(d.name) > 64:
            err("skills/%s: name must be kebab-case, <= 64 chars" % d.name)
        if not desc:
            err("skills/%s: description is required" % d.name)
        elif len(desc) > 1024:
            err("skills/%s: description is %d chars (> 1024)" % (d.name, len(desc)))
        if not body.strip():
            err("skills/%s: SKILL.md body is empty" % d.name)
        size = sum(p.stat().st_size for p in d.rglob("*") if p.is_file())
        if size > MAX_SKILL_BYTES:
            err("skills/%s: %.1f MB > 5 MB; move large assets out of git" % (d.name, size / 1048576))
        if (d / "skill.json").exists():
            try:
                json.loads((d / "skill.json").read_text(encoding="utf-8"))
            except ValueError as e:
                err("skills/%s/skill.json: %s" % (d.name, e))
        names[d.name] = True
    return names


def check_registry(names):
    reg, _ = build_registry.build()
    ext = reg["external"]
    for n in ext:
        if n in names:
            err("external %r collides with an own skill" % n)
        if not KEBAB.match(n):
            err("external %r: not kebab-case" % n)
        for k in ("repo", "path"):
            if not ext[n].get(k):
                err("external %r: missing %s" % (n, k))
    cat = load_yaml(ROOT / "catalog" / "external.yaml").get("sources") or []
    if len(cat) != len(ext):
        err("catalog/external.yaml has duplicate names")
    for a in reg["aliases"]:
        if a in names or a in ext:
            err("alias %r collides with a skill name" % a)
    alias_owner = {}
    for d in (ROOT / "skills").iterdir():
        sj = d / "skill.json"
        for a in (json.loads(sj.read_text(encoding="utf-8")).get("aliases", []) if sj.exists() else []):
            if a in alias_owner:
                err("alias %r used by both %s and %s" % (a, alias_owner[a], d.name))
            alias_owner[a] = d.name
    known = set(names) | set(ext)
    for prof, members in reg["profiles"].items():
        for m in members:
            if m not in known:
                err("profiles/%s.txt: unknown name %r" % (prof, m))
    for client, conf in reg["clients"].items():
        if client not in reg["agents"]:
            err("profiles/clients.yaml: unknown client %r" % client)
        for p in conf.get("profiles", []):
            if p not in reg["profiles"]:
                err("profiles/clients.yaml: %s uses unknown profile %r" % (client, p))
    if build_registry_check():
        err("registry.json / marketplace.json out of date: run python scripts/build_registry.py")


def build_registry_check():
    argv, sys.argv = sys.argv, ["build_registry.py", "--check"]
    try:
        return build_registry.main()
    finally:
        sys.argv = argv


def check_mcp():
    servers = load_yaml(ROOT / "mcp" / "servers.yaml").get("servers") or {}
    for n, s in servers.items():
        t = s.get("transport", "stdio")
        if t not in ("stdio", "http"):
            err("mcp %s: transport must be stdio|http" % n)
        if t == "stdio" and not s.get("command"):
            err("mcp %s: command required" % n)
        if t == "http" and not s.get("url"):
            err("mcp %s: url required" % n)
        if s.get("command") == "TODO" and s.get("verified") is not False:
            err("mcp %s: TODO command must be marked verified: false" % n)
        for group in ("env", "headers"):
            for k, v in (s.get(group) or {}).items():
                if re.search(r"(?i)key|token|secret|pass|auth", k) and "${" not in str(v):
                    err("mcp %s: %s.%s must be a ${ENV} reference, not a literal" % (n, group, k))
                if group == "env" and "${" in str(v) and not ENV_REF.match(str(v)):
                    err("mcp %s: env.%s should be exactly ${VAR}" % (n, k))


def check_files():
    for f in repo_files():
        if FORBIDDEN.search(f) and not f.endswith(".env.example"):
            err("forbidden file in repo: %s" % f)
        p = ROOT / f
        if p.stat().st_size > 2 * 1024 * 1024:
            err("large file (> 2 MB): %s" % f)
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if f == "scripts/validate.py":
            continue
        for label, rx in SECRETS:
            m = rx.search(text)
            if m:
                line = text.count("\n", 0, m.start()) + 1
                err("possible secret (%s) in %s:%d" % (label, f, line))


def main():
    names = check_skills()
    check_registry(names)
    check_mcp()
    check_files()
    if errors:
        print("\n".join("ERROR " + e for e in errors))
        print("validate: %d error(s)" % len(errors))
        return 1
    print("validate: ok (%d skills)" % len(names))
    return 0


if __name__ == "__main__":
    sys.exit(main())
