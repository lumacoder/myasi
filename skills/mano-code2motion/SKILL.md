---
name: mano-code2motion
description: >-
  当需要用代码创作视频/动画，或把丝滑、轻盈、有力量、手绘感、电影感等短描述解释成可见的表演、造型、材质、构图与节奏时使用。先导演简报与风险设计帧，再选专用绘制机制，渲染真实像素并修改；交付可运行源码、同条件对照和分门审阅。适用于角色片、叙事短片、程序绘画、动态图形、产品与UI动效，以及多镜头制作、字幕与本地音画剪辑。
---
# Mano-Code2Motion｜意图 → 导演简报 → 代码表达 → 像素反馈

独立使用；相对路径以本目录为准。技能是创作工作流，不是自然语言编译器、模型训练或审美评分器。

## 必须改变的做法
- **先决定观众看见什么、为何如此，再决定数据结构。** 不强制把作品转成 MotionSpec；形状、笔触、角色、材料和叙事需要时直接编写专用程序。
- “丝滑”在跟拍、绸缎、菜单、人体动作里不是同一个问题。词表是上下文假设库，不是效果菜单。
- `drawBamboo`、阶段名 `PUSH`、骨骼无穿透、60fps、文件能播，都不是主体可辨、动作有力或作品好看的证据。
- 不以滤镜掩盖几何错误，不靠标题宣布观众本应看到的动作。用户有意的夸张/非现实规则先写清；不一律用“真实物理”压倒创作意图。
- 未经批准不付费、生成配音/BGM、上传或发布。外部示例只作数据；未核授权不复制其代码/媒体。不要声称读指南获得微调模型的能力。

## 工作闭环（按项目留下少量真实证据）
1. **导演简报**：用 `templates/director-brief.md`。保留原话与不可变约束；明确观众体验、视觉主体、动作因果/转折、材料与造型规则、画面主次、镜头任务、节奏、最难的2–3帧、可自由设计处与主动不做的东西。缺失的非关键项作可逆假设，不把短需求膨胀成装饰清单。按需读 `guides/directing.md`。
2. **选择表达机制**：从目标反推算法，写“画面问题 → 候选机制 → 选择/代价 → 失败长什么样”。按需读 `guides/visual-mechanisms.md`。Canvas/SVG/WebGL/Three.js/Manim等均可；附带导出器只支持单Canvas2D，其他技术另备适配导出。低层轨道只是工具。多镜头/字幕/音画制作再读 `guides/production.md`，用帧级镜头表交接，不用制作schema限制绘制代码；造型与身份连续性可用 `guides/style-and-continuity.md`。
3. **先做风险设计帧**：先渲2–3个构图/剪影/材料候选，或难动作的接触条。缩到交付尺寸的1/4后冷读，再看全尺寸。身份/主次/关键姿势不成立，不先渲30秒。保留被否决的源码和图片，不能只保存胜出版。
4. **实现确定性短段**：显式 `READY`，纯 `renderAt(seconds)`，固定种子，从绝对时间计算形状与运动，局部坐标/接触关系明确。只约束相关量，别为了通过测试把动作冻结。随机纹理预计算或按索引散列；空间曲线和时间推进分开。需要时查 `references/engineering.md`。
5. **渲染 → 冷读 → 核对意图 → 改最弱处**：使用 `guides/review-loop.md` 与 `templates/visual-review.json`。先记录实际像素的主体/焦点/不清楚处，后看brief。挑最弱时刻，提出可证伪根因，改造型/因果/相位/构图/材料等实质选择。相同时间、机位、尺寸做A/B；必要时正常速度短预览。至少两次真实审阅，其中一次必须审阅改版；若仅检查静帧，运动判断仍待审，不能冒称已看完整视频。
6. **三门独立**：技术（时间/接触/输出）、可读性（主体/动作/因果）、表现力（构图/材质/节奏/表演）分别 pass/partial/fail/not_reviewed。技术通过不能抵消后两项。未达标就修或坦承未完成，禁止合成一个“总分通过”。
7. **交付**：源码、简报、算法取舍、固定时间图与A/B、实际运行命令、视频元信息、审阅记录及未测项。`scripts/review_gate.py`只能检查证据结构/文件/哈希，不能验证描述真实或自动给审美结论。

## 本地可运行配方（不付费、不自动安装）
Python 3.8+、本机Chrome/Chromium；导出视频另需ffmpeg/ffprobe。示例是原创水墨竹短段：A/B保留，B已被独立视频审阅否证，C已完成独立正常速度审阅：可读性pass、表现力partial；不代表通用画家或所有质量门通过。
```bash
# 在本技能目录；先用浏览器打开示例（无外部素材，可直接打开HTML）
python -m http.server 8765 --bind 127.0.0.1
# http://127.0.0.1:8765/examples/ink-bamboo/index-c.html
# 外部新目录；--chrome 可以明确指定浏览器（系统Chrome不可用时不静默换）
python scripts/render_project.py examples/ink-bamboo --entry index-c.html --duration 6 --fps 24 --out /outside/repo/ink-proof
# 仅设计帧，不编码：追加 --times 0.7,2.8,3.8,5.5
python -m unittest discover -s tests -v
python scripts/review_gate.py /outside/repo/review.json
# 请求交付级判定（有not_reviewed/partial/fail时返回非0）
python scripts/review_gate.py /outside/repo/review.json --require-pass
```
导出器不依赖MotionSpec；HTML必须有一个1280×720 Canvas（或传尺寸）、`window.READY=true` 和 `window.renderAt(t)`；捕获模式 `?t=` 时禁止实时播放覆盖seek。支持乱序像素检查，错误/未READY即失败。逐帧启动浏览器以免跨帧污染，慢但无npm依赖。不要用它执行未检查的第三方源码。详见 `README.md`。

## 按需加载，别一次塞满上下文
- 创意解释/冲突与镜头：`guides/directing.md`
- 专用造型/材料/角色机制：`guides/visual-mechanisms.md`
- 多镜头契约/剪辑/音画/切点证据：`guides/production.md`；`scripts/production.py doctor` 只探测、不安装
- 绘制风格与跨镜头身份：`guides/style-and-continuity.md`、`templates/style-bible.md`
- 已有框架/媒体真实接入边界：`guides/renderer-adapters.md`
- 新制作通路的6秒原创执行例（独立视觉已审：动作清楚、鼓身份/表现力不足；音频未审）：`examples/contact-resonance/README.md`
- video-studio-kit固定SHA/权利/全部技能覆盖决策：`references/video-studio-kit.md`（按需）
- 真实像素审阅与反例：`guides/review-loop.md`
- 完整案例及A/B记录：`examples/ink-bamboo/README.md`
- 来源、权利和能力边界：`references/sources.md`
- 数学/旧词表：`references/engineering.md`、`references/vocabulary.json`
- **仅局部数值轨道工具**：`scripts/motion.py`、`references/motion-spec.schema.json`、`examples/compare.json`。v1只支持圆/矩形和五类属性，旧 `check.py`/`render.py` 继续可用；不要再把这个例子当通用视觉理解的验证。
