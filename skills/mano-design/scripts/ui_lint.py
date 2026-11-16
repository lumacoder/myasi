#!/usr/bin/env python3
"""Mano-Design 静态 UI 交互检查器（纯标准库）。

输入 HTML / JSX 片段或完整页面，输出结构化 JSON：rule / severity / element / evidence / fix。
规则元数据（标题、严重级、修复建议）唯一来源：rules/rules.json（detect=lint 的条目）。
检查器只看代码本身，不读取文件名、测试清单或期望结果。

用法：
  python3 scripts/ui_lint.py page.html [more.html ...]       # JSON 报告
  python3 scripts/ui_lint.py --stdin < snippet.html
  python3 scripts/ui_lint.py --format text src/App.jsx
退出码：0=PASS，2=存在 critical/major（FAIL），1=输入错误。
"""
import argparse
import colorsys
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCKING = {"critical", "major"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
NAMED = {"white": "#ffffff", "black": "#000000", "gray": "#808080", "grey": "#808080", "silver": "#c0c0c0",
         "red": "#ff0000", "green": "#008000", "blue": "#0000ff", "yellow": "#ffff00", "orange": "#ffa500",
         "purple": "#800080", "pink": "#ffc0cb", "lightgray": "#d3d3d3", "lightgrey": "#d3d3d3",
         "darkgray": "#a9a9a9", "whitesmoke": "#f5f5f5", "gainsboro": "#dcdcdc", "navy": "#000080",
         "teal": "#008080", "violet": "#ee82ee", "indigo": "#4b0082", "magenta": "#ff00ff", "cyan": "#00ffff"}

BINARY_PAIRS = [{"开", "关"}, {"开启", "关闭"}, {"打开", "关闭"}, {"启用", "禁用"}, {"启用", "停用"},
                {"on", "off"}, {"yes", "no"}, {"是", "否"}, {"enabled", "disabled"}, {"enable", "disable"},
                {"true", "false"}, {"显示", "隐藏"}, {"show", "hide"}, {"允许", "禁止"}, {"允许", "不允许"},
                {"接收", "不接收"}, {"开通", "关闭"}, {"active", "inactive"}]
PLACEHOLDER_OPT = re.compile(r"^(请选择|选择|--|—|select|choose|please select)", re.I)
METRIC_BOX = re.compile(r"(metric|kpi|stat|tile|card)", re.I)
VALUE_CLS = re.compile(r"(value|num|number|figure|amount)", re.I)
PLACEHOLDER_VAL = re.compile(r"^(—|–|-|--|——|N/?A|null|TBD|未启用|暂无|暂无数据|无数据|未知|待接入|未配置)$", re.I)
OPAQUE_ID = re.compile(r"(?<![\w…])[A-Za-z][A-Za-z0-9]*[_-][A-Za-z0-9_-]{4,}(…|\.{3})(?=\s|$)")
QUESTION = re.compile(r"[?？]|^(如何|怎么|怎样|为什么|为何|什么|能否|是否|可以|可否|我能|我可以|how|what|why|can|do|does|is|are|when|where)\b", re.I)
DESTRUCTIVE = re.compile(r"删除|移除|清空|注销|销毁|永久|delete|remove|erase|destroy|clear all|reset all", re.I)
VAGUE_DIALOG_BTN = {"确定", "确认", "是", "好", "好的", "ok", "yes", "确定删除?"}
VAGUE_LINK = {"点击这里", "点这里", "这里", "点此", "请点击", "点击此处", "click here", "here", "click", "this link"}
VAGUE_ERROR = {"出错了", "错误", "发生错误", "操作失败", "失败", "系统错误", "未知错误", "网络错误", "error",
               "something went wrong", "an error occurred", "error occurred", "oops", "oops something went wrong"}
CLICHES_ZH = ["赋能", "一站式", "全方位", "极致体验", "无缝", "革命性", "颠覆", "释放潜力", "释放无限", "开启全新",
              "之旅", "打造生态", "全链路", "引领未来", "智慧赋能", "重新定义", "下一代", "前所未有", "触手可及",
              "让一切", "尽在掌握", "助力", "一键开启"]
CLICHES_EN = ["unlock", "elevate", "seamless", "revolutioniz", "empower", "supercharge", "in today's fast-paced",
              "welcome to the future", "next-generation", "game-chang", "cutting-edge", "unleash", "effortless",
              "transform the way", "take your", "to the next level", "like never before"]
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2728\u26A1\u2B50\u2705\u274C\U0001F680]")
LOADING_HINT = re.compile(r"disabled|aria-busy|loading|spinner|skeleton|加载|中…|中\.\.\.|isPending|pending", re.I)
EMPTY_HINT = re.compile(r"暂无|还没有|没有找到|无数据|空空|empty|no (results|data|items|records)|nothing (here|yet)| yet\b", re.I)
DATE_HINT = re.compile(r"日期|生日|出生|date|birthday|dob|yyyy|mm/dd|dd/mm|年-月-日", re.I)
NUMERIC = re.compile(r"^[\d.,]+\s*(%|px|元|岁|kg|分钟|min|小时|h|个|人)?$", re.I)
JS_NAV = re.compile(r"location\s*(\.href)?\s*=|location\.assign|router\.push|navigate\(|window\.open", re.I)
ASYNC = re.compile(r"\bfetch\(|axios|XMLHttpRequest|\bawait\b|\.then\(", re.I)


def load_rules():
    data = json.loads((ROOT / "rules" / "rules.json").read_text(encoding="utf-8"))
    return {r["id"]: r for r in data["rules"]}


