#!/usr/bin/env python3
"""可选：真实浏览器检查（Playwright + 可选 axe-core）。缺依赖时输出 skipped JSON 并以 0 退出，不阻断流程。

检查项（与 rules.json 同一套 id）：
- co.low-contrast   用 getComputedStyle 计算真实前景/背景对比度（静态检查在复杂页面上的补充）
- tt.small-target   交互元素实际包围盒 <24×24px
- a11y.keyboard-trap / st.focus-removed  连续 Tab：焦点是否前进、是否有可见焦点样式
- axe:<rule>        若能加载 axe-core（本地 AXE_PATH 或 --axe-url），附带 axe 违规

用法：
  python3 scripts/browser_check.py page.html            # 或 http://localhost:5173
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
    ap.add_argument("--axe-url", help="axe-core 脚本 URL（可选，需要联网）")
    a = ap.parse_args(argv)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(json.dumps({"skipped": True, "reason": "未安装 playwright（pip install playwright）；已退回静态检查 ui_lint.py"}, ensure_ascii=False))
        return 0
    url = a.target if "://" in a.target else Path(a.target).resolve().as_uri()
    w, h = (int(x) for x in a.viewport.lower().split("x"))
    findings, notes = [], []
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
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(url, wait_until="load")
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
        axe_src = os.environ.get("AXE_PATH")
        try:
            if axe_src and Path(axe_src).exists():
                page.add_script_tag(path=axe_src)
            elif a.axe_url:
                page.add_script_tag(url=a.axe_url)
            if axe_src or a.axe_url:
                res = page.evaluate("async () => (await axe.run(document, {resultTypes: ['violations']})).violations.map(v => ({id: v.id, impact: v.impact, help: v.help, nodes: v.nodes.length}))")
                for v in res:
                    findings.append({"rule": "axe:" + v["id"], "severity": "major" if v["impact"] in ("serious", "critical") else "minor", "element": f"{v['nodes']} 个节点", "evidence": v["help"]})
            else:
                notes.append("未加载 axe-core（设置 AXE_PATH 或 --axe-url 可启用）")
        except Exception as e:  # noqa: BLE001
            notes.append(f"axe-core 加载失败：{e.__class__.__name__}")
        browser.close()
    verdict = "FAIL" if any(f["severity"] in ("critical", "major") for f in findings) else "PASS"
    print(json.dumps({"target": a.target, "viewport": a.viewport, "verdict": verdict, "findings": findings, "notes": notes}, ensure_ascii=False, indent=2))
    return 2 if verdict == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
