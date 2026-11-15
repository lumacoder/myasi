# RSI：递归自我改进回路
目标：每次生成 UI 后发现的问题都沉淀为**可回归的用例或规则**，检查器和规则只在「不降分、不回退」时才升级。

```
生成 UI ─► ① ui_lint（确定性） ─► ② browser_check（可选，真实渲染） ─► ③ LLM rubric 评审
   ▲                                                                     │
   │                                     ④ 记录失败日志 rsi/failures-<日期>.json
   │                                                                     │
   └── ⑧ 用新规则重新生成/修复 ◄── ⑦ gate --accept（版本+1、CHANGELOG） ◄── ⑥ gate 门禁 ◄── ⑤ ingest → 改规则/检查器
```

## 步骤
1. **生成**：按 `capabilities/generate.md` 先输出组件决策 JSON，再写代码。
2. **确定性检查**：`python3 scripts/ui_lint.py <文件> --format text`；有 critical/major 先修，修完再测。
3. **真实渲染（可选）**：`python3 scripts/browser_check.py <文件或URL> --viewport 390x844`；未装 Playwright 会返回 `skipped`，不阻断。
4. **语义评审**：把 `rsi/rubric.md` 的提示 + 代码 + ui_lint JSON 交给评审模型（新会话，避免自我辩护），得到 JSON findings。
5. **记录失败**：凡是「检查器漏报 / 误报 / rubric 新发现」都写一条到 `rsi/failures-<日期>.json`（格式见 `failure_log.schema.json`；可用 `python3 rsi/ingest.py --draft <文件>` 起草）。要求：
   - 最小复现片段，删掉无关代码与隐私；`verdict/rules` 写**应有**结果，不是当前输出。
   - 同时补一个**正确版本**（PASS 用例），防止规则过宽；约 1/4 标 `"split": "holdout"`。
   - 新问题没有对应规则时，先在 `rules/rules.json` 增加规则（id、signal、correct、anti_patterns、severity、detect、sources）。
6. **入库**：`python3 rsi/ingest.py rsi/failures-<日期>.json`（预演）→ `--apply`。lint 规则进 `tests/fixtures`，rubric 规则进 `rsi/rubric_cases.json`。
7. **改检查器**：修改 `scripts/ui_lint.py` 的通用逻辑（禁止按文件名/用例 id 特判），`python3 scripts/eval.py` 看漏报误报。
8. **门禁**：`python3 rsi/gate.py`。只有满足：基线判对的用例仍判对、基线用例集得分不降、完全正确数不降、holdout 得分不降，才输出 ACCEPT。然后 `python3 rsi/gate.py --accept --note "<改了什么>"`：版本号 +0.0.1、更新 `rsi/baseline.json` 与 `CHANGELOG.md`。
9. **收尾**：`python3 scripts/validate.py`；删除临时生成物、截图、`__pycache__`；失败日志入库后可删除（内容已在 fixtures/manifest）。

## 防过拟合
- 检查器不得读取 `tests/`、文件名或期望值；validate 会检查规则实现与声明一致。
- holdout 用例在改检查器**之前**写好，并单独报告首轮成绩（见 CHANGELOG）。
- 标注错误也是一种失败：若检查器「误报」其实是真问题（例如白字在 #a855f7 上确实 <4.5:1），改标注而不是改检查器，并在 note 里写明。
- 两轮无进展：缩成最小复现，或把规则降为 rubric-only，不堆正则。

## 产物
| 文件 | 作用 |
|---|---|
| `rubric.md` | LLM 评审提示（挑最严重 3 个先修） |
| `failure_log.schema.json` / `failures.example.json` | 失败日志格式与示例 |
| `ingest.py` | 失败日志 → 用例（校验 id/规则/严重级一致/隐私/去重） |
| `gate.py` | 回归门禁与版本记录 |
| `baseline.json` | 当前被接受的基线 |
| `rubric_cases.json` | rubric-only 规则的回归样例（给评审模型做 few-shot 与抽查） |
