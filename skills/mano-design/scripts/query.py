#!/usr/bin/env python3
"""查询开源方案目录 cases/cases.json；默认摘要 ≤3 条，--full 显示完整记录。"""
import argparse
import json
import sys

sys.dont_write_bytecode = True  # 不在 skill 目录留下 __pycache__

from _common import ROOT, utf8_stdio


def main(argv=None):
    utf8_stdio()
    ap = argparse.ArgumentParser(description="筛选 mano-design 开源方案目录；条件 AND 组合")
    ap.add_argument("--tag", action="append", default=[])
    ap.add_argument("--category")
    ap.add_argument("--borrow", choices=("direct-dep", "pattern", "reference"))
    ap.add_argument("--pick", action="store_true", help="只看核心组合（pick=true）")
    ap.add_argument("--keyword")
    ap.add_argument("--limit", type=int, default=3, help="0 表示全部")
    ap.add_argument("--full", action="store_true")
    a = ap.parse_args(argv)
    cases = json.loads((ROOT / "cases" / "cases.json").read_text(encoding="utf-8"))
    out = []
    for c in cases:
        tags = {t.casefold() for t in c["tags"]}
        if any(t.casefold() not in tags for t in a.tag):
            continue
        if a.category and a.category != c["category"]:
            continue
        if a.borrow and a.borrow != c["borrow"]:
            continue
        if a.pick and not c["pick"]:
            continue
        if a.keyword and a.keyword.casefold() not in json.dumps(c, ensure_ascii=False).casefold():
            continue
        out.append(c)
    if a.limit:
        out = out[:a.limit]
    if not a.full:
        keys = ("id", "repo_url", "one_liner_zh", "combine_role", "borrow", "license", "stars_snapshot")
        out = [{k: c[k] for k in keys} for c in out]
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
