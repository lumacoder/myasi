# 渲染适配：可以汇合，不假装所有引擎都已安装

本技能实际自带 **Canvas2D捕获** 与 **本地视频/音轨→FFmpeg制作**。以下平台只有在项目已有依赖、授权及可运行工程时才使用；没有则报告缺失，不安装整套参考仓、注册MCP、执行其bootstrap或付费fallback。

## 内建Canvas2D（新增示例已执行此通路）
HTML提供`READY=true`、纯`renderAt(seconds)`、单Canvas和捕获时禁RAF。自己的绘制/角色代码不限形状。执行：
```bash
python scripts/render_project.py /project/scene --duration 2 --fps 24 --width 768 --height 432 --out /outside/shot
# 把生成的film.mp4复制到project.json所列clip，记录源文件/工具版本及SHA
```
源码必须经过检查；浏览器不是执行未知仓代码的沙箱。`render_project.py`只接受Canvas2D，不能拿WebGL页面通过READY便宣称已支持。

## 已有本地媒体（真正实现的通用适配）
把自己渲好的MP4/MOV/WebM放工程内，用shot.clip声明；填真实`renderer`与rights。`production.py assemble`取明确源入点、conform画幅/帧率与准确帧数、静音源音轨、串接。异帧率会重采样帧，透明视频会输出不透明yuv420p；若需要alpha/色彩管理/逐像素无损，留在原引擎合成，不用该适配冒充无损迁移。

## 项目已有框架时的真实输出边界（本次未逐平台运行）
- **Remotion / React / Three.js卡片**：使用该项目锁定的本地CLI。例如 `npx --no-install remotion render src/index.ts Scene clips/scene.mp4 --frames=0-47 --fps=24 --width=768 --height=432`。`src/index.ts`/`Scene`须换为真实入口和composition；无本地CLI就停。所有Remotion相关包应同版；框架/商业许可单独核对，不因skills可读就认为运行时许可免费。用useCurrentFrame/props驱动；不要机械把有state/effect/async/第三方UI的React翻成另一引擎。保留原渲染视频作为对照。
- **GSAP / DOM / HyperFrames**：项目的timeline应暂停并从绝对时间seek，字体/图片/布局ready后才取帧。已有HyperFrames工程可用 `npx --no-install hyperframes check`、`npx --no-install hyperframes render --output clips/scene.mp4`；先核该项目CLI的`--help`，不同锁定版的lint/check选项不能混用。不要把根data-duration和子scene duration弄反，检查组件挂载与CSS盒模型。需要DOM/WebGL截图的项目用其自己的导出器，**不是**内建Canvas2D捕获器。
- **Blender**：已审核的本地blend可用 `blender -b scene.blend -o /outside/frames/frame_#### -s 1 -e 48 -a`；先在文件里确定相机、分辨率与帧率，再 `ffmpeg -framerate 24 -start_number 1 -i /outside/frames/frame_%04d.png -frames:v 48 -c:v libx264 -pix_fmt yuv420p clips/scene.mp4`。先廉价关键帧；父子局部坐标、脚地接触、单帧显存与采样预算另验。没有Blender不启动下载或改别人的场景。
- **Manim / Motion Canvas / p5 / Lottie / 其他**：原工具导出本地片段再接入同一媒体契约。检查seek的副作用、随机、字体、滤镜与末帧；不宣称本次有原生控制器。
- **Figma / 真实影像 / 数据**：先用已授权工具导出自己的素材/色字token/真实数据，记来源与权利；绑定组件身份而非靠hex猜token。frame是关键状态，不是必须做成幻灯片。真实人物、事实、Logo与样片不能因为可下载就复用。
- **配音 / ASR / 音频模型**：已允许的本地录音或TTS文件作为tracks接入；逐词时码必须来自真实分析或明确标为估计。本技能不会下载Kokoro/Whisper/分类模型，不会读取API key、调用订阅CLI或跨provider兜底。现有本地工具的音质与语言支持仍要试听。

任何适配都保留：原始输出、相同时间/画幅对照、实际命令/版本、未匹配项。clip可播 ≠ 平台功能全部迁移 ≠ 视觉审核通过。
