# 从 18 个仓库提炼的可执行精华（0.5）

来源：`references/repos-18.json`（2026-11-20，GitHub API 核对许可 + README/SKILL.md 头部；未运行任何仓库代码）。
原则：只提炼机制与数字，不复制代码、提示词长文、媒体、字体或模型；每条先问“本技能缺什么”，再决定进不进 SKILL.md。

查库方法：先用工具查，再读全文，不要一次把整个 JSON 塞进上下文。
```bash
python scripts/repos_lookup.py --list-tags
python scripts/repos_lookup.py --tag timing --verbose
python scripts/repos_lookup.py --query captions --verbose
python scripts/repos_lookup.py --repo librosa/librosa --verbose
```

## P0 — 直接进 SKILL.md / language-to-code.md 的（本技能原来没有）

### 1. 实测运动数表（motionmaxxing）
原来只有“形容词换数字”的例子，没有一张可查的数表。现在补：
- 中位移动 10 帧（0.33s）；入场 11–12 帧、不透明度 6 帧、模糊 7–8 帧。
- 落地减速（58% ease-out），离开加速（37% ease-in）；过冲 <9%，晚段慢 lean，不要快弹簧。
- logo 从约 3.5× 处减速入场，任何东西都不从 0 长出来；transform 入场远多于 opacity 淡入。
- 硬切 96%，约 20 个/时刻，切在运动上，不切在静止上。
- 死帧门：3–7s 的时刻约 99% 的帧都在动，中位静止 1 帧；连续 >3 帧不动即 fail。尾 hold 0.6–1.4s，最后一镜 ≤25%，尾 hold ≤1.4s。
- 一帧一个主角（G4）：两面板只在其中一个面积 2× 或镜头在两者间移动时才成立；UI 文字 ≥0.04H。
- G5 排版 lint：角落标签、计数器、时间码、进度条、标题上的 kicker、左标题+右媒体、逐字打出标题、vibe-coded UI 卡片都 fail；lint 是线索不是判决。

### 2. 人格 × 时长 × 缓动查表（motion-design-skill）
- Playful 150–300ms / ease-out-back / 过冲 10–20%；Premium 350–600ms / `cubic-bezier(0.4,0,0.2,1)` / 0%；Corporate 200–400ms / `cubic-bezier(0.2,0,0,1)` / 0–3%；Energetic 100–250ms / ease-out-expo / 15–30%。
- 品牌 = 1 个招牌缓动（80% 的动画）+ 3 个时长 + 1 个入场 pattern。
- 距离缩放：100px=基准，200px=1.3×，400px=1.6×，全屏=1.8–2.0×；入场比退场长 30–50%（退场=入场的 65–75%）。
- 延迟上限：hover <100ms，press <150ms，释放/落定 200–300ms，错误抖动 300–400ms（2–3 次，±10–15px，0% 过冲）。
- stagger：微 20–40ms，标准 50–100ms，戏剧 100–200ms；总 stagger <500ms。
- 弹簧：标准 stiffness 250–350 / damping 18–24；弹跳 150–250 / 10–15；阻尼比 <1 振荡，=1 最快无振荡，>1 慢落定。

### 3. 复刻的判定标准（reanimate）
- 先声明两档：moves the same（触发、顺序、stagger、时序误差 ≤80ms、缓动家族、距离）；pixel-perfect（再加字体/尺寸/颜色/间距/素材，平均像素差 ≤2%）。
- 流程：录 → 规格表（每元素每属性一行：起帧、时长、from→to、缓动、stagger）→ 建 → 同法复拍对比 → 重复，通常 2–5 轮；5 轮后列出仍不符项与原因，不宣称完成。
- 缓动/弹簧靠拟合（过冲 + 落定时间），不靠猜；虚拟时钟 + 有种子随机，保证两次捕获逐帧一致；不可复现的粒子比模糊后的密度/颜色/运动，不逐点比。

