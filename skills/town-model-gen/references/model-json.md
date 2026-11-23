# 模型 JSON 约定

## 普通建筑和口袋公园

- [building.schema.json](building.schema.json) 为 Draft 2020-12。顶层需要 `schema`、`id`、`name`、`kind`、`lot`、`seed`、`colorway`、`parts` 和 `anchors`。每份模型使用唯一稳定 ID。嵌套部件、关节和锚点只用 schema 中已有字段。
- 每格 4 m。地块中心为原点，Y 向上，按示例用 +Z 朝街，`at` 为 `[x, y, z]`，`ry` 为绕 Y 轴角度。几何尺寸和位移用米。几何外缘距地块边界至少 0.4 m，核对屋檐、扶手与树冠。
- 普通建筑推荐 2×2、2×3 或 3×3。只有 `prop`、`tree` 使用 1×1。景观型口袋公园可用 `kind: "fun"`，让入口、主路、休息处和绿植构成连续游线。
- `anchors.door` 用于检查出入口，它是接向街道的通行锚点，须在地块内且距边缘最多 0.6 m。门槛或园区开口到该锚点之间留出无障碍通路。部件从地坪或真实支承处起算，检查每个等级都有支承。使用 `minLevel` 分阶段增添部件时，保留 Lv1 的主体和通路。
- 小楼用 `wall` 开窗开门，`roofGable` 或 `roofHip` 做可识别屋顶，`signBoard` 标记用途，树分 `trunk` 与 `canopy`。普通建筑优先用算子自带的倒角。夜景需要时按 schema 使用 `night`，每个发光点对应窗、招牌或灯具。
- 保持在 12 KB、展开后 200 个部件以内。2 格宽预算为 4,000 三角面和 3 次绘制，3 格宽为 8,000 三角面和 3 次绘制。几何预算以 AITown 检查器为准。

## 大型园区

- 先用 `ceil(米制宽度 / 4)` 和 `ceil(米制深度 / 4)` 得到格数。在本版基线下按长边 ≤20、短边 ≤14、面积 ≤260 格²做尺寸筛查。当前地图的可建地块、旋转与实际接路需由 AITown 核对。
- 用米制坐标或分区范围标清入口、主路、休憩、服务、围护。选 2–3 个主角，用稳定 ID 标记位置、活动范围和与其他部件的关系。按一个时钟安排动作，检查交接时的净距、支承与越界。静态小配件可以单独交付建筑 JSON。
- 无渲染驱动时，输出 Brief 草稿，使用 `schema: "aitown.scene-brief/1"`、`id`、`request`、`intent`、`space`、`look`、`layers`、`operations`。其中 `space` 使用 `widthMetres`、`depthMetres`、`datum`、`circulation`，`look` 使用 `surfaces`、`lighting`、`camera`。用 `layers[].actors` 与 `operations[].actors` 列出计划使用的部件 ID。可附 `sequence.inline`，其 `duration`、`referenceSeconds` 与 `stages` 的 `id`、`label`、`start`、`end` 应一致，阶段连续覆盖全程。
- 只有拿到可用驱动或可直接渲染的建筑模型后才填写 `model` 绑定。优先询问用户是否已有可参照的驱动、布局 JSON 或原始规格。Brief 需要模型、动作阶段、部件引用和驱动全部可解析后才能编译。

## 验证

可用 JSON Schema 工具时，先校验普通建筑的字段与类型。在 AITown 仓库运行 `npm run building:check -- /path/to/model.json`，核对几何预算、越界、浮空和门前通行。在 `/dev/building` 查看剪影、材质与空间关系。大型园区准备好驱动后，用 `node scripts/scene/compile.mjs /path/to/brief.json --out /path/to/output` 验证 Brief 与模型绑定。报告实际完成的检查。
