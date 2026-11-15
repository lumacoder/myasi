#!/usr/bin/env python3
"""Mano-Design 自测评估：对 tests/manifest.json 中所有用例运行 ui_lint，与期望比对。

指标：
- verdict 准确率（PASS/FAIL 是否一致）
- 每条规则 precision / recall（按「用例 × 规则 id」计 TP/FP/FN）
- 每个类别的 verdict 准确率与规则 F1
- score = 50×verdict准确率 + 50×micro-F1（0—100）
用法：
  python3 scripts/eval.py                 # 全部用例
  python3 scripts/eval.py --split holdout # 只跑留出集
  python3 scripts/eval.py --out report.json --quiet
退出码：0=全部正确，3=存在错判（供 CI/RSI 门禁使用）。
"""
import argparse
import json
import sys

sys.dont_write_bytecode = True  # 不在 skill 目录留下 __pycache__
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ui_lint import lint_source, load_rules  # noqa: E402


def f1(p, r):
    return 0.0 if p + r == 0 else 2 * p * r / (p + r)


def evaluate(manifest_path=None, split=None):
    manifest_path = manifest_path or ROOT / "tests" / "manifest.json"
    cases = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    rules = load_rules()
    fixtures = Path(manifest_path).parent / "fixtures"
    per_rule = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    per_cat = defaultdict(lambda: {"n": 0, "verdict_ok": 0, "tp": 0, "fp": 0, "fn": 0})
    results, ok_verdict = [], 0
    for c in cases:
        if split and c.get("split", "train") != split:
            continue
        path = fixtures / c["file"]
        rep = lint_source(path.read_text(encoding="utf-8"), rules, str(path.name))
        got = {f["rule"] for f in rep["findings"]}
        exp = set(c["rules"])
        tp, fp, fn = got & exp, got - exp, exp - got
        for r in tp:
            per_rule[r]["tp"] += 1
        for r in fp:
            per_rule[r]["fp"] += 1
        for r in fn:
            per_rule[r]["fn"] += 1
        cat = per_cat[c["category"]]
        cat["n"] += 1
        cat["tp"] += len(tp)
        cat["fp"] += len(fp)
        cat["fn"] += len(fn)
        vok = rep["verdict"] == c["verdict"]
        ok_verdict += vok
        cat["verdict_ok"] += vok
        results.append({"id": c["id"], "split": c.get("split", "train"), "category": c["category"],
                        "expected": c["verdict"], "got": rep["verdict"], "verdict_ok": vok,
                        "missing": sorted(fn), "unexpected": sorted(fp),
                        "correct": vok and not fn and not fp})
    n = len(results)
    TP = sum(v["tp"] for v in per_rule.values())
    FP = sum(v["fp"] for v in per_rule.values())
    FN = sum(v["fn"] for v in per_rule.values())
    P = TP / (TP + FP) if TP + FP else 1.0
    R = TP / (TP + FN) if TP + FN else 1.0
    va = ok_verdict / n if n else 0.0
    rule_tbl = {}
    for r, v in sorted(per_rule.items()):
        p = v["tp"] / (v["tp"] + v["fp"]) if v["tp"] + v["fp"] else 1.0
        rc = v["tp"] / (v["tp"] + v["fn"]) if v["tp"] + v["fn"] else 1.0
        rule_tbl[r] = dict(v, precision=round(p, 3), recall=round(rc, 3))
    cat_tbl = {}
    for k, v in sorted(per_cat.items()):
        p = v["tp"] / (v["tp"] + v["fp"]) if v["tp"] + v["fp"] else 1.0
        rc = v["tp"] / (v["tp"] + v["fn"]) if v["tp"] + v["fn"] else 1.0
        cat_tbl[k] = {"cases": v["n"], "verdict_acc": round(v["verdict_ok"] / v["n"], 3), "rule_f1": round(f1(p, rc), 3)}
    lint_rules = sorted(r for r, m in rules.items() if m["detect"] == "lint")
    return {
        "split": split or "all", "cases": n,
        "exact_correct": sum(r["correct"] for r in results),
        "verdict_accuracy": round(va, 4), "precision": round(P, 4), "recall": round(R, 4),
        "micro_f1": round(f1(P, R), 4), "score": round(50 * va + 50 * f1(P, R), 2),
        "lint_rules_total": len(lint_rules),
        "lint_rules_covered_by_fixtures": sorted(set(lint_rules) & {r for c in cases for r in c["rules"]}),
        "per_category": cat_tbl, "per_rule": rule_tbl, "results": results,
    }


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            try:
                s.reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass
    ap = argparse.ArgumentParser(description="运行 Mano-Design 自测用例并打分")
    ap.add_argument("--manifest", type=Path)
    ap.add_argument("--split", choices=("train", "holdout"))
    ap.add_argument("--out", type=Path, help="写入完整 JSON 报告")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    rep = evaluate(a.manifest, a.split)
    if a.out:
        a.out.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    if not a.quiet:
        print(f"用例 {rep['cases']}（{rep['split']}）  完全正确 {rep['exact_correct']}  verdict 准确率 {rep['verdict_accuracy']:.1%}  "
              f"P {rep['precision']:.1%}  R {rep['recall']:.1%}  F1 {rep['micro_f1']:.1%}  score {rep['score']}")
        print(f"lint 规则 {rep['lint_rules_total']} 条，用例覆盖 {len(rep['lint_rules_covered_by_fixtures'])} 条")
        print("类别：" + "  ".join(f"{k} {v['verdict_acc']:.0%}/F1 {v['rule_f1']:.2f}({v['cases']})" for k, v in rep["per_category"].items()))
        bad = [r for r in rep["results"] if not r["correct"]]
        for r in bad:
            print(f"  ✗ {r['id']} [{r['split']}] 期望 {r['expected']} 得到 {r['got']}  漏报 {r['missing']}  误报 {r['unexpected']}")
        weak = {k: v for k, v in rep["per_rule"].items() if v["precision"] < 1 or v["recall"] < 1}
        for k, v in weak.items():
            print(f"  · {k}: P {v['precision']} R {v['recall']} (tp {v['tp']} fp {v['fp']} fn {v['fn']})")
    return 0 if rep["exact_correct"] == rep["cases"] else 3


if __name__ == "__main__":
    sys.exit(main())
