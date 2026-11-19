/* Original proof scene. Stylized resonant membrane, not a fluid or acoustic simulation. */
(function () {
  'use strict';
  const K = window.ManoSceneKit, c = document.querySelector('canvas'), ctx = c.getContext('2d');
  const W = c.width, H = c.height, close = c.dataset.shot === 'close';
  const ink = '#24394b', red = '#ba4838';
  const look = {
    backdrop(g) {
      g.fillStyle = '#eee8d9'; g.fillRect(0, 0, W, H);
      // Fixed fibres, not fresh random noise that defeats seeking or makes a false idle.
      g.strokeStyle = '#a29b8625'; g.lineWidth = 0.6;
      for (let i = 0; i < 170; i++) {
        const x = K.sample(31, i * 3) * W, y = K.sample(31, i * 3 + 1) * H;
        g.beginPath(); g.moveTo(x, y); g.lineTo(x + 3 + K.sample(31, i * 3 + 2) * 12, y - 0.7); g.stroke();
      }
    },
    bead(g, x, y, r) {
      g.fillStyle = red; g.strokeStyle = ink; g.lineWidth = 2;
      g.beginPath(); g.ellipse(x, y, r, r * 0.96, -0.1, 0, Math.PI * 2); g.fill(); g.stroke();
      g.strokeStyle = '#f1b391'; g.lineWidth = 2.5;
      g.beginPath(); g.arc(x - r * 0.12, y - r * 0.03, r * 0.54, 3.5, 4.65); g.stroke();
    }
  };
  function ellipse(g, x, y, rx, ry) { g.beginPath(); g.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2); }
  function wide(g, t) {
    const y0 = 81, contact = 273, release = 0.55;
    const u = Math.max(0, Math.min(1, (t - release) / (2 - release)));
    const y = y0 + (contact - y0) * u * u;
    g.fillStyle = '#26394b18'; ellipse(g, 384, 340, 172, 15); g.fill();
    // Taut skin supported by a warm wooden rim; same red bead in both framings.
    g.fillStyle = '#aa7252'; g.strokeStyle = ink; g.lineWidth = 2.5;
    g.beginPath(); g.moveTo(220, 298); g.lineTo(236, 331); g.quadraticCurveTo(384, 370, 532, 331); g.lineTo(548, 298); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = '#e0c8a3'; ellipse(g, 384, 294, 164, 47); g.fill(); g.stroke();
    g.strokeStyle = '#ab8667'; g.lineWidth = 1.2; ellipse(g, 384, 294, 150, 38); g.stroke();
    // Shadow tightens continuously as the actual contact approaches.
    g.fillStyle = '#24394b'; g.globalAlpha = 0.035 + 0.11 * u * u;
    ellipse(g, 384, 293, 28 - 10 * u, 5); g.fill(); g.globalAlpha = 1;
    look.bead(g, 384, y, 20);
  }
  function detail(g, t) {
    const age = Math.max(0, t - 2), x = 384, y = 223;
    g.fillStyle = '#a36c4d'; g.strokeStyle = ink; g.lineWidth = 3;
    ellipse(g, x, y, 216, 158); g.fill(); g.stroke();
    g.fillStyle = '#e0c8a3'; ellipse(g, x, y - 5, 200, 144); g.fill(); g.stroke();
    g.strokeStyle = '#b39474'; g.lineWidth = 1;
    for (let k = 0; k < 16; k++) {
      const a = k / 16 * Math.PI * 2;
      g.beginPath(); g.moveTo(x + Math.cos(a) * 201, y - 5 + Math.sin(a) * 145);
      g.lineTo(x + Math.cos(a) * 212, y - 2 + Math.sin(a) * 153); g.stroke();
    }
    // A single outward disturbance, then two weaker trailing fronts; no endless sine idle.
    for (let k = 0; k < 3; k++) {
      const a = age - k * 0.23;
      if (a < 0 || a > 2.4) continue;
      const r = 32 + 65 * a, alpha = (0.75 / (k + 1)) * Math.pow(Math.max(0, 1 - a / 2.4), 0.7);
      g.globalAlpha = alpha; g.strokeStyle = ink; g.lineWidth = 3.2 - k * 0.45;
      ellipse(g, x, y - 5, r, r * 0.72); g.stroke();
    }
    g.globalAlpha = 1;
    const rebound = age < 0.65 ? 7 * Math.sin(Math.PI * age / 0.65) * Math.exp(-age * 3) : 0;
    g.fillStyle = '#24394b20'; ellipse(g, x + 1, y + 1, 30, 9); g.fill();
    look.bead(g, x, y - 17 - rebound, 29);
  }
  window.renderAt = function (seconds) {
    if (!Number.isFinite(seconds)) throw Error('invalid seek');
    const local = Math.max(0, Math.min(close ? 4 : 2, seconds));
    K.compose(ctx, close ? local + 2 : local, W, H, look, close ? detail : wide);
  };
  window.READY = true;
  window.renderAt(0);
  // Capture mode never starts a competing RAF. Live playback is optional and absolute-time based.
  if (!new URLSearchParams(location.search).has('t')) {
    const start = performance.now();
    function live(now) { window.renderAt(Math.min(close ? 4 : 2, (now - start) / 1000)); if ((now - start) / 1000 < (close ? 4 : 2)) requestAnimationFrame(live); }
    requestAnimationFrame(live);
  }
})();
