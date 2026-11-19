# 从单段到可编辑的制作工程

先完成导演简报。这里的JSON只管理**镜头交接、媒体与帧时间**，不规定画什么、如何画；专用算法仍是作品本体。

## 一个真源，而不是几份互相漂移的秒表
- 用 `templates/production-project.json` 起步。时间全部是输出帧，区间 `[start,end)`，从0连续；`risk_frames` 是镜头内帧，`landmarks`/字幕/音轨是全片帧。
- `fps` 可以是整数或精确分数字符串 `30000/1001`，不能静默四舍五入成30。拼接显式写每段帧长对应秒数，不依赖容器毫秒舍入的duration；输出仍须解码核帧数/实际帧率。Canvas导出器目前仅整数fps；分数率用既有外部渲染器或已渲视频，再由制作管线conform。
- 每镜头保留：可见动作 `visual`、剪切用途 `cut_reason`、跨镜头 `identity`、造型材质 `look`、真实clip路径与生成来源。可另放自由格式简报，不把这些短字段当导演能力。
- 用户修改镜头表后重新校验；不要拿旧表继续生成。`renderer` 只是溯源字符串，不会执行代码、下载依赖或证明该引擎已安装。
- `source_in` 也按**输出帧时钟**计，从源视频的对应秒位置开始取，不是源文件原始帧索引。画幅采用等比完整装入+留边，不擅自裁主体。

## 真正能跑的顺序（全部本地，无自动安装）
```bash
python scripts/production.py doctor
python scripts/production.py plan /project/project.json
# 先在自己选的引擎里渲染各镜头，路径与manifest.clip一致，见renderer-adapters.md
python scripts/production.py assemble /project/project.json --out /outside/assembly --burn-captions
python scripts/production.py inspect /project/project.json --video /outside/assembly/proof.mp4 --out /outside/inspection
# 看inspection/sheet.jpg + 对应frame索引；再正常速度审视频，并试听声音。
# 按review-loop.md做冷读/核意图/选最弱处/实改/同条件对照，不把下面的打包命令当门禁。
python scripts/production.py package /outside/assembly --out /outside/draft-proof.zip
```
`plan`不要求媒体已经渲完，但声明的源码必须存在。`assemble`只接收本地媒体，不运行manifest中的命令；产物目录必须全新、在创作工程外。缺clip、过短clip、音轨越界/过短、未明确权利依据均失败，不补占位卡、不自动配音、不用付费provider兜底。只有明确 `shortfall:"hold"` 的画面才允许末帧延长，并写警告。没有变速功能。

### 字段与失败约定
| 区域 | 必填/可选与语义 |
|---|---|
| root | `version:1,title,fps,width,height,shots`；偶数尺寸；可加 `captions,caption_position,tracks,landmarks,beat_grid,notes` |
| shot | `id,start,end,clip,renderer,visual,cut_reason,identity,look,rights`；可加 `source_in,shortfall,risk_frames,sources,narration,notes` |
| rights | `basis:original/permission/public-domain/licensed,credit,evidence`；evidence填核对记录/许可文件或来源，不用“网上找到”；脚本只查声明完整，不作法律结论 |
| caption_position | `top`或`bottom`（默认）；按当前镜头留白选择，不假定底部永远安全 |
| captions | `start,end,text`；≤2行纯文本，不支持HTML/ASS标记；拒绝重叠；实际字体、行宽、手机UI仍须看图 |
| tracks | `file,start,end,role,gain_db,rights`；role为voice/music/sfx/ambience；可加source_in/fade_in/fade_out（均帧） |
| beat_grid | `bpm,offset_frame,subdivision,tolerance_frames`；偏拍只警告，有意脱拍可保留；没有音乐节拍的片不填 |
| landmarks | `frame,purpose`；只描述应检查的接触/转折/安静，不能当实际发生的证据 |

## 声音从画面事件来，不从“默认BGM”来
1. 先列接触/速度峰值/转折的帧和需要的声音，包含主动留白。一次接触不该配循环whoosh。
2. 只加入用户允许、已有本地且许可明确的声音。`tracks:[]`就是无声，不暗中生成或下载；有narration文本也不会自动TTS。录音/现有本地TTS输出都以相同WAV/MP3适配进入。
3. 保留voice/music/sfx角色和源文件。显式gain/fade，源视频音轨全部静音，再混这些允许的轨；旁白超时失败，不静默丢词或拉伸。没有自动ducking、ASR/逐词对齐、自然音真实性判断。
4. 48000Hz混音、样本单位延迟、限幅后编码AAC；**不保证-14LUFS**。`inspect/decode.log`有实际EBU R128/true-peak与静音观察，按交付要求决定是否再做两遍响度处理；数值不能证明听感/语义/清晰度。
5. 若未真正试听，写`audio_listened:false`。自然录音、合成提示音、估计词时、实测词时必须区分；不能因装了音频分类器就声称“我听过”。

## 渲染后的证据，而非label证据
- `inspect`解码当前MP4，取每镜头中点、风险帧、每个切点的前1/当帧/后1和全片首尾；PNG与`inspection.json`帧号一一对应。`sheet.jpg`只是一种浏览方式，不等于已观看视频。
- black/freeze/silence是诊断事件，不是审美判决。安静结尾应静；不要为了消除freeze告警加入无意义idle。切点须逐对看身份、位置、光色、声音尾巴和丢帧，必要时看±3–6帧。
- `assembly.json`记录管线自身/输入/声明源码/输出SHA、帧数、画幅、帧率和独立pending三门。源码哈希仅覆盖明确列出的`sources`，不是自动完整依赖图；缺少依赖必须补，不支持智能增量重渲缓存。
- `package`仅打包5个已知草稿产物，核对哈希，不扫整个目录。它不包含源码、模型、私有参考图或.env；源码另按明确白名单交付。包仍是draft，正式交付前另跑`review_gate.py --require-pass`并保存真实审阅。

## 代表性执行
`examples/contact-resonance/build.py --out /outside/contact-proof` 自动完成本技能原创6秒两镜头、合成演示cue、字幕、剪辑、检查、草稿包。需Chrome + FFmpeg/ffprobe，见该例README；它不是被引仓93个预览的复播，也不证明未安装的19种工具可用。
