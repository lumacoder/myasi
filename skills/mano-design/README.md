# Mano-Design｜视觉 + 交互体验把关
解决「AI 生成的 UI 不好看、没创意、交互不友好」，适用于任何页面类型。两层：
- **视觉与创意**：原型识别（17 类）→ 逐区块对标主流基准（65 条种子 + 现找现核实流程）→ DESIGN.md-lite 风格规格 → 按行业/受众自动选主题（8 套，明暗均实测 AA）→ 领域签名可视化/交互（51 个模式）→ 截图联系表 + 苛刻评审先修 3 个 → 0—10 视觉评分 ≥8 门禁。机制出处见 `capabilities/mechanism-sources.md`。
- **交互正确性**：规则 + 静态检查器 + 浏览器检查（多路由、等待真实内容）+ LLM 评审清单 + 自测用例 + RSI 回路。
纯 Markdown + JSON + Python 标准库；Playwright 可选。

## 目录
| 路径 | 内容 |
|---|---|
| `SKILL.md` | 入口与路由 |
| `rules/` | `rules.json`（全部规则，唯一真源）、组件选型、交互、配色、中文文案、词汇表、资源卫生 |
| `capabilities/` | **视觉设计主流程** `visual-design.md`、机制出处 `mechanism-sources.md`、基准发现 `benchmark-discovery.md`、生成前组件决策、评审流程、开源方案组合 |
| `visual/` | 原型 `archetypes.json`、基准 `benchmarks.json`、签名创意 `creative-patterns.json`、主题 `themes.json`、视觉评分 `rubric.md`、风格规格模板、自测样例 `examples/` |
| `cases/` | 开源方案目录 `cases.json` + schema + 来源帖 `sources/` |
| `scripts/` | `archetype.py` 原型识别、`theme.py` 主题、`visual_capture.py` 截图联系表、`visual_score.py` 视觉评分门禁、`ui_lint.py` 静态检查、`browser_check.py` 浏览器检查（可选）、`eval.py` 自测评分、`rules.py` / `query.py` 查询、`validate.py` 校验 |
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
生成、重做、评审或修复 UI 时：先读 <skill路径>/mano-design/SKILL.md，新做/重做按 capabilities/visual-design.md（原型→基准→风格规格→主题→签名创意→实现→检查→联系表评审→视觉评分 ≥8）；完成后 ui_lint 无 critical/major；交付写明检查结果、视觉分与未验证项。
```

## 常用命令（Windows 用 `py`）
```bash
python3 scripts/archetype.py "给咖啡豆电商做商品详情页"   # 原型、区块、基准、签名候选
python3 scripts/theme.py --pick "本地生活 商家" --mode Operate && python3 scripts/theme.py --css market-ember
python3 scripts/visual_capture.py dist/index.html --views "home=#/;detail=#/p/1" --archetype ecommerce --dark --mobile
python3 scripts/visual_score.py shots/score.json --check-files   # ≥8 才可交付
python3 scripts/ui_lint.py page.html --format text       # 静态检查；退出码 2 = 不合格
python3 scripts/ui_lint.py src/Settings.jsx              # JSON 报告（rule/severity/element/evidence/fix）
python3 scripts/browser_check.py dist/index.html --routes "#/,#/runs" --wait-for "main [data-ready]" --color-scheme dark   # 需 pip install playwright
python3 scripts/rules.py --detect rubric --format checklist                   # 生成评审清单
python3 scripts/eval.py && python3 scripts/validate.py
python3 rsi/ingest.py rsi/failures.example.json          # 预演入库
python3 rsi/gate.py                                      # 回归门禁
```

## 已知限制
- 视觉评分依赖模型看截图：脚本只校验证据完整性、与基准的一致性和加权门槛，不能替代审美判断；自评有偏高倾向（自评 −0.5），优先用新会话评审。
- 基准 stars/许可是快照；`capture_url` 页面会改版，截图失败不阻断。
- 静态检查看不到运行时：JS 动态生成的控件、绝对定位叠层背景、图片上的文字对比度需 `browser_check.py` 或人工确认。
- 同级视图/FAQ 区分靠标题启发式（短名词 vs 问句、面板内是否为筛选控件）；语义更复杂时交给 rubric。
- 文案套话为词表匹配，可能误伤品牌合法用词；可在评审中标为误报并沉淀。
- 自测用例由本 skill 作者编写（含两批先写后测的 holdout），不能代表所有真实页面。

## 维护
新增规则/用例按 `rsi/README.md`。版本与 eval 记录见 `CHANGELOG.md`。
