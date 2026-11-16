#!/usr/bin/env python3
"""视觉评分门禁：校验评分 JSON 的证据完整性，按模式加权，判定是否达到交付门槛（默认 ≥8）。

  python3 scripts/visual_score.py score.json [--check-files] [--gate 8]   # 退出码 0=通过 3=未通过 2=评分无效
  python3 scripts/visual_score.py --template workflow-automation          # 打印空白评分模板
  python3 scripts/visual_score.py --self-test                             # 跑 visual/examples/score-*.json
规则见 visual/rubric.md。
"""
import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from _common import ROOT, utf8_stdio  # noqa: E402

DIMS = ["hierarchy", "typography", "color", "polish", "density", "motion", "creativity", "consistency"]
WEIGHTS = {
    "Operate":    dict(hierarchy=.18, typography=.10, color=.10, polish=.16, density=.16, motion=.08, creativity=.10, consistency=.12),
    "Persuade":   dict(hierarchy=.14, typography=.16, color=.12, polish=.12, density=.06, motion=.14, creativity=.16, consistency=.10),
    "Read":       dict(hierarchy=.18, typography=.22, color=.08, polish=.12, density=.12, motion=.04, creativity=.08, consistency=.16),
    "Experience": dict(hierarchy=.10, typography=.12, color=.12, polish=.12, density=.04, motion=.18, creativity=.22, consistency=.10),
}


def score(doc, gate=8.0, check_files=False, base=None):
    errs, fails = [], []
    mode = doc.get("mode")
    if mode not in WEIGHTS:
        errs.append(f"mode 必须是 {list(WEIGHTS)}")
        return {"valid": False, "errors": errs}
    if not doc.get("screenshots"):
        errs.append("缺 screenshots：没有截图证据不能打视觉分")
    if not doc.get("benchmarks"):
        errs.append("缺 benchmarks：必须写明对标的基准（visual/benchmarks.json 的 id 或 URL）")
    if check_files:
        for s in doc.get("screenshots", []):
            p = Path(s) if Path(s).is_absolute() else (base or Path.cwd()) / s
            if not p.exists():
                errs.append(f"截图不存在：{s}")
    dims = doc.get("dimensions", {})
    total = 0.0
    for d in DIMS:
        v = dims.get(d)
        if not v:
            errs.append(f"缺维度 {d}")
            continue
        s, vs, ev = v.get("score"), v.get("vs_benchmark"), (v.get("evidence") or "").strip()
        if not isinstance(s, (int, float)) or not 0 <= s <= 10 or (s * 2) != int(s * 2):
            errs.append(f"{d}.score 需 0—10、步长 0.5")
            continue
        if vs not in ("below", "par", "above"):
            errs.append(f"{d}.vs_benchmark 需 below/par/above")
        if len(ev) < 20:
            errs.append(f"{d}.evidence 太短（≥20 字，写截图/区域/与基准的对比）")
        if s >= 8 and vs == "below":
            errs.append(f"{d}：低于基准却给 {s} 分（≥8 需 par/above）")
        if s >= 9 and vs != "above":
            errs.append(f"{d}：给 {s} 分需 vs_benchmark=above")
        if s < 6:
            fails.append(f"{d} = {s} < 6（单维下限）")
        total += WEIGHTS[mode][d] * s
    if errs:
        return {"valid": False, "errors": errs}
    raw = round(total, 2)
    adj = raw - (0.5 if doc.get("reviewer", "self") == "self" else 0)
    if doc.get("lint_blocking", 0) or doc.get("browser_blocking", 0):
        fails.append("ui_lint / browser_check 仍有 critical/major")
        adj = min(adj, 6.0)
    if fails:
        adj = min(adj, 7.5 if not any("lint" in f for f in fails) else 6.0)
    adj = round(adj, 2)
    passed = adj >= gate and not fails
    if not passed and not doc.get("top3"):
        fails.append("未通过时必须给出 top3（最该先修的 3 个问题）")
    return {"valid": True, "mode": mode, "weighted": raw, "final": adj, "gate": gate, "pass": passed, "fails": fails,
            "weakest": sorted(DIMS, key=lambda d: dims[d]["score"])[:3]}


def self_test():
    ok = True
    for p in sorted((ROOT / "visual" / "examples").glob("score-*.json")):
        doc = json.loads(p.read_text(encoding="utf-8"))
        exp = doc.pop("_expect")
        r = score(doc)
        got = "invalid" if not r["valid"] else ("pass" if r["pass"] else "fail")
        mark = "✓" if got == exp else "✗"
        ok &= got == exp
        print(f"{mark} {p.name}: 期望 {exp} 得到 {got} {r.get('final', '')} {r.get('errors', r.get('fails', ''))}")
    return 0 if ok else 1


def template(arch):
    a = next((x for x in json.loads((ROOT / "visual" / "archetypes.json").read_text(encoding="utf-8"))["archetypes"] if x["id"] == arch), None)
    mode = a["mode"] if a else "Operate"
    return {"target": "", "archetype": arch, "mode": mode, "reviewer": "fresh", "screenshots": [],
            "benchmarks": a["seed_benchmarks"][:3] if a else [], "lint_blocking": 0, "browser_blocking": 0,
            "dimensions": {d: {"score": 0, "vs_benchmark": "below", "evidence": ""} for d in DIMS}, "top3": []}


def main(argv=None):
    utf8_stdio()
    ap = argparse.ArgumentParser(description="视觉评分门禁")
    ap.add_argument("file", nargs="?")
    ap.add_argument("--gate", type=float, default=8.0)
    ap.add_argument("--check-files", action="store_true")
    ap.add_argument("--template")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if a.template:
        print(json.dumps(template(a.template), ensure_ascii=False, indent=1))
        return 0
    if not a.file:
        ap.error("需要评分 JSON")
    p = Path(a.file)
    r = score(json.loads(p.read_text(encoding="utf-8")), a.gate, a.check_files, p.parent)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 2 if not r["valid"] else (0 if r["pass"] else 3)


if __name__ == "__main__":
    sys.exit(main())
