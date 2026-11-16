# 视觉设计流程（任何页面类型）：从「挑错」到「做得好看、做得有创意」

> 机制来源逐条见 `capabilities/mechanism-sources.md`。交互正确性（组件选型、状态、对比度）仍由 `rules/` + `ui_lint` 把关；
> 本流程负责**视觉质量与创意**，并以 `visual_score.py` 的 ≥8 分门禁收口。商户治理后台只是第一个测试案例，不是默认风格。

```
理解 → ① 原型识别 → ② 基准（逐区块）→ ③ 风格规格 DESIGN.md → ④ 主题 → ⑤ 领域创意 pass → ⑥ 方案自审（反默认）
     → ⑦ 用主流组件实现 → ⑧ ui_lint + browser_check → ⑨ 取证对照表 → ⑩ 苛刻评审·先修 3 个 → ⑪ 视觉评分 ≥8 → 交付
```

## 0 理解（30 秒）
一句话写清：**这是什么产品 / 给谁用 / 这一屏的主要任务 / 领域对象是什么**（工作流、商品、文章、运行、商户、订单…）。
用户给了截图：先把截图转成结构描述（区块、组件、数据、状态），再走后续步骤；原图的配色**只是证据，不是约束**（用户没指定主题时）。

## ① 原型识别
`python3 scripts/archetype.py "<一句话需求>"` 或 `--file page.html` → 主原型（定外壳）+ 次原型（定局部），以及模式：
Persuade（说服）/ Operate（操作）/ Read（阅读）/ Experience（沉浸）。模式决定创意预算与评分权重：
Operate/Read 的大胆体现为**精确与克制 + 一个签名可视化**；Persuade/Experience 才放开动效与视觉冲击。
未命中时按 `visual/archetypes.json` 的 17 类手动归类，必要时新增原型（同时加基准与签名模式，并补 `visual/examples/archetype_cases.json`）。

## ② 基准（逐区块）
- 先用 `archetypes.json` 的 `seed_benchmarks`；种子不够或过期时，按 `capabilities/benchmark-discovery.md` 现找、现核实（GitHub stars/许可/最近提交 + 打开 demo 截图）。
- **逐区块找参考**（来自 himanshubuildss 帖的 navbar.gallery / footer.design / cta.gallery 与 scrolltide 的「整页/区块/组件/背景」分层）：
  原型的 `sections` 每一块都要有一个参考（导航、首屏、KPI 行、表格、详情抽屉、页脚、CTA…），而不是整页只看一个。
- 写下「从每个基准借什么」（版式/密度/组件/交互），**不复制代码、文案、图片或签名特效**（taste-skill「Never」条款）；reference-only 许可只借思路。

## ③ 风格规格（DESIGN.md-lite，动手前写）
来自 refero styles（真实网站 → AI 可读 DESIGN.md）与 anthropics frontend-design 的「两遍法」。模板：`visual/design-spec.template.md`。
先写 unslop 的**方向五行**：产品（做什么、给谁）/ 性格（2—3 个具体词，禁用 clean、modern、sleek、minimal、premium、简洁、高级）/ 世界（产品天然所属的场所或材质，决定中性色调、强调色与视觉）/ 时刻（1—2 处承载色彩与细节的内容）/ 签名（只有这个产品才有的一个小细节）。
再写：一句**材质隐喻**（如「夜间调度台」）、4—6 个命名色（hex）、字体角色与字阶、布局概念（一句话 + ASCII 线框）、签名元素、动效预算、明确**不做**什么。
用户/品牌有 DESIGN.md 或设计系统 → 直接用它，跳过 ④ 的挑选。

## ④ 主题（未指定时必须自己选）
`python3 scripts/theme.py --pick "<行业 受众 产品>" --mode <模式>` → 前 3 候选与理由；`--css <id>` 输出 shadcn 命名的 `:root/.dark` 变量（全部经 `--check` 实测 AA）。
选择原则：
1. 行业/受众优先（金融运营→信号蓝；本地生活→市集橙；医疗教育→诊所青；AI/创意→工作室紫的**实色**；阅读→暖纸只在有理由时）。
2. **语义色不与品牌色撞**：大量「成功/盈利」用绿 → 品牌别选绿；大量「需关注」用琥珀 → 品牌别选橙。
3. 明暗两套都要做；Operate 页面提供切换。
4. 不知道选什么时**不要**落到 AI 默认（暖奶油+衬线+陶土色、黑底+荧光绿、紫蓝渐变，见 ⑥）。

