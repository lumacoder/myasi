# 原创6秒制作案例：Contact / resonance

验证新增的镜头契约→自由绘制→逐镜头输出→准确剪辑→显式cue/字幕→切点证据→草稿包通路。不是上游样片复播，也不是用旧水墨C证明新能力。

## 运行（在技能目录）
```bash
python scripts/production.py doctor
python examples/contact-resonance/build.py --out /outside/repo/contact-proof
# 可选：--chrome /your/local/chrome --workers 1
```
只用已有Python、Chrome/Chromium、FFmpeg/ffprobe。没有网络/模型下载/订阅CLI/自动安装。build把本例源码与本技能原创runtime复制到**新产物目录**后生成WAV、渲染48+96帧；源示例目录不写入clip或媒体。源HTML的shared/scene-kit.js由build从runtime复制，所以先build，再浏览产物authored/wide/index.html或close/index.html。

产物：
- `authored/project.json`：用户可编辑的真实制作契约；两个shot的源码在authored/，合成演示cue在assets/，clip在clips/。
- `capture-wide/`、`capture-close/`：单Canvas真像素、乱序seek探测、无声film.mp4与capture-report。
- `assembly/proof.mp4`：6秒/144帧/768×432，字幕burn-in；唯一音轨是frame48开始的原创合成提示声。`captions.srt`、CREDITS、assembly.json含输入/输出/源码哈希。
- `inspection/sheet.jpg`、PNG与inspection.json：实际MP4首尾、镜头中点、风险帧、47/48/49切点；decode.log有黑/冻结/静音/响度诊断。它们不会自动证明故事/材质/声音好。
- `draft-proof.zip`：5个已知草稿交付文件，不扫源码/参考图/.env。源码在authored明确提供，不把整个工作目录随包发送。

## 继续改哪里
对故事/画面修改 `shared/scene.js` 或镜头HTML；可替换全部绘制机制。对剪辑/字幕/音量改产物manifest，然后重新assemble到新目录，不覆盖旧证据。先按brief的风险帧看当前输出，再正常速度复核；最弱处的下一版要保留旧源码和同时间对照，不能拿改了函数名当改了像素。

## 真实执行与一次修正
初版/改版都已在盒子用**显式选择的既有Chromium Headless Shell**按同配方渲染，144帧/24fps/768×432/6秒。系统Chrome连空页也超时，未归咎场景、未绕sandbox；MalePC低磁盘预算未跑整例，但确实跑本地FFmpeg/Node回归。通用入口仍用`--chrome /your/local/browser`，不绑定某机器路径。

制作者看真实PNG发现：初版4秒波纹过淡、底字幕贴近鼓框。一次有边界改版：波前从珠子轮廓外开始、加强有限寿命线条/减缓有限衰减，字幕改到上方留白；不是改函数名。期间“top”参数实际输出middle-left，被像素否证；修正实际参数后新增glyph位置回归。对照帧48/66/96/132；开段原始帧0/47像素相同，解码音轨相同。完整证据索引/视频与代码SHA见`review-status.json`；`revision-initial-to-revised.patch`可从当前改版逆向恢复初版scene/template。源码快照、MP4、PNG、比较视频在外部证据目录，不塞进技能包。

## 独立视觉审核与交付门禁
独立正常速度视觉反馈：红球落在浅圆形平面，接触时切俯视；三条有限圆环扩散消失。动作因果/切点时间连续性清楚、焦点一致，尺度变化但空间可读，未见漂移/几何pop。改版上方字幕确实减轻0:04对边缘的遮挡。

但器物读成盘/浅托盘/杯垫，**不是原brief要求的鼓**；没有可见鼓膜变形/张力/反弹。保留原意图，不通过把概念改成盘子“修复”结论。当前三门均partial：技术的帧/媒体测量通过仅限实测范围；可读性中动作/空间通过但主体身份不足；表现力未全面通过。delivery_gate仍blocked，详见review-status.json。

**审阅者音频不可访问，完全未试听；制作者也未试听。** 音轨存在、数值cue时序、解码/响度诊断不能充当实际听感或主观音画同步通过。合成tone不是自然foley。组装/检查JSON保留生成当时not_reviewed历史，不回写成全门通过。此次只记录审核，不再调效果或重渲染。

原水墨A/B/C及独立审阅不变：C可读性pass、表现力partial；旧12例评估仍未完成。
