# UI规范 / design提取
输入：截图、网站或Figma；输出下列JSON契约。先读现有tokens，不为还原外观强制换栈。

## 程序
1. 记录画布尺寸、来源和可观测范围；网站优先查computed styles，Figma查变量/样式，截图只做估计。
2. 建立语义tokens：color、type_scale、spacing、radius、shadow、motion；重复值归一，不逐像素描摹。
3. 提取容器宽度、grid、对齐、断点与组件状态；区分布局规律与单个元素的例外。
4. 将“美观/丝滑”等对照vocab转为数值或已知组件；无法观察字体、动画、hover或断点时不伪造。
5. 先一页/一组件对照验证，再批量应用；截图估计与后续建议分开，记录差异和可访问性风险。

## 固定输出契约
```json
{
  "sources": [{"id": "s1", "kind": "screenshot", "location": "路径或URL", "viewport": {"width": null, "height": null}}],
  "tokens": {
    "color": [{"name": "surface", "value": null, "unit": null, "certainty": "unknown", "evidence": ["s1"]}],
    "type_scale": [],
    "spacing": [],
    "radius": [],
    "shadow": [],
    "motion": []
  },
  "layout": {"container_max_width": null, "columns": null, "gap": null, "breakpoints": [], "evidence": ["s1"], "certainty": "unknown"},
  "components": [{"name": "组件", "variants": [], "states": [], "token_refs": [], "keyboard": null, "evidence": ["s1"], "certainty": "unknown"}],
  "recommendations": [{"target": "组件或token", "spec": "建议值与理由", "acceptance": "检查方法"}],
  "unknowns": [{"field": "字段路径", "reason": "不可见或未测量"}]
}
```
- 六类token数组使用相同条目形状 `{name,value,unit,certainty,evidence}`；value 为 string/number/object/null，unit 为 string|null。
- type_scale的value可用 `{font_family,font_size,font_weight,line_height,letter_spacing}`；motion可用 `{duration,easing,stiffness,damping,properties}`。
- `certainty` 只取 measured/estimated/unknown；source.kind只取 screenshot/site/figma；建议只放recommendations。
- spacing等长度默认px并明确unit；breakpoints条目用 `{min_width,columns,evidence,certainty}`。
- 不可见的动效不能标measured；截图采样色受压缩/色彩管理影响，应标estimated。
- 门禁：token_refs存在；文字/背景对比度有检查或明确未测；focus/disabled/loading等未见状态进入unknowns。
