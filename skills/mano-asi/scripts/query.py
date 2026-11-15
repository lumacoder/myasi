#!/usr/bin/env python3
"""用标准库筛选Mano-ASI案例；默认摘要JSON，--full显示完整记录。跨平台：python3 / py 均可。"""
import argparse
import json
from pathlib import Path
import sys


def _utf8_stdio():
    """Windows控制台默认非UTF-8时，保证中文正常输出。"""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


def load_cases(path):
    """拒绝损坏结构和重复ID/规范仓库URL，不把查询检查冒充完整schema验证。"""
    cases = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cases, list):
        raise ValueError("案例库必须为JSON数组")
    ids, urls = set(), set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"第{index + 1}条案例必须为对象")
        for key in ("id", "name", "repo_url", "one_liner_zh", "category"):
            if not isinstance(case.get(key), str) or not case[key]:
                raise ValueError(f"第{index + 1}条缺少有效字段：{key}")
        if not isinstance(case.get("tags"), list) or not all(isinstance(t, str) for t in case["tags"]):
            raise ValueError(f"第{index + 1}条tags必须为字符串数组")
        if not isinstance(case.get("verified"), bool):
            raise ValueError(f"第{index + 1}条verified必须为boolean")
        url = case["repo_url"].rstrip("/").casefold()
        if case["id"] in ids or url in urls:
            raise ValueError(f"重复ID或仓库URL：{case['id']}")
        ids.add(case["id"])
        urls.add(url)
    return cases


def main(argv=None):
    _utf8_stdio()
    parser = argparse.ArgumentParser(description="筛选Mano-ASI案例；不同条件AND组合，多次tag全部匹配，keyword不区分大小写。")
    parser.add_argument("--file", type=Path, default=Path(__file__).resolve().parents[1] / "cases" / "cases.json", help="案例JSON路径，默认定位本包")
    parser.add_argument("--tag", action="append", default=[], help="精确标签，可重复；忽略大小写")
    parser.add_argument("--category", help="精确分类，忽略大小写")
    parser.add_argument("--keyword", help="对整条记录做文本子串匹配，忽略大小写")
    parser.add_argument("--verified", choices=("true", "false"), help="按元数据核实状态筛选")
    parser.add_argument("--limit", type=int, default=3, help="最多返回条数，默认3；0表示全部")
    parser.add_argument("--full", action="store_true", help="返回完整记录，而非摘要")
    args = parser.parse_args(argv)
    if args.limit < 0:
        parser.error("--limit不能为负数")
    try:
        cases = load_cases(args.file)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"案例库读取失败：{exc}\n")
    result = []
    for case in cases:
        tags = {tag.casefold() for tag in case["tags"]}
        if any(tag.casefold() not in tags for tag in args.tag):
            continue
        if args.category and args.category.casefold() != case["category"].casefold():
            continue
        if args.verified is not None and case["verified"] != (args.verified == "true"):
            continue
        if args.keyword and args.keyword.casefold() not in json.dumps(case, ensure_ascii=False).casefold():
            continue
        result.append(case)
    if args.limit:
        result = result[:args.limit]
    if not args.full:
        fields = ("id", "name", "repo_url", "one_liner_zh", "category", "tags", "borrow", "verified")
        result = [{key: case[key] for key in fields} for case in result]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
