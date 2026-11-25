# Mano-ASI｜超人工智能全栈研发工程师
用具体词汇、实测网页审美标尺、可复用滚动模式、结构化产物与验证门禁，降低对高级模型的依赖。纯 Markdown + JSON + Python 标准库（另附可选 Node + Playwright `scrollshot.mjs` 全轨迹验屏脚本）。

## 目录
`SKILL.md` 入口 · `rules/` 输出/网页审美/词汇/动效/资源卫生 · `patterns/` 单循环引擎与滚动叙事模式 · `capabilities/` 三种提取程序 · `cases/` 案例库+schema+来源记录 · `scripts/` 查询、校验与 `scrollshot.mjs` · `agents/openai.yaml` Codex 界面元数据

## 安装
推荐用 myasi 按名安装：`myasi get mano-asi`（别名 `devasi` 也可）。也可把整个 `mano-asi/` 文件夹放到下列位置，文件夹名必须为 mano-asi。
| Agent | 用户级路径 | 说明 |
|---|---|---|
| Codex（新版） | `~/.agents/skills/mano-asi/`；Windows `%USERPROFILE%\.agents\skills\mano-asi\` | 项目级：`<仓库>/.agents/skills/mano-asi/` |
| Codex（旧版兼容） | `~/.codex/skills/mano-asi/`；Windows `%USERPROFILE%\.codex\skills\mano-asi\` | 旧版本读取此处；两处都放会出现两个同名 skill，择一 |
| Claude Code | `~/.claude/skills/mano-asi/`；项目级 `.claude/skills/mano-asi/` | — |
| Gemini CLI | 任意位置；在 `GEMINI.md` 加下方片段 | 不依赖特定 tool 语法 |
| Grok Bot | 安装为 skill，或让它读取 `SKILL.md` | — |
Codex 用法：输入 `$mano-asi` 或 `/skills` 选择；任务匹配 description 时也会自动触发。更新后若未生效，重启 Codex。

## AGENTS.md / CLAUDE.md / GEMINI.md 片段
```md
## Mano-ASI
研发、网页与官网设计/滚动叙事、UI/动效/视频、产品逻辑/UI规范/架构提取任务：先读取 <skill路径>/mano-asi/SKILL.md，按其路由表只加载需要的 rules/ patterns/ capabilities/ 文件；案例用 scripts/query.py 查询，不通读 cases.json；交付按 rules/output.md 并附清理报告。
```

## 脚本（Windows 用 `py`，macOS/Linux 用 `python3`）
```bash
python3 scripts/query.py --keyword stagger          # 摘要，默认≤3条
python3 scripts/query.py --category 3D与游戏 --tag three.js --full
python3 scripts/validate.py                         # 装有 jsonschema 时做完整校验
node scripts/scrollshot.mjs http://localhost:5173 shots --reduced  # 可选：需项目或全局装有 playwright
```

## 致谢与许可
- 网页审美标尺（317 站实测规范）、原生滚动模式（`patterns/`）与 `scripts/scrollshot.mjs` 精髓适配自 [scrolltide/ai-studio-skill](https://github.com/scrolltide/ai-studio-skill) 的 **MIT License** 开源部分（Copyright (c) 2026 Scrolltide）。遵循其许可边界，未包含或再分发其 `library/*.md` 专有模板及下载资产。

## 维护
新增案例流程见 `SKILL.md`「补充案例」。快照：60 条，2026-11-25（Asia/Shanghai）；`verified` 仅指元数据核实。