# ---------------- DOM ----------------
class Node:
    __slots__ = ("tag", "attrs", "children", "parent", "line", "text_parts")

    def __init__(self, tag, attrs, parent, line):
        self.tag, self.attrs, self.parent, self.line = tag, attrs, parent, line
        self.children, self.text_parts = [], []

    def get(self, k, d=None):
        return self.attrs.get(k, d)

    @property
    def classes(self):
        return set((self.attrs.get("class") or "").split())

    def iter(self):
        for c in self.children:
            yield c
            yield from c.iter()

    def ancestors(self):
        p = self.parent
        while p is not None and p.tag != "#root":
            yield p
            p = p.parent

    def text(self):
        out = list(self.text_parts)
        for c in self.children:
            if c.tag not in ("script", "style"):
                out.append(c.text())
        return re.sub(r"\s+", " ", " ".join(out)).strip()

    def own_text(self):
        return re.sub(r"\s+", " ", " ".join(self.text_parts)).strip()

    def desc(self):
        bits = [self.tag]
        if self.get("id"):
            bits.append("#" + self.get("id"))
        if self.get("class"):
            bits.append("." + ".".join(sorted(self.classes))[:40])
        t = self.text()[:24]
        return "".join(bits) + (f' "{t}"' if t else "") + f" (line {self.line})"


class Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None, 0)
        self.cur = self.root
        self.styles, self.scripts = [], []
        self._raw = None

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v if v is not None else "") for k, v in attrs}
        if "classname" in a:
            a["class"] = a.pop("classname")
        if "htmlfor" in a:
            a["for"] = a.pop("htmlfor")
        n = Node(tag, a, self.cur, self.getpos()[0])
        self.cur.children.append(n)
        if tag in ("style", "script"):
            self._raw = (tag, [])
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID and self.cur.tag == tag:
            self.cur = self.cur.parent

    def handle_endtag(self, tag):
        if self._raw and tag == self._raw[0]:
            (self.styles if tag == "style" else self.scripts).append("".join(self._raw[1]))
            self._raw = None
        n = self.cur
        while n is not None and n.tag != "#root":
            if n.tag == tag:
                self.cur = n.parent
                return
            n = n.parent

    def handle_data(self, data):
        if self._raw:
            self._raw[1].append(data)
            return
        if data.strip():
            self.cur.text_parts.append(data)


def jsx_to_html(src):
    """把 JSX 近似为 HTML：{表达式} 属性值转字符串，{/* */} 注释删除。"""
    src = re.sub(r"\{/\*.*?\*/\}", "", src, flags=re.S)
    out, i = [], 0
    while i < len(src):
        if src[i] == "=" and i + 1 < len(src) and src[i + 1] == "{":
            depth, j = 0, i + 1
            while j < len(src):
                depth += src[j] == "{"
                depth -= src[j] == "}"
                if depth == 0:
                    break
                j += 1
            val = src[i + 2:j].replace('"', "'").replace("<", " ").replace(">", " ")
            out.append('="' + val + '"')
            i = j + 1
            continue
        out.append(src[i])
        i += 1
    return "".join(out)


# ---------------- CSS ----------------
def parse_css(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    rules, media = [], []
    for m in re.finditer(r"@media([^{]*)\{((?:[^{}]*\{[^{}]*\})*)\s*\}", text):
        media.append(m.group(1).strip())
        for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", m.group(2)):
            rules.append((sel.strip(), decls(body), m.group(1).strip()))
    rest = re.sub(r"@media[^{]*\{(?:[^{}]*\{[^{}]*\})*\s*\}", "", text)
    rest = re.sub(r"@keyframes[^{]*\{(?:[^{}]*\{[^{}]*\})*\s*\}", "", rest)
    for sel, body in re.findall(r"([^{}@]+)\{([^{}]*)\}", rest):
        rules.append((sel.strip(), decls(body), None))
    return rules, media


def decls(body):
    d = {}
    for part in body.split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            d[k.strip().lower()] = v.strip().lower().replace("!important", "").strip()
    return d


def compound_matches(node, comp):
    comp = re.split(r":", comp, maxsplit=1)[0]
    if not comp or comp == "*":
        return comp == "*"
    m = re.match(r"^([a-z][a-z0-9-]*)?((?:[.#][\w-]+|\[[^\]]+\])*)$", comp, re.I)
    if not m:
        return False
    tag, rest = m.group(1), m.group(2)
    if tag and tag.lower() != node.tag:
        return False
    for kind, name in re.findall(r"([.#])([\w-]+)", re.sub(r"\[[^\]]+\]", "", rest)):
        if kind == "." and name not in node.classes:
            return False
        if kind == "#" and node.get("id") != name:
            return False
    for attr in re.findall(r"\[([^\]=]+)(?:=[\"']?([^\"'\]]+)[\"']?)?\]", rest):
        if attr[0] not in node.attrs or (attr[1] and node.get(attr[0]) != attr[1]):
            return False
    return bool(tag or rest)


def selector_matches(node, sel):
    parts = sel.replace(">", " ").split()
    if not parts or not compound_matches(node, parts[-1]):
        return False
    anc = list(node.ancestors())
    for comp in reversed(parts[:-1]):
        while anc and not compound_matches(anc[0], comp):
            anc.pop(0)
        if not anc:
            return False
        anc.pop(0)
    return True


class Styles:
    def __init__(self, css_rules):
        self.rules = [(s.strip(), d) for sel, d, med in css_rules if med is None or "dark" not in med
                      for s in sel.split(",") if ":" not in s or ":root" in s]
        self.vars = {k: v for _, d in self.rules for k, v in d.items() if k.startswith("--")}
        self.cache = {}

    def resolve(self, v, depth=0):
        """解析 var(--x, fallback)；无法解析返回 None（视为未知，不做判断）。"""
        if v is None or "var(" not in v:
            return v
        if depth > 8:
            return None
        m = re.search(r"var\(\s*(--[\w-]+)\s*(?:,\s*([^()]*(?:\([^()]*\))?[^()]*))?\)", v)
        if not m:
            return None
        val = self.vars.get(m.group(1), m.group(2))
        if val is None:
            return None
        return self.resolve(v[:m.start()] + val.strip() + v[m.end():], depth + 1)

    def of(self, node):
        if id(node) in self.cache:
            return self.cache[id(node)]
        st = {}
        for sel, d in self.rules:
            if sel == ":root" or not selector_matches(node, sel):
                continue
            st.update(d)
        st.update(decls(node.get("style") or ""))
        self.cache[id(node)] = st
        return st


# ---------------- Color ----------------
def parse_color(v):
    if not v:
        return None
    v = v.strip().lower()
    m = re.search(r"#([0-9a-f]{3,8})\b", v)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        if len(h) not in (6, 8):
            return None
        a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)
    m = re.search(r"rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:\s*[,/]\s*([\d.]+%?))?", v)
    if m:
        a = m.group(4)
        a = 1.0 if a is None else (float(a[:-1]) / 100 if a.endswith("%") else float(a))
        return (float(m.group(1)), float(m.group(2)), float(m.group(3)), a)
    m = re.search(r"hsla?\(\s*([\d.]+)(?:deg)?[,\s]+([\d.]+)%[,\s]+([\d.]+)%(?:\s*[,/]\s*([\d.]+))?", v)
    if m:
        r, g, b = colorsys.hls_to_rgb(float(m.group(1)) / 360, float(m.group(3)) / 100, float(m.group(2)) / 100)
        return (r * 255, g * 255, b * 255, float(m.group(4) or 1))
    for word in re.findall(r"[a-z]+", v):
        if word in NAMED:
            return parse_color(NAMED[word])
    return None


