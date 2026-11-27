# gen-aitown-model

写一个自包含的 ES Module：调用 `createModel()` 返回 AITown 可用的动画园区模型。

只依赖 `three@0.186`。§A 的 `AITOWN` 规范参数、§C 的内联工具、§D 的 `selfCheck` 原样复制进生成的文件；代码中引用参数名，不另写魔法数字。文件完整可运行，不能出现 `...`、`// 省略`、`TODO`。

## 何时使用

- 用户要一个 AITown 园区模型（早市、发射中心、工地、机场……），且产物是可直接接入宿主游戏的 ES Module 文件。
- 与 `town-model-gen` 的区别：`town-model-gen` 生成静态模型 JSON（导入用）；本 skill 生成会动、可昼夜切换、可释放的**活的**园区模块（`seek(t)` 纯函数 + `setNight` + `dispose`）。
- 与 `mano-3dmodel-gen` 的区别：`mano-3dmodel-gen` 是自然语言 → Web 3D 场景的通用工作流；本 skill 是 AITown 宿主约定的**模型模块规格**，输出物必须通过 `selfCheck` 门禁才能上架。

## 工作方式

1. 先输出 Brief + 节拍表 + 风格锁，再写代码。
2. 主角 2–3 个，程序化建模（车床 / 圆角挤出 / 放样管 / 圆角盒），园区零人物。
3. `seek(t)` 纯函数：`rampTravel` 闭式积分，`seek(0)` 与 `seek(cycleSeconds)` 画面一致。
4. 跑 `selfCheck`：扫掠包络、占地、纯函数、预算、灯光、释放全过才算交付。
5. 输出顺序：Brief 与表 → 完整模块代码 → 自检 JSON → 每主角 L1–L4 自评 → 10 项自查清单。

## 版本

`0.1.0` — 首版，直接取自 AITown 模型模块规格（含卫星发射中心实测沉淀的三条硬规则：`userData.moving` 只标最顶层祖先、动态材质不用共享 `toyMat`、`budgetEstimate` 往高估 20%）。
