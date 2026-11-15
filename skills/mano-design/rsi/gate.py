#!/usr/bin/env python3
"""RSI 回归门禁：只接受「不降分、不回退」的修改。

  python3 rsi/gate.py                    # 对比 rsi/baseline.json，输出 ACCEPT/REJECT
  python3 rsi/gate.py --accept --note "新增 xx 规则"   # 通过时更新基线、版本号 +0.0.1、写 CHANGELOG
  python3 rsi/gate.py --init             # 首次建立基线

硬性条件（任何一条不满足即 REJECT）：
1. 基线里判对的用例，现在仍全部判对（无回退）
2. 基线用例集合上的 score 不下降
3. 全集 exact_correct 不少于基线
4. holdout 子集 score 不下降（防止只为训练用例调参）
新增但仍判错的用例记为 open，不阻断，但会在报告中列出，下一轮优先修。
"""
import argparse
import datetime
import json
import re
import sys

sys.dont_write_bytecode = True  # 不在 skill 目录留下 __pycache__
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from _common import utf8_stdio  # noqa: E402
from eval import evaluate  # noqa: E402

BASE = ROOT / "rsi" / "baseline.json"


def subset_score(rep, ids):
    rows = [r for r in rep["results"] if r["id"] in ids]
    return round(100 * sum(r["correct"] for r in rows) / len(rows), 2) if rows else 100.0


def bump(version):
    a, b, c = (int(x) for x in version.split("."))
    return f"{a}.{b}.{c + 1}"


def main(argv=None):
    utf8_stdio()
    ap = argparse.ArgumentParser(description="RSI 回归门禁")
    ap.add_argument("--accept", action="store_true")
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--note", default="")
    a = ap.parse_args(argv)
    rep = evaluate()
    hold = evaluate(split="holdout")
    now = {"score": rep["score"], "exact_correct": rep["exact_correct"], "cases": rep["cases"],
           "holdout_score": hold["score"], "correct_ids": sorted(r["id"] for r in rep["results"] if r["correct"]),
           "all_ids": sorted(r["id"] for r in rep["results"]),
           "open_ids": sorted(r["id"] for r in rep["results"] if not r["correct"])}
    if a.init or not BASE.exists():
        sj = json.loads((ROOT / "skill.json").read_text(encoding="utf-8"))
        BASE.write_text(json.dumps(dict(now, version=sj["version"], date=str(datetime.date.today())), ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"基线已建立：score {now['score']}，{now['exact_correct']}/{now['cases']}，holdout {now['holdout_score']}")
        return 0
    base = json.loads(BASE.read_text(encoding="utf-8"))
    reasons = []
    regressed = sorted(set(base["correct_ids"]) - set(now["correct_ids"]))
    if regressed:
        reasons.append(f"回退用例：{regressed}")
    old_set = set(base["all_ids"])
    s_old = subset_score({"results": [{"id": i, "correct": i in base["correct_ids"]} for i in old_set]}, old_set)
    s_new = subset_score(rep, old_set)
    if s_new < s_old:
        reasons.append(f"基线用例集得分下降 {s_old} → {s_new}")
    if now["exact_correct"] < base["exact_correct"]:
        reasons.append(f"完全正确数下降 {base['exact_correct']} → {now['exact_correct']}")
    if now["holdout_score"] < base["holdout_score"]:
        reasons.append(f"holdout 得分下降 {base['holdout_score']} → {now['holdout_score']}")
    print(f"基线 v{base['version']}：score {base['score']} ({base['exact_correct']}/{base['cases']}) holdout {base['holdout_score']}")
    print(f"当前：score {now['score']} ({now['exact_correct']}/{now['cases']}) holdout {now['holdout_score']}；open {now['open_ids'] or '无'}")
    if reasons:
        print("REJECT：" + "；".join(reasons))
        return 4
    print("ACCEPT")
    if a.accept:
        sj_path = ROOT / "skill.json"
        sj = json.loads(sj_path.read_text(encoding="utf-8"))
        sj["version"] = bump(sj["version"])
        sj_path.write_text(json.dumps(sj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        rj_path = ROOT / "rules" / "rules.json"
        rj = json.loads(rj_path.read_text(encoding="utf-8"))
        rj["version"] = sj["version"]
        rj_path.write_text(json.dumps(rj, ensure_ascii=False, indent=1), encoding="utf-8")
        BASE.write_text(json.dumps(dict(now, version=sj["version"], date=str(datetime.date.today())), ensure_ascii=False, indent=1), encoding="utf-8")
        log = ROOT / "CHANGELOG.md"
        text = log.read_text(encoding="utf-8")
        entry = (f"\n## {sj['version']} — {datetime.date.today()}\n- {a.note or 'RSI 迭代'}\n"
                 f"- eval：{now['exact_correct']}/{now['cases']}，score {now['score']}，holdout {now['holdout_score']}\n")
        text = re.sub(r"(# 更新记录\n)", r"\1" + entry.replace("\\", "\\\\"), text, count=1)
        log.write_text(text, encoding="utf-8")
        print(f"已接受：版本 → {sj['version']}，基线与 CHANGELOG 已更新")
    return 0


if __name__ == "__main__":
    sys.exit(main())
