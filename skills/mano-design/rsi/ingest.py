#!/usr/bin/env python3
"""把 RSI 失败日志转成回归用例（带校验）。默认只预演，--apply 才写入。

  python3 rsi/ingest.py --draft generated.html            # 用当前检查器结果起草一条失败记录（打印 JSON，人工/LLM 修正 verdict 与 rules）
  python3 rsi/ingest.py rsi/failures.json                 # 预演：校验并显示将新增的用例
  python3 rsi/ingest.py rsi/failures.json --apply         # 写入 tests/fixtures + manifest；rubric 规则写入 rsi/rubric_cases.json

校验：id 格式与唯一、规则存在、verdict 与严重级一致、片段可解析且 ≤20KB、内容不重复、无隐私（路径/令牌/私钥/真实邮箱）。
lint 规则 → tests/fixtures/{bad,good}/<id>.<ext>；仅 rubric/browser 规则 → rsi/rubric_cases.json（供 LLM 评审回归）。
"""
import argparse
import hashlib
import json
import re
import sys

sys.dont_write_bytecode = True  # 不在 skill 目录留下 __pycache__
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from _common import utf8_stdio  # noqa: E402
from ui_lint import Builder, jsx_to_html, lint_source, load_rules  # noqa: E402
from validate import PRIVATE  # noqa: E402

ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
EMAIL = re.compile(r"[\w.+-]+@(?!example\.(com|org|net)\b)[\w-]+\.[\w.-]+")
CATS = {"component", "state", "a11y", "color", "copy", "layout", "type"}


def check(entry, rules, existing_ids, existing_hashes):
    errs = []
    for k in ("id", "category", "verdict", "rules", "html", "note", "source"):
        if k not in entry:
            errs.append(f"缺字段 {k}")
    if errs:
        return errs, None
    if not ID.match(entry["id"]) or len(entry["id"]) > 60:
        errs.append("id 需 kebab-case 且 ≤60")
    if entry["id"] in existing_ids:
        errs.append("id 已存在")
    if entry["category"] not in CATS:
        errs.append("category 非法")
    if entry["verdict"] not in ("PASS", "FAIL"):
        errs.append("verdict 只能 PASS/FAIL")
    unknown = [r for r in entry["rules"] if r not in rules]
    if unknown:
        errs.append(f"未知规则 {unknown}（新规则先加进 rules/rules.json）")
    blocking = any(rules[r]["severity"] in ("critical", "major") for r in entry["rules"] if r in rules)
    if entry["verdict"] == "FAIL" and not blocking and "cp.ai-cliche" not in entry["rules"]:
        errs.append("FAIL 但没有 critical/major 规则")
    if entry["verdict"] == "PASS" and blocking:
        errs.append("PASS 但含 critical/major 规则")
    html = entry["html"]
    if not (10 <= len(html) <= 20000):
        errs.append("html 长度需 10—20000")
    try:
        b = Builder()
        b.feed(jsx_to_html(html) if entry.get("ext") == "jsx" else html)
        b.close()
    except Exception as e:  # noqa: BLE001
        errs.append(f"片段无法解析：{e}")
    for name, rx in PRIVATE + [("邮箱", EMAIL)]:
        if rx.search(html) or rx.search(entry["note"]) or rx.search(entry["source"]):
            errs.append(f"疑似隐私信息：{name}")
    h = hashlib.sha1((html.strip() + "\n").encode("utf-8")).hexdigest()
    if h in existing_hashes:
        errs.append(f"内容与已有用例重复：{existing_hashes[h]}")
    kinds = {rules[r]["detect"] for r in entry["rules"] if r in rules}
    target = "rubric" if entry["rules"] and "lint" not in kinds else "fixture"
    if target == "rubric" and kinds - {"rubric", "browser"}:
        errs.append("同一条记录不要混用 lint 与 rubric 规则，拆成两条")
    return errs, target


def draft(path, rules):
    src = Path(path).read_text(encoding="utf-8")
    rep = lint_source(src, rules, str(path))
    got = sorted({f["rule"] for f in rep["findings"]})
    stem = re.sub(r"[^a-z0-9]+", "-", Path(path).stem.lower()).strip("-") or "case"
    return [{"id": f"rsi-{stem}", "category": rep["findings"][0]["category"] if rep["findings"] else "component",
             "verdict": rep["verdict"], "rules": got, "html": src, "note": "TODO：写明真实问题；修正 verdict/rules 为『应有』而非『当前输出』",
             "source": "TODO：生成任务/模型/评审者", "observed": {"verdict": rep["verdict"], "rules": got}}]


def main(argv=None):
    utf8_stdio()
    ap = argparse.ArgumentParser(description="RSI：失败日志 → 回归用例")
    ap.add_argument("log", nargs="?", type=Path)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--draft", type=Path, help="对一个 UI 文件起草失败记录")
    a = ap.parse_args(argv)
    rules = load_rules()
    if a.draft:
        print(json.dumps(draft(a.draft, rules), ensure_ascii=False, indent=1))
        return 0
    if not a.log:
        ap.error("需要失败日志路径或 --draft")
    entries = json.loads(a.log.read_text(encoding="utf-8"))
    mpath = ROOT / "tests" / "manifest.json"
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    rpath = ROOT / "rsi" / "rubric_cases.json"
    rubric = json.loads(rpath.read_text(encoding="utf-8"))
    ids = {c["id"] for c in manifest} | {c["id"] for c in rubric}
    hashes = {hashlib.sha1((ROOT / "tests" / "fixtures" / c["file"]).read_bytes()).hexdigest(): c["id"] for c in manifest}
    ok, bad = [], 0
    for e in entries:
        errs, target = check(e, rules, ids, hashes)
        if errs:
            bad += 1
            print(f"✗ {e.get('id')}: {'；'.join(errs)}")
            continue
        ids.add(e["id"])
        hashes[hashlib.sha1((e["html"].strip() + "\n").encode("utf-8")).hexdigest()] = e["id"]
        obs = e.get("observed") or lint_source(e["html"], rules)
        kind = ""
        if target == "fixture":
            exp, got = set(e["rules"]), set(obs.get("rules") or [f["rule"] for f in obs.get("findings", [])])
            kind = "漏报 " + ",".join(sorted(exp - got)) if exp - got else ""
            kind += (" 误报 " + ",".join(sorted(got - exp))) if got - exp else ""
        print(f"✓ {e['id']} → {target}{('（' + kind.strip() + '）') if kind.strip() else ''}")
        ok.append((e, target))
    if not a.apply:
        print(f"预演：可新增 {len(ok)} 条，拒绝 {bad} 条。确认后加 --apply。")
        return 1 if bad else 0
    for e, target in ok:
        if target == "rubric":
            rubric.append({k: e[k] for k in ("id", "category", "verdict", "rules", "html", "note", "source")})
            continue
        sub = "bad" if e["rules"] else "good"
        ext = e.get("ext", "html")
        (ROOT / "tests" / "fixtures" / sub / f"{e['id']}.{ext}").write_text(e["html"].strip() + "\n", encoding="utf-8")
        manifest.append({"id": e["id"], "category": e["category"], "verdict": e["verdict"], "rules": sorted(e["rules"]),
                         "note": e["note"], "split": e.get("split", "train"), "file": f"{sub}/{e['id']}.{ext}", "source": e["source"]})
    mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    rpath.write_text(json.dumps(rubric, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"已写入 {len(ok)} 条（拒绝 {bad}）。下一步：python3 rsi/gate.py")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
