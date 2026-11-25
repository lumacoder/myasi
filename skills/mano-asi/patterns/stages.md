# 四大主力滚动舞台（Stages）

> 源自 Scrolltide AI Studio（MIT）。每页通常只选 **1 个**核心舞台；均基于 `patterns/engine.md` 的 `drive` 驱动。

---

## 1. 帧序列滚动影片（`film`）
**何时使用**：让访客通过滚动条亲自操控一段连续运镜、产品旋转或拆解动画。
**关键原则**：**用 WebP 帧序列 + Canvas，不用 `<video>` 改 `currentTime`**（高频改写 `currentTime` 会触发异步 seek 丢帧/卡顿）；用 `HTMLImageElement` 而非 `ImageBitmap`（防止解码位图撑爆手机内存）。

### 切帧（`ffmpeg`，横竖双裁切）
```bash
mkdir -p public/frames/d public/frames/m
# d = 桌面横版 1600 宽，24fps，每帧目标 15–40KB
ffmpeg -i film.mp4 -vf "fps=24,scale=1600:-2" -c:v libwebp -quality 72 -compression_level 6 -f image2 public/frames/d/f%03d.webp
# m = 手机竖版 9:16 居中裁切，720 宽
ffmpeg -i film.mp4 -vf "fps=24,crop=ih*9/16:ih:(iw-ih*9/16)*0.5:0,scale=720:-2" -c:v libwebp -quality 70 -compression_level 6 -f image2 public/frames/m/f%03d.webp
```

### 粗到细加载 + 焦点裁切 + Fritsch–Carlson 单调速度曲线
```js
// 1) 粗到细队列：优先帧 -> 步长 32 -> 16 -> 8 -> 4 -> 2 -> 1，并发 6 个
export function loadFrames(set, count, priority, onFrame) {
  const seen = new Set(), queue = [];
  const push = (i) => { if (i >= 0 && i < count && !seen.has(i)) { seen.add(i); queue.push(i); } };
  priority.forEach(push);
  for (let s = 32; s >= 1; s /= 2) for (let i = 0; i < count; i += s) push(i);
  push(count - 1);
  let cancelled = false;
  const loadOne = (i) => new Promise((res, rej) => {
    const img = new Image();
    img.decoding = 'async';
    img.onerror = () => rej();
    img.src = `/frames/${set}/f${String(i + 1).padStart(3, '0')}.webp`;
    img.decode().then(() => res(img), () => (img.complete ? res(img) : (img.onload = () => res(img))));
  });
  const worker = async () => {
    while (!cancelled && queue.length) {
      const i = queue.shift();
      try { const img = await loadOne(i); if (!cancelled) onFrame(i, img); } catch {}
    }
  };
  const first = queue.shift();
  loadOne(first).then((img) => !cancelled && onFrame(first, img)).catch(() => {}).finally(() => {
    for (let k = 0; k < 6; k++) worker();
  });
  return () => (cancelled = true);
}

// 2) 找最近已加载帧 + 带主体焦点 (fx, fy) 的 cover 绘制（卡片占半屏时保持主体可见）
export function nearest(frames, i) {
  if (frames[i]) return frames[i];
  for (let d = 1; d < frames.length; d++) {
    if (frames[i - d]) return frames[i - d];
    if (frames[i + d]) return frames[i + d];
  }
  return null;
}
export function drawCover(ctx, img, w, h, fx = 0.5, fy = 0.5) {
  const s = Math.max(w / img.naturalWidth, h / img.naturalHeight);
  const dw = img.naturalWidth * s, dh = img.naturalHeight * s;
  const dx = Math.min(0, Math.max(w - dw, w / 2 - fx * dw));
  const dy = Math.min(0, Math.max(h - dh, h / 2 - fy * dh));
  ctx.drawImage(img, dx, dy, dw, dh);
}

// 3) Fritsch–Carlson 单调三次曲线：beats = [[progress, filmSeconds], ...]
// 平段（如 [0.25, 10] -> [0.39, 10]）表示“停顿 hold”，供产品卡/文案停留阅读
export function createRemap(beats) {
  const n = beats.length, xs = beats.map((b) => b[0]), ys = beats.map((b) => b[1]), d = [];
  for (let i = 0; i < n - 1; i++) d.push((ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]));
  const m = new Array(n);
  m[0] = d[0]; m[n - 1] = d[n - 2];
  for (let i = 1; i < n - 1; i++) m[i] = d[i - 1] * d[i] <= 0 ? 0 : (d[i - 1] + d[i]) / 2;
  for (let i = 0; i < n - 1; i++) {
    if (d[i] === 0) { m[i] = m[i + 1] = 0; continue; }
    const a = m[i] / d[i], b = m[i + 1] / d[i], s = a * a + b * b;
    if (s > 9) { const t = 3 / Math.sqrt(s); m[i] = t * a * d[i]; m[i + 1] = t * b * d[i]; }
  }
  return (u) => {
    const x = Math.min(xs[n - 1], Math.max(xs[0], u));
    let i = 0;
    while (i < n - 2 && x > xs[i + 1]) i++;
    const h = xs[i + 1] - xs[i], t = (x - xs[i]) / h, t2 = t * t, t3 = t2 * t;
    return (2*t3 - 3*t2 + 1)*ys[i] + (t3 - 2*t2 + t)*h*m[i] + (-2*t3 + 3*t2)*ys[i+1] + (t3 - t2)*h*m[i+1];
  };
}
```
> 预加载策略：每隔约 16 帧解码（约 30 帧覆盖全片）即可揭开 preloader，最多等 6 秒超时放行，底层先画出首帧防黑屏。

