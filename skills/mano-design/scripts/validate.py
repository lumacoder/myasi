#!/usr/bin/env python3
"""校验整个 skill：frontmatter、rules.json、lint 实现一致性、fixtures/manifest、案例库 schema、vocab、隐私扫描，最后跑一次 eval。

  python3 scripts/validate.py            # 失败退出 1
  python3 scripts/validate.py --no-eval  # 只做结构校验
"""
import argparse
import hashlib
import json
import re
import sys

sys.dont_write_bytecode = True  # 不在 skill 目录留下 __pycache__

from _common import ROOT, utf8_stdio

PRIVATE = [("Windows 用户路径", re.compile(r"[A-Za-z]:\\\\?Users\\\\?[A-Za-z]", re.I)),
           ("家目录路径", re.compile(r"/home/(?!box\b)[a-z_][\w-]+/|/Users/[A-Za-z][\w-]+/")),
           ("GitHub token", re.compile(r"\b(ghp|gho|ghs|ghu)_[A-Za-z0-9]{30,}|github_pat_\w{40,}")),
           ("API key", re.compile(r"\bsk-[A-Za-z0-9_-]{24,}|\bAKIA[0-9A-Z]{16}\b|\bAIza[0-9A-Za-z_-]{35}\b")),
           ("私钥", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"))]
SEVERITIES = {"critical", "major", "minor"}
CATS = {"component", "state", "a11y", "color", "copy", "layout", "type"}


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    fm, key = {}, None
    for line in m.group(1).splitlines():
        if re.match(r"^\w[\w-]*:", line):
            key, _, v = line.partition(":")
            fm[key.strip()] = v.strip().lstrip(">-").strip()
        elif key:
            fm[key] += line.strip()
    return fm


def main(argv=None):
    utf8_stdio()
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-eval", action="store_true")
    a = ap.parse_args(argv)
    errs, info = [], []
    # 1 SKILL.md
    fm = frontmatter((ROOT / "SKILL.md").read_text(encoding="utf-8"))
    if not fm or fm.get("name") != "mano-design":
        errs.append("SKILL.md frontmatter name 必须为 mano-design")
    elif not (0 < len(fm.get("description", "")) <= 1024):
        errs.append("SKILL.md description 需 1—1024 字符")
    # 2 rules.json
    data = json.loads((ROOT / "rules" / "rules.json").read_text(encoding="utf-8"))
    rules = {}
    for r in data["rules"]:
        for k in ("id", "category", "severity", "detect", "title_zh", "signal", "correct", "anti_patterns", "rationale", "fix_zh", "sources"):
            if k not in r:
                errs.append(f"rule {r.get('id')} 缺字段 {k}")
        if r["id"] in rules:
            errs.append(f"rule id 重复：{r['id']}")
        if r["severity"] not in SEVERITIES or r["category"] not in CATS or r["detect"] not in ("lint", "rubric", "browser"):
            errs.append(f"rule {r['id']} 枚举值非法")
        if not r["sources"]:
            errs.append(f"rule {r['id']} 缺来源")
        rules[r["id"]] = r
    impl = set(re.findall(r'self\.add\("([a-z0-9.\-]+)"', (ROOT / "scripts" / "ui_lint.py").read_text(encoding="utf-8")))
    declared = {k for k, v in rules.items() if v["detect"] == "lint"}
    for x in sorted(impl - declared):
        errs.append(f"ui_lint 实现了未声明为 lint 的规则：{x}")
    for x in sorted(declared - impl):
        errs.append(f"rules.json 声明 lint 但 ui_lint 未实现：{x}")
    # 3 manifest + fixtures
    man = json.loads((ROOT / "tests" / "manifest.json").read_text(encoding="utf-8"))
    ids, hashes, covered = set(), {}, set()
    for c in man:
        p = ROOT / "tests" / "fixtures" / c["file"]
        if c["id"] in ids:
            errs.append(f"fixture id 重复：{c['id']}")
        ids.add(c["id"])
        if not p.is_file():
            errs.append(f"fixture 文件不存在：{c['file']}")
            continue
        h = hashlib.sha1(p.read_bytes()).hexdigest()
        if h in hashes:
            errs.append(f"fixture 内容重复：{c['id']} = {hashes[h]}")
        hashes[h] = c["id"]
        if c["category"] not in CATS or c["verdict"] not in ("PASS", "FAIL") or c.get("split", "train") not in ("train", "holdout"):
            errs.append(f"fixture {c['id']} 枚举值非法")
        for r in c["rules"]:
            if r not in rules:
                errs.append(f"fixture {c['id']} 引用未知规则 {r}")
            elif rules[r]["detect"] != "lint":
                errs.append(f"fixture {c['id']} 引用非 lint 规则 {r}（rubric 用例放 rsi/rubric_cases.json）")
        blocking = any(rules.get(r, {}).get("severity") in ("critical", "major") for r in c["rules"])
        if c["verdict"] == "PASS" and blocking:
            errs.append(f"fixture {c['id']} 期望 PASS 但含阻断级规则")
        if c["verdict"] == "FAIL" and not blocking and "cp.ai-cliche" not in c["rules"]:
            errs.append(f"fixture {c['id']} 期望 FAIL 但没有阻断级规则")
        covered |= set(c["rules"])
    for d in ("bad", "good"):
        for f in (ROOT / "tests" / "fixtures" / d).iterdir():
            if f"{d}/{f.name}" not in {c["file"] for c in man}:
                errs.append(f"孤立 fixture（不在 manifest）：{d}/{f.name}")
    # 4 catalog
    cases = json.loads((ROOT / "cases" / "cases.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "cases" / "cases.schema.json").read_text(encoding="utf-8"))
    req = schema["items"]["required"]
    seen = set()
    for c in cases:
        miss = [k for k in req if k not in c]
        if miss:
            errs.append(f"case {c.get('id')} 缺字段 {miss}")
        key = c["repo_url"].lower()
        if key in seen or c["id"] in seen:
            errs.append(f"case 重复：{c['id']}")
        seen |= {key, c["id"]}
    try:
        import jsonschema
        for e in jsonschema.Draft202012Validator(schema).iter_errors(cases):
            errs.append(f"cases schema: {'/'.join(map(str, e.absolute_path))}: {e.message}")
        info.append("cases：完整 jsonschema 校验")
    except ImportError:
        info.append("cases：未装 jsonschema，仅做必填/去重校验")
    # 5 vocab
    vocab = json.loads((ROOT / "rules" / "vocab.json").read_text(encoding="utf-8"))
    for v in vocab:
        for k in ("term", "concrete_spec", "acceptance", "rule_ids"):
            if k not in v:
                errs.append(f"vocab {v.get('term')} 缺 {k}")
        for r in v.get("rule_ids", []):
            if r not in rules:
                errs.append(f"vocab {v['term']} 引用未知规则 {r}")
    # 5b visual layer：原型/基准/签名/主题互相引用完整 + 三个自测
    V = ROOT / "visual"
    try:
        arch = json.loads((V / "archetypes.json").read_text(encoding="utf-8"))["archetypes"]
        bench = json.loads((V / "benchmarks.json").read_text(encoding="utf-8"))["benchmarks"]
        pats = json.loads((V / "creative-patterns.json").read_text(encoding="utf-8"))["patterns"]
        bids, pids = {b["id"] for b in bench}, {x["id"] for x in pats}
        for b in bench:
            for k in ("id", "license", "demo_url", "archetypes", "use", "what", "borrow", "verified"):
                if k not in b:
                    errs.append(f"benchmark {b.get('id')} 缺 {k}")
        for a_ in arch:
            for k in ("id", "mode", "signals", "sections", "signature_patterns", "seed_benchmarks", "discovery_queries", "theme_hint"):
                if k not in a_:
                    errs.append(f"archetype {a_.get('id')} 缺 {k}")
            if a_.get("mode") not in ("Persuade", "Operate", "Read", "Experience"):
                errs.append(f"archetype {a_['id']} mode 非法")
            errs += [f"archetype {a_['id']} 引用未知基准 {x}" for x in a_.get("seed_benchmarks", []) if x not in bids]
            errs += [f"archetype {a_['id']} 引用未知签名 {x}" for x in a_.get("signature_patterns", []) if x not in pids]
        for x in pats:
            errs += [f"pattern {x['id']} 引用未知来源 {s}" for s in x.get("sources", []) if s not in bids]
        sys.path.insert(0, str(ROOT / "scripts"))
        import io
        import contextlib
        import archetype as _arch
        import theme as _theme
        import visual_score as _vs
        with contextlib.redirect_stdout(io.StringIO()):
            r1, r2 = _arch.self_test(), _vs.self_test()
        terrs = _theme.check(_theme.load())
        if r1:
            errs.append("原型识别自测失败（python3 scripts/archetype.py --self-test）")
        if r2:
            errs.append("视觉评分门禁自测失败（python3 scripts/visual_score.py --self-test）")
        errs += [f"主题对比度：{e}" for e in terrs]
        info.append(f"视觉层：原型 {len(arch)} 类、基准 {len(bench)} 条、签名模式 {len(pats)} 个、主题 {len(_theme.load())} 套；原型识别/评分门禁自测与主题 AA 检查{'通过' if not (r1 or r2 or terrs) else '有失败'}")
    except (OSError, KeyError, ValueError) as e:
        errs.append(f"视觉层文件无法读取：{e}")
    # 6 privacy & junk
    for f in ROOT.rglob("*"):
        if f.is_dir():
            if f.name in ("__pycache__", "node_modules", ".venv", "venv"):
                errs.append(f"残留目录：{f.relative_to(ROOT)}")
            continue
        if f.suffix in (".pyc", ".bak", ".zip", ".tmp"):
            errs.append(f"残留文件：{f.relative_to(ROOT)}")
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for name, rx in PRIVATE:
            if f.name != "validate.py" and rx.search(text):
                errs.append(f"疑似隐私信息（{name}）：{f.relative_to(ROOT)}")
    info.append(f"规则 {len(rules)} 条（lint {len(declared)} / rubric {sum(r['detect']=='rubric' for r in rules.values())} / browser {sum(r['detect']=='browser' for r in rules.values())}）；fixtures {len(man)} 个，覆盖 lint 规则 {len(covered & declared)}/{len(declared)}；案例 {len(cases)} 条；词汇 {len(vocab)} 条")
    if not a.no_eval and not errs:
        sys.path.insert(0, str(ROOT / "scripts"))
        from eval import evaluate
        rep = evaluate()
        info.append(f"eval：{rep['exact_correct']}/{rep['cases']} 完全正确，score {rep['score']}")
        if rep["exact_correct"] != rep["cases"]:
            errs.append("eval 存在错判（详见 python3 scripts/eval.py）")
    for i in info:
        print("· " + i)
    for e in errs:
        print("✗ " + e)
    print("校验通过" if not errs else f"校验失败：{len(errs)} 个问题")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
