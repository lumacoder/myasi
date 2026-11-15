#!/usr/bin/env python3
"""校验Mano-ASI案例库：JSON解析、ID/URL去重、可选jsonschema完整校验。跨平台：python3 / py 均可。"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass
    parser = argparse.ArgumentParser(description="校验cases.json；装有jsonschema时做完整schema校验，否则只做结构与去重检查。")
    parser.add_argument("--file", type=Path, default=ROOT / "cases" / "cases.json")
    parser.add_argument("--schema", type=Path, default=ROOT / "cases" / "cases.schema.json")
    args = parser.parse_args(argv)
    sys.path.insert(0, str(ROOT / "scripts"))
    from query import load_cases  # 结构与ID/URL去重
    try:
        cases = load_cases(args.file)
    except (OSError, ValueError) as exc:
        print(f"失败：{exc}")
        return 1
    errors = []
    try:
        import jsonschema
    except ImportError:
        print(f"结构/去重通过：{len(cases)}条；未安装jsonschema，跳过完整schema校验（pip install jsonschema）。")
        return 0
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    for err in validator.iter_errors(cases):
        errors.append(f"{'/'.join(map(str, err.absolute_path))}: {err.message}")
    for line in errors[:20]:
        print(line)
    print(f"schema校验：{len(cases)}条，错误{len(errors)}个。")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
