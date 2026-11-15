#!/usr/bin/env python3
"""Generate registry.json and .claude-plugin/marketplace.json from skills/, profiles/, catalog/.

Usage: python scripts/build_registry.py [--check]
--check exits 1 if the committed files are out of date (used by validate/CI).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from myasi import AGENT_DIRS, DEFAULT_REF, DEFAULT_REPO, load_yaml, parse_frontmatter, write_lf  # noqa: E402

REPO, OWNER = DEFAULT_REPO, DEFAULT_REPO.split("/")[0]


def read_profiles():
    profiles = {}
    for f in sorted((ROOT / "profiles").glob("*.txt")):
        names = [ln.split("#")[0].strip() for ln in f.read_text(encoding="utf-8").splitlines()]
        profiles[f.stem] = [n for n in names if n]
    return profiles


def dir_size_kb(d):
    total = sum(p.stat().st_size for p in d.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    return round(total / 1024)


def build():
    profiles = read_profiles()
    in_profiles = {}
    for prof, names in profiles.items():
        for n in names:
            in_profiles.setdefault(n, []).append(prof)
    skills, aliases = {}, {}
    for d in sorted(p for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file()):
        fm, _ = parse_frontmatter((d / "SKILL.md").read_text(encoding="utf-8"))
        meta = dict(fm.get("metadata") or {})
        if (d / "skill.json").exists():
            meta.update(json.loads((d / "skill.json").read_text(encoding="utf-8")))
        name = str(fm.get("name") or d.name)
        for a in meta.get("aliases", []):
            aliases[str(a).lower()] = name
        skills[name] = {
            "description": " ".join(str(fm.get("description") or "").split()),
            "tags": meta.get("tags", []),
            "version": str(meta.get("version", "0.0.0")),
            "path": "skills/" + d.name,
            "clients": meta.get("clients", ["*"]),
            "profiles": sorted(in_profiles.get(name, [])),
            "license": meta.get("license", fm.get("license", "")),
            "size_kb": dir_size_kb(d),
        }
    external = {}
    cat = ROOT / "catalog" / "external.yaml"
    for e in (load_yaml(cat).get("sources") or []) if cat.exists() else []:
        external[e["name"]] = {
            "description": e.get("description", ""), "repo": e["repo"], "path": e["path"],
            "ref": e.get("ref"), "license": str(e.get("license") or "unknown"), "install": e.get("install", ""),
            "tags": e.get("tags", []), "profiles": sorted(in_profiles.get(e["name"], [])),
        }
    clients = (load_yaml(ROOT / "profiles" / "clients.yaml").get("clients") or {})
    registry = {
        "version": 1, "name": "myasi", "repo": REPO, "ref": DEFAULT_REF,
        "agents": AGENT_DIRS, "skills": skills, "aliases": dict(sorted(aliases.items())),
        "external": external, "profiles": profiles, "clients": clients,
    }
    market = {
        "name": "myasi",
        "owner": {"name": OWNER},
        "metadata": {"description": "myasi（我的超级人工智能）：按名安装的个人 skills 工具集", "version": "0.1.0"},
        "plugins": [
            {"name": n, "description": s["description"][:300], "version": s["version"], "source": "./",
             "strict": False, "skills": ["./" + s["path"]]}
            for n, s in skills.items()
        ],
    }
    return registry, market


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def main():
    registry, market = build()
    targets = {ROOT / "registry.json": dump(registry), ROOT / ".claude-plugin" / "marketplace.json": dump(market)}
    if "--check" in sys.argv:
        stale = [str(p.relative_to(ROOT)) for p, t in targets.items()
                 if not p.exists() or p.read_text(encoding="utf-8") != t]
        if stale:
            print("out of date: %s (run python scripts/build_registry.py)" % ", ".join(stale))
            return 1
        print("registry up to date (%d skills, %d external)" % (len(registry["skills"]), len(registry["external"])))
        return 0
    for p, t in targets.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        write_lf(p, t)
    print("wrote registry.json (%d skills, %d external, %d aliases) and .claude-plugin/marketplace.json"
          % (len(registry["skills"]), len(registry["external"]), len(registry["aliases"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
