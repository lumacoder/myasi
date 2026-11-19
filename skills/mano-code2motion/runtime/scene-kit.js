/* Original optional drawing tools, not a scene schema or a renderer requirement. */
(function (root) {
  'use strict';
  function sample(seed, index) {
    let n = (seed ^ Math.imul(index + 1, 0x45d9f3b)) >>> 0;
    n = Math.imul(n ^ (n >>> 16), 0x45d9f3b);
    return ((n ^ (n >>> 16)) >>> 0) / 4294967296;
  }
  function onFrames(t, fps, stride) {
    if (![t, fps, stride].every(Number.isFinite) || fps <= 0 || !Number.isInteger(stride) || stride < 1) throw Error('bad frame cadence');
    return Math.floor(t * fps / stride + 1e-9) * stride / fps;
  }
  // Arc-length prefix: a long segment does not draw as quickly as a short one.
  function prefix(points, progress) {
    if (!Number.isFinite(progress)) throw Error('nonfinite progress');
    if (!points.length) return [];
    const lengths = points.slice(1).map((p, i) => Math.hypot(p[0] - points[i][0], p[1] - points[i][1]));
    let left = lengths.reduce((a, b) => a + b, 0) * Math.max(0, Math.min(1, progress));
    const out = [points[0].slice()];
    for (let i = 0; i < lengths.length; i++) {
      if (left <= 0) break;
      const d = lengths[i], a = points[i], b = points[i + 1];
      if (d === 0) continue;
      if (left >= d) { out.push(b.slice()); left -= d; }
      else { const u = left / d; out.push([a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u]); break; }
    }
    return out;
  }
  function stroke(ctx, points, progress) {
    const p = prefix(points, progress);
    if (p.length < 2) return;
    ctx.beginPath(); ctx.moveTo(...p[0]); p.slice(1).forEach(q => ctx.lineTo(...q)); ctx.stroke();
  }
  // A look is executable drawing code. Authors may replace all hooks or ignore this kit entirely.
  function compose(ctx, t, width, height, look, draw, camera) {
    ctx.save();
    try {
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, width, height);
      if (look.backdrop) look.backdrop(ctx, t, width, height);
      ctx.save();
      try { if (camera) camera(ctx, t, width, height); draw(ctx, t, width, height, look); }
      finally { ctx.restore(); }
      if (look.post) look.post(ctx, t, width, height);
    } finally { ctx.restore(); }
  }
  const kit = Object.freeze({sample, onFrames, prefix, stroke, compose});
  if (typeof module !== 'undefined' && module.exports) module.exports = kit;
  else root.ManoSceneKit = kit;
})(typeof globalThis === 'undefined' ? this : globalThis);