---

## 2. 同源分层视差舞台（`layers`）
**何时使用**：无视频/WebGL，用一张高分辨率渲染图切出 4–6 层透明 PNG/WebP，打造极强空间纵深。
**关键设计**：
1. 所有层必须从**同一张宽画幅原图**切出且同画布尺寸、共用同一 `object-position`，确保任意视口下严丝合缝不漂移（另有手机竖版 `m/` 图集）。
2. **夹心标题**：把 `<h1>` 放在中景与前景层之间，滚动时前景层从文字前面掠过，瞬间产生真实三维空间感。
3. **退场倍率由远及近递增 + `.apron`**：远景慢（`-12vh`）、中景中（`-26vh`）、前景快（`-44vh`）、地面最快（`-78vh`）并带 `.apron` 实色块无缝衔接到下一区。

```html
<section class="stage" id="rise" style="height: 440svh" aria-label="场景开场">
  <div class="stage__pin">
    <div class="layer" data-layer="sky"><picture><source media="(max-width:767px)" srcset="/layers/m/sky.webp" /><img src="/layers/d/sky.webp" alt="" aria-hidden="true" fetchpriority="high" decoding="async" /></picture></div>
    <div class="layer" data-layer="subject">…</div>
    <div class="layer" data-layer="midground">…</div>
    <h1 class="stage-title">Watch the Earth rise</h1>
    <div class="layer" data-layer="foreground">…</div>
    <div class="layer" data-layer="ground">…<div class="apron"></div></div>
  </div>
</section>
```
```css
.layer { position: absolute; inset: 0; will-change: transform; }
.layer img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: 58% 50%; }
@media (min-width: 768px) { .layer img { object-position: center; } }
.apron { position: absolute; left: 0; right: 0; top: 100%; height: 110vh; background: var(--ground); }
```
```js
drive(stage, (p) => {
  const settle = easeOutCubic(range(p, 0, 0.5));
  const exit = range(p, 0.7, 1);
  set('sky', lerp(0, -6, p), lerp(1.14, 1, settle));
  const rise = easeOutCubic(range(p, 0.04, 0.5));
  set('subject', lerp(34, 0, rise) - exit * 12, lerp(0.92, 1, rise));
  set('midground', lerp(9, 0, settle) - exit * 26);
  const rim = easeOutCubic(range(p, 0.28, 0.58));
  set('foreground', -exit * 44, lerp(1.6, 1, rim), rim);
  const up = easeOutCubic(range(p, 0.34, 0.6));
  set('ground', lerp(36, 0, up) - exit * 78);
});
```

---

## 3. 自绘 SVG 路径 + 领航点（`drawn`）
**何时使用**：航线、工艺步骤、时间线、发展路线，随滚动一段一段描摹并同步更新里程/阶段数。
- 给每段 `<path>` 设 `pathLength="1"` 与 `stroke-dasharray="1 1"`、`stroke-dashoffset="1"`，用 `stroke-dashoffset = 1 - k` 统一控笔；底层垫一层 `opacity: 0.08` 的虚线幽灵全轨。
- 领航光点坐标用 `path.getPointAtLength(path.getTotalLength() * k)` 实时定位。
- 实时跳动的数字设 `aria-live="off"` + `tabular-nums`，阶段说明文本设 `aria-live="polite"`（只在切换段时更新 DOM）。

---

## 4. 横向滚动胶片卷（`reel`）
**何时使用**：3–6 张照片/案例卡随垂直滚动横向穿过视线（每张配约 80–90svh，4 张约 `340svh`）。
- 设一条焦点基准线（如 `FOCUS = 0.62 * vw`），计算每张卡中心到焦点线的距离 `off`：越近越清晰且满尺寸，越远越淡（`opacity: 1 - a * 0.55`）且微缩（`scale(1 - a * 0.07)`）。
- 卡片内部图片 `scale(1.15)` 并随 `off` 反向平推 `translate3d(off * -60px, 0, 0)`，形成画框内视差。
- 严格遵循「先读完所有 `getBoundingClientRect()` 再写样式」避免每帧强制回流；键盘/读屏仍可读原生有序列表 `<ol>`。