### 4. 字幕是类型化契约，不是手工文本（Remotion Skills + WhisperX）
- 字幕类型：`Caption {text, startMs, endMs, timestampMs, confidence, pageBreakAfter?}`。
- 逐词，不逐行：绝不用“把一行时长平分给每个词”伪造词时；统一归一化为 `{text, startMs, endMs}[]`。
- TikTok 分页：`combineTokensWithinMilliseconds: 1200`，每页 4–6 词；活动词高亮，弹簧 pop 0.6→1，活动词 1→1.1；词弹簧 damping 10–15，mass 0.5–0.8。
- 语言要对齐模型：`--language <code>` 自动选对齐模型，错语言 = 错词时；VAD 先行；diarization 只给 speaker ID，不给名字，且“远非完美”。

### 5. 节拍要实测，不猜 BPM（librosa）
- `beat_track` → `frames_to_time` 得到 beat_times；每拍帧数 = fps × 60 / BPM；切在节拍上，布局在小节（每 4 拍）换。
- 无节拍（氛围/合成）时 fallback：onset_strength → onset tempo，全部失败默认 120.0。
- onset_detect 给 SFX/切点触发时间；chroma + mel + RMS（RMS 权重 5×）做段落切分（intro/verse/chorus/drop/outro），节奏跟段落走，不跟一张平网格。
- hop_length（默认 512）全程一致，否则 frames_to_time 会漂。

### 6. 交付 QC 要测成品文件，不是渲染器（FFmpeg）
- 编码：`-framerate 30 -i frames/%04d.png -c:v libx264 -profile:v high -pix_fmt yuv420p -crf 16-18 -movflags +faststart`；只用 PNG 帧，不用 JPEG。
- 响度两遍：先 `loudnorm=I=-14:TP=-1:LRA=11:print_format=json -f null -` 测，再用测得值二遍；`-ar 48000`；AAC 编码后用 `ebur128=peak=true` 复测（AAC 会改峰值）。
- QC 在成品 MP4 上：`freezedetect`（非声明 hold 下冻结 ≥1s 告警）、`blackdetect=d=0.1:pix_th=0.10`（黑 ≥0.1s 告警）、`silencedetect`、`signalstats` YDIF；暗界面/慢镜头误报只告警不 fail。
- 先 `ffprobe -show_format -show_streams` 再定方案，不信渲染器内部数字。

## P1 — 进指南/参考的（按镜头选路时用）

### 7. 文案先行，方向是发的不是想的（cinetic）
- 文案门：3s 内说清产品是什么，每行一件事、2–7 个 plain 词；copy-check 拦：含糊词、口号、关键词堆、>7 词行、同屏两行、“Introducing…”、kicker 标签、假数据/lorem。
- 方向：`deck.py --options 3` 发 3 个完整方向，agent 各写一句 idea，留下一个竞品无法声称的。
- 速度交接切点：出镜加速、在最快帧切；入镜同向以 0.5–1.5× 速度开场再减速落定；每切交接一个载体（速度/缩放方向/形状/位置）。出 ease-in 4–29f，入 20–60f 落定，切速 15–200 px/f（1080p）；切点音在节拍 ±30ms 内。
- 一张总谱：`b(bar, beat, 16ths)` 把所有帧号映射到实测小节；声音从不手工放，由运动常数算出接触帧/落定帧/速度峰值帧。
- 声音克制：只用授权真人器乐；每行文字一个软音，阅读时近静默，全片一个大 hit；任意 4s 内 ≤2 个带音高音效。

### 8. 分镜表是硬门，不是草稿（huashu-art-motion）
- 先写分镜表（一行一镜：时间 | 对象（名词）| 动作（动词）| 镜头 | 屏上文字 ≤8 字 | 方法），锁定一种风格 + 一个调色板（3–6 色，无蓝紫）再写代码；红灯 = 改表重跑，不开始写码。
- 镜长 2–6s；文字主导镜 ≤30%；前 3s 是具体小场景（手/物件在做事），不是标题卡。
- 交付红灯：整片几乎无镜内运动、蓝紫帧 >30%、中段空 >0.3s，任一即不交付；镜头纪律：画面动或观众在读时镜头静止；快推/砸入/甩镜只作点缀，全片可数。

