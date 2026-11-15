# Mano-Design｜交互体验把关
解决「AI 生成的 UI 交互不友好」：组件选错、状态缺失、对比度不足、配色杂乱、AI 味文案。规则 + 静态检查器 + 可选浏览器检查 + LLM 评审清单 + 自测用例 + RSI 回路。纯 Markdown + JSON + Python 标准库。

## 目录
| 路径 | 内容 |
|---|---|
| `SKILL.md` | 入口与路由 |
| `rules/` | `rules.json`（全部规则，唯一真源）、组件选型、交互、配色、中文文案、词汇表、资源卫生 |
| `capabilities/` | 生成前组件决策、评审流程、开源方案组合 |
| `cases/` | 开源方案目录 `cases.json` + schema + 来源帖 `sources/` |
| `scripts/` | `ui_lint.py` 静态检查、`browser_check.py` 浏览器检查（可选）、`eval.py` 自测评分、`rules.py` / `query.py` 查询、`validate.py` 校验 |
| `tests/` | `manifest.json` + `fixtures/{bad,good}`（HTML/JSX，含 holdout 留出集） |
| `rsi/` | 自我改进回路：评审提示、失败日志 schema、`ingest.py`、`gate.py`、基线 |
| `agents/openai.yaml` | Codex 界面元数据 |

## 安装（整个 `mano-design/` 文件夹放到下列位置之一，文件夹名必须为 mano-design）
| Agent | 路径 |
|---|---|
| Codex（新版）/ pi / DeepSeek Harness | `~/.agents/skills/mano-design/`（Windows `%USERPROFILE%\.agents\skills\mano-design\`） |
| Codex（旧版） | `~/.codex/skills/mano-design/`（与上面二选一） |
| Claude Code | `~/.claude/skills/mano-design/` |
| 其他 | 在 AGENTS.md / GEMINI.md 加下方片段 |

```md
## Mano-Design
生成、评审或修复 UI 时：先读 <skill路径>/mano-design/SKILL.md；生成前按 rules/component-selection.md 输出组件决策；完成后运行 scripts/ui_lint.py，有 critical/major 必须修复；交付写明已运行的检查与未验证项。
```

## 常用命令（Windows 用 `py`）
```bash
python3 scripts/ui_lint.py page.html --format text       # 静态检查；退出码 2 = 不合格
python3 scripts/ui_lint.py src/Settings.jsx              # JSON 报告（rule/severity/element/evidence/fix）
python3 scripts/browser_check.py http://localhost:5173 --viewport 390x844   # 需 pip install playwright
python3 scripts/rules.py --detect rubric --format checklist                   # 生成评审清单
python3 scripts/eval.py && python3 scripts/validate.py
python3 rsi/ingest.py rsi/failures.example.json          # 预演入库
python3 rsi/gate.py                                      # 回归门禁
```

## 已知限制
- 静态检查看不到运行时：JS 动态生成的控件、绝对定位叠层背景、图片上的文字对比度需 `browser_check.py` 或人工确认。
- 同级视图/FAQ 区分靠标题启发式（短名词 vs 问句、面板内是否为筛选控件）；语义更复杂时交给 rubric。
- 文案套话为词表匹配，可能误伤品牌合法用词；可在评审中标为误报并沉淀。
- 自测用例由本 skill 作者编写（含两批先写后测的 holdout），不能代表所有真实页面。

## 维护
新增规则/用例按 `rsi/README.md`。版本与 eval 记录见 `CHANGELOG.md`。
