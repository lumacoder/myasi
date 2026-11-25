# 排版、表面细节与无白屏显隐（Surface & Type）

> 源自 Scrolltide AI Studio（MIT）。零额外依赖，直接提升页面精密感与完稿度。

## 1. 实测贴边全宽字标（`fitText`）
不要用 `vw` 猜测大字标宽度（不同字体前进宽度不同），用探针字号测量后按容器可用宽度精确缩放，并在 `document.fonts.ready` 与 `ResizeObserver` 时重算：
```js
/** el 需设 display: inline-block; white-space: nowrap; 放在父容器内 */
export function fitText(el) {
  const parent = el.parentElement;
  const PROBE = 100;
  const fit = () => {
    el.style.fontSize = `${PROBE}px`;
    const cs = getComputedStyle(parent);
    const available = parent.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
    const natural = el.offsetWidth; // 用 offsetWidth 而非 scrollWidth，避免被内部 transform 干扰
    if (natural > 0) el.style.fontSize = `${(PROBE * available) / natural}px`;
  };
  fit();
  document.fonts?.ready.then(fit);
  const ro = new ResizeObserver(fit);
  ro.observe(parent);
  return () => ro.disconnect();
}
```
宽字距字标末尾会多出一个 `letter-spacing` 尾空，用等量负 `margin-right`（如 `margin-right: -0.24em`）拉回视觉居中。

## 2. 收束型标题（Blur + Tracking）
固定舞台内的标题可用字距收敛 + 失焦变清晰入场，清晰后**务必清空 `filter = ''`** 以停止合成层开销：
```js
const tIn = easeOutCubic(range(p, 0.08, 0.24));
title.style.opacity = String(tIn * (1 - range(p, 0.42, 0.52)));
title.style.letterSpacing = `${lerp(0.6, 0.24, tIn)}em`;
title.style.filter = tIn < 0.99 ? `blur(${(1 - tIn) * 10}px)` : '';
```

## 3. 实时 HUD 仪表读数 + 单斜体衬线词 + 自适应导航
```css
.hud { font-family: var(--font-mono); font-size: 0.625rem; letter-spacing: 0.14em; text-transform: uppercase; opacity: 0.75; font-variant-numeric: tabular-nums; }
.serif { font-family: 'Instrument Serif', serif; font-style: italic; font-weight: 400; letter-spacing: -0.01em; }
/* 跨深/浅背景时自动反色的透明导航；内含实底 CTA 按钮如遇反色需独立层 */
.nav { position: fixed; inset: 0 0 auto; z-index: 50; color: #fff; mix-blend-mode: difference; }
```
- 实时读数（如任务计时 `T+ 00:12:40`、俯仰角、当地实时时间）仅作质感纹理，标注 `aria-hidden="true"`。
- 单斜体衬线词全标题只用 **1 个词**：`<h1>Technology crafted for all.<br />Not <em class="serif">machines</em>.</h1>`。

## 4. 渐进增强显隐（`data-reveal`，绝不白屏）
在 `<head>` 所有样式表前放首行脚本，保证未加载 JS 或脚本出错时页面内容全部直接可见：
```html
<script>document.documentElement.classList.add('js')</script>
```
```css
.js [data-reveal] {
  opacity: 0;
  transform: translate3d(0, 24px, 0);
  transition: opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1), transform 0.8s cubic-bezier(0.16, 1, 0.3, 1);
  transition-delay: calc(var(--i, 0) * 70ms);
}
.js [data-reveal].is-in { opacity: 1; transform: none; }
@media (prefers-reduced-motion: reduce) {
  .js [data-reveal] { opacity: 1; transform: none; transition: none; }
}
```
用 `IntersectionObserver`（`rootMargin: '0px 0px -10% 0px'`）+ `MutationObserver` 监听动态挂载区块，触发一次即 `unobserve`；入场完成后 `.is-in` 把 `transform` 置 `none`，不会盖掉元素自身的 hover `transform`。

## 5. 循环视频 Hero（`video-hero`）
```html
<section class="hero">
  <video class="hero__film" autoplay muted loop playsinline preload="auto" poster="/media/hero-poster.webp" aria-hidden="true">
    <source src="/media/hero.webm" type="video/webm" />
    <source src="/media/hero.mp4" type="video/mp4" />
  </video>
  <div class="hero__copy">
    <p class="hero__note rise" style="--d: 0.1s">2026 冬季开放两席定制</p>
    <h1 class="hero__title rise" style="--d: 0.2s">为所有人打磨的工具，<br />而非<em class="serif">机器</em>。</h1>
  </div>
</section>
```
```css
.hero { position: relative; min-height: 100svh; overflow: clip; background: var(--ground); }
.hero__film { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; opacity: 0; transition: opacity 0.9s cubic-bezier(0.16, 1, 0.3, 1); }
.hero__film.is-ready { opacity: 1; }
@keyframes rise { from { opacity: 0; transform: translate3d(0, 18px, 0); } to { opacity: 1; transform: none; } }
.rise { animation: rise 0.8s cubic-bezier(0.16, 1, 0.3, 1) both; animation-delay: var(--d, 0s); }
@media (prefers-reduced-motion: reduce) { .rise { animation: none; } .hero__film { transition: none; } }
```
```js
const film = document.querySelector('.hero__film');
const ready = () => film.classList.add('is-ready');
if (film.readyState >= 3) ready();
else film.addEventListener('canplay', ready, { once: true });
```
- **对比度保护**：先把文案锚定在画面安静区域，或调整 `object-position`；确有必要时仅在文案底部加局部渐变或柔阴影（`0 2px 18px rgb(0 0 0 / 0.4)`），**不要铺一层全屏黑罩**毁掉视频质感。
- 视频压制建议：1080p 无音轨 MP4（`-movflags +faststart`）+ VP9 WebM，单循环控制在 ~6 MB 内，首帧导出 WebP 作 `poster`。