### 9. 风格 prompt 的形状 + 独立陪审（mg-styles-15）
- 一个风格一个 prompt：固定共享部分 + 4 个填空（Output 规格 / 建议技术路线 / 创意种子 / 招牌特征）。复用时只换创意种子，保留招牌特征；招牌特征必须可检查。
- 创意种子必须有节拍：hook → 升级 → 高潮 → 尾帧，按秒写，否则模型出平模板。
- 独立陪审（没做片子的新会话）：每 0.5s 联络表，最快/主角动作周围 filmstrip，5–8 个关键时刻全分辨率帧；规格检查（正好 10.00s、分辨率/fps、响度约 -14 LUFS ±1、真峰 ≤-1 dBTP、无意外黑/静止段、命中点对齐音频 onset）；7 维 1–10 分（风格 fidelity、概念/wow、运动 craft、设计/字体、完成/质感、声音同步、技术），5=合格学生，8=高端 agency，9=获奖提名；5–10 个 fix 按影响排序，每个带 timecode + 可观察缺陷 + 带数字的具体做法；至少一个 fix 要提 wow，不只抛光。

### 10. 画的顺序就是做的顺序（anidoodle）
- 什么都不淡入：每笔长出来，每洇从落点扩开；影片最后一帧 = 交付静帧，逐像素一致。
- 一个 idea + 一个焦点主体 / 静帧；一镜一个转变、一个 payoff、一个回归 token。
- 决定性门：gate.mjs 一次查决定性、契约与死空气；verify-export.mjs 解码交付 MP4 再查。
- 发布片：5s 内说清是什么，字不压在画上，切在 downbeat 上，第一帧 = 缩略图；尾卡留够抄写安装行的时间；各比例（16:9、1:1、4:5、9:16）各自重排，不裁剪。

### 11. 身份连续 + 便宜静帧先行（Manim）
- 同一对象跨阶段用 Transform/Create/FadeOut，不用标题卡序列；每 `play()` 显式写 `run_time` 与 `rate_func`。
- 相对定位（move_to/next_to/align_to），不用绝对像素；`ValueTracker` + `always_redraw` = 从单一时间/值参数推导画面（renderAt(t) 的类比）。
- 便宜静帧先行：`-s` 只渲尾帧，`-n <k>` 跳到第 k 个动画，`-ql` 低质量预览。

### 12. 合成是 JSON 工程，关键帧带插值类型（EffectCraft）
- 工程是可版本化、可 diff 的 JSON（comp、layer、property、keyframes），agent 可文本编辑。
- 每个动画属性声明插值类型（linear / Bezier / hold / auto / continuous-Bezier、roving keys、Easy Ease），不只写值。
- 表达式是闭式 JS（wiggle、loopOut、thisComp.layer(…)），对应 renderAt(t) 纯函数，不带逐帧状态。
- 效果是 checklist 不是菜单：308 个效果分 14 类、38 种混合模式，先点名要的那一个 VFX pass，不堆效果；编码规格按交付物选，写进简报。

### 13. 粒子是数据规格，不是形容词（three.quarks）
- 粒子系统写成数字：life/speed/size/color 的区间或常量、maxParticle、emissionOverTime、发射器形状、生命期行为（Bezier 曲线）；可 JSON 加载复用（QuarksLoader.load('effects/explosion.json')，clone() 多实例）。
- 发射器形状带身份：从模型表面或结构化网格发射，不用随机云；粒子要服务可辨剪影。
- 决定性警告：quarks 是 delta 驱动（update(delta)），帧精确 renderAt(t) 导出要 reset + 从绝对时间确定性步进，不能默认 seek 可用。