## ⑤ 领域创意 pass（一页一个记忆点）
从 `visual/creative-patterns.json` 选 **1 个**签名可视化/交互（主原型或次原型的 `signature_patterns`），写清：
它表达哪个领域对象、点了会怎样、动效时长、reduced-motion 降级、用哪个开源组件实现（许可）。
例：工作流 → 节点图 + 运行回放（@xyflow/react）；看板 → KPI + sparkline；日志 → 时间线；电商 → 规格色块 + 吸底购买栏；文档 → ⌘K 搜索；作品集 → 指针揭示。
**Spend your boldness in one place**：其余部分保持安静；签名必须同时更好用，不只是好看。

## ⑥ 方案自审：反默认（动手写代码前）
逐条问「这是为这个产品做的选择，还是任何页面都会出现的默认？」（anthropics frontend-design 的 AI 聚类 + hallmark Floor + impeccable 禁令）：
- 暖奶油底 + 高反差衬线 + 陶土色；近黑底 + 单一荧光色；报纸式细线零圆角；
- SaaS 卡片套件（同一圆角、同一灰阴影、渐变装饰）；卡片套卡片；
- 每个标题上的全大写小眉标、`A · B · C` 中点元信息、链接后缀「→」、emoji 当图标；
- 首屏「大数字 + 小标签 + 渐变点缀」；01/02/03 编号却不是顺序内容；每个区块都淡入上滑。
命中的要么改掉，要么写明理由（例如用户点名要这种风格）。

## ⑥b 改多少（重做已有页面时）
先按 signs 审计（`ui_lint` 的 co./ty./ly./cp. 视觉卫生规则 + `browser_check --visual-stats`）：**重度**（颜色、字体、图标、文案多处命中）→ 全流程重做；**轻度** → 只修审计到的点，沿用现有品牌与版式，大想法写进建议；**无** → 直说，最多给 2—3 个带具体数值的微调，不为不同而改（unslop）。

## ⑦ 实现：主流组件 + token
- 组件：项目已有设计系统 > shadcn/ui（Radix）风格 > 其他；图标一套（lucide）；Toast 用 sonner 风格；图表 Recharts/Tremor；节点图 @xyflow/react。
- 按 unslop 的九遍顺序落地：间距 → 颜色 → 图标 → 文案 → 字体 → 布局 → 细节（嵌套圆角 = 外圆角 − 内边距、计数用安静文字/键帽、图表一个强调色）→ 视觉 → 动效；每遍覆盖全屏再进下一遍。
- 所有颜色/字体走 token（hallmark Floor #1）；`transform/opacity` 动画，不用 `transition: all`；每个动画有 reduced-motion。
- 交付形态需要「双击即开」时：Vite + vite-plugin-singlefile 打成单个 HTML（离线可用，不依赖 CDN）。

## ⑧ 检查（确定性）
`ui_lint.py`（源码/产物）+ `browser_check.py dist/index.html --routes "#/a,#/b" --wait-for "<真实内容选择器>" --axe-path axe.min.js --visual-stats`（渲染后的字体家族/字号/调色板/奇数间距作为视觉评分证据），明暗各一次。critical/major 必须清零。

## ⑨ 取证：联系表
`python3 scripts/visual_capture.py dist/index.html --out shots --views "..." --archetype <主>,<次> --dark --mobile`
→ 所有视图（含关键状态：抽屉打开、对话框、空状态）+ 暗色 + 手机宽度 + 基准截图 → `contact-sheet.png` + `review.md`。

## ⑩ 苛刻评审·先修 3 个（Y0urDumble 帖引用文章的 review loop）
新会话/子代理执行 `review.md`：「这不是你做的，你是最苛刻的设计总监」，列出所有问题 → **只修最严重的 3 个 → 只重拍受影响的视图** → 再看。
预算：一次批量检查、一次修复批、至多一次确认轮（hallmark：verification is budgeted）。

## ⑪ 视觉评分门禁
按 `visual/rubric.md` 写评分 JSON → `python3 scripts/visual_score.py score.json --check-files`。
通过条件：加权 ≥8、单维 ≥6、无阻断级 lint/browser 问题；≥8 的维度必须与基准 par/above，并有截图证据；自评额外 −0.5。
未通过：按 `weakest` 与 top3 回到 ③—⑦。两轮仍 <8：如实交付当前分数与差距原因，不虚报（「A fabricated pass is itself slop」——hallmark）。

## 沉淀（RSI）
评审发现的新问题：能静态判定的 → 失败日志 → `rsi/ingest.py` → 改 `ui_lint` → `rsi/gate.py`；视觉/创意类 → 补 `creative-patterns.json`、`archetypes.json`、`themes.json` 或 rubric 锚点，并补对应自测样例。
