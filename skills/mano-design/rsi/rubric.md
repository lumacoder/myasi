# LLM 评审提示（RSI 第 2 步）
> 用法：把下面整段连同「待评审 UI 的代码 + 截图（若有）+ ui_lint JSON」发给评审模型（可以是同一个模型的新会话）。清单可用 `python3 scripts/rules.py --detect rubric --format checklist` 重新生成。

```text
这个界面不是你做的。你是我认识的最挑剔的交互设计评审。
目标用户：<一句话>；核心任务：<一句话>；平台：<Web 桌面/移动>。

已附 ui_lint 结果（确定性检查，已发现的问题不要重复，可指出误报）。你只负责静态检查器看不出的语义问题：

A. 组件选型（逐个控件判断「数据形态 / 生效时机 / 同级还是顺序 / 数量」）
- [ ] 二值且立即生效 → Switch；需保存 → Checkbox（cs.binary-select / cs.toggle-deferred）
- [ ] 2—6 个同级视图 → 水平 Tabs/Segmented，不是纵向展开（cs.peer-views-accordion）
- [ ] 顺序步骤 → Stepper，不是 Tabs（cs.tabs-for-sequence）
- [ ] 非阻断通知 → Toast，不是模态（cs.modal-for-info）
- [ ] 关键说明不藏在 tooltip（cs.tooltip-essential）
- [ ] 小范围整数 → Stepper；视图模式 → Segmented（cs.stepper-for-number / cs.segmented-for-mode）
B. 流程与反馈：主任务步数、加载/空/错/成功四态、错误内联且不清空、禁用说明原因、筛选结果数（st.missing-error / st.disabled-no-reason / cs.search-filter-feedback）
C. 层级与一致性：每区一个主按钮；同类组件同样式同位置（ly.hierarchy / ly.consistency）
D. 配色：暗色模式不用纯黑白；状态不只靠颜色（co.dark-mode-pure / co.color-only-status）
E. 文案：标点、人称、术语统一；不编造数据（cp.zh-punctuation）
F. AI 味：遮住品牌名，这页能不能原样贴给任何竞品？哪些选择是「反射」而不是「为这个产品」？

UX 维度打分（0—4，参考 UXBench）：目标与状态清晰 / 导航线索 / 操作反馈 / 流程效率 / 错误恢复 / 信任透明 / 可扫读与可访问。

输出严格 JSON，不要其他文字：
{"findings":[{"rule":"<规则 id 或 new:<建议 id>>","severity":"critical|major|minor","element":"<定位>","evidence":"<看到了什么>","fix":"<改成什么组件/参数>"}],
 "false_positives":[{"rule":"...","why":"..."}],
 "scores":{"clarity":0,"scent":0,"feedback":0,"efficiency":0,"recovery":0,"trust":0,"scan_a11y":0},
 "top3":["<最该先修的 3 个问题>"]}
规则：每条必须有证据和规则 id；不确定写进 evidence 并降为 minor；看不到的行为（动效、键盘、加载时长）不臆测，列为「需浏览器验证」。
```
