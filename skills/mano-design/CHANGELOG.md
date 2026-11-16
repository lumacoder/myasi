# 更新记录

## 0.2.2 — 2026-11-16
- RSI 第 4 轮（案例 v2 商户治理首轮验证暴露的工具缺陷）：① ty.font-family-sprawl 把打包产物里库样式的 var() 回退栈、系统字体栈、等宽栈里的 Monaco 当成设计字体 → 识别系统字体栈与等宽栈；ty.heavy-weight 不再把 preflight 的 bolder 当重字重（holdout us-lib-font-stacks-ok 先写后测，首轮 REJECT 96.57）；② cs.destructive-no-confirm 把「清空搜索」当危险操作 → 只改视图状态的清空/清除搜索/筛选/输入不算（holdout clear-search-not-destructive，首轮 REJECT 97.62）；两条都配了仍应报的反例。另：visual_capture --views 步骤按书写顺序执行（先 wait 等回放再 click），多原型基准轮流取（次原型的 React Flow 基准不再被挤掉）；workflow-graph-replay 增加 pitfalls（React Flow 不可选节点吞点击等）
- eval：110/110，score 100.0，holdout 100.0

## 0.2.1 — 2026-11-16
- RSI 第 3 轮（借鉴 heydamir/unslop，CC BY 4.0 署名）：新增 type 类别与 9 条视觉卫生 lint 规则——co.glow-shadow、co.gradient-text、co.near-duplicate-colors（只看文字色）、ty.font-family-sprawl、ty.size-sprawl、ty.heavy-weight、ty.uppercase-tracked、ly.off-scale-spacing（含 Tailwind 任意值）、cp.shouty-copy；18 个用例（4 个 holdout 先写后测：首轮 3/4，us-tw-glow-class 暴露了阴影模糊半径解析缺陷——未带单位的 0 偏移被跳过——通用修复后全对）；browser_check --visual-stats 渲染后统计调色板/字体/字号/奇数间距；流程加入方向五行、改多少分级、九遍顺序；unslop 自带的 3 个 vibecoded 示例被新规则全部命中
- eval：106/106，score 100.0，holdout 100.0

## 0.2.0 — 2026-11-16
用户反馈 v0.1 只会挑错、视觉 4.5/10、缺创意 → 新增「视觉与创意」层，面向任何页面类型，机制逐条源自用户给的 3 条帖子（`capabilities/mechanism-sources.md`）。
- 新流程 `capabilities/visual-design.md`：理解 → 原型 → 逐区块基准 → DESIGN.md-lite → 主题 → 领域创意 pass → 反默认自审 → 主流组件实现 → 检查 → 联系表苛刻评审（先修 3 个）→ 视觉评分 ≥8 门禁。
- `visual/archetypes.json` 17 类原型（含 impeccable 四种模式）；`visual/benchmarks.json` 65 条基准/画廊（GitHub API 与站点核实，2026-11-16 快照，含许可与 capture_url）；`capabilities/benchmark-discovery.md` 现找现核实流程。
- `visual/creative-patterns.json` 51 个领域签名可视化/交互；`visual/themes.json` 8 套主题（明暗、shadcn 命名、全部 AA 实测）+ `scripts/theme.py`（--pick/--css/--check）。
- `visual/rubric.md` 8 维 × 锚点 × 模式权重；`scripts/visual_score.py` 门禁（证据、与基准一致性、单维下限、阻断级问题封顶、自评 −0.5）；`scripts/archetype.py` 原型识别；`scripts/visual_capture.py` 截图联系表 + 基准对照 + 评审提示。
- `browser_check.py`：多路由 `--routes`、等待真实内容 `--wait-for/--wait-ms`、`--color-scheme dark`、`--shots`、`--axe-path`、页面脚本报错计入。
- 自测：原型识别 17/17、评分门禁 7/7、主题对比度 8/8 并入 `validate.py`（首轮实测发现 4 个主题的焦点环对比 <3:1，已修正）。

## 0.1.2 — 2026-11-16
- RSI 第 2 轮（商户治理案例）：新增 6 条规则——lint：ly.placeholder-as-metric / cs.stat-card-filter（含事件委托）/ cp.opaque-id；rubric：st.contradictory-status / st.selection-panel-mismatch / cp.redundant-status。新增 12 个 fixture（6 个 holdout 在改检查器前写好，首轮即全对；1 个 holdout 删除了与规则无关的空 <ul> 噪声）与 3 个 rubric 回归样例
- eval：88/88，score 100.0，holdout 100.0

## 0.1.1 — 2026-11-15
- RSI 第 1 轮：cs.binary-select 扩展到二值单选对（有默认选中、组标题非问句）与 aria-pressed 按钮组；新增 4 个用例（2 漏报 + 2 正确对照，其中 2 个 holdout）
- eval：76/76，score 100.0，holdout 100.0

## 0.1.0 — 2026-11-15
- 首版：53 条规则（lint 35 / rubric 17 / browser 1），72 个自测用例（train 50 / holdout 22），开源方案目录 27 条（核心 13）。
- 首轮成绩：train 47/50（3 处：2 处为标注错误——白字在 #a855f7 上与橙色字在白底上确属低对比；1 处检查器缺陷——`.a` 类名被当成 `a` 标签；另修正长段落按 CJK 字宽计算），第一批 holdout 12/12（先写后测）；修复后全集 62/62。第二批 holdout 10 条先写后测 10/10。
- 真实页面抽查发现 CSS 变量（var(--x, #fff)）被按回退值计算导致对比度误报，增加 var() 解析，无法解析时视为未知。