### 14. 电影感收尾是一次合成，不是逐个渲染（react-postprocessing）
- `<EffectComposer>` 一次合并 EffectPass，顺序即效果顺序；起始值（先验证再用）：DoF focusDistance 0 / focalLength 0.02 / bokehScale 2 / height 480；Bloom luminanceThreshold 0 / luminanceSmoothing 0.9 / height 300；Noise opacity 0.02；Vignette offset 0.1 / darkness 1.1。
- 文字/UI 在 DoF 之后单独一层画，不让景深/模糊吃掉文字；颗粒 ≤0.02；MSAA 默认开，不再加第二遍 AA。

### 15. 调参是工具，不是成品（Tweakpane）
- 每个运动数字都绑到 pane（Number/Color/Point），不用把调好的值硬编码进影片代码；JSON import/export 作 preset。
- 只读绑定显示实测值（主体像素宽、freeze 数、fps），放在影响它的控件旁边；调参时拖滑杆 → 同帧重跑 renderAt(t) → 对比。
- 交付前去掉 pane（或放 debug flag 后面）。

### 16. 声音要找授权来源，不是现合成（Openverse）
- 许可过滤先行：`license=cc0,by,pdm`，商用再加 `license_type=commercial`；NC/ND/SA 不用于发布片；Openverse 不验证许可，要读原页面。
- 每种声音只搜一次，从短名单里挑，不换词重搜；`page_size` 匿名最大 20。
- attribution 原文抄进 `credits.txt`；CC BY 无 credit 即不合法；先用 `duration` 字段核对 cue 长度再下载。
- 画面先静音成立；SFX 落点比画面晚 1 帧，比音乐床高 3–6dB。

### 17. 3D 的 QA 是脚本 + 翻转表（blender-skills）
- 脚本驱动，不点鼠标：每场景一个可重跑的 Python 文件；改 = 改一个数字 + 重渲。
- 翻转表 QA：wireframe → clay → 全彩，按手机尺寸判；先修穿插/穿透再全渲。
- 资产 QA 门：z-fighting、悬浮件、坏法线、坏权重、坏贴图，出口前 fail；texel 密度 + 烘焙 normal/AO/curvature/ORM；PBR 粗糙度/金属度写对，磨损/灰尘/贴花是显式规则。

## P2 — 不进技能，只作查库提示的
- Remotion 的 `interpolate()` 优先于 `spring()`（除非明确要物理）；`delayRender()/continueRender()/cancelRender(err)`：失败要让渲染失败，不静默出占位图。
- FFmpeg GIF：fps=25（GIF 百分秒下 25fps 精确，24fps 快约 4%），≤15MB、≤350 帧。
- motionmaxxing 的“修技能不骂 agent”：某个默认反复出现时，改写规定它的那条技能规则。
- cinetic 的成本提示：一次 cinetic 约 3× 基线时间/token；短 doodle/单镜循环别走这条路。

## 未验证（不要当结论用）
- 各仓库 README 里的效果数字（motionmaxxing 53 个 pro 时刻 / 4,288 个动作、mg-styles-15 陪审 7.57–8.21、cinetic 评测表、WhisperX 70× 实时、FFmpeg 阈值等）均未独立复现。
- 许可：reanimate / motion-design-skill / mg-styles-15 / huashu / cinetic / Manim / blender-skills / three.quarks / react-postprocessing / Tweakpane = MIT；anidoodle / motionmaxxing / EffectCraft = Apache-2.0；librosa = ISC；WhisperX = BSD-2-Clause；Remotion Skills = 未列出（不要默认 MIT）；FFmpeg GitHub 镜像 = NOASSERTION（上游主要 LGPL，部分组件 GPL，视构建配置而定）；Openverse 是 API，媒体按件授权。motionmaxxing 内捆的 GSAP 是 GreenSock 标准许可，不是开源。
- 5 个 README 之外未细读的子文件、10 个 Remotion 子技能、51 个 cinetic 脚本、53 张 huashu 配方卡均未逐一核对。
