# CHANGELOG — gen-aitown-model

## 0.1.0 — 2026-11-27

- 首版：AITown 模型模块生成 skill（SKILL.md 461 行）。
- 内容：§A 规范参数（`AITOWN` 常量）、§B 导出接口（`AITOWN` / `META` / `createModel` / `selfCheck` / `liveModels`）、§C 内联工具、§D 自检、建模要求与输出顺序。
- 规格来源：与 2026-11-27 卫星发射中心（`satellite-launch-center`）实测同一套约定，并沉淀了那次构建的三条硬规则：`userData.moving` 只标最顶层运动祖先（§建模要求 8）、动态材质不得用共享 `toyMat`（规则 9）、`budgetEstimate` 往高估 20%（规则 10）。
- 与 `town-model-gen`（静态模型 JSON）互补，不重复；与 `mano-3dmodel-gen`（通用 Web 3D 工作流）分工：本 skill 只负责符合 AITown 宿主约定的模型模块。
