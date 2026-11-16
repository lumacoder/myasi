#!/usr/bin/env python3
"""页面原型识别 → 模式、逐区块参考、签名创意、主题候选、rubric 权重。纯标准库，确定性关键词打分；
模型应把它当『初判』，再结合截图/需求确认（可多选：主原型定外壳，次原型定局部）。

  python3 scripts/archetype.py "商户治理工作流管理后台，执行记录与详情"     # 文本需求
  python3 scripts/archetype.py --file page.html                            # 从页面文本/标题抽信号
  python3 scripts/archetype.py --self-test                                 # 跑 visual/examples/archetype_cases.json
"""
import argparse
import json
import re
import sys

sys.dont_write_bytecode = True
from _common import ROOT, utf8_stdio  # noqa: E402

V = ROOT / "visual"


def data():
    arch = json.loads((V / "archetypes.json").read_text(encoding="utf-8"))["archetypes"]
    bench = {b["id"]: b for b in json.loads((V / "benchmarks.json").read_text(encoding="utf-8"))["benchmarks"]}
    pats = {p["id"]: p for p in json.loads((V / "creative-patterns.json").read_text(encoding="utf-8"))["patterns"]}
    return arch, bench, pats


def text_of_html(src):
    src = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", src)
    return re.sub(r"<[^>]+>", " ", src)


def rank(text, arch):
    t = text.lower()
    rows = []
    for a in arch:
        hits = [s for s in a["signals"] if s.lower() in t]
        if hits:
            rows.append({"id": a["id"], "score": len(hits), "hits": hits})
    rows.sort(key=lambda r: (-r["score"], r["id"]))
    return rows


def plan(text, top=2):
    arch, bench, pats = data()
    rows = rank(text, arch)
    by = {a["id"]: a for a in arch}
    out = {"archetypes": rows[:top] or [{"id": "unknown", "score": 0, "hits": []}], "plan": []}
    for r in rows[:top]:
        a = by[r["id"]]
        out["plan"].append({
            "archetype": a["id"], "name_zh": a["name_zh"], "mode": a["mode"], "sections": a["sections"],
            "benchmarks": [{"id": b, "url": bench[b]["demo_url"], "use": bench[b]["use"]} for b in a["seed_benchmarks"]],
            "discovery_queries": a["discovery_queries"],
            "signature_candidates": [{"id": p, "name_zh": pats[p]["name_zh"], "what": pats[p]["what"]} for p in a["signature_patterns"]],
            "theme_hint": a["theme_hint"]})
    if not rows:
        out["note"] = "没有命中信号：先用一句话写清『这是什么产品、给谁用、主要任务』，再识别；或按 capabilities/benchmark-discovery.md 手动归类"
    return out


def self_test():
    cases = json.loads((V / "examples" / "archetype_cases.json").read_text(encoding="utf-8"))
    arch, _, _ = data()
    bad = []
    for c in cases:
        got = [r["id"] for r in rank(c["text"], arch)[:2]]
        if c["expect"] not in got:
            bad.append(f"{c['text'][:30]}… 期望 {c['expect']} 得到 {got}")
    for b in bad:
        print("✗ " + b)
    print(f"原型识别自测 {len(cases) - len(bad)}/{len(cases)}")
    return 1 if bad else 0


def main(argv=None):
    utf8_stdio()
    ap = argparse.ArgumentParser(description="页面原型识别")
    ap.add_argument("text", nargs="?")
    ap.add_argument("--file")
    ap.add_argument("--top", type=int, default=2)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    text = a.text or ""
    if a.file:
        from pathlib import Path
        src = Path(a.file).read_text(encoding="utf-8", errors="replace")
        text += " " + (text_of_html(src) if a.file.endswith((".html", ".htm")) else src)
    if not text.strip():
        ap.error("需要需求文本或 --file")
    print(json.dumps(plan(text, a.top), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