def all_colors(v):
    found = re.findall(r"#[0-9a-f]{3,8}\b|rgba?\([^)]*\)|hsla?\([^)]*\)", v or "", re.I)
    return [c for c in (parse_color(x) for x in found) if c]


def blend(fg, bg):
    a = fg[3]
    return tuple(fg[i] * a + bg[i] * (1 - a) for i in range(3)) + (1.0,)


def lum(c):
    def ch(x):
        x /= 255
        return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def hsl(c):
    h, l, s = colorsys.rgb_to_hls(c[0] / 255, c[1] / 255, c[2] / 255)
    return h * 360, s, l


def px(v):
    if not v:
        return None
    m = re.match(r"^\s*([\d.]+)\s*(px|rem|em)?\s*$", v)
    if not m:
        return None
    n = float(m.group(1))
    return n * 16 if m.group(2) in ("rem", "em") else n


def visual_len(t):
    """CJK/全角字符按 2 个半角宽计算，近似行长。"""
    return sum(2 if ord(ch) > 0x2E7F else 1 for ch in t)


def ms(v):
    out = []
    for n, unit in re.findall(r"([\d.]+)\s*(ms|s)\b", v or ""):
        out.append(float(n) * (1 if unit == "ms" else 1000))
    return out


# ---------------- Linter ----------------
class Linter:
    def __init__(self, src, rules):
        self.meta = rules
        self.findings = []
        b = Builder()
        b.feed(src)
        b.close()
        self.root, self.src = b.root, src
        self.nodes = list(self.root.iter())
        css_text = "\n".join(b.styles)
        self.css_rules, self.media = parse_css(css_text)
        self.css_text = css_text.lower()
        self.all_style = (self.css_text + " " + " ".join((n.get("style") or "") for n in self.nodes)).lower()
        self.script = "\n".join(b.scripts) + " " + " ".join(
            v for n in self.nodes for k, v in n.attrs.items() if k.startswith("on"))
        self.styles = Styles(self.css_rules)
        self.doc_text = self.root.text()

    def add(self, rule, node, evidence, severity=None):
        m = self.meta[rule]
        self.findings.append({"rule": rule, "severity": severity or m["severity"], "category": m["category"],
                              "title": m["title_zh"], "element": node.desc() if node else None,
                              "line": node.line if node else None, "evidence": evidence, "fix": m["fix_zh"]})

    def run(self):
        for name in sorted(n for n in dir(self) if n.startswith("check_")):
            getattr(self, name)()
        seen, out = set(), []
        for f in self.findings:
            key = (f["rule"], f["line"], f["evidence"])
            if key not in seen:
                seen.add(key)
                out.append(f)
        self.findings = out
        return out

    # ---- helpers
    def options(self, sel):
        opts = []
        for n in sel.iter():
            if n.tag in ("option", "selectitem", "menuitem") or n.get("role") == "option":
                t = (n.text() or n.get("label") or n.get("value") or "").strip()
                if n.get("disabled") is not None and n.get("value", "x") == "":
                    continue
                if n.get("value") == "" or PLACEHOLDER_OPT.match(t) or not t:
                    continue
                opts.append(t)
        return opts

    def select_like(self):
        for n in self.nodes:
            if n.tag in ("select", "dropdown") or n.get("role") in ("listbox", "combobox") or \
                    any(c in ("dropdown", "select", "dropdown-menu") for c in n.classes):
                if n.tag == "select" or n.get("role") or n.classes:
                    yield n

    def label_of(self, n):
        return (n.get("aria-label") or n.get("title") or n.text() or n.get("value") or "").strip()

    def interactive(self, n):
        return n.tag in ("button", "a", "select", "textarea") or n.get("role") in ("button", "link", "tab", "switch", "checkbox") \
            or (n.tag == "input" and (n.get("type") or "text") not in ("hidden",)) or "onclick" in n.attrs

    # ---- component
    def check_cs_selects(self):
        for n in self.select_like():
            if any(a.tag == "select" for a in n.ancestors()):
                continue
            opts = self.options(n)
            norm = {o.strip().lower() for o in opts}
            multiple = n.get("multiple") is not None or n.get("aria-multiselectable") == "true"
            if len(opts) == 2 and any(norm == p for p in BINARY_PAIRS):
                self.add("cs.binary-select", n, f"下拉只有两个二值选项：{' / '.join(opts)}")
                continue
            if multiple and n.tag == "select":
                if len(opts) <= 7:
                    self.add("cs.multi-select-native", n, f"select multiple，{len(opts)} 个选项")
                else:
                    self.add("cs.multi-select-native", n, f"select multiple，{len(opts)} 个选项需 Ctrl/⌘ 多选")
                continue
            if len(opts) >= 8 and all(NUMERIC.match(o) for o in opts):
                self.add("cs.numeric-select", n, f"{len(opts)} 个连续数值选项：{opts[0]}…{opts[-1]}")
                continue
            if len(opts) > 15 and not n.get("list") and n.tag == "select":
                self.add("cs.long-select-no-search", n, f"{len(opts)} 个选项，无搜索")
                continue
            if 3 <= len(opts) <= 5 and n.tag == "select":
                self.add("cs.few-options-select", n, f"仅 {len(opts)} 个互斥选项：{' / '.join(opts)}")

    def accordion_items(self, parent):
        items = []
        for c in parent.children:
            label, panel = None, None
            if c.tag == "details":
                s = next((x for x in c.children if x.tag == "summary"), None)
                label = s.text() if s else None
                panel = c
            elif c.tag in ("accordionitem", "collapsible", "accordion-item", "collapse-item", "el-collapse-item", "a-collapse-panel"):
                trig = next((x for x in c.iter() if x.tag in ("accordiontrigger", "summary", "button")), None)
                label = c.get("title") or c.get("header") or c.get("label") or (trig.text() if trig else c.get("value"))
                panel = c
            else:
                trig = next((x for x in c.iter() if x.get("aria-expanded") is not None and x.tag != "a"), None)
                if trig is not None and not any(x.get("role") == "tab" for x in c.iter()):
                    label, panel = trig.text(), c
                elif {"accordion-item", "collapse-item", "panel"} & c.classes and c.children:
                    label, panel = c.children[0].text(), c
            if label is not None:
                items.append((c, label.strip(), panel))
        return items

    def check_cs_peer_views(self):
        for parent in [self.root] + self.nodes:
            items = self.accordion_items(parent)
            if not 2 <= len(items) <= 6:
                continue
            labels = [l for _, l, _ in items]
            short = all(0 < len(l) <= 12 and len(l.split()) <= 3 for l in labels)
            questions = any(QUESTION.search(l) for l in labels)
            filters = sum(1 for _, _, p in items if any(
                x.tag == "input" and (x.get("type") in ("checkbox", "radio", "range")) for x in p.iter()))
            if short and not questions and filters < len(items) / 2:
                self.add("cs.peer-views-accordion", items[0][0],
                         f"{len(items)} 个同级视图做成纵向展开：{' / '.join(labels)}")

    def radio_label(self, r):
        lab = next((a for a in r.ancestors() if a.tag == "label"), None)
        if lab is None and r.get("id"):
            lab = next((l for l in self.nodes if l.tag == "label" and l.get("for") == r.get("id")), None)
        return (lab.text() if lab is not None else r.get("aria-label") or r.get("value") or "").strip()

    def group_question(self, first):
        """取单选组的组标题（legend/aria-label）；问句说明是问卷题而非设置项。"""
        for a in first.ancestors():
            if a.tag == "fieldset":
                lg = next((x for x in a.children if x.tag == "legend"), None)
                return lg.text() if lg else ""
            if a.get("role") in ("radiogroup", "group"):
                return a.get("aria-label") or ""
        return ""

    def check_cs_radios(self):
        groups = {}
        for n in self.nodes:
            if n.tag == "input" and n.get("type") == "radio" and n.get("name"):
                groups.setdefault(n.get("name"), []).append(n)
        for name, g in groups.items():
            if len(g) > 7:
                self.add("cs.many-radios", g[0], f"name={name} 平铺 {len(g)} 个单选")
            if len(g) == 2:
                labels = [self.radio_label(r) for r in g]
                norm = {l.lower() for l in labels}
                has_state = any(r.get("checked") is not None for r in g)
                if any(norm == p for p in BINARY_PAIRS) and has_state and not QUESTION.search(self.group_question(g[0])):
                    self.add("cs.binary-select", g[0], f"二值设置做成两个单选：{' / '.join(labels)}")

    def check_cs_pressed_pair(self):
        for parent in self.nodes:
            btns = [c for c in parent.children if c.tag == "button" and c.get("aria-pressed") is not None]
            if len(btns) == 2 and len([c for c in parent.children if c.tag == "button"]) == 2:
                labels = [self.label_of(b) for b in btns]
                if any({l.lower() for l in labels} == p for p in BINARY_PAIRS):
                    self.add("cs.binary-select", parent, f"二值设置做成按钮组：{' / '.join(labels)}")

    def check_cs_date(self):
        labels = {l.get("for"): l.text() for l in self.nodes if l.tag == "label" and l.get("for")}
        for n in self.nodes:
            if n.tag == "input" and (n.get("type") or "text") == "text":
                blob = " ".join([n.get("name", ""), n.get("id", ""), n.get("placeholder", ""),
                                 n.get("aria-label", ""), labels.get(n.get("id"), ""),
                                 next((a.text() for a in n.ancestors() if a.tag == "label"), "")])
                if DATE_HINT.search(blob):
                    self.add("cs.date-as-text", n, f"日期字段用 type=text：{blob.strip()[:40]}")

    def has_confirm(self, n):
        blob = " ".join(v for k, v in n.attrs.items() if k.startswith("on") or k.startswith("data-") or k.startswith("aria-"))
        if re.search(r"confirm|dialog|modal|undo|撤销", blob, re.I) or n.get("aria-haspopup") in ("dialog", "true"):
            return True
        if any(a.tag == "dialog" or a.get("role") in ("dialog", "alertdialog") for a in n.ancestors()):
            return True
        return False

    def check_cs_destructive(self):
        page_guard = bool(re.search(r"\bconfirm\(|showModal\(|alertdialog|撤销|undo", self.script + self.src, re.I))
        for n in self.nodes:
            if n.tag == "button" or n.get("role") == "button":
                t = self.label_of(n)
                if t and DESTRUCTIVE.search(t) and len(t) <= 20 and not self.has_confirm(n) and not page_guard:
                    self.add("cs.destructive-no-confirm", n, f"危险操作「{t}」直接执行，无确认/撤销")

    def check_cs_dialog_buttons(self):
        for d in self.nodes:
            if d.tag == "dialog" or d.get("role") in ("dialog", "alertdialog"):
                if not DESTRUCTIVE.search(d.text()):
                    continue
                for b in d.iter():
                    if b.tag == "button" and self.label_of(b).strip("！!。. ").lower() in VAGUE_DIALOG_BTN:
                        self.add("cs.dialog-vague-buttons", b, f"危险确认框按钮只写「{self.label_of(b)}」")

    def check_cs_long_form(self):
        for f in self.nodes:
            if f.tag != "form":
                continue
            fields = [n for n in f.iter() if n.tag in ("select", "textarea") or
                      (n.tag == "input" and (n.get("type") or "text") not in ("hidden", "submit", "button", "reset"))]
            grouped = any(n.tag in ("fieldset", "h2", "h3", "h4", "legend") or n.get("aria-current") == "step"
                          or any("step" in c for c in n.classes) for n in f.iter())
            if len(fields) >= 12 and not grouped:
                self.add("cs.long-form-ungrouped", f, f"{len(fields)} 个字段平铺，无分组/分步")

    def check_cs_clickables(self):
        for n in self.nodes:
            if "onclick" in n.attrs and n.tag in ("div", "span", "li", "img", "td", "p", "section", "article"):
                if not n.get("role") and n.get("tabindex") is None:
                    self.add("cs.clickable-div", n, f"<{n.tag} onclick> 无 role/tabindex")
            if n.tag == "button" and JS_NAV.search(n.get("onclick", "")):
                self.add("cs.button-as-link", n, f"按钮用脚本跳转：{n.get('onclick')[:40]}")

    def check_cs_stat_filter(self):
        # 统计卡/状态块兼做筛选：带筛选数据属性的兄弟元素却没有按钮/标签页语义
        clicky = re.search(r"addEventListener\(\s*['\"]click|onclick|@click|onClick", self.script + self.src)
        groups = {}
        for n in self.nodes:
            keys = [k for k in n.attrs if k.startswith("data-filter") or (k in ("data-status", "data-tab", "data-view") and clicky)]
            if not keys or n.tag in ("button", "a", "input", "select", "option", "label", "tr", "td", "th"):
                continue
            if n.get("role") in ("tab", "button", "radio", "option", "checkbox", "link", "menuitem", "menuitemradio", "switch") \
                    or n.get("tabindex") is not None:
                continue
            groups.setdefault(id(n.parent), []).append(n)
        for g in groups.values():
            if len(g) >= 2:
                self.add("cs.stat-card-filter", g[0], f"{len(g)} 个 <{g[0].tag}> 带筛选属性（{', '.join(k for k in g[0].attrs if k.startswith('data-'))}）却无按钮/tab 语义")

    # ---- state
    def check_st_focus(self):
        removed = re.search(r"outline\s*:\s*(none|0)\b", self.all_style)
        visible = re.search(r":focus-visible|:focus-within|:focus\s*[{,]", self.css_text) and \
            re.search(r":focus[^{]*\{[^}]*(outline|box-shadow|border|ring)", self.css_text)
        if removed and not visible:
            self.add("st.focus-removed", None, "样式中有 outline:none/0，且没有 :focus-visible 替代样式")

    def check_st_hover(self):
        styled = any(re.search(r"(^|[\s,>])(button|a)(?![\w-])|\.btn[\w-]*", sel) and
                     any(k in d for k in ("background", "background-color", "color", "border"))
                     for sel, d, _ in self.css_rules if ":" not in sel)
        if styled and ":hover" not in self.css_text and ":focus" not in self.css_text:
            self.add("st.no-hover-focus", None, "自定义按钮/链接样式缺少 :hover 与 :focus 状态")

    def check_st_loading(self):
        if ASYNC.search(self.script) and not LOADING_HINT.search(self.src):
            self.add("st.missing-loading", None, "存在异步请求，但没有禁用/加载/aria-busy 等加载态线索")

    def check_st_empty(self):
        if EMPTY_HINT.search(self.src):
            return
        for n in self.nodes:
            if n.tag == "tbody" and not any(c.tag == "tr" for c in n.children):
                self.add("st.missing-empty", n, "空 tbody，没有空状态说明")
            if n.tag in ("ul", "ol") and not n.children and not n.text():
                self.add("st.missing-empty", n, f"空 <{n.tag}>，没有空状态说明")

    def check_st_motion(self):
        if re.search(r"transition(-property)?\s*:\s*all\b", self.all_style):
            self.add("st.transition-all", None, "使用 transition: all")
        for m in re.finditer(r"transition(?:-duration)?\s*:\s*([^;}\"]+)", self.all_style):
            slow = [d for d in ms(m.group(1)) if d > 500]
            if slow:
                self.add("st.slow-transition", None, f"过渡时长 {int(max(slow))}ms：{m.group(0)[:50]}")
                break
        if re.search(r"@keyframes|animation\s*:", self.all_style) and "prefers-reduced-motion" not in self.all_style:
            self.add("st.no-reduced-motion", None, "有动画但没有 prefers-reduced-motion 适配")

    # ---- a11y
    def check_tt_targets(self):
        for n in self.nodes:
            itype = (n.get("type") or "").lower()
            if not (n.tag == "button" or n.get("role") in ("button", "switch", "checkbox", "tab") or
                    (n.tag == "a" and not any(a.tag == "p" for a in n.ancestors())) or
                    (n.tag == "input" and itype in ("checkbox", "radio", "button", "submit"))):
                continue
            st = self.styles.of(n)
            w = max(filter(None, [px(st.get("width")), px(st.get("min-width"))]), default=None)
            h = max(filter(None, [px(st.get("height")), px(st.get("min-height"))]), default=None)
            pad = px(st.get("padding")) or 0
            dims = [d + 2 * pad for d in (w, h) if d is not None]
            if dims and min(dims) < 24:
                self.add("tt.small-target", n, f"点击区域约 {int(min(dims))}px < 24px")

    def check_a11y_labels(self):
        label_for = {l.get("for") for l in self.nodes if l.tag == "label"}
        for n in self.nodes:
            itype = (n.get("type") or "text").lower()
            if n.tag in ("select", "textarea") or (n.tag == "input" and itype not in ("hidden", "submit", "button", "reset", "image")):
                if n.tag == "select" and any(a.tag == "select" for a in n.ancestors()):
                    continue
                ok = (n.get("id") in label_for and n.get("id")) or n.get("aria-label") or n.get("aria-labelledby") \
                    or n.get("title") or any(a.tag == "label" for a in n.ancestors())
                if not ok:
                    self.add("a11y.input-no-label", n, f"<{n.tag} type={itype}> 无标签" +
                             ("（仅有 placeholder）" if n.get("placeholder") else ""))

    def check_a11y_names(self):
        for n in self.nodes:
            if n.tag == "button" or (n.get("role") == "button"):
                t = re.sub(r"[\s]", "", n.text())
                if n.get("aria-label") or n.get("aria-labelledby") or n.get("title"):
                    continue
                if len(t) == 0 or (len(t) <= 2 and not re.search(r"[\w\u4e00-\u9fff]", t)):
                    self.add("a11y.icon-button-no-name", n, f"按钮无可访问名称（内容：{t or '仅图标'}）")
            if n.tag == "img" and "alt" not in n.attrs:
                self.add("a11y.img-no-alt", n, "img 缺少 alt")

    # ---- color
    def resolved(self, n, prop):
        for x in [n] + list(n.ancestors()):
            st = self.styles.of(x)
            if prop == "color" and st.get("color"):
                v = self.styles.resolve(st["color"])
                return (parse_color(v) if v else None), True
            if prop == "bg":
                raw = st.get("background-color") or st.get("background")
                v = self.styles.resolve(raw)
                if raw and v is None:
                    return None, True
                c = parse_color(v) if v and "gradient" not in (v or "") and "url(" not in (v or "") else None
                if v and "gradient" in v:
                    cs = all_colors(v)
                    if cs:
                        c = min(cs, key=lambda c_: -contrast(c_, (0, 0, 0)))  # 取最亮色作为保守背景
                if c:
                    return c, True
        return ((0, 0, 0, 1.0) if prop == "color" else (255, 255, 255, 1.0)), False

    def check_co_contrast(self):
        done = set()
        for n in self.nodes:
            if n.tag in ("script", "style", "head", "title", "option") or not n.own_text():
                continue
            fg, fset = self.resolved(n, "color")
            bg, bset = self.resolved(n, "bg")
            if not (fset or bset) or fg is None or bg is None:
                continue
            bg_s = bg if bg[3] >= 1 else blend(bg, (255, 255, 255, 1))
            fg_s = blend(fg, bg_s) if fg[3] < 1 else fg
            st = self.styles.of(n)
            size = px(st.get("font-size")) or {"h1": 32, "h2": 24, "h3": 18.7}.get(n.tag, 16)
            bold = (st.get("font-weight") in ("bold", "600", "700", "800", "900")) or n.tag in ("h1", "h2", "h3", "strong", "b")
            need = 3.0 if size >= 24 or (bold and size >= 18.66) else 4.5
            ratio = contrast(fg_s, bg_s)
            key = (round(ratio, 2), n.own_text()[:10])
            if ratio < need and key not in done:
                done.add(key)
                self.add("co.low-contrast", n, f"对比度 {ratio:.2f}:1 < {need}:1（{int(size)}px）")

    def check_co_palette(self):
        buckets, purple_grad = set(), None
        for m in re.finditer(r"(color|background(?:-color)?|border(?:-color)?|fill|stroke)\s*:\s*([^;}\"]+)", self.all_style):
            for c in all_colors(m.group(2)) + ([parse_color(m.group(2))] if not all_colors(m.group(2)) else []):
                if not c:
                    continue
                h, s, l = hsl(c)
                if s > 0.25 and 0.12 < l < 0.92:
                    buckets.add(int(h // 30))
        if len(buckets) >= 5:
            self.add("co.palette-sprawl", None, f"有彩色相分布在 {len(buckets)} 个 30° 区间")
        for m in re.finditer(r"gradient\(([^;}\"]+)", self.all_style):
            hs = [hsl(c) for c in all_colors(m.group(1))]
            chroma = [h for h, s, l in hs if s > 0.3 and 0.15 < l < 0.9]
            if any(255 <= h <= 300 for h in chroma) and any(min(abs(h - p), 360 - abs(h - p)) >= 25 for h in chroma for p in chroma):
                purple_grad = m.group(0)[:60]
                break
        if purple_grad:
            self.add("co.ai-gradient", None, f"紫色系跨色相渐变：{purple_grad}")

    # ---- copy
    def check_cp_copy(self):
        visible = self.doc_text
        low = visible.lower()
        hits = [w for w in CLICHES_ZH if w in visible] + [w for w in CLICHES_EN if re.search(r"\b" + re.escape(w), low)]
        if hits:
            self.add("cp.ai-cliche", None, f"套话 {len(hits)} 处：{'、'.join(hits[:6])}",
                     severity="major" if len(hits) >= 2 else "minor")
        for n in self.nodes:
            if n.tag in ("a", "button"):
                t = n.text().strip("。.!！ ").lower()
                if t in VAGUE_LINK:
                    self.add("cp.vague-link", n, f"链接文案「{n.text()}」不说明去向")
            if n.tag in ("h1", "h2", "h3", "button", "label") or "eyebrow" in " ".join(n.classes):
                if EMOJI.search(n.text()):
                    self.add("cp.emoji-heading", n, f"标题/按钮含 emoji：{n.text()[:20]}")
            if n.get("role") == "alert" or {"error", "toast", "alert", "error-message", "err"} & n.classes:
                t = re.sub(r"[。.!！~～…]+", "", n.text()).strip().lower()
                if t in VAGUE_ERROR:
                    self.add("cp.vague-error", n, f"错误提示只有「{n.text()}」")

    # ---- layout
    def check_ly(self):
        for n in self.nodes:
            if "card" in n.classes and any("card" in a.classes for a in n.ancestors()):
                self.add("ly.nested-card", n, "卡片嵌套在卡片里")
            st = self.styles.of(n)
            for k in ("width", "min-width"):
                v = px(st.get(k))
                if v and v >= 1000 and "max-width" not in st:
                    self.add("ly.fixed-wide", n, f"{k}:{int(v)}px 无 max-width")
                    break
            if n.tag == "p" and st.get("text-align") == "center" and visual_len(n.text()) > 120:
                self.add("ly.centered-paragraph", n, f"约 {visual_len(n.text())} 个半角字宽的段落居中")
        if re.search(r"<html|<head", self.src, re.I) and not any(
                n.tag == "meta" and n.get("name") == "viewport" for n in self.nodes):
            self.add("ly.no-viewport", None, "完整页面缺少 viewport meta")

    def check_ly_placeholder_metric(self):
        groups = {}
        for c in self.nodes:
            if not any(METRIC_BOX.search(k) for k in c.classes) or c.tag in ("table", "tr", "td"):
                continue
            vals = [n for n in c.iter() if any(VALUE_CLS.search(k) for k in n.classes)]
            if not vals:
                vals = [n for n in c.iter() if n.tag in ("strong", "b", "em", "h2", "h3")][:1]
            for v in vals:
                t = v.text()
                if 0 < len(t) <= 24:
                    groups.setdefault(id(c.parent), []).append(v)
        for vs in groups.values():
            if len(vs) < 3:
                continue
            sig = lambda n: (n.tag, tuple(sorted(n.classes)))
            nums = {sig(n) for n in vs if re.search(r"\d", n.text())}
            ph = [n for n in vs if PLACEHOLDER_VAL.match(n.text()) and sig(n) in nums]
            if nums and ph:
                self.add("ly.placeholder-as-metric", ph[0], f"占位值「{'」「'.join(n.text() for n in ph[:3])}」与真实指标同样式并列")

    def check_cp_opaque_id(self):
        for n in self.nodes:
            m = OPAQUE_ID.search(n.own_text())
            if m:
                self.add("cp.opaque-id", n, f"编号前缀截断：{m.group(0)}")


    # ---- 视觉卫生（借鉴 heydamir/unslop 的 signs/tokens，CC BY 4.0；实现为本 skill 自写）
    def all_decls(self):
        """(节点或 None, 属性, 值)：样式表 + 行内样式 + Tailwind 任意值类。"""
        for sel, d, _m in self.css_rules:
            for k, v in d.items():
                yield None, k, v
        for n in self.nodes:
            for part in (n.get("style") or "").split(";"):
                if ":" in part:
                    k, v = part.split(":", 1)
                    yield n, k.strip().lower(), v.strip().lower()

    def tw_classes(self):
        for n in self.nodes:
            for c in n.classes:
                yield n, c

    def check_us_color(self):
        glow = None
        shadows = [(n, v) for n, k, v in self.all_decls() if k in ("box-shadow", "text-shadow", "filter")]
        shadows += [(n, c[c.index("[") + 1:-1].replace("_", " ")) for n, c in self.tw_classes() if re.match(r"^(drop-)?shadow-\[", c) and c.endswith("]")]
        for n, v in shadows:
            for part in re.split(r",(?![^(]*\))", v):
                col = parse_color(part)
                if not col:
                    continue
                nums = [float(x) for x in re.findall(r"(?<![\w.])(-?[\d.]+)(?:px)?(?![\w.%])", re.sub(r"rgba?\([^)]*\)|hsla?\([^)]*\)|#[0-9a-f]+|drop-shadow|inset", " ", part))]
                blur = nums[2] if len(nums) >= 3 else (nums[-1] if "drop-shadow" in part and nums else 0)
                h, sat, l = hsl(col)
                if sat > 0.35 and 0.2 < l < 0.85 and col[3] >= 0.2 and blur >= 8:
                    glow = (n, part.strip()[:60])
                    break
            if glow:
                break
        if glow:
            self.add("co.glow-shadow", glow[0], f"彩色发光阴影：{glow[1]}")
        grad_text = None
        for sel, d, _m in self.css_rules:
            bg = d.get("background", "") + d.get("background-image", "")
            if "gradient(" in bg and "text" in (d.get("background-clip", "") + d.get("-webkit-background-clip", "")):
                grad_text = sel
        for n in self.nodes:
            cl = n.classes
            if "bg-clip-text" in cl and any(c.startswith(("bg-gradient-", "bg-linear-", "bg-radial-")) for c in cl):
                grad_text = n.desc()
            st = (n.get("style") or "").lower()
            if "gradient(" in st and "background-clip:text" in st.replace(" ", ""):
                grad_text = n.desc()
        if grad_text:
            self.add("co.gradient-text", None, f"渐变文字：{grad_text[:60]}")
        cols = set()
        for _n, k, v in self.all_decls():
            if k == "color":  # 只看文字色：表面色阶本来就该是相近的几步
                c = parse_color(v)
                if c and c[3] >= 0.99:
                    cols.add(tuple(int(round(x)) for x in c[:3]))
        cols = sorted(cols)
        near = [(a, b) for i, a in enumerate(cols) for b in cols[i + 1:] if 0 < sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5 < 14]
        if len(near) >= 3:
            self.add("co.near-duplicate-colors", None, f"{len(near)} 组肉眼难分的近似色，如 " + "、".join("#%02x%02x%02x" % a for a, _ in near[:3]))

    def check_us_type(self):
        generic = {"serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui", "inherit", "initial", "unset",
                   "-apple-system", "blinkmacsystemfont", "ui-sans-serif", "ui-serif", "ui-monospace", "emoji", "math"}
        fams, sizes = set(), set()
        for _n, k, v in self.all_decls():
            if k in ("font-family", "font"):
                if k == "font" and "," not in v and not re.search(r"['\"]", v):
                    continue
                for f in v.split(","):
                    f = f.strip().strip("'\"").strip()
                    if k == "font":
                        f = re.sub(r"^.*\d(px|rem|em|%)(/[\d.]+\w*)?\s+", "", f)
                    if not f or f in generic or f.startswith("var(") or re.search(r"mono|code|courier|consolas|menlo", f):
                        continue
                    fams.add(f)
                    break
            if k == "font-size":
                m = re.match(r"([\d.]+)(px|rem)$", v)
                if m:
                    sizes.add(round(float(m.group(1)) * (16 if m.group(2) == "rem" else 1), 1))
            if k == "font-weight" and v in ("800", "900", "bolder", "black"):
                self.add("ty.heavy-weight", None, f"font-weight:{v}")
        if any(c in ("font-black", "font-extrabold") for _n, c in self.tw_classes()):
            self.add("ty.heavy-weight", None, "font-black/font-extrabold")
        if len(fams) > 2:
            self.add("ty.font-family-sprawl", None, f"{len(fams)} 个字体家族：{'、'.join(sorted(fams)[:5])}")
        if len(sizes) > 8:
            self.add("ty.size-sprawl", None, f"{len(sizes)} 种字号：{', '.join(str(int(x) if x == int(x) else x) for x in sorted(sizes))}")
        for sel, d, _m in self.css_rules:
            ls = d.get("letter-spacing", "")
            m = re.match(r"([\d.]+)(em|px)", ls)
            if d.get("text-transform") == "uppercase" and m and float(m.group(1)) >= (0.05 if m.group(2) == "em" else 1):
                self.add("ty.uppercase-tracked", None, f"{sel[:30]}：uppercase + letter-spacing {ls}")
                break
        for n, c in self.tw_classes():
            if c == "uppercase" and any(x.startswith("tracking-w") for x in n.classes):
                self.add("ty.uppercase-tracked", n, "uppercase + tracking-wide*")
                break

    def check_us_spacing(self):
        odd = set()
        for _n, k, v in self.all_decls():
            if re.match(r"^(margin|padding|gap|row-gap|column-gap)(-|$)", k):
                for x in re.findall(r"(?<![\w.-])(\d+)px", v):
                    if int(x) > 1 and int(x) % 2:
                        odd.add(int(x))
        for _n, c in self.tw_classes():
            m = re.match(r"^-?(m|p|gap|space)[trblxyse]?(-[xy])?-\[(\d+)px\]$", c)
            if m and int(m.group(3)) > 1 and int(m.group(3)) % 2:
                odd.add(int(m.group(3)))
        if len(odd) >= 3:
            self.add("ly.off-scale-spacing", None, f"{len(odd)} 个随意间距值：{', '.join(f'{x}px' for x in sorted(odd))}")

    def check_us_copy(self):
        t = self.doc_text
        if re.search(r"[!！]{2,}", t):
            self.add("cp.shouty-copy", None, "双感叹号：" + re.search(r".{0,12}[!！]{2,}", t).group(0))
        for n in self.nodes:
            if n.tag in ("h1", "h2") and re.match(r"^(欢迎回来|欢迎|welcome back|hi|hello|hey)\b.*[!！]$", n.text().strip(), re.I):
                self.add("cp.shouty-copy", n, f"问候式标题：{n.text()[:20]}")
                break


def lint_source(src, rules=None, path=""):
    rules = rules or load_rules()
    if path.endswith((".jsx", ".tsx")) or re.search(r"className=|onClick=\{", src):
        src = jsx_to_html(src)
    findings = Linter(src, rules).run()
    sev = {s: sum(f["severity"] == s for f in findings) for s in ("critical", "major", "minor")}
    verdict = "FAIL" if any(f["severity"] in BLOCKING for f in findings) else "PASS"
    return {"file": path, "verdict": verdict, "counts": sev, "findings": findings}


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            try:
                s.reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass
    ap = argparse.ArgumentParser(description="Mano-Design 静态 UI/交互检查（HTML/JSX）")
    ap.add_argument("files", nargs="*", type=Path)
    ap.add_argument("--stdin", action="store_true", help="从标准输入读取")
    ap.add_argument("--format", choices=("json", "text"), default="json")
    ap.add_argument("--min-severity", choices=("minor", "major", "critical"), default="minor")
    a = ap.parse_args(argv)
    if not a.files and not a.stdin:
        ap.error("需要文件或 --stdin")
    rules = load_rules()
    order = {"minor": 0, "major": 1, "critical": 2}
    reports = []
    try:
        sources = [("<stdin>", sys.stdin.read())] if a.stdin else [(str(p), p.read_text(encoding="utf-8")) for p in a.files]
    except OSError as e:
        print(f"读取失败：{e}", file=sys.stderr)
        return 1
    for path, src in sources:
        rep = lint_source(src, rules, path)
        rep["findings"] = [f for f in rep["findings"] if order[f["severity"]] >= order[a.min_severity]]
        reports.append(rep)
    if a.format == "json":
        print(json.dumps(reports if len(reports) > 1 else reports[0], ensure_ascii=False, indent=2))
    else:
        for rep in reports:
            print(f"{rep['file']}: {rep['verdict']}  {rep['counts']}")
            for f in rep["findings"]:
                print(f"  [{f['severity']}] {f['rule']} {f['title']} @ {f['element'] or '-'}\n      证据：{f['evidence']}\n      修复：{f['fix']}")
    return 2 if any(r["verdict"] == "FAIL" for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
