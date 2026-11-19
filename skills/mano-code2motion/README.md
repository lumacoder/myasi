# mano-code2motion 0.3

自然语言创意 → 导演简报 → 适合题目的绘制/动画机制 → 真实渲染 → 针对最弱画面的修改。

不是把所有作品变成“形容词→ease→圆/矩形播放器”；也不是声称拥有新的训练模型或自动审美器。主入口见 [SKILL.md](SKILL.md)。

## 内容与接线
- `templates/director-brief.md`：观众体验、因果、造型/材料、构图/镜头、节奏、风险与自由。
- `guides/`：按需阅读导演决策、专用绘制机制、真实像素反馈及反例。
- `scripts/render_project.py`：与MotionSpec解耦的单Canvas2D项目导出；显式READY、绝对时间seek、乱序像素检查、PNG/无声H264/元信息。
- `scripts/review_gate.py`：审阅证据/文件/哈希及三门状态的结构检查；**不验证审美或描述真实性**。
- `examples/ink-bamboo/`：原创6秒挑战短段，A/B/C源码、独立审阅fail与一次动作修正记录；不复制SenseNova素材。
- `references/research-findings.md`、`references/sources.md`：可核查研究结论、来源与未开源/许可边界。
- 原`motion.py`/schema/`check.py`/`render.py`/compare保持兼容，只作**局部数值轨道**工具，不再规定作品表达上限。

## 新增制作通路（0.3）
- `scripts/production.py`：可编辑帧级镜头表→本地媒体conform/剪辑→显式音轨/字幕→真实解码/切点前后图→哈希校验草稿包；缺媒体/过短默认失败，不用占位卡假成功。
- `guides/production.md`：精确时钟、声音/留白、许可与交付；`guides/style-and-continuity.md`、`runtime/scene-kit.js`：造型规则与可自由替换的绘制代码，不是风格enum。
- `examples/contact-resonance/`：新的6秒两镜头、本地合成提示音和字幕执行例；独立正常速度/试听仍待审，不借用水墨竹的通过结论。
- `references/video-studio-kit.md` + `.audit.json`：固定SHA、完整树/全部技能覆盖决策、原生实现与外部依赖/付费/许可边界。没有导入上游代码/字体/模型/素材，没有安装19个引擎或获得109种已验证效果。
```bash
python scripts/production.py doctor
python examples/contact-resonance/build.py --out /outside/repo/contact-proof
# 可在新输出目录authored/project.json修改字幕、cue和镜头，再assemble到另一个全新目录
```
实际媒体适配支持精确有理数fps；Canvas捕获仍是整数fps、单Canvas2D。无自动TTS/ASR/ducking/听感判断；所有平台适配的实测范围见示例与指南。

## 运行原创水墨案例
Python 3.8+标准库；Node只用于案例几何QA，浏览器与ffmpeg/ffprobe需本机可用，不自动安装，不收费。
```bash
# 本目录执行；HTML也可直接双击
python -m http.server 8765 --bind 127.0.0.1
# examples/ink-bamboo/index-c.html 是独立可读性pass、表现力partial的C；index.html 是独立动作审阅fail的冻结B；index-a.html 是冻结A
# 指定当前机器实际的浏览器路径，而不是照抄其他机器路径
python scripts/render_project.py examples/ink-bamboo --entry index-c.html --duration 6 --fps 24 --out /outside/repo/ink-c --chrome /path/to/chrome
python scripts/render_project.py examples/ink-bamboo --entry index-a.html --duration 6 --fps 24 --out /outside/repo/ink-a --chrome /path/to/chrome
# 只做同条件风险设计帧（新目录）：加 --times 0.7,2.8,3.8,5.5
node examples/ink-bamboo/qa.js
python -m unittest discover -s tests -v
```
Windows的输出例如 `D:\motion-exports\ink-b`，Chrome例如 `C:\Program Files\Google\Chrome\Application\chrome.exe`，用引号包围带空格路径。

每次输出目录必须不存在，且在skill及任何git仓库之外；错误时保留部分输出，不覆盖或假装成功。输出 `frames/`、`probe-*.png`、`film.mp4`、`ffprobe.json`、`capture-report.json`。`--times`模式不编码MP4，也不要求ffmpeg。逐帧浏览器启动，速度慢但免npm依赖；不对SVG/WebGL/多Canvas或有异步资源的任意网页承诺开箱即用。

### 你自己的作品适配
HTML内一个Canvas，内在像素为1280×720（或用`--width/--height`传偶数尺寸）；`window.renderAt(t)`必须重建完整画面，加载完毕后`window.READY=true`。捕获URL带`?t=`时禁用实时播放，避免rAF覆盖。`renderAt`可异步，但初始化必须有界并在资产错误时拒绝READY。不得执行未经检查的第三方项目。导出器在每帧检查READY和尺寸，初始化失败即非0退出，不把空截图当成功。

### 审阅记录
复制 `templates/visual-review.json` 到产物目录，填入真实证据相对路径和实际观察；模板里的REPLACE不是已执行证据。
```bash
python scripts/review_gate.py /outside/repo/review.json
python scripts/review_gate.py /outside/repo/review.json --require-pass
```
默认只检查记录完整性，允许诚实的partial/not_reviewed；`--require-pass`在任何一门未通过时非0退出。两种模式都不验证画面含义，不会自动升级门禁。作者知道题目时不能称为独立冷读；仅看过PNG不能称看过正常速度视频。

## 旧数值工具（保留，不是创作能力验收）
```bash
python scripts/check.py examples/compare.json
python scripts/render.py --out /outside/repo/compare --chrome /path/to/chrome
```
MotionSpec v1只支持circle/rect和x/y/scale/rotation/opacity；数值合法/轨道连续不代表能理解任意视觉需求。

## 验证边界
原12例预注册评估尚未完成，仍针对350efba冻结版本；不能把此次单案例或新增测试冒充它的通过结论。案例展示一种任务专用表达和真实修改，不证明泛化质量、完整滑板动作修复、微调能力或与SenseNova等效。本例C已完成独立正常速度审阅（可读性pass、表现力partial）；叶片偏刚性、内部柔性/迟响应不明显、回落稍机械，不能宣称全部通过。其他作品仍须独立审阅。
