#!/usr/bin/env python3
"""可选：真实浏览器检查（Playwright + 可选 axe-core）。缺依赖时输出 skipped JSON 并以 0 退出，不阻断流程。

检查项（与 rules.json 同一套 id）：
- co.low-contrast   用 getComputedStyle 计算真实前景/背景对比度（静态检查在复杂页面上的补充）
- tt.small-target   交互元素实际包围盒 <24×24px
- a11y.keyboard-trap / st.focus-removed  连续 Tab：焦点是否前进、是否有可见焦点样式
- axe:<rule>        若能加载 axe-core（本地 AXE_PATH 或 --axe-url），附带 axe 违规

- 多路由 / SPA：--routes "#/,#/runs,#/runs/38" 逐个检查；--wait-for <选择器> / --wait-ms 等真实内容渲染后再查（骨架屏不算）
- --color-scheme dark 检查暗色模式；--shots <目录> 每个路由截一张图（给 visual_capture / 视觉评分用）

用法：
  python3 scripts/browser_check.py page.html            # 或 http://localhost:5173
  python3 scripts/browser_check.py dist/index.html --routes "#/workflows,#/runs" --wait-for "main [data-ready]" --wait-ms 600
  python3 scripts/browser_check.py page.html --viewport 390x844 --axe-url https://cdn.jsdelivr.net/npm/axe-core@4/axe.min.js
安装（可选）：pip install playwright；使用本机 Chrome（CHROME_PATH）或 `playwright install chromium`。
"""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path

PAGE_JS = r"""
() => {
  const out = [];
  const parse = c => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; };
  const lum = c => { const f = x => { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
  const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
  const bgOf = el => { let layers = []; for (let n = el; n; n = n.parentElement) { const s = getComputedStyle(n);
      if (s.backgroundImage && s.backgroundImage !== 'none') return null;  // 图片/渐变：交给 axe/人工
      const c = parse(s.backgroundColor); if (c && c[3] > 0) { layers.push(c); if (c[3] >= 1) break; } }
    let base = [255, 255, 255]; for (const c of layers.reverse()) base = base.map((v, i) => v * (1 - c[3]) + c[i] * c[3]); return base; };
  const desc = el => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + ' "' + (el.innerText || el.getAttribute('aria-label') || '').trim().slice(0, 24) + '"';
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const seen = new Set();
  while (walker.nextNode()) { const t = walker.currentNode; const el = t.parentElement;
    if (!el || !t.textContent.trim() || seen.has(el)) continue; seen.add(el);
    const s = getComputedStyle(el); const r = el.getBoundingClientRect();
    if (s.visibility === 'hidden' || s.display === 'none' || r.width === 0 || r.height === 0) continue;
    const fg = parse(s.color); const bg = bgOf(el); if (!fg || !bg) continue;
    const fgc = fg.slice(0, 3).map((v, i) => v * fg[3] + bg[i] * (1 - fg[3]));
    const size = parseFloat(s.fontSize), bold = parseInt(s.fontWeight) >= 700;
    const need = size >= 24 || (bold && size >= 18.66) ? 3 : 4.5; const cr = ratio(fgc, bg);
    if (cr < need) out.push({rule: 'co.low-contrast', severity: 'major', element: desc(el), evidence: `computed ${cr.toFixed(2)}:1 < ${need}:1`}); }
  for (const el of document.querySelectorAll('button,a[href],input[type=checkbox],input[type=radio],[role=button],[role=switch],[role=tab],[onclick]')) {
    const r = el.getBoundingClientRect(); if (!r.width || !r.height) continue;
    if (el.tagName === 'A' && el.closest('p')) continue;
    if (Math.min(r.width, r.height) < 24) out.push({rule: 'tt.small-target', severity: 'major', element: desc(el), evidence: `${Math.round(r.width)}×${Math.round(r.height)}px < 24px`}); }
  return out;
}
"""

FOCUS_JS = r"""
() => { const el = document.activeElement; if (!el || el === document.body) return null;
  const s = getComputedStyle(el);
  const visible = (s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0) || (s.boxShadow && s.boxShadow !== 'none');
  return {tag: el.tagName.toLowerCase(), text: (el.innerText || el.getAttribute('aria-label') || '').trim().slice(0, 24), visible}; }
"""


