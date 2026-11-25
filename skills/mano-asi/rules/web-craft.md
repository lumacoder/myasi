# 网页审美与滚动叙事规范（Web Craft）

> 适用：任何网页、落地页、产品官网、作品集、交互展示页与品牌站点。
> 宗旨：拒绝「文档式堆叠 + 处处淡入」的 AI 模板感，用**单一主角时刻、克制舞台底色、实测审美参数与全滚动链路验屏**做出具备顶级开源项目水准的网页。
> 理念与基准参考 [scrolltide/ai-studio-skill](https://github.com/scrolltide/ai-studio-skill)（MIT 部分：指令、House Style、模式与检查脚本），按 Mano-ASI 工程约束本土化重构。

## 1. 动笔前先定 Brief（不写废话）
快速定出 4 件事并在首轮简短告知用户，只在缺真实业务名等不可编造项时发问：
1. **对象与受众**：什么产品/团队，要打动哪类访客。
2. **主角时刻（一句说清）**：用户交互或滚动时发生哪件令人记住的事（如「滚动把相机从工作台推入表芯」「六层前景随滚动错层退开」「路线随滚动自绘并驱动里程读数」）。**说不出这一句，就先别堆区块。**
3. **气质三词**：不用 `clean / modern / premium / 高级 / 简洁` 等空词，改用具体质感词（如「冷墨、航天仪表、克制」「暖纸、手工制表、沉稳」）。
4. **落地载体**：
   - 已有项目：严守其现有技术栈（Next.js / Vite / Astro 等）与既有设计系统。
   - 新建工程（有 Node）：Vite + React + TypeScript + Tailwind（或按需引入 Lenis）。
   - 单文件交付 / 无构建环境：原生 HTML + CSS + JS（可从固定版本 CDN 引入 Lenis）。
   - 给其他建站工具出提示词：见第 6 节「全源码交接」。

## 2. 实测开源审美标尺（House Style）
> 下述默认参数源自 Scrolltide 对 **317 个已发布高质量网页作品**的源码统计；用户明确指定或项目已有设计系统时，以既有规范为先。

### 2.1 底色（Ground）：底色是舞台，不是装饰
- **深色底用调过色相的墨色，不用纯 `#000000`**：推荐冷调深墨 `#04050a`、`#05070c`、`#07080b`、`#03060a`。
- **浅色底用温润纸/石色，不用纯 `#ffffff`**：推荐暖石纸 `#e9e1d3`、`#efe9df`、`#f2eee6`、`#ebe8e1`。
- **防首屏白闪**：在第一条 CSS 规则就给 `html, body` 设上底色（`background: var(--ground)`）。
- **固定舞台无接缝退场（Apron）**：当 `position: sticky` 舞台结束时，最前景层底部带一块与下一区块同色的实色裙边（`.apron { position: absolute; left: 0; right: 0; top: 100%; height: 110vh; background: var(--ground); }`），让舞台像幕布一样滑走而不断层。

### 2.2 强调色（Accent）：全页单强调色
- **每页只允许 1 个主强调色（accent）**，仅用在小而关键的「工作部件」上：眉标（eyebrow）、实时状态点、进度条、主按钮/焦点环、标题里的那 1 个高亮词。
- 卡片与面板保持中性石墨（深色）或暖石（浅色），仅用极细微的内高光或 hairline 边框区隔层级；**把色彩 richness 留给真实媒体本身**。
- **严禁**：每张卡片各自配不同颜色发光（紫/橙/绿角落 glow）、玻璃拟态叠玻璃拟态、紫蓝渐变作主视觉、抽象彩色 blob 充当插画。

### 2.3 字体排印（Typography）
- **字体族克制**：全页 1–2 个字体族（含等宽读数时最多 3 个）：
  - 正文与 UI：`Inter`（中文混排配 `Noto Sans SC` / 系统黑体回退，不假定西文字体含中文）。
  - 展示标题：按品牌气质选 1 款有性格的字体（如 `Satoshi` / `Archivo` / `Fraunces` / `Playfair Display` / `Michroma`）。
  - **单斜体衬线关键词（The Serif Word）**：在无衬线主标题里，挑**唯一 1 个核心词**用斜体衬线（如 `Instrument Serif italic`）强调（如 `Technology crafted for all. Not *machines*.`）；仅限 1 个词，多用即失效。
  - 等宽读数与眉标：`JetBrains Mono` / `Geist Mono` / `IBM Plex Mono`。
- **尺度与字距**：
  - 展示大字用流式 `clamp`：区块标题 `clamp(2rem, 5vw, 64px)`，Hero 主标题 `clamp(2.75rem, 6vw~8vw, 80px~104px)`；`line-height: 0.9~1.0`；字距 `-0.02em` ~ `-0.04em`。
  - 正文：`16px` 左右，`line-height: 1.5~1.6`，字距 `-0.01em`（中文正文不套用英文宽字距）。
  - 全大写等宽小标签：`0.625rem~0.75rem`，字距 `+0.14em ~ +0.2em`，降低不透明度（约 `0.75`）。
  - **动态数字强制 `font-variant-numeric: tabular-nums`**（计时器、里程、价格、百分比），避免数字跳动。
  - **贴边全宽字标（Wordmark）实测缩放**：不要靠 `vw` 瞎猜（字形宽窄不同必溢出或留白），用 `fitText()` 探测后按容器宽比缩放（见 `patterns/surface-and-type.md`）。

### 2.4 形状与圆角（Shape）
- 主操作按钮：胶囊 `border-radius: 999px`。
- 常规内容卡片：`28px`（或全站统一的主卡片圆角）。
- 技术/数据元件（标签、HUD 框、胶片框、chip）：锐利 `2px–6px`。
- **嵌套圆角法则**：内层圆角 = `外层圆角 - 内边距`（若结果 ≤ 0 则用直角）。

### 2.5 双轨动效（定时动效 vs 滚动数学）
- **定时动效（入场、悬停、状态切换）**：
  - 主入场与揭示：`cubic-bezier(0.16, 1, 0.3, 1)`（600–800ms）
  - 柔和入场：`cubic-bezier(0.22, 1, 0.36, 1)`
  - 弹性微弹/开关：`cubic-bezier(0.34, 1.56, 0.64, 1)`
  - 卡片/步骤切换：`cubic-bezier(0.2, 0.7, 0.1, 1)`（250–400ms）
  - 悬停反馈：`200ms`
- **滚动驱动动效（绝不定时，也不走 framework state）**：
  - 完全由**滚动进度 `p ∈ [0, 1]` 的纯数学函数**计算（`range` + `easeOutCubic` / `smoothstep` + `lerp` + 显式 `BEATS` 区间）。
  - **绝不对 rAF 每帧写入的属性加 CSS `transition`**（两者打架会导致粘滞与掉帧）。

## 3. 工程结构与选型（按需组合 `patterns/`）
- **内容与主题分离**：所有文案集中放在单一内容文件（如 `src/content.ts`），所有色板/字体/间距 token 集中放在 `:root` / `@theme`，换品牌只需改这两处。
- **单一 `rAF` 引擎 + 单个重型舞台**：
  - 全页只跑 **1 个 `requestAnimationFrame` 循环**（可由它驱动 Lenis `lerp: 0.09`），**禁止**同时装两个滚动库或把手写循环叠在第三方滚动触发器上。
  - **同一视口只放 1 个重型舞台**（Canvas 帧电影 / 多层视差 / WebGL / 视频 Hero），避免视觉抢戏与性能过载。
  - 舞台高度用 `svh`（如主影片 `600svh`、多层/路径 `380–440svh`、胶片卷 `340svh`），固定容器用 `100svh`；防横向溢出在 `html, body` 用 `overflow-x: clip`，**绝不用 `overflow: hidden`**（会直接杀死 `position: sticky`）。

| 页面需求 | 推荐组合（详见 `patterns/INDEX.md`） |
|---|---|
| 滚动推动产品/相机运镜、按节点停顿出卡片 | `engine.md` + `stages.md#film`（WebP 帧序列 + 单调速度曲线） |
| 叙事型官网/发布会、空间纵深开场 | `engine.md` + `stages.md#layers`（同源切层 + 夹心标题 + `.apron`） |
| 路线/流程/时间轴随滚动自绘 + 数字联动 | `engine.md` + `stages.md#drawn`（`pathLength="1"` + 领航点） |
| 3–6 张作品/里程碑横向穿过焦点线 | `engine.md` + `stages.md#reel`（焦点缩放 + 画框反向视差） |
| 单屏大气官网/工作室/SaaS 首屏 | `surface-and-type.md#video-hero`（`canplay` 淡入 + 局部对比保护） |
| 其余普通区块与文字收尾 | `surface-and-type.md#reveals` + `#type`（无 JS 不白屏 + 实测字标 + `difference` 导航） |

- **媒体优先级（严禁外链与灰框）**：
  1. 用户提供的真实图片/视频/3D 资源，全部下载进 `public/` 自托管（**源码中不得残留来源下载 URL**）。
  2. 需要铺满屏幕的视觉准备**桌面横版 `d/` 与手机竖版 `m/` 两套构图**（`<picture>` 或宽高比切换），保证小屏不是硬裁切。
  3. 有生成工具时生成配套静帧/分层；**没有媒体就做纯排版主导页（type-led）**，绝不用灰色占位框，也不在图库照片上糊一层全屏黑罩来凑文字对比度。
- **文案真实与具体**：优先写带单位的具体数字（`384,400 km`、`481 帧`）与直接行动按钮（`预约演示`、`查看源码`）；不编造真实公司的价格、评价与客户数，演示占位数据在 `content` 文件中显式标明。
- **可访问性与降级（硬门槛）**：
  - `prefers-reduced-motion: reduce`：关掉 Lenis 平滑与漂移循环，保留滚动位置映射或直接呈现终态，所有入场直达可见。
  - `(hover: none)`：关闭仅依赖鼠标悬停的效果。
  - 无 JS 防白屏：`<head>` 首行加 `js` 类，隐藏 `[data-reveal]` 仅在 `.js` 存在时生效。
  - 390 / 768 / 1280 / 1920 四个宽度均无横向滚动条；可读 `<title>`、真实 `alt`、装饰层 `aria-hidden="true"`、可见键盘焦点。

## 4. 沿滚动轨迹验屏（不止看首屏）
滚动页面常出现「首屏完美、滚到 40% 卡死或裁切」的问题。有 Node + Playwright 环境时，交付前**必须**运行 `scripts/scrollshot.mjs` 检查全轨迹：
```bash
node <mano-asi>/scripts/scrollshot.mjs http://localhost:5173 shots --reduced
# 或针对构建目录 / 单文件：
node <mano-asi>/scripts/scrollshot.mjs dist shots --stops 0,10,20,30,40,50,60,70,80,90,100 --reduced
```
检查清单（并结合 `rules/output.md` 如实汇报；无浏览器环境时如实写「未截图检查」并对照代码逐项静态核对）：
1. **阻断项清零**：控制台/脚本报错、请求失败/404、破损图片、视频未就绪、横向溢出、首屏白闪、`<h1>` 回退成系统字体、残留占位文案（`Lorem`/`Feature 1`）、外链盗链媒体。
2. **逐停靠点审图**：桌面（`1440×900`）与手机（`390×844`）相邻截帧在固定舞台内是否真的在变化（`sameAsPrevious` 为真说明 sticky/循环失效）；主体是否在框内；字幕在各位置是否清晰可读；退场 `.apron` 衔接是否无接缝；`reduced-*.png` 所有内容是否直接可见。
3. **House Style 集中修前 3 项**：对照第 2 节挑出最破坏审美的 3 处（常见：多强调色/彩光、标题太小或字距为 0、纯黑/纯白底、同屏双重强动效、默认 `ease`/`linear`、空洞文案），修完复拍一轮，最后按 `rules/hygiene.md` 清理临时截图目录或明确汇报保留的证据。

## 5. 全源码交接（输出给其他 AI 建站工具时）
当用户要求生成给 Lovable / Bolt / v0 / Cursor / Windsurf 使用的提示词时，**不要输出空泛描述**，而是先保证架构与代码自洽，再输出包含「项目意图 + 核心加载机制（如单循环/Beat 窗口）+ 精确依赖清单 + 资源自托管路径 + 集中式 `content` 与 token + 完整文件源码」的可直接复现提示词（如目标为 v0/Next.js，提醒将滚动引擎与舞台标记为 `'use client'`）。

## 6. 复杂业务后台补充说明
若任务属于复杂的企业级 SaaS 控制台、密集表格、审批流或需要逐组件静态规则审计（如 Switch vs Checkbox、Tabs vs Accordion）与 0–10 视觉评分门禁，可同时结合本仓库的 `mano-design`（若已安装）；一般官网、展示页、产品页与全栈 Web 交付直接按本规范 + `patterns/` 执行即可闭环。
