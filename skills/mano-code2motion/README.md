# mano-code2motion 0.1.0

目标不是更多视频工具，而是把“丝滑”等描述解释为**有情境、有单位、可实现、可检查**的运动计划。

入口：`SKILL.md`。不依赖 mano-design；需要界面造型评审时再配合使用。

## 实际包含什么
- 十个感受词，每个有两种情境、参数假设、反例和验证方法。
- MotionSpec v1 JSON Schema、严格结构/语义校验、Python 与浏览器求值器。
- 同一球/相同位移/相同时段的线性、丝滑、厚重对照；可播放、可 seek，无自动播放、无音频。
- Chrome固定时刻PNG → ffmpeg无声MP4导出；浏览器像素seek自测、Python/JS数值对照、ffprobe检查。
- 叙事/角色/镜头/转场/特效配方；v1执行器**不实现**骨骼、3D、粒子、空间贝塞尔或任意文字自动编译。

## 运行（Python 3.8+，无Python第三方包）
在本技能目录：
```bash
python scripts/check.py examples/compare.json
python -m unittest discover -s tests -v
python -m http.server 8765 --bind 127.0.0.1
```
浏览器访问 `http://127.0.0.1:8765/examples/index.html`。控制台 `renderAt(1.375)` 可验证绝对时间。URL `?capture=1&time=1.375` 隐藏控件以供截图。`?selftest=1` 运行乱序seek像素和曲线自测。

导出另需 Chrome/Chromium（或手动指定兼容的Edge）和有 libx264 的 ffmpeg/ffprobe，在PATH或用 `--chrome` 指定；不自动安装，不联网取素材。
```bash
python scripts/render.py --out /tmp/code2motion-output
# Windows示例，选一个尚不存在且在仓库外的目录
python scripts/render.py --out C:\Users\Administrator\g3v-xfer\code2motion-output --chrome "C:\Program Files\Google\Chrome\Application\chrome.exe"
# 只跑浏览器和Python/JS一致性检查，不要求ffmpeg
python scripts/render.py --out /tmp/code2motion-browser-check --check-only
```
`--workers 1..4` 控制并行Chrome进程，默认2。每帧独立临时profile，慢但不依赖实时录屏；4秒24fps共96帧。导出期间仅向自身 `127.0.0.1` 临时端口提供三个示例文件，不暴露整个仓库。失败会保留部分输出诊断，**不覆盖、不自动删除输出目录**。Chrome在root容器运行才自动加 `--no-sandbox`，桌面保留sandbox。

输出 `frames/*.png`、`first/middle/last.png`、`compare.mp4`、`browser-test.json`、`sampling-report.json`、`ffprobe.json`。不将这些构建产物提交进技能仓库。

## 单位与扩展
1280×720诊断示例中圆心从x=300到1170px，0.5秒开始，2.6秒运动，余下保持；三个圆的几何与基线相同，颜色/标签仅用于识别。
示例页面是该对照的专用展示适配器（标题、速度图、端点标注固定），不是通用影片排版器；`render.py`仅导出附带示例。要生成新影片，先用语义工作流出规格，再实现影片自己的 `renderAt(t)` 和导出适配器。底层 MotionSpec v1 求值器可复用，不能把不支持的相机/角色计划冒充可执行字段。

默认噪声hash已固定种子并提供Python/JS一致性测试；本例不添加噪声，避免扰动影响运动对照。浏览器播放按真实时间求t，离线导出按 i/fps，不依赖刷新率；reduced-motion用户默认也不自动播放，可用静态seek检查，无闪烁/自动摇镜。

`references/engineering.md` 说明时间贝塞尔求逆、C0/C1/C2、接段世界速度与帧数契约。建议参数不是审美定律，实测速度不是质量分数。

## 测试范围
单元测试无需浏览器；像素/跨语言测试与编码检查只有运行 `render.py` 才发生。支持Python 3.8语法；是否实际在Windows、特定Chrome、3.8解释器测试应看交付报告，不由代码存在推断。跨机器字体/抗锯齿/编码器不同，不保证视频字节级哈希一致。
