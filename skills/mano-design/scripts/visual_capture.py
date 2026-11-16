#!/usr/bin/env python3
"""视觉评审取证：把『自己的页面』各路由/状态/明暗/手机宽度截图，和『同原型基准』截图拼成对照表（contact sheet），
并生成评审提示 review.md（来自 Y0urDumble 帖引用文章的 review loop：联系表 + 手机测试 + 苛刻评审 + 先修 3 个最严重的）。
可选依赖 Playwright（pip install playwright；用本机 Chrome 或 playwright install chromium）。缺依赖输出 skipped。

  python3 scripts/visual_capture.py dist/index.html --out shots \
      --views "workflows=#/workflows;runs=#/runs;node=#/workflows|click:[data-node=calc]" \
      --archetype workflow-automation --dark --mobile
  python3 scripts/visual_capture.py https://example.com --out shots --bench-urls https://ui.shadcn.com/blocks

--views：名字=路由[|wait:<毫秒>][|click:<选择器>]…，分号分隔，步骤按书写顺序执行（例：先 wait 等回放结束再 click 打开详情）；路由可为 #hash、/path 或完整 URL。
基准截图默认取 --archetype（可逗号分隔多个：主原型,次原型）的 seed_benchmarks 中有 capture_url 的，多原型时轮流各取一个，共 4 个（需联网；失败不阻断）。
输出：<out>/<name>-light.png、-dark.png、-mobile.png、bench-<id>.png、contact-sheet.png、review.md。截图是临时证据，交付后按 hygiene 清理或只保留最终版。
"""
import argparse
import html
import json
import os
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from _common import ROOT, utf8_stdio  # noqa: E402

REVIEW = """# 视觉评审（新会话执行；不要看生成过程）
打开 contact-sheet.png（左：你的页面各视图；右：同原型基准）。
**这不是你做的。你是我认识的最苛刻的设计总监。**

逐项检查（visual/rubric.md 8 维）：层级、字体排印、配色与主题、组件精致度、密度节奏、动效、创意与领域契合、一致性。
另外必查：
- 遮住品牌名，这页能不能原样贴到任何竞品？哪些是「反射」而不是「为这个产品」做的选择？
- 有没有一个来自领域对象的签名可视化/交互（visual/creative-patterns.json）？它是否服务任务？
- 手机宽度（*-mobile.png）是否可读、可点？
- 与右侧基准相比，每一维是 below / par / above？

列出每个问题（截图文件名 + 区域）。**先修最严重的 3 个，只重拍受影响的视图**，再给新的联系表。
最后按 visual/rubric.md 的 JSON 格式输出评分，交给 scripts/visual_score.py 判定（≥8 才可交付）。

原型：{archetype}（模式 {mode}）；基准：{benches}
"""


