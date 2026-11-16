#!/usr/bin/env python3
"""主题选择与 token 输出（未指定主题时用）。纯标准库。

  python3 scripts/theme.py --list
  python3 scripts/theme.py --pick "商户治理 运营后台 工作流" [--mode Operate]   # 按行业/受众/模式打分推荐，附理由
  python3 scripts/theme.py --css signal-blue                                    # 输出 :root / .dark CSS 变量（shadcn 命名）
  python3 scripts/theme.py --check                                              # 全部主题 WCAG 实测，失败退出 1
"""
import argparse
import json
import sys

sys.dont_write_bytecode = True
from _common import ROOT, utf8_stdio  # noqa: E402

THEMES = ROOT / "visual" / "themes.json"
TEXT_PAIRS = [("foreground", "background", 4.5), ("foreground", "card", 4.5), ("muted-foreground", "background", 4.5),
              ("muted-foreground", "card", 4.5), ("muted-foreground", "muted", 4.0), ("primary-foreground", "primary", 4.5),
              ("success", "background", 4.5), ("warning", "background", 4.5), ("danger", "background", 4.5), ("info", "background", 4.5),
              ("primary", "background", 3.0), ("ring", "background", 3.0)]


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lum(c):
    def ch(x):
        x /= 255
        return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in rgb(c))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    x, y = sorted((lum(a), lum(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


def load():
    return json.loads(THEMES.read_text(encoding="utf-8"))["themes"]


def check(themes):
    errs = []
    for t in themes:
        for mode in ("light", "dark"):
            tok = t[mode]
            for fg, bg, need in TEXT_PAIRS:
                if fg in tok and bg in tok:
                    r = contrast(tok[fg], tok[bg])
                    if r < need:
                        errs.append(f"{t['id']}.{mode}: {fg} on {bg} = {r:.2f} < {need}")
            for c in tok.get("chart", []):
                if contrast(c, tok["background"]) < 3.0:
                    errs.append(f"{t['id']}.{mode}: chart {c} on background < 3")
    return errs


def pick(themes, text, mode=None):
    text = text.lower()
    rows = []
    for t in themes:
        f = t["fits"]
        hits = [w for w in f["industries"] + f["audiences"] if any(k and k.lower() in text for k in w.replace("/", " ").replace("（", " ").replace("）", " ").split())]
        score = 2 * len(hits) + (2 if mode and mode in f["modes"] else 0)
        if any(k in text for k in t["avoid"].split("（")[0].split("、")):
            score -= 1
        rows.append((score, t["id"], hits, t))
    rows.sort(key=lambda r: -r[0])
    return [{"id": i, "score": s, "matched": h, "metaphor": t["metaphor"], "avoid": t["avoid"]} for s, i, h, t in rows[:3]]


def css(t):
    def block(sel, tok):
        lines = [f"{sel} {{"]
        for k, v in tok.items():
            if k == "chart":
                lines += [f"  --chart-{i + 1}: {c};" for i, c in enumerate(v)]
            else:
                lines.append(f"  --{k}: {v};")
        return "\n".join(lines + ["}"])
    return f"/* theme: {t['id']} — {t['metaphor']} */\n" + block(":root", t["light"]) + "\n" + block(".dark", t["dark"])


def main(argv=None):
    utf8_stdio()
    ap = argparse.ArgumentParser(description="主题选择与 token")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--pick")
    ap.add_argument("--mode", choices=("Persuade", "Operate", "Read", "Experience"))
    ap.add_argument("--css")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    themes = load()
    if a.check:
        errs = check(themes)
        for e in errs:
            print("✗ " + e)
        print(f"主题 {len(themes)} 个，对比度检查{'通过' if not errs else f'失败 {len(errs)} 处'}")
        return 1 if errs else 0
    if a.css:
        t = next((t for t in themes if t["id"] == a.css), None)
        if not t:
            print("未知主题；--list 查看", file=sys.stderr)
            return 2
        print(css(t))
        return 0
    if a.pick:
        print(json.dumps(pick(themes, a.pick, a.mode), ensure_ascii=False, indent=1))
        return 0
    for t in themes:
        print(f"{t['id']:15} {t['name_zh']}  {t['metaphor']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
