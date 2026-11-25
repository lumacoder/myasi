# 网页滚动与审美工程模式索引（Patterns）

> 适配自 [scrolltide/ai-studio-skill](https://github.com/scrolltide/ai-studio-skill)（MIT License）。
> 全部为轻量原生 JavaScript / CSS 模式，可零摩擦放进 Vanilla、Vite + React 或 Next.js（`'use client'`）。
> 所有文件均构建在 `engine.md` 的单一 `rAF` 引擎之上。

| 模式 | 文件 | 适用场景 |
|---|---|---|
| 单循环引擎与 Beat 窗口 | `patterns/engine.md` | **所有**滚动驱动页面的底座：Lenis、固定舞台 `pinProgress`、`BEATS` 区间、React/Next.js 接入与避坑 |
| 四大主力滚动舞台 | `patterns/stages.md` | **按页面主角时刻选 1 个**：Canvas 帧序列影片（`film`）、同源分层视差（`layers`）、自绘 SVG 路径（`drawn`）、横向胶片卷（`reel`） |
| 排版、表面与无白屏显隐 | `patterns/surface-and-type.md` | 实测全宽字标（`fitText`）、Blur+Tracking 收束标题、实时 HUD 读数、`difference` 自适应导航、单斜体衬线词、`data-reveal` 与循环视频 Hero |

## 组合法则
- **1 个主力舞台 + 安静支撑**：一页围绕 **1 个核心滚动/视觉时刻**展开，其余普通区块用 `data-reveal` 与排版节奏承接。
- **不并排争抢**：同一个视口内绝不同时放两个高负载动效舞台；若长页面包含两个重舞台（如 `layers` 开场 + `drawn` 路线），中间必须隔着普通内容区块。
- **典型长页面节奏**：`layers` 或 `film` 舞台（`440–600svh`） → 普通图文揭示区 → `drawn` 或 `reel` 舞台（`340–380svh`） → 卡片区 → 带 `fitText` 字标的深/浅对比收尾区。
