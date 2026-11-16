# 基准发现：给任何页面类型找到「当前主流、有代表性」的参考

种子目录 `visual/benchmarks.json`（65 条，覆盖 17 类原型；stars/许可为 2026-11-16 快照）只是起点。种子缺失、过期或与需求不贴合时，按下面流程现找现核实。

## 1 拆成「整页 + 区块」两级
- 整页：同原型、同模式的 2—3 个产品（例：工作流 → React Flow Workflow Editor 模板、n8n 执行视图、Kestra 拓扑）。
- 区块：原型 `sections` 里每块一个参考（导航 → navbar.gallery；页脚 → footer.design；CTA → cta.gallery；Hero 背景 → scrollshaders；滚动区块/组件 → scrolltide、snapblocks；整站风格 → styles.refero.design）。
  这是 himanshubuildss / nikosolenne 两帖给出的资源结构：**按区块分类的画廊**，比整页模板更容易拼出「主流且不雷同」的页面。

## 2 找候选（并行）
| 渠道 | 查询写法 | 适用 |
|---|---|---|
| GitHub | `<原型英文> template shadcn` / `<领域> dashboard open source` / topic:`admin-dashboard` `workflow` `landing-page`，按 stars 与最近提交排序 | Operate / Read 类，可直接用的开源实现 |
| 组件官方示例 | ui.shadcn.com/blocks、reactflow.dev/ui、tremor.so/blocks、各文档框架 showcase | 区块级、组件级 |
| 风格库 | styles.refero.design（按「Linear-style SaaS」「Dense marketplace」「Dark mode SaaS」等标签）| 风格规格与主题 |
| 区块画廊 | navbar.gallery / footer.design / cta.gallery / scrolltide / snapblocks / scrollshaders | Persuade / Experience 的区块与动效 |
| 行业头部产品 | 该行业 2—3 个头部产品的公开页面/文档截图 | 领域惯例（术语、数据形态） |

## 3 核实（每个候选都做，写进记录）
1. **存在且活跃**：GitHub API 取 `stargazers_count / license / pushed_at`（近 12 个月有提交）；站点 HTTP 200。
2. **许可**：MIT/Apache/ISC 可作依赖；NOASSERTION/AGPL/自定义许可 → `reference-only`，只借思路。
3. **看真实界面**：用 headless Chrome（`visual_capture.py --bench-urls`）打开并截图——营销首页不能当 Operate 基准，要找真实产品屏（demo、模板预览、文档截图）。
4. **代表性**：同类中 stars/采用度靠前，或被官方组件库/头部产品采用；小众但惊艳的放进「创意来源」而不是「主流基准」。

## 4 记录与沉淀
- 在评分 JSON 的 `benchmarks` 写 id 或 URL；在 DESIGN.md-lite 写「区块 → 参考 → 借什么」。
- 新的好基准：补进 `visual/benchmarks.json`（id、repo、stars、license、demo_url、capture_url、archetypes、use、what、borrow、verified），并更新对应原型的 `seed_benchmarks`；`validate.py` 会检查引用完整性。
