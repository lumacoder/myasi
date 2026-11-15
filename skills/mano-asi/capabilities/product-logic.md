# 产品逻辑快速提取
输入：PRD、可见页面或仓库；输出只用下列JSON契约，字段不可改名，数组允许为空。

## 程序
1. 列出可访问的来源与定位；仅阅读核心说明、路由、模型和主流程，不遍历无关代码。
2. 提取目标用户、角色权限、核心对象及对象生命周期；区分观察事实与推断。
3. 沿“触发→输入→权限→动作→结果”追一条主流程；标出持久化、副作用与退出条件。
4. 枚举加载、空、成功、失败、无权限及重试状态；检查重复提交、并发、取消、边界输入。
5. 输出可执行验收；没证据的能力放 `unknowns`，不得从一个按钮推断完整后端存在。

## 固定输出契约
```json
{
  "goal": null,
  "sources": [{"id": "s1", "location": "文档路径/URL/截图名称", "locator": "章节/行号/区域"}],
  "roles": [{"id": "r1", "name": "角色", "permissions": [], "evidence": ["s1"], "certainty": "observed"}],
  "core_objects": [{"id": "o1", "name": "业务对象", "fields": [], "owner_role": null, "evidence": ["s1"], "certainty": "observed"}],
  "main_flow": [{"step": 1, "actor": "r1", "trigger": null, "input": [], "action": "动作", "output": [], "side_effects": [], "evidence": ["s1"], "certainty": "observed"}],
  "states": [{"object": "o1", "values": [], "transitions": [{"from": "状态A", "event": "事件", "to": "状态B", "guard": null}], "evidence": ["s1"], "certainty": "observed"}],
  "edge_cases": [{"condition": "边界条件", "expected": "可观察结果", "evidence": [], "certainty": "inferred"}],
  "acceptance": [{"given": "前置", "when": "操作", "then": "可断言结果"}],
  "unknowns": [{"question": "待核实问题", "impact": "影响", "blocking": false}]
}
```
- `goal`：string|null；`sources[].id` 唯一；所有 `evidence` 只能引用已列source ID。
- `certainty` 只取 observed/inferred；验收用例是建议，不表示已经测试。
- 未知标量 `null`、未知集合 `[]`；示例条目是类型模板，实际没有数据时删除条目，不照抄占位符。
- 门禁：角色与对象ID引用有效；主流程有输入/结果；每个关键状态有出口或明确为终态；unknowns显式列出。
