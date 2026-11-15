# 生成 UI 前的组件决策（输出 JSON 再写代码）
1. 列出界面里每个「需要用户输入或切换」的点，填下表（不确定写 null 并进 unknowns）。
2. 每项按 `rules/component-selection.md` 的 4 个问题选组件；冲突时：用户/品牌设计系统 > 项目现有组件库 > 本规则默认。
3. 写代码时只用决策表里的组件；完成后跑 `scripts/ui_lint.py`。

```json
{
  "screen": "通知设置",
  "user_goal": "快速开关各类通知",
  "controls": [
    {"label": "消息推送", "data": "binary", "apply": "immediate", "relation": null, "count": 2,
     "component": "Switch", "rule": "cs.binary-select", "states": ["default","hover","focus-visible","disabled"]},
    {"label": "概览/成员/设置", "data": "view", "apply": "immediate", "relation": "peer", "count": 3,
     "component": "Tabs", "rule": "cs.peer-views-accordion", "states": ["selected","hover","focus-visible"]}
  ],
  "states_required": ["loading", "empty", "error", "success"],
  "tokens": {"accent": 1, "semantic": ["success","warning","danger"], "radius": "8px", "motion_ms": 160},
  "unknowns": []
}
```
