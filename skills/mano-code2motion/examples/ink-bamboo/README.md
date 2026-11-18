# Ink bamboo：6秒原创案例与真实否证循环

**最终状态：C已独立正常速度审阅，可读性pass、表现力partial；不是所有门通过。** 观察到一次明显右弯、较小左回与末尾归静，未见漂叶/拉伸/橡胶塌陷；叶片仍偏刚性，内部柔性/迟响应不明显，回落稍机械，水墨partial。详见 `independent-review-C.json`。

## 文件与历史
- `index-c.html` / `scene-c.js`：最终C。`brief-c.md`解释唯一一轮动作修正与边界。
- `index.html` / `scene-b.js`：冻结B；两轮独立观看认为造型/连接改善但动作像重复idle，表现力fail，见 `independent-review-AB.json`。
- `index-a.html` / `scene-a.js`：冻结A。A/B不覆盖；原`brief.md`是历史初始简报。
- `review-summary.md`：作者静帧观察→独立否证→C修正→独立部分通过的时间顺序。
- `qa.js` / `qa-c.js`：工程QA，不判断审美或读图真实性。

全部原创纯Canvas2D，无外部位图/字体/音视频/生成依赖。定弧长弯曲与解析风包络是风格化机制，不是植物/流体仿真。

在技能根目录运行：
```bash
node examples/ink-bamboo/qa.js
node examples/ink-bamboo/qa-c.js
python scripts/render_project.py examples/ink-bamboo --entry index-c.html --duration 6 --fps 24 --out /outside/repo/ink-c --chrome /path/to/chrome
# 同时间设计帧：追加 --times 0.95,2.8,3.32,3.75,4.08,4.62,5.05,5.7
```
可直接打开HTML；正常播放循环仅供预览，每段导出仍为6.000秒单次事件。捕获URL带`?t=`时停止实时播放并绝对时间seek。实际导出1280×720、24fps、144帧、H264/yuv420p、无声。输出必须在仓库外新目录；本目录不提交视频/PNG/压缩包。

技术检查、独立可读性、表现力分别保留结论；数字/函数名不能替代真实视觉观察。此案例不是原30秒滑板修复，不代表12例冻结评估完成，也不证明通用创作能力或与研究来源等效。
