# 开源方案组合（Glue Code，不从零造）
快照 2026-11-15（Asia/Shanghai），GitHub API 核实元数据；未安装实测的标注为 reference/pattern。查询：`python3 scripts/query.py --pick --limit 0`。

## 推荐组合（13 个核心）
| 环节 | 方案 | 怎么接 | 许可 |
|---|---|---|---|
| 正确组件 | shadcn-ui/ui + radix-ui/primitives | 选型规则的「正确组件」直接映射到 Switch/Tabs/ToggleGroup/AlertDialog/Combobox | MIT |
| 配色 | adobe/leonardo | 按目标对比度生成色阶，修 co.low-contrast | Apache-2.0 |
| 风格起点 | nextlevelbuilder/ui-ux-pro-max-skill | 无设计系统时检索风格/配色/字体候选，再过本 skill 规则 | MIT |
| 交互规范 | vercel-labs/web-interface-guidelines | 状态、表单、焦点、动效规则来源 | MIT |
| 反 AI 味检测 | pbakaus/impeccable | `npx impeccable detect --json` 作为第二检测器，结果按 rule 合并 | Apache-2.0 |
| 门禁分层 | Nutlope/hallmark | Floor/Reflex/Finish → critical/major/minor | MIT |
| 浏览器终检 | Leonxlnx/taste-skill | 「先定方向、浏览器验收」流程 | MIT |
| 被动质量门 | MengTo/Skills（no-ai-design-slop） | 「可原样贴到无关产品=可疑」写进 rubric | MIT |
| 渲染验证 | microsoft/playwright + dequelabs/axe-core | `scripts/browser_check.py`（可选依赖） | Apache-2.0 / MPL-2.0 |
| agent 浏览 | ChromeDevTools/chrome-devtools-mcp | 宿主 agent 查看真实渲染、性能 | Apache-2.0 |
| 评审维度 | Jackwwj619/UXBench | 7 个 UX 维度 + 「修复后 Δ」作为 RSI 接受标准的思路 | 无 license，仅借思路 |

## 其余参考
vercel-labs/agent-skills（web-design-guidelines）、anthropics/skills（frontend-design）、GoogleChrome/lighthouse、microsoft/playwright-mcp、style-dictionary、IIGROUP/WebRISE（交互契约图）、memi-design/memi（设计 CI）、EliaAlberti/ux-audit-skill（Nielsen 0—4）、nexu-io/open-design、alchaincyf/huashu-design（中文、偏好沉淀）、google-labs-code/stitch-skills、LottieFiles/motion-design-skill、guanmo-ai/design-style（中文风格库，无 license）、dominikmartn/nothing-design-skill。

## 灵感站点（非开源，不作依赖）
scrolltide.co、snapblocks.site、scrollshaders.com、navbar.gallery、footer.design、cta.gallery、styles.refero.design（真实网站 DESIGN.md）。来源帖见 `cases/sources/`。

## 许可提醒
无 LICENSE / NOASSERTION 的仓库只借思路，不复制代码或素材；MPL-2.0（axe-core）作为独立脚本注入使用。
