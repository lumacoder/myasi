# heydamir/unslop（用户补充来源）

仓库：https://github.com/heydamir/unslop（GitHub API 2026-11-16：16,771★，CC-BY-4.0，最近推送 2026-11-15）
作者：Damir Sokolovsky（@heydamir）。许可 CC BY 4.0：可改编与商用，须署名并链接原仓库。

读过的文件：README.md、skills/unslop/SKILL.md、references/signs.md、references/tokens.md、visuals.md、effects.md、refs.md、scripts/snapshot.mjs；并用 mano-design 的 ui_lint / browser_check 跑了它的 examples（dashboard/hero/store 三个 vibecoded 页面），新规则全部命中（发光、渐变字、任意间距、900 字重、全大写宽字距、喊叫文案）。

机制要点：
1. 审计：signs.md 按 表面与颜色 / 字体 / 图标 / 间距 / 文案 / 组件 / 落地页 / 视觉 / 动效 / RTL / 模板感 列出痕迹与修法。
2. 改多少：重度 slop 全流程；轻度只修审计项；无 slop 直说、最多 2—3 个微调。
3. 方向五行：产品 / 性格（禁用 clean、modern、sleek、minimal、premium）/ 世界 / 时刻 / 签名。
4. 九遍修复：间距 → 颜色 → 图标 → 文案 → 字体 → 布局 → 细节 → 视觉 → 动效。
5. tokens：4px 间距阶梯、字阶、嵌套圆角、Graphite/Warm/Ink 中性色阶、一条缓动曲线。
6. 「富足放在一两个内容时刻，chrome 保持安静」；统计卡是数字，不要每张都塞 sparkline。

mano-design 的落点见 `capabilities/mechanism-sources.md`。规则文字与检查器实现为本 skill 自写，未复制其代码或文本。
