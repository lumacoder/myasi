# 机制来源：mano-design 的视觉/创意机制从哪里来

用户给的 3 条帖子（及其链接资源）以及用户补充的 heydamir/unslop 是本机制的出处。下表把**每个机制步骤 → 来源 → 这个 skill 怎么用**一一对应。帖子原文与链接核实记录见 `cases/sources/`；资源内容 2026-11-16 重新打开阅读。

## 三条帖子各自体现的机制
| 帖子 | 资源 | 体现的机制 | 落到 skill |
|---|---|---|---|
| [himanshubuildss](https://x.com/himanshubuildss/status/2118769896591106302) | navbar.gallery、footer.design、cta.gallery | **按区块分类的参考画廊**：好页面是由一个个被认真设计过的区块组成的，参考应逐区块找 | `archetypes.json` 每类原型列出 `sections`；`benchmark-discovery.md` 第 1 步「整页 + 区块」；DESIGN.md-lite 的「区块 → 参考 → 借什么」表 |
| 同上 | styles.refero.design（2,000+ 真实网站风格 + AI 可读 DESIGN.md；每个风格一句材质隐喻，如 Vercel「白纸上的排版终端」、Raycast「午夜指挥中心」） | **先从真实产品抽取风格规格，再动手**；用材质隐喻统一所有微观决策 | 流程第 ③ 步 DESIGN.md-lite（必须写材质隐喻）；`themes.json` 每个主题带 `metaphor`；主题选择看真实同类产品 |
| 同上 + [nikosolenne](https://x.com/nikosolenne/status/2121378167927480347) | scrolltide.co（149 模板/107 组件/55 shader/区块 bands/「landing 背后的产品屏」，每项一条可复制的提示词） | **四层素材**：整页 → 区块 → 组件 → 背景；连「产品屏」（dashboard/wallet/console）也要按参考排布 | 基准分层；`creative-patterns.json` 的 Persuade/Experience 条目（scroll-story、shader-hero、live-product-hero）以它为来源；Operate 页面也要做「一个记忆点」 |
| [nikosolenne](https://x.com/nikosolenne/status/2121378167927480347) | snapblocks.site（136 个滚动驱动组件，每个附「完整重建提示词」：文件全文 + 固定版本） | **组件级创意 pass**，且创意必须可复现（明确依赖与版本） | 创意 pass 要写「用哪个开源组件 + 许可」；引入前过本 skill 的状态/可访问性规则 |
| 同上 | scrollshaders.com（WebGL2 无缝循环；离屏暂停、DPR≤2、reduced-motion 显示静帧） | **动效礼仪**：氛围动效必须便宜、可暂停、可降级 | rubric「motion」锚点；`creative-patterns.json` 每条写 motion 预算与降级；shader 只用于技术类品牌（与 taste-skill 一致） |
| [Y0urDumble](https://x.com/Y0urDumble/status/2120197632500887856) | anthropics/skills `frontend-design` | **从题材里长出设计**；两遍法（先出 token 计划→对照「默认」自审→再写码）；AI 默认审美聚类清单；「把大胆花在一个地方」；边做边截图自评 | 流程 ⓪ 理解（领域对象）、③ DESIGN.md-lite、⑥ 反默认自审、⑤ 一页一个签名 |
| 同上 | pbakaus/impeccable | **模式（Persuade/Operate/Read/Experience）决定野心**：Operate/Read 的野心是精确与克制；按渲染结果验证，批量检查 | `archetypes.json` 的 `mode`；rubric 按模式加权；创意预算按模式 |
| 同上 | Nutlope/hallmark | **分层门禁**：Floor（不可豁免）/ Reflex（可带理由豁免）/ Finish（必须回答）；新会话做终审；「编造的通过本身就是 slop」；验证预算 | 交互规则 critical/major/minor ↔ Floor/Reflex/Finish；视觉评分门禁 + 单维下限；自评 −0.5、新会话评审优先；如实报告未达标 |
| 同上 | Leonxlnx/taste-skill | **行业类型决定一切**（软件/游戏/硬件/产品/服务/门店 → 不同素材与特效许可）；不复制参考站的代码/文案/签名特效；浏览器多宽度验收 | 主题与创意按行业选；`benchmark-discovery.md` 的许可与「只借思路」；`visual_capture.py --mobile` |
| 同上 | nexu-io/open-design（critique 模板，源自 huashu-design） | **0—10 分维度评审 + 锚点**（0–4 Broken / 5–6 Functional / 7–8 Strong / 9–10 Exceptional），不平均掉有意思的失败；Keep/Fix/Quick-wins | `visual/rubric.md` 8 维 × 锚点；单维 <6 不能被平均掉 |
| 同上 | alchaincyf/huashu-design | 「你有自己的默认审美」；**摆出来和参考并排让人看**才是验证；偏好沉淀 | 联系表（自己 vs 基准并排）；≥8 必须 par/above 基准 |
| 同上 | google-labs-code/stitch-skills | DESIGN.md 作为设计系统的可交换载体（提取/上传/应用） | DESIGN.md-lite 模板；用户已有 DESIGN.md 时直接遵循 |
| 同上 | dominikmartn/nothing-design-skill | **三层层级规则**（主/次/三级，眯眼测试） | rubric「hierarchy」锚点（眯眼测试） |
| 用户补充 | [heydamir/unslop](https://github.com/heydamir/unslop)（16.7k★，CC BY 4.0，作者 Damir Sokolovsky / @heydamir） | **先审计再定方向再分层修**：signs.md 逐类列出 slop 痕迹（彩色发光、渐变字、近似色、800/900 字重、全大写宽字距、任意间距、喊叫文案、每张卡都塞 sparkline…）；按「重度/轻度/无 slop」决定改多少；方向五行（产品/性格/世界/时刻/签名，禁用 clean/modern/premium 这类词）；九遍修复顺序（间距→颜色→图标→文案→字体→布局→细节→视觉→动效）；tokens.md 给出间距阶梯、字阶、圆角嵌套、中性色阶 | 新增 9 条 lint 规则（co.glow-shadow、co.gradient-text、co.near-duplicate-colors、ty.font-family-sprawl、ty.size-sprawl、ty.heavy-weight、ty.uppercase-tracked、ly.off-scale-spacing、cp.shouty-copy）+ 18 个用例；`browser_check.py --visual-stats` 渲染后统计调色板/字体/字号/奇数间距；流程 ③ 方向五行、⑦ 九遍顺序、「改多少」分级；rubric 证据引用这些统计。规则与实现为本 skill 自写，按 CC BY 4.0 署名 |
| 同上（引用文章 2115164938884862375） | 评审提示：「Open review/contact.png and review/phone.png. You did not make this. You are the harshest animation director I know… List every problem… Fix the 3 worst. Re-render only those seconds. Show me the new sheet.」 | **联系表 + 手机测试 + 局外人苛刻评审 + 只修最严重 3 个 + 只重做受影响部分** | `visual_capture.py` 生成 contact-sheet + mobile 截图 + `review.md`（同一姿态）；流程 ⑩；`rsi/rubric.md` 的 top3 |

## 机制步骤 → 来源 速查
| 步骤 | 来源 |
|---|---|
| ① 原型识别 + 模式 | impeccable（modes）、taste-skill（kind decides everything） |
| ② 逐区块基准 | navbar/footer/cta gallery、scrolltide 分层、refero |
| ③ DESIGN.md-lite（材质隐喻 + 方向五行） | refero styles、stitch DESIGN.md、frontend-design 两遍法、unslop Direction |
| ④ 主题按行业/受众 | refero（真实产品配色）、taste-skill、frontend-design（AI 默认色避让） |
| ⑤ 领域创意 pass（一个记忆点） | frontend-design（boldness in one place）、scrolltide/snapblocks/scrollshaders（素材）、huashu |
| ⑥ 反默认自审 | frontend-design 聚类清单、hallmark Floor、impeccable 禁令、unslop signs.md |
| ⑥b 改多少（重度/轻度/无 slop） | unslop「Decide how much to change」 |
| ⑦ 主流组件 + token | hallmark Floor #1（全部走 token）、shadcn/ui 生态 |
| ⑦ 实现顺序（九遍） | unslop passes：间距→颜色→图标→文案→字体→布局→细节→视觉→动效 |
| ⑧ 确定性检查 | ui_lint/browser_check（vercel web-interface-guidelines、axe-core）+ unslop 视觉卫生规则与 --visual-stats |
| ⑨ 联系表取证 | 引用文章的 contact.png / phone.png |
| ⑩ 苛刻评审·先修 3 个 | 引用文章评审提示、hallmark 新会话终审 |
| ⑪ 0—10 评分 ≥8 门禁 | open-design critique 锚点、huashu「并排看」、hallmark「编造的通过即 slop」 |
