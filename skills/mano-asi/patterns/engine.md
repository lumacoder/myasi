# 单循环滚动引擎（Engine）

> 源自 Scrolltide AI Studio（MIT）。核心思想：全页只跑 **1 个 `requestAnimationFrame` 循环**；Lenis 先推进，各滚动区块自己计算进度并直接写 DOM `style`，**绝不在滚动中更新框架 `state`**（仅离散步骤切换时更新）。

## 1. 数学基础（`scroll-math.js`）
```js
export const clamp = (v, min = 0, max = 1) => Math.min(max, Math.max(min, v));
export const lerp = (a, b, t) => a + (b - a) * t;
/** v 在 [a, b] 间的归一化进度（0~1），所有 Beat 窗口的基础单位 */
export const range = (v, a, b) => clamp((v - a) / (b - a));
export const smoothstep = (t) => t * t * (3 - 2 * t);
export const easeOutCubic = (t) => 1 - (1 - t) ** 3;

/** 计算高容器（内部有 position: sticky 子元素）的滚动进度 0→1 */
export function pinProgress(el) {
  const rect = el.getBoundingClientRect();
  const vh = window.innerHeight;
  return { p: clamp(-rect.top / Math.max(1, rect.height - vh)), rect, vh };
}
```

## 2. 单一 rAF 引擎（`scroll-engine.js`）
```js
import Lenis from 'lenis'; // 无构建环境可用 pinned CDN：<script src="https://unpkg.com/lenis@1.3.11/dist/lenis.min.js"></script>
import { pinProgress } from './scroll-math.js';

const subscribers = new Set();
let lenis = null;

export function startScroll() {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  // reduced-motion 下关闭平滑插值，但保留滚动映射
  if (!reduced) lenis = new Lenis({ lerp: 0.09, smoothWheel: true, wheelMultiplier: 0.9 });

  let raf = 0;
  const loop = (time) => {
    lenis?.raf(time);
    subscribers.forEach((fn) => fn(time));
    raf = requestAnimationFrame(loop);
  };
  raf = requestAnimationFrame(loop);
  return () => {
    cancelAnimationFrame(raf);
    lenis?.destroy();
    lenis = null;
  };
}

export function onFrame(fn) {
  subscribers.add(fn);
  return () => subscribers.delete(fn);
}

/** 仅当区块在视口内且进度真实变化时才回调 render(p, rect, vh) */
export function drive(section, render) {
  let last = -1;
  return onFrame(() => {
    const { p, rect, vh } = pinProgress(section);
    if (rect.bottom < 0 || rect.top > vh) return;
    if (Math.abs(p - last) < 0.00005) return;
    last = p;
    render(p, rect, vh);
  });
}

export function scrollToTarget(hashOrY) {
  const target = typeof hashOrY === 'number' ? hashOrY : document.querySelector(hashOrY);
  if (target == null) return;
  if (lenis) lenis.scrollTo(target, { duration: 1.6 });
  else if (typeof target === 'number') window.scrollTo({ top: target });
  else target.scrollIntoView();
}
```

## 3. 固定舞台 + Beat 窗口写法
```html
<section class="stage" id="hero-stage" style="height: 440svh">
  <div class="stage__pin"><!-- sticky 内部放画布/分层/文案 --></div>
</section>
```
```css
.stage { position: relative; }
.stage__pin { position: sticky; top: 0; height: 100svh; overflow: hidden; }
```
把整段编排写成文件顶部的显式 `[start, end]` 区间：
```js
// 0.00–0.18 尘雾散开  0.04–0.50 主体升起  0.10–0.50 标题显影  0.70–1.00 整体退场
const BEATS = { dust: [0, 0.18], rise: [0.04, 0.5], title: [0.1, 0.5], exit: [0.7, 1] };

drive(stage, (p) => {
  const tIn = easeOutCubic(range(p, ...BEATS.title));
  const tOut = range(p, 0.42, 0.52);
  title.style.opacity = String(tIn * (1 - tOut));
  title.style.transform = `translate3d(0, ${-p * 6}vh, 0)`;
});
```
离散步骤切换（如章节文字）**只在索引真正改变时**改 DOM：
```js
let current = -1;
drive(stage, (p) => {
  const step = Math.min(STEPS.length - 1, Math.floor(range(p, 0.06, 0.92) * STEPS.length));
  if (step !== current) {
    current = step;
    label.textContent = STEPS[step].title;
  }
});
```

## 4. React / Next.js 接入与避坑清单
- **React / Next.js**：顶层布局 `useEffect` 调 `startScroll()` 并返回清理函数；每个舞台组件在自己的 `useEffect` 里用 `drive(ref.current, ...)` 直接写 `elRef.current.style`；Next.js App Router 下引擎与舞台均为 `'use client'`。
- **禁止祖先 `overflow: hidden`**：它会直接破坏 `position: sticky`！防横向溢出请在 `html, body` 用 `overflow-x: clip`；祖先元素也不要加 `transform`。
- **用 `svh` 不用 `vh`**：移动端地址栏收放不会让舞台总高在滚动途中跳变。
- **读写分离**：每帧先读完所有 `getBoundingClientRect()`，再批量写 `style`，避免强制同步回流（layout thrashing）。
- **禁止与 CSS `transition` 混用**：rAF 每帧写的属性绝不加 `transition`。