def find_chrome():
    for c in (os.environ.get("CHROME_PATH"), shutil.which("google-chrome"), shutil.which("chromium"),
              shutil.which("chromium-browser"), r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
        if c and Path(c).exists():
            return c
    return None


def route_url(base, route):
    if not route:
        return base
    if route.startswith(("http://", "https://", "file:")):
        return route
    if route.startswith("#"):
        return base.split("#")[0] + route
    root = base.split("#")[0].rstrip("/")
    return root + ("" if route.startswith("/") else "/") + route


def check_page(page, a, w):
    findings, notes = [], []
    findings += page.evaluate(PAGE_JS)
    sw = page.evaluate("document.documentElement.scrollWidth")
    if sw > w + 1:
        findings.append({"rule": "ly.fixed-wide", "severity": "minor", "element": "document", "evidence": f"横向溢出：scrollWidth {sw}px > 视口 {w}px"})
    visited, invisible = [], []
    for _ in range(a.tabs):
        page.keyboard.press("Tab")
        f = page.evaluate(FOCUS_JS)
        if f is None:
            continue
        visited.append(f"{f['tag']}:{f['text']}")
        label = f"{f['tag']} \"{f['text']}\""
        if not f["visible"] and label not in invisible:
            invisible.append(label)
    focusable = page.evaluate("""() => [...document.querySelectorAll('a[href],button,input,select,textarea,[tabindex]')]
        .filter(e => !e.disabled && e.tabIndex >= 0 && e.getBoundingClientRect().width > 0).length""")
    if focusable > 1 and visited and len(set(visited)) == 1 and len(visited) > 2:
        findings.append({"rule": "a11y.keyboard-trap", "severity": "critical", "element": visited[0], "evidence": "连续 Tab 焦点不前进"})
    if invisible:
        findings.append({"rule": "st.focus-removed", "severity": "major", "element": invisible[0], "evidence": f"{len(invisible)} 个焦点位置无可见轮廓（outline/box-shadow）"})
    axe_src = a.axe_path or os.environ.get("AXE_PATH")
    try:
        if axe_src and Path(axe_src).exists():
            page.add_script_tag(path=axe_src)
        elif a.axe_url:
            page.add_script_tag(url=a.axe_url)
        if (axe_src and Path(axe_src).exists()) or a.axe_url:
            res = page.evaluate("async () => (await axe.run(document, {resultTypes: ['violations']})).violations.map(v => ({id: v.id, impact: v.impact, help: v.help, nodes: v.nodes.length, target: (v.nodes[0]||{}).target}))")
            for v in res:
                findings.append({"rule": "axe:" + v["id"], "severity": "major" if v["impact"] in ("serious", "critical") else "minor",
                                 "element": f"{v['nodes']} 个节点，如 {v.get('target')}", "evidence": v["help"]})
        else:
            notes.append("未加载 axe-core（设置 AXE_PATH / --axe-path 或 --axe-url 可启用）")
    except Exception as e:  # noqa: BLE001
        notes.append(f"axe-core 加载失败：{e.__class__.__name__}")
    return findings, notes


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            try:
                s.reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass
    ap = argparse.ArgumentParser(description="可选的真实浏览器 UI 检查")
    ap.add_argument("target", help="HTML 文件路径或 URL")
    ap.add_argument("--viewport", default="1280x800")
    ap.add_argument("--tabs", type=int, default=15, help="键盘 Tab 次数")
    ap.add_argument("--routes", default="", help="逗号分隔：#/hash、/path 或完整 URL；为空只查 target")
    ap.add_argument("--wait-for", default="", help="每个路由等待该 CSS 选择器出现（SPA 真实内容）")
    ap.add_argument("--wait-ms", type=int, default=400, help="额外等待毫秒（动画/骨架屏）")
    ap.add_argument("--color-scheme", choices=("light", "dark"), default="light")
    ap.add_argument("--shots", default="", help="截图输出目录（每个路由一张）")
    ap.add_argument("--axe-path", help="本地 axe.min.js 路径")
    ap.add_argument("--axe-url", help="axe-core 脚本 URL（可选，需要联网）")
    a = ap.parse_args(argv)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(json.dumps({"skipped": True, "reason": "未安装 playwright（pip install playwright）；已退回静态检查 ui_lint.py"}, ensure_ascii=False))
        return 0
    base = a.target if "://" in a.target else Path(a.target).resolve().as_uri()
    routes = [r.strip() for r in a.routes.split(",") if r.strip()] or [""]
    w, h = (int(x) for x in a.viewport.lower().split("x"))
    pages, all_notes = [], []
    with sync_playwright() as p:
        kw = {"headless": True}
        chrome = find_chrome()
        if chrome:
            kw["executable_path"] = chrome
        try:
            browser = p.chromium.launch(**kw)
        except Exception as e:  # noqa: BLE001
            print(json.dumps({"skipped": True, "reason": f"浏览器启动失败：{e.__class__.__name__}；设置 CHROME_PATH 或 playwright install chromium"}, ensure_ascii=False))
            return 0
        ctx = browser.new_context(viewport={"width": w, "height": h}, color_scheme=a.color_scheme)
        for i, r in enumerate(routes):
            page = ctx.new_page()
            errors = []
            page.on("pageerror", lambda e, errors=errors: errors.append(str(e)[:160]))
            url = route_url(base, r)
            page.goto(url, wait_until="load")
            note = []
            if a.wait_for:
                try:
                    page.wait_for_selector(a.wait_for, timeout=10000)
                except Exception:  # noqa: BLE001
                    note.append(f"等待 {a.wait_for} 超时，结果可能只覆盖骨架屏")
            page.wait_for_timeout(a.wait_ms)
            if a.shots:
                Path(a.shots).mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(Path(a.shots) / f"route-{i + 1}-{a.color_scheme}.png"))
            f, n = check_page(page, a, w)
            f += [{"rule": "st.missing-error", "severity": "major", "element": "console", "evidence": "页面脚本报错：" + e} for e in errors[:3]]
            pages.append({"route": r or "/", "url": url, "findings": f, "notes": note + n})
            page.close()
        browser.close()
    findings = [dict(x, route=pg["route"]) for pg in pages for x in pg["findings"]]
    verdict = "FAIL" if any(f["severity"] in ("critical", "major") for f in findings) else "PASS"
    out = {"target": a.target, "viewport": a.viewport, "color_scheme": a.color_scheme, "verdict": verdict,
           "findings": findings, "routes": [{"route": pg["route"], "count": len(pg["findings"]), "notes": pg["notes"]} for pg in pages]}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 2 if verdict == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
