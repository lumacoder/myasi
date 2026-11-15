# 动效 / 视频 / 3D 流程
## 管线：Brief → build → animate → refine → render
| 阶段 | 产物 | 门禁 |
|---|---|---|
| Brief | 目标、时长、画幅/fps、受众、风格参考；时间轴表（镜头/起止秒/谁在动/字幕/转场） | 用户确认总时长与镜头数 |
| build | 场景、资产、关键姿态静帧（style frame） | 静帧确认风格，再写动画 |
| animate | 时间轴/缓动/stagger；默认约30秒样片，不足30秒做关键镜头 | 节奏、分镜确认后再批量 |
| refine | 反馈带时间点+元素ID+预期/实际，不只说“不够美” | 制作→渲染→观察→修改 循环收敛 |
| render | 终版导出 | 查分辨率、时长、fps、字幕安全区、音轨；删中间帧 |

## 选库（先用项目已有，再按下表；元数据见案例库）
| 需求 | 首选 | 备选/说明 |
|---|---|---|
| React 视频 | Remotion（+ remotion-dev/skills） | 讲解类：Motion Canvas |
| UI 状态/布局过渡 | motion（layout、AnimatePresence） | 小数值插值：ola、shifty |
| 时间轴、错峰 stagger | anime.js / GSAP timeline | 旧 CreateJS 项目：TweenJS |
| 数学/公式讲解 | Manim（Python） | 网页内：Motion Canvas |
| 2D 矢量场景 | two.js | 可交互/拖拽/编辑器：Konva |
| 设计师 AE 动效播放 | lottie-web（Bodymovin JSON） | 不手写复杂路径动画 |
| 粒子 | Proton | 简单发光：Canvas2D `globalCompositeOperation:'lighter'` |
| 网页 3D | three.js | 引擎级/物理/检查器：Babylon.js；HTML 元素式：LUME |
| 角色绑定、离线渲染 | Blender（GPL，作工具不作依赖） | 自动化见 Blender MCP 案例 |
| 游戏动画状态机 | Godot AnimationTree | — |
| GIF 导出 | gifenc（量化+抖动） | 长视频走 MP4，不用 GIF |

## 约束
- 只动 transform/opacity；尊重 `prefers-reduced-motion`；60fps 单帧预算约16.7ms，以实测为准。
- 同一画面只用一个动画引擎驱动同一属性，避免多库抢写。
- 迭代先发静帧，再样片，最后全片；中间帧导出后即清理（见 `hygiene.md`）。
