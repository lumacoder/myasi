# 来源记录：scrolltide/ai-studio-skill（2026-11-25）

- 仓库：https://github.com/scrolltide/ai-studio-skill
- 检出核对日期：2026-11-25（Asia/Shanghai）
- 许可边界（来自仓库根 `LICENSE`）：
  1. `SKILL.md`、`house-style.md`、`patterns/`、`checks.md`、`handoff.md`、`scripts/scrollshot.mjs`、`library/INDEX.md`：**MIT License**（Copyright (c) 2026 Scrolltide）。
  2. `library/*.md`（除 `INDEX.md` 外的 9 个完整模板）及其下载媒体资产：**© 2026 Scrolltide. All rights reserved**，允许用于自用与客户建站，**禁止**作为模板/提示词/套件再分发。

## 融入 Mano-ASI 的精髓（仅取 MIT 部分与设计方法论，未复制任何 `library/*.md` 专有模板）
1. **核心审美公式**：1 句主角滚动/视觉时刻 + 真实自托管媒体 + 克制舞台底色（`rules/web-craft.md`）。
2. **317 站实测 House Style 默认尺**：
   - 非纯黑/纯白底色（深墨 `#04050a`/`#05070c`，暖石 `#efe9df`/`#e9e1d3`），首条 CSS 设在 `html/body` 防白闪；`.apron` 衔接退场。
   - 全页单强调色 + 中性卡片；严禁彩虹发光与紫蓝渐变背景。
   - 流体 `clamp` 字阶、单斜体衬线关键词、等宽 HUD 读数（`tabular-nums`）、实测贴边 `fitText` 字标、`difference` 导航。
   - 形状阶梯（999px / 28px / 2–6px / 嵌套减法）。
   - 双轨动效：定时曲线（`cubic-bezier(0.16,1,0.3,1)` 等）与纯滚动数学映射严格分离。
3. **原生工程模式（`patterns/`）**：
   - `engine.md`：单一 `rAF` 循环 + Lenis + `pinProgress` + `BEATS` 窗口 + `svh` / `overflow-x: clip` 避坑。
   - `stages.md`：帧序列 Canvas（粗到细加载 + Fritsch–Carlson 速度曲线）、同源分层视差、SVG `pathLength="1"` 自绘路径、焦点线横向胶片卷。
   - `surface-and-type.md`：`fitText`、Blur+Tracking 标题、无 JS 不白屏 `data-reveal`、`canplay` 循环视频 Hero。
4. **沿滚动全轨迹验屏（`scripts/scrollshot.mjs`）**：
   - 桌面 `1440×900` + 手机 `390×844` + `first-paint` + `--reduced`，覆盖 `0/25/50/75/100%` 停靠点与卡死舞台/横向溢出/字体加载/外链检查。
