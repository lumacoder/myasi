# Mano-ASI｜超人工智能全栈研发工程师
用具体词汇、可复用程序、结构化产物与验证门禁，降低对高级模型的依赖。纯 Markdown + JSON + Python 标准库。

## 目录
`SKILL.md` 入口 · `rules/` 输出/词汇/动效/资源卫生 · `capabilities/` 三种提取程序 · `cases/` 案例库+schema+来源帖 · `scripts/` 查询与校验 · `agents/openai.yaml` Codex 界面元数据

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
研发、UI/动效/视频、产品逻辑/UI规范/架构提取任务：先读取 <skill路径>/mano-asi/SKILL.md，按其路由表只加载需要的 rules/ capabilities/ 文件；案例用 scripts/query.py 查询，不通读 cases.json；交付按 rules/output.md 并附清理报告。
```

## 脚本（Windows 用 `py`，macOS/Linux 用 `python3`）
```bash
python3 scripts/query.py --keyword stagger          # 摘要，默认≤3条
python3 scripts/query.py --category 3D与游戏 --tag three.js --full
python3 scripts/validate.py                         # 装有 jsonschema 时做完整校验
```

## 维护
新增案例流程见 `SKILL.md`「补充案例」。快照：58 条，2026-11-15（Asia/Shanghai）；`verified` 仅指元数据核实。
