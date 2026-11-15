#!/usr/bin/env python3
"""按需查询 rules/rules.json（不要通读整个文件）。

  python3 scripts/rules.py --id cs.binary-select
  python3 scripts/rules.py --category component --format table
  python3 scripts/rules.py --detect rubric --format checklist     # 生成 LLM 评审清单
  python3 scripts/rules.py --keyword 开关
"""
import argparse
import json
import sys

sys.dont_write_bytecode = True  # 不在 skill 目录留下 __pycache__

from _common import ROOT, utf8_stdio


def main(argv=None):
    utf8_stdio()
    ap = argparse.ArgumentParser(description="查询 mano-design 规则")
    ap.add_argument("--id", action="append", default=[])
    ap.add_argument("--category", choices=("component", "state", "a11y", "color", "copy", "layout"))
    ap.add_argument("--detect", choices=("lint", "rubric", "browser"))
    ap.add_argument("--severity", choices=("critical", "major", "minor"))
    ap.add_argument("--keyword")
    ap.add_argument("--format", choices=("json", "table", "checklist"), default="json")
    a = ap.parse_args(argv)
    data = json.loads((ROOT / "rules" / "rules.json").read_text(encoding="utf-8"))
    out = []
    for r in data["rules"]:
        if a.id and r["id"] not in a.id:
            continue
        if a.category and r["category"] != a.category:
            continue
        if a.detect and r["detect"] != a.detect:
            continue
        if a.severity and r["severity"] != a.severity:
            continue
        if a.keyword and a.keyword.casefold() not in json.dumps(r, ensure_ascii=False).casefold():
            continue
        out.append(r)
    if a.format == "json":
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif a.format == "table":
        print("| id | 级别 | 检测 | 场景 → 正确组件 |\n|---|---|---|---|")
        for r in out:
            print(f"| {r['id']} | {r['severity']} | {r['detect']} | {r['signal']} → {r['correct']} |")
    else:
        for r in out:
            print(f"- [ ] `{r['id']}`（{r['severity']}）{r['title_zh']}：当「{r['signal']}」时应为「{r['correct']}」；反例：{'、'.join(r['anti_patterns'])}")
    print(f"共 {len(out)} 条", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
