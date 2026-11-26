# CHANGELOG — mano-code2motion

## 0.6.0
- **Web 3D 直播交付**：`guides/web-3d-delivery.md`（按题材选 Web 3D、页面即交付物、Three.js 版 `renderAt` 契约、`?drive=1`、标注投影顺序、esbuild IIFE 打包、沙箱验证边界）。
- `SKILL.md`：补充介质/网页交付/标注投影规则，扩展交付形态与 Web 打包说明。

## 0.5.0
- **18 个仓库 JSON 资料库**：`references/repos-18.json`（2026-11-20 逐个核对 GitHub API 许可/语言/简介 + README/SKILL.md 头部），附 `lookup_by_task` 与 tags 索引。
- **查库工具**：`scripts/repos_lookup.py`（纯标准库，只读，`--tag` / `--query` / `--repo` / `--list-tags` / `--all`）。
- **精华提炼**：`references/essences.md`（P0 6 条直接进技能、P1 11 条按镜头选路、P2 查库提示；不复制代码、提示词长文、媒体、字体或模型）。
- `SKILL.md` 新增「选路先查库」规则；`references/language-to-code.md` 补实测数表与字幕契约速查。

## 0.4.0
- **Copy → Style → Paint → VFX → Beat → Captions**：有参考先逐帧复刻结构与节拍，再原创；只学语法，不复制角色/代码/字体/媒体（`guides/copy-and-reference.md`）。
- **语言生成代码精华**：`references/language-to-code.md`（渲染契约、形容词换数字、提示词模板、数字速查、禁单、时间总谱先行、运动量测、按镜头选路）。
- **时间总谱先行**与**运动量测**（freeze 检测、运动曲线、1080p 主镜头主体像素宽 ≥170px、关键动作帧号误差）。
- 18 个仓库已按 GitHub API 核对许可（2026-11-20，见 `references/sources.md`），不导入其中任何代码与素材。

## 0.3.0
- 新增 `scripts/production.py`：帧级镜头表 → 本地媒体 conform/剪辑 → 显式音轨/字幕 → 解码/切点前后图 → 哈希校验草稿包。
- 新增 `guides/production.md`、`guides/style-and-continuity.md`、`runtime/scene-kit.js` 与 `examples/contact-resonance/` 6 秒两镜头示例。
- 新增 `references/video-studio-kit.md` + `.audit.json`（固定 SHA、许可边界与原生实现说明）。