def find_chrome():
    for c in (os.environ.get("CHROME_PATH"), shutil.which("google-chrome"), shutil.which("chromium"), shutil.which("chromium-browser"),
              r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
        if c and Path(c).exists():
            return c
    return None


def parse_views(spec):
    views = []
    for part in [p for p in spec.split(";") if p.strip()]:
        name, _, rest = part.partition("=")
        bits = rest.split("|")
        v = {"name": name.strip(), "route": bits[0].strip(), "steps": [], "clicks": [], "wait": 600}
        for b in bits[1:]:
            k, _, val = b.partition(":")
            if k == "click":
                v["steps"].append(("click", val))
                v["clicks"].append(val)
            elif k == "wait":
                v["steps"].append(("wait", int(val)))
        # 步骤按书写顺序执行（先等动画/数据，再点击）；末尾不是 wait 时补 600ms 让界面稳定
        if not v["steps"] or v["steps"][-1][0] != "wait":
            v["steps"].append(("wait", 600))
        views.append(v)
    return views or [{"name": "page", "route": "", "steps": [("wait", 600)], "clicks": [], "wait": 600}]


def url_for(base, route):
    if not route:
        return base
    if route.startswith(("http://", "https://", "file:")):
        return route
    if route.startswith("#"):
        return base.split("#")[0] + route
    return base.split("#")[0].rstrip("/") + "/" + route.lstrip("/")


def shoot(ctx, url, view, path, wait_for):
    page = ctx.new_page()
    page.goto(url, wait_until="load", timeout=45000)
    if wait_for:
        try:
            page.wait_for_selector(wait_for, timeout=10000)
        except Exception:  # noqa: BLE001
            pass
    for kind, val in view.get("steps") or [("wait", view.get("wait", 600))]:
        if kind == "click":
            page.click(val, timeout=5000)
            page.wait_for_timeout(300)
        else:
            page.wait_for_timeout(val)
    page.screenshot(path=str(path))
    page.close()


def main(argv=None):
    utf8_stdio()
    ap = argparse.ArgumentParser(description="视觉评审取证：截图 + 基准对照表 + 评审提示")
    ap.add_argument("target")
    ap.add_argument("--out", default="shots")
    ap.add_argument("--views", default="")
    ap.add_argument("--viewport", default="1440x900")
    ap.add_argument("--dark", action="store_true", help="额外截暗色（prefers-color-scheme: dark；页面需跟随系统或读取 ?theme=dark）")
    ap.add_argument("--mobile", action="store_true", help="额外截 390x844")
    ap.add_argument("--wait-for", default="")
    ap.add_argument("--archetype", default="")
    ap.add_argument("--bench-urls", default="", help="逗号分隔，覆盖默认基准")
    ap.add_argument("--no-bench", action="store_true")
    a = ap.parse_args(argv)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(json.dumps({"skipped": True, "reason": "未安装 playwright；请手动截图并按 visual/rubric.md 评审"}, ensure_ascii=False))
        return 0
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    base = a.target if "://" in a.target else Path(a.target).resolve().as_uri()
    w, h = (int(x) for x in a.viewport.split("x"))
    allarch = {x["id"]: x for x in json.loads((ROOT / "visual" / "archetypes.json").read_text(encoding="utf-8"))["archetypes"]}
    picked = [allarch[x] for x in a.archetype.split(",") if x in allarch]
    arch = picked[0] if picked else None
    bench = {b["id"]: b for b in json.loads((ROOT / "visual" / "benchmarks.json").read_text(encoding="utf-8"))["benchmarks"]}
    if a.bench_urls:
        benches = [(f"url{i + 1}", u) for i, u in enumerate(a.bench_urls.split(","))]
    elif picked and not a.no_bench:
        # 每个原型轮流取一个，保证次原型（签名所在）也有基准：主,次,主,次…，最多 4 个
        seen, benches = set(), []
        queues = [[b for b in ar["seed_benchmarks"] if b in bench and bench[b].get("capture_url")] for ar in picked]
        while len(benches) < 4 and any(queues):
            for q in queues:
                while q and q[0] in seen:
                    q.pop(0)
                if q and len(benches) < 4:
                    b = q.pop(0)
                    seen.add(b)
                    benches.append((b, bench[b]["capture_url"]))
    else:
        benches = []
    mine, refs, notes = [], [], []
    with sync_playwright() as p:
        kw = {"headless": True}
        if find_chrome():
            kw["executable_path"] = find_chrome()
        browser = p.chromium.launch(**kw)
        variants = [("light", {"viewport": {"width": w, "height": h}, "color_scheme": "light"})]
        if a.dark:
            variants.append(("dark", {"viewport": {"width": w, "height": h}, "color_scheme": "dark"}))
        if a.mobile:
            variants.append(("mobile", {"viewport": {"width": 390, "height": 844}, "color_scheme": "light", "is_mobile": True, "has_touch": True}))
        for tag, opts in variants:
            ctx = browser.new_context(**opts)
            for v in parse_views(a.views):
                f = out / f"{v['name']}-{tag}.png"
                try:
                    shoot(ctx, url_for(base, v["route"]), v, f, a.wait_for)
                    mine.append(f)
                except Exception as e:  # noqa: BLE001
                    notes.append(f"{v['name']}-{tag} 截图失败：{e.__class__.__name__}")
            ctx.close()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        for bid, url in benches:
            f = out / f"bench-{bid}.png"
            try:
                pg = ctx.new_page()
                pg.goto(url, wait_until="networkidle", timeout=45000)
                pg.wait_for_timeout(1500)
                pg.screenshot(path=str(f))
                pg.close()
                refs.append(f)
            except Exception as e:  # noqa: BLE001
                notes.append(f"基准 {bid} 截图失败：{e.__class__.__name__}（离线时可跳过，或手动打开 {url}）")
        ctx.close()
        cells = lambda fs: "".join(f'<figure><img src="{Path(x).resolve().as_uri()}"><figcaption>{html.escape(Path(x).name)}</figcaption></figure>' for x in fs)
        sheet = out / "_sheet.html"
        sheet.write_text(f"""<!doctype html><meta charset=utf-8><style>body{{margin:0;font:12px system-ui;background:#f4f4f5;display:grid;grid-template-columns:2fr 1fr;gap:12px;padding:12px}}
section{{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;align-content:start}}section.ref{{grid-template-columns:1fr}}figure{{margin:0;background:#fff;padding:4px;border-radius:6px}}
img{{width:100%;display:block}}h2{{grid-column:1/-1;margin:0}}</style><section><h2>你的页面</h2>{cells(mine)}</section><section class=ref><h2>基准</h2>{cells(refs)}</section>""", encoding="utf-8")
        ctx = browser.new_context(viewport={"width": 1600, "height": 900})
        pg = ctx.new_page()
        pg.goto(sheet.resolve().as_uri())
        pg.wait_for_timeout(500)
        pg.screenshot(path=str(out / "contact-sheet.png"), full_page=True)
        browser.close()
        sheet.unlink()
    (out / "review.md").write_text(REVIEW.format(archetype=a.archetype or "未指定", mode=arch["mode"] if arch else "?",
                                                  benches=", ".join(f"{b} {u}" for b, u in benches) or "无"), encoding="utf-8")
    print(json.dumps({"shots": [str(x) for x in mine], "benchmarks": [str(x) for x in refs], "contact_sheet": str(out / "contact-sheet.png"),
                      "review": str(out / "review.md"), "notes": notes}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
