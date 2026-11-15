# 架构解读
输入：仓库或目录快照；输出下列JSON契约。只读分析，不因解读而安装依赖或运行不可信脚本。

## 程序
1. 先读项目规则、README、依赖锁、目录、构建与运行入口；锁文件版本优先于记忆。
2. 从一个真实请求/事件追踪 UI/入口→业务→存储/外部服务，标出数据与权限边界。
3. 按职责画module_map，注明对外接口、依赖、状态所有者；不按每个文件机械复述目录。
4. 查配置、adapter、plugin与API等extension_points；区分“发现入口”与“已验证扩展可用”。
5. 输出风险、最小改动面和验证路径；复杂度、性能、部署能力没有证据就不下确定结论。

## 固定输出契约
```json
{
  "sources": [{"id": "s1", "path": "仓库文件", "locator": "符号/行号", "revision": null}],
  "stack": [{"name": "技术", "version": null, "role": "职责", "evidence": ["s1"], "certainty": "observed"}],
  "entry_points": [{"path": "入口", "symbol": null, "trigger": "启动/请求/事件", "evidence": ["s1"]}],
  "module_map": [{"id": "m1", "path": "模块", "responsibility": "单一职责", "interfaces": [], "depends_on": [], "state_owner": null, "evidence": ["s1"]}],
  "data_flow": [{"from": "m1", "to": "外部系统或模块ID", "payload": "数据", "boundary": "信任边界", "evidence": ["s1"], "certainty": "observed"}],
  "extension_points": [{"path": "扩展位置", "mechanism": "config/adapter/plugin/API", "contract": "输入输出", "core_changes_needed": null, "evidence": ["s1"], "certainty": "observed"}],
  "risks": [{"severity": "medium", "finding": "风险", "evidence": [], "certainty": "inferred", "mitigation": "最小措施"}],
  "change_surface": [{"path": "建议改动位置", "reason": "原因", "reuse_mode": "pattern"}],
  "verification": [{"command_or_check": "建议检查", "expected": "结果", "status": "未执行", "evidence": []}],
  "unknowns": [{"question": "缺口", "impact": "影响"}]
}
```
- `certainty`：observed/inferred；severity：low/medium/high；reuse_mode：direct-dep/pattern/reference。
- `version/revision/symbol/state_owner`：string|null；core_changes_needed：boolean|null；未知数组为空。
- module_map.depends_on仅引用模块ID或显式标明的外部服务；evidence引用sources ID。
- verification.status只取 未执行/通过/失败/不适用；静态阅读不等于已运行，建议命令默认未执行。
- 门禁：能解释一个端到端数据流、定位真实入口、指出扩展边界；无证据的推断必须进unknowns或标inferred。
