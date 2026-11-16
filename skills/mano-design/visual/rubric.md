# 视觉评分 Rubric（0—10，交付门槛 ≥ 8）

> 用于**任何页面类型**。先用 `scripts/archetype.py` 定原型与模式（Persuade / Operate / Read / Experience），模式决定权重；
> 再把**自己的截图**与**同原型基准截图**并排看（`scripts/visual_capture.py` 生成对照表），逐维打分并写证据。
> 评审姿态（来自 Y0urDumble 帖引用文章的 review loop）：**「这不是你做的。你是我认识的最苛刻的设计总监。」**
> 列出每个问题（带截图文件名/区域），**先修最严重的 3 个，只重拍受影响的视图**，再给新的对照表。

## 核心原则：主流 + 有代表性 = 高分
- 高分不是「我觉得好看」，而是**和该原型的主流优秀产品并排时不掉档**（`vs_benchmark`：below / par / above）。
- **≥8 必须 par 或 above；≥9 必须 above 且说明超出点**。说不出基准是谁，就不能给 8。
- 门禁同时看「下限」：任何一维 < 6、或 ui_lint / browser_check 仍有 critical/major → 直接不通过（总分封顶 6）。

## 8 个维度与锚点
| 维度 | 2 | 4 | 6 | 8 | 10 |
|---|---|---|---|---|---|
| **hierarchy 布局与层级** | 元素平铺无主次 | 有分区但主次混乱，关键信息不突出 | 主次清楚，但个别区块争抢注意力 | 一眼知道先看什么；栅格/对齐/留白与基准同档 | 层级本身成为表达；眯眼测试仍清晰 |
| **typography 字体排印** | 系统默认、字号随意 | 字号层级少于 3 档或过多，行长失控 | 有字阶，数字未用等宽/表格数字 | 字阶、字重、行高、数字对齐都讲究；中文排版（标点、混排间距）到位 | 字体选择带个性且服务题材 |
| **color 配色与主题** | 杂乱/对比不足 | 主题与产品无关（照搬截图色或 AI 默认色） | 克制可用，但语义色与品牌色冲突或暗色模式敷衍 | 主题按行业/受众选并能说明理由；语义色独立；明暗两套都实测 AA | 配色形成记忆点且不牺牲可读性 |
| **polish 组件精致度** | 原生控件/错位 | 圆角/阴影/边框不统一，状态缺失 | 主流组件库水准，偶有粗糙处（图标大小、间距） | 与 shadcn/ui 等主流组件同档：8 种状态、焦点环、骨架屏、空状态都有 | 微交互细节超出基准 |
| **density 信息密度与节奏** | 过空或塞满 | 密度与模式不符（后台像海报 / 落地页像表格） | 基本合适，个别区域拥挤或稀疏 | 密度符合模式与基准，间距节奏统一（4/8 倍数） | 密度随任务自适应（紧凑/舒适切换等） |
| **motion 动效与愉悦** | 无反馈或乱动 | 动效随意、transition: all、无 reduced-motion | 有基本过渡与反馈 | 动效解释变化（进入/退出/状态），时长 150—300ms，有 reduced-motion | 有一处编排得很好的「记忆点」动效 |
| **creativity 创意与领域契合** | 模板感、可贴到任何产品 | 只是把原组件换皮 | 有一点领域化处理 | 有一个**来自领域对象的签名可视化/交互**（见 creative-patterns.json），且服务任务 | 签名设计让人想截图转发，同时更好用 |
| **consistency 一致性** | 多种风格打架 | 页面间组件/术语不一致 | 大体一致，少量漂移 | 一个设计方向贯穿所有页面与状态（philosophy consistency） | 每个细节都在论证同一个方向 |

## 模式权重（总和 1）
| 维度 | Operate | Persuade | Read | Experience |
|---|---|---|---|---|
| hierarchy | .18 | .14 | .18 | .10 |
| typography | .10 | .16 | .22 | .12 |
| color | .10 | .12 | .08 | .12 |
| polish | .16 | .12 | .12 | .12 |
| density | .16 | .06 | .12 | .04 |
| motion | .08 | .14 | .04 | .18 |
| creativity | .10 | .16 | .08 | .22 |
| consistency | .12 | .10 | .16 | .10 |

## 输出（交给 `scripts/visual_score.py` 校验与计算）
```json
{"target":"dist/index.html","archetype":"workflow-automation","mode":"Operate","reviewer":"fresh|self",
 "screenshots":["shots/01-workflows-light.png"],"benchmarks":["shadcn-admin","react-flow"],
 "lint_blocking":0,"browser_blocking":0,
 "dimensions":{"hierarchy":{"score":8,"vs_benchmark":"par","evidence":"…截图/区域/对比基准…"}, "…":{}},
 "top3":["最该修的 3 个问题"]}
```
`reviewer: self` 时总分额外 −0.5（自评偏高的已知偏差；有条件就用新会话/子代理评审）。
