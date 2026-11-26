# mano-code2motion 0.6

自然语言创意 → 时间总谱 → 导演简报 → 适合题目的绘制/动画机制 → 真实渲染 → 针对最弱画面的修改。

不是把所有作品变成「形容词→ease→圆/矩形播放器」，也不是新的训练模型或自动审美器。主入口见 [SKILL.md](SKILL.md)，版本演进见 [CHANGELOG.md](CHANGELOG.md)。

## 目录与核心工具
- `templates/director-brief.md`：观众体验、因果、造型/材料、构图/镜头、节奏、风险与自由。
- `guides/`：按需阅读导演决策、复刻流程、Web 3D 直播交付（`web-3d-delivery.md`）、专用绘制机制、多镜头制作与像素审阅反例。
- `references/`：`repos-18.json`（18 仓库资料库）、`essences.md`（可执行精华）、`language-to-code.md`（形容词换数字）、`sources.md`、`video-studio-kit.md`。
- `scripts/repos_lookup.py`：查库工具（`--tag timing|captions|particles|copy|encode`、`--query <词>`、`--repo <owner/name>`、`--list-tags`、`--all`）。
- `scripts/render_project.py`：与 MotionSpec 解耦的单 Canvas2D 导出（显式 `READY`、绝对时间 seek、乱序像素检查、PNG/无声 H.264/元信息）。
- `scripts/production.py`：帧级镜头表 → 本地媒体 conform/剪辑 → 显式音轨/字幕草稿包（例：`examples/contact-resonance/`）。
- `scripts/review_gate.py`：审阅证据/文件/哈希及三门状态结构检查（**不验证审美或描述真实性**）。
- `examples/ink-bamboo/`：原创 6 秒水墨竹短段，含 A/B/C 源码与独立审阅记录。

## 运行示例
Python 3.8+ 标准库；Node 仅用于案例几何 QA，浏览器与 `ffmpeg`/`ffprobe` 需本机可用。

```bash
# 本目录执行（HTML 也可直接双击）
python -m http.server 8765 --bind 127.0.0.1
# 指定本机浏览器路径渲染（输出目录必须在仓库之外且事先不存在）
python scripts/render_project.py examples/ink-bamboo --entry index-c.html --duration 6 --fps 24 --out /outside/repo/ink-c --chrome /path/to/chrome
# 仅渲染固定时间点设计帧（不要求 ffmpeg）
python scripts/render_project.py examples/ink-bamboo --entry index-c.html --duration 6 --fps 24 --out /outside/repo/ink-c --times 0.7,2.8,3.8,5.5
# 制作通路示例
python scripts/production.py doctor
python examples/contact-resonance/build.py --out /outside/repo/contact-proof
# 单元测试
python -m unittest discover -s tests -v
```
> 逐帧启动浏览器，免 npm 依赖但较慢；不对 SVG/WebGL/多 Canvas 或异步资源任意网页承诺开箱即用。

## 你自己的作品适配
HTML 内一个 Canvas（默认 1280×720，或 `--width/--height` 传偶数尺寸）；`window.renderAt(t)` 必须完整重建画面，就绪后设 `window.READY=true`。URL 带 `?t=` 时禁用实时播放循环以免覆盖 seek。不得执行未经检查的第三方项目；导出器每帧检查 `READY` 与尺寸，失败即非 0 退出。

## 审阅记录与旧数值工具
```bash
# 审阅门禁（复制 templates/visual-review.json 到产物目录并填写真实观察）
python scripts/review_gate.py /outside/repo/review.json [--require-pass]

# 旧 MotionSpec v1 数值工具（仅作局部数值轨道，不代表创作能力验收）
python scripts/check.py examples/compare.json
python scripts/render.py --out /outside/repo/compare --chrome /path/to/chrome
```

## 验证边界
原 12 例预注册评估尚未完成，仍针对 `350efba` 冻结版本；单案例或新增测试不代表泛化质量或与 SenseNova 等效。`ink-bamboo` C 版已完成独立正常速度审阅（可读性 pass、表现力 partial：叶片偏刚性、内部柔性不足），`0.4`/`0.5` 新增资料库与复刻流程未经独立评估，各仓库 README 宣称效果均未独立复现。
