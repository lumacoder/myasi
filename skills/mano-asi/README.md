# Mano-ASI｜超人工智能全栈研发工程师
用具体词汇、实测网页审美标尺、可复用滚动模式、结构化产物与验证门禁，降低对高级模型的依赖。纯 Markdown + JSON + Python 标准库（另附可选 Node + Playwright `scrollshot.mjs` 全轨迹验屏脚本）。

## 目录
- `SKILL.md`：入口与五步研发闭环
- `rules/`：输出契约（`output.md`）、网页审美（`web-craft.md`）、词汇表（`vocab.json`）、动效（`motion.md`）、资源卫生（`hygiene.md`）
- `patterns/`：单一 `rAF` 滚动引擎与 4 大原生滚动舞台（`INDEX.md`、`engine.md`、`stages.md`、`surface-and-type.md`）
- `capabilities/`：产品逻辑 / UI 规范 / 架构解读三种提取程序
- `cases/`：开源案例库（`cases.json` + schema + `sources/`）
- `scripts/`：案例查询（`query.py`）、校验（`validate.py`）与全滚动轨迹验屏（`scrollshot.mjs`）
- `agents/openai.yaml`：Codex 界面元数据

## 安装与引用
推荐用 myasi 按名安装：`myasi get mano-asi`（别名 `devasi` 也可）；手动路径见 [使用与开发指南](../../docs/GUIDE.md)。

```md
## Mano-ASI
研发、网页与官网设计/滚动叙事、UI/动效/视频、产品逻辑/UI规范/架构提取任务：先读取 <skill路径>/mano-asi/SKILL.md，按其路由表只加载需要的 rules/ patterns/ capabilities/ 文件；案例用 scripts/query.py 查询，不通读 cases.json；交付按 rules/output.md 并附清理报告。
```

## 常用脚本（Windows 用 `py`，macOS/Linux 用 `python3`）
```bash
python3 scripts/query.py --keyword stagger          # 摘要，默认≤3条
python3 scripts/query.py --category 3D与游戏 --tag three.js --full
python3 scripts/validate.py                         # 装有 jsonschema 时做完整校验
node scripts/scrollshot.mjs http://localhost:5173 shots --reduced  # 可选：需装有 playwright
```

## 致谢、许可与维护
- 网页审美标尺、原生滚动模式（`patterns/`）与 `scripts/scrollshot.mjs` 适配自 [scrolltide/ai-studio-skill](https://github.com/scrolltide/ai-studio-skill) 的 **MIT License** 开源部分，未包含其专有 `library/*.md` 模板及下载资产。
- 案例快照：60 条，2026-11-25（Asia/Shanghai）；`verified` 仅指元数据核实。版本记录见 [CHANGELOG.md](CHANGELOG.md)。
