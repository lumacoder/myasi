# CHANGELOG — mano-asi

## 0.2.0 — 2026-11-25
- 融入 [scrolltide/ai-studio-skill](https://github.com/scrolltide/ai-studio-skill) 的 MIT 开源精髓（不含其专有 `library/*.md` 模板）：
  - 新增 `rules/web-craft.md`：一句主角时刻、317 站实测 House Style（深墨/暖石底色、单强调色、单斜体衬线词、`fitText`、双轨动效、`svh`/`overflow-x: clip`）与全源码交接规范。
  - 新增 `patterns/`（`INDEX.md`、`engine.md`、`stages.md`、`surface-and-type.md`）：单一 `rAF` 引擎 + Lenis、WebP 帧序列 Canvas、同源分层视差、自绘 SVG 路径、横向胶片卷、`data-reveal` 与视频 Hero。
  - 新增 `scripts/scrollshot.mjs`：基于 Playwright 的桌面/手机/reduced-motion 多停靠点全滚动轨迹验屏。
  - `rules/vocab.json` 新增 6 条网页与滚动词汇（共 36 条）；`cases/cases.json` 新增 `scrolltide/ai-studio-skill` 与 `darkroomengineering/lenis`（共 60 条，附 `cases/sources/2026-11-25_scrolltide_ai-studio-skill.md` 许可记录）。

## 0.1.0 — 2026-11-15
- 首版发布（前身 DevASI）：五步研发闭环、`rules/`（output/vocab/motion/hygiene）、`capabilities/`（product-logic/design-extract/arch-read）与 58 条开源案例库。
