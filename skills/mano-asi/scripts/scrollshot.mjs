#!/usr/bin/env node
// scrollshot: photographs a page at scroll checkpoints, on a desktop and a phone, and writes a
// QA report, so a scroll-driven page is checked where it actually changes, not only at the top.
// Adapted from scrolltide/ai-studio-skill (MIT License, Copyright (c) 2026 Scrolltide).
//
//   node scrollshot.mjs <url | page.html | folder> [out-dir] [options]
//
//   url        a running dev server or a live page, e.g. http://localhost:5173
//   page.html  a single file; its folder is served on a local port
//   folder     a build output (dist/, build/, out/); served on a local port
//
//   --stops 0,25,50,75,100   checkpoints, as % of the scrollable height
//   --wait 900               ms to let the page settle at each checkpoint
//   --settle 1500            ms to wait after load before the first checkpoint (entrances, preloaders)
//   --only desktop|mobile    one viewport instead of both
//   --reduced                also run a pass with prefers-reduced-motion: reduce
//
// Needs Playwright, from the project or globally:
//   npm i -D playwright && npx playwright install chromium
// With only playwright-core installed it drives an installed Chrome or Edge instead.
//
// Exit code 1 when something blocking turned up (page errors, failed requests, broken images,
// sideways scroll), so a script can stop on it.
import { createHash } from 'node:crypto';
import { createReadStream, existsSync, mkdirSync, statSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { createRequire } from 'node:module';
import { basename, dirname, extname, join, resolve, sep } from 'node:path';
import { pathToFileURL } from 'node:url';

const argv = process.argv.slice(2);
const flag = (name, fallback) => {
  const i = argv.indexOf(`--${name}`);
  return i === -1 ? fallback : argv[i + 1];
};
const SWITCHES = new Set(['--reduced']); // flags that take no value
const positional = argv.filter((a, i) => !a.startsWith('--') && !(i > 0 && argv[i - 1].startsWith('--') && !SWITCHES.has(argv[i - 1])));
const target = positional[0];
if (!target) {
  console.log(readUsage());
  process.exit(2);
}
const outDir = resolve(positional[1] ?? 'shots');
const stops = flag('stops', '0,25,50,75,100').split(',').map(Number).filter((n) => n >= 0 && n <= 100);
const wait = Number(flag('wait', 900));
const settle = Number(flag('settle', 1500));
const only = flag('only', '');
const reduced = argv.includes('--reduced');

const VIEWS = [
  { name: 'desktop', viewport: { width: 1440, height: 900 }, isMobile: false, hasTouch: false },
  { name: 'mobile', viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true },
].filter((v) => !only || v.name === only);

function readUsage() {
  return 'usage: node scrollshot.mjs <url | page.html | folder> [out-dir] [--stops 0,25,50,75,100] [--wait 900] [--settle 1500] [--only desktop|mobile] [--reduced]';
}

/* ------------------------------------------------------------ playwright */

async function loadChromium() {
  // Resolve from the project being checked first, then from wherever this script lives.
  const bases = [join(process.cwd(), 'noop.js'), import.meta.url];
  for (const base of bases) {
    for (const name of ['playwright', 'playwright-core']) {
      try {
        const mod = await import(pathToFileURL(createRequire(base).resolve(name)).href);
        const chromium = mod.chromium ?? mod.default?.chromium;
        if (chromium) return chromium;
      } catch {}
    }
  }
  return null;
}

async function launch(chromium) {
  const attempts = [{}, { channel: 'chrome' }, { channel: 'msedge' }];
  let last;
  for (const opts of attempts) {
    try {
      return await chromium.launch(opts);
    } catch (e) {
      last = e;
    }
  }
  throw last;
}

/* ------------------------------------------------------------ static server */

const TYPES = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.map': 'application/json', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp',
  '.avif': 'image/avif', '.gif': 'image/gif', '.ico': 'image/x-icon', '.mp4': 'video/mp4',
  '.webm': 'video/webm', '.mp3': 'audio/mpeg', '.woff2': 'font/woff2', '.woff': 'font/woff',
  '.ttf': 'font/ttf', '.otf': 'font/otf', '.glb': 'model/gltf-binary', '.gltf': 'model/gltf+json',
  '.hdr': 'application/octet-stream', '.ktx2': 'image/ktx2', '.wasm': 'application/wasm', '.txt': 'text/plain',
};

function serve(root) {
  const base = resolve(root);
  const server = createServer((req, res) => {
    const path = decodeURIComponent(new URL(req.url, 'http://local').pathname);
    let file = resolve(base, '.' + path);
    if (file !== base && !file.startsWith(base + sep)) return res.writeHead(403).end();
    if (existsSync(file) && statSync(file).isDirectory()) file = join(file, 'index.html');
    // Client-side routes (no extension) fall back to the app shell; a missing asset stays a 404.
    if (!existsSync(file) && !extname(path)) file = join(base, 'index.html');
    if (!existsSync(file)) return res.writeHead(404).end();
    const size = statSync(file).size;
    const type = TYPES[extname(file).toLowerCase()] ?? 'application/octet-stream';
    const range = /bytes=(\d*)-(\d*)/.exec(req.headers.range ?? '');
    if (range) {
      const start = range[1] ? Number(range[1]) : 0;
      const end = range[2] ? Math.min(Number(range[2]), size - 1) : size - 1;
      res.writeHead(206, { 'Content-Type': type, 'Content-Length': end - start + 1, 'Content-Range': `bytes ${start}-${end}/${size}`, 'Accept-Ranges': 'bytes' });
      return createReadStream(file, { start, end }).pipe(res);
    }
    res.writeHead(200, { 'Content-Type': type, 'Content-Length': size, 'Accept-Ranges': 'bytes' });
    createReadStream(file).pipe(res);
  });
  return new Promise((ok) => server.listen(0, '127.0.0.1', () => ok(server)));
}

async function resolveTarget(t) {
  if (/^https?:\/\//.test(t)) return { url: t, server: null };
  const p = resolve(t);
  if (!existsSync(p)) throw new Error(`not found: ${t}`);
  const isDir = statSync(p).isDirectory();
  const server = await serve(isDir ? p : dirname(p));
  const { port } = server.address();
  return { url: `http://127.0.0.1:${port}/${isDir ? '' : encodeURIComponent(basename(p))}`, server };
}

/* ------------------------------------------------------------ in-page probes */

const pad = (n) => String(n).padStart(3, '0');
const sha = (buf) => createHash('sha1').update(buf).digest('hex');
const pause = (ms) => new Promise((r) => setTimeout(r, ms));

async function scrollTo(page, y) {
  // Step there a half-screen at a time, two frames per step, so anything driven by the scroll
  // (a frame film, a drawn path, a counter) sees the in-between positions like a real visit.
  await page.evaluate(async (to) => {
    const from = window.scrollY;
    const steps = Math.max(1, Math.min(60, Math.ceil(Math.abs(to - from) / (innerHeight * 0.5))));
    for (let i = 1; i <= steps; i++) {
      window.scrollTo(0, from + ((to - from) * i) / steps);
      await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
    }
  }, y);
}

const PROBE_SIDEWAYS = () => {
  const y = window.scrollY;
  window.scrollTo(99999, y);
  const canScrollX = window.scrollX > 0;
  window.scrollTo(0, y);
  if (!canScrollX) return { sideways: false, culprits: [] };
  const vw = document.documentElement.clientWidth;
  const clips = (el) => {
    for (let a = el.parentElement; a && a !== document.body && a !== document.documentElement; a = a.parentElement) {
      const o = getComputedStyle(a).overflowX;
      if (o !== 'visible') return true;
    }
    return false;
  };
  const describe = (el) => el.tagName.toLowerCase() + (el.id ? `#${el.id}` : '') + (typeof el.className === 'string' && el.className.trim() ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : '');
  const culprits = [...document.querySelectorAll('body *')]
    .filter((el) => {
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.right > vw + 1 && getComputedStyle(el).position !== 'fixed' && !clips(el);
    })
    .slice(0, 6)
    .map((el) => `${describe(el)} (right edge ${Math.round(el.getBoundingClientRect().right)}px of ${vw}px)`);
  return { sideways: true, culprits };
};

const PROBE_PAGE = () => {
  const family = (f) => f.family.replace(/["']/g, '');
  const loadedFonts = [...new Set([...document.fonts].filter((f) => f.status === 'loaded').map(family))];
  const declaredFonts = new Set([...document.fonts].map(family));
  const h1 = document.querySelector('h1');
  const h1Font = h1 ? getComputedStyle(h1).fontFamily.split(',')[0].replace(/["']/g, '').trim() : null;
  const generic = ['serif', 'sans-serif', 'monospace', 'system-ui', 'cursive', 'fantasy', 'ui-sans-serif', 'ui-serif', 'ui-monospace', '-apple-system', 'BlinkMacSystemFont'];
  return {
    title: document.title,
    screens: +(document.documentElement.scrollHeight / innerHeight).toFixed(1),
    ground: { html: getComputedStyle(document.documentElement).backgroundColor, body: getComputedStyle(document.body).backgroundColor },
    loadedFonts,
    h1: h1
      ? {
          text: h1.textContent.trim().replace(/\s+/g, ' ').slice(0, 80),
          font: h1Font,
          // declared = the page ships it as a web font; a system font is never declared.
          fontDeclared: declaredFonts.has(h1Font),
          fontLoaded: generic.includes(h1Font) || loadedFonts.includes(h1Font),
        }
      : null,
    videos: [...document.querySelectorAll('video')].map((v) => ({ src: (v.currentSrc || v.src || '').slice(-90), readyState: v.readyState, paused: v.paused, error: v.error ? v.error.code : null })),
    brokenImages: [...document.images].filter((i) => i.complete && i.naturalWidth === 0 && (i.currentSrc || i.src)).map((i) => (i.currentSrc || i.src).slice(-120)),
    reducedMotionRules: [...document.styleSheets].some((s) => {
      try {
        return [...s.cssRules].some((r) => r.media && /prefers-reduced-motion/.test(r.media.mediaText));
      } catch {
        return false;
      }
    }),
  };
};

/* ------------------------------------------------------------ one viewport */

async function run(browser, url, view, { stopsFor, motion, label }) {
  const context = await browser.newContext({
    viewport: view.viewport, isMobile: view.isMobile, hasTouch: view.hasTouch,
    deviceScaleFactor: 1, reducedMotion: motion,
  });
  const page = await context.newPage();
  const log = { consoleErrors: [], pageErrors: [], failedRequests: [], abortedRequests: 0, httpErrors: [], requests: [] };
  // The browser asks for /favicon.ico on its own; a page without one isn't broken.
  const favicon = (u) => /\/favicon\.ico(\?|$)/.test(u ?? '');
  page.on('console', (m) => m.type() === 'error' && !favicon(m.location()?.url) && log.consoleErrors.push(m.text().slice(0, 300)));
  page.on('pageerror', (e) => log.pageErrors.push(String(e.message).slice(0, 300)));
  page.on('requestfailed', (r) => {
    const why = r.failure()?.errorText ?? 'failed';
    // Media elements cancel their own range requests all the time; that's not a failure.
    if (why.includes('ERR_ABORTED')) log.abortedRequests++;
    else if (!favicon(r.url())) log.failedRequests.push(`${why} ${r.url().slice(0, 160)}`);
  });
  page.on('response', (r) => r.status() >= 400 && !favicon(r.url()) && log.httpErrors.push(`${r.status()} ${r.url().slice(0, 160)}`));
  page.on('request', (r) => log.requests.push({ url: r.url(), type: r.resourceType() }));

  const shots = [];
  await page.goto(url, { waitUntil: 'commit', timeout: 45000 });
  if (view.name === 'desktop' && motion === 'no-preference') {
    await pause(350);
    const file = join(outDir, 'desktop-first-paint.png');
    await page.screenshot({ path: file }).catch(() => {});
    shots.push({ stop: 'first paint', file });
  }
  await page.waitForLoadState('load', { timeout: 45000 }).catch(() => {});
  await page.waitForLoadState('networkidle', { timeout: 8000 }).catch(() => {});
  await page.evaluate(() => document.fonts?.ready).catch(() => {});
  await pause(settle);

  const max = await page.evaluate(() => Math.max(0, document.documentElement.scrollHeight - innerHeight));
  // A single-screen page has one checkpoint; shooting it five times would only read as "stuck".
  const checkpoints = max < 10 ? [0] : stopsFor;
  let previous = null;
  for (const s of checkpoints) {
    const y = Math.round((max * s) / 100);
    await scrollTo(page, y);
    await pause(wait);
    const at = await page.evaluate(() => window.scrollY);
    const file = join(outDir, `${label}-${pad(s)}.png`);
    const buf = await page.screenshot({ path: file });
    const hash = sha(buf);
    shots.push({ stop: `${s}%`, file, scrollY: at, reached: Math.abs(at - y) <= Math.max(4, max * 0.01), sameAsPrevious: previous !== null && hash === previous });
    previous = hash;
  }

  const sideways = await page.evaluate(PROBE_SIDEWAYS);
  const probe = await page.evaluate(PROBE_PAGE);
  const origin = new URL(page.url()).origin;
  const foreignMedia = {};
  for (const r of log.requests) {
    if (r.type !== 'image' && r.type !== 'media') continue;
    let host;
    try {
      const u = new URL(r.url);
      if (u.protocol === 'data:' || u.protocol === 'blob:' || u.origin === origin) continue;
      host = u.host;
    } catch {
      continue;
    }
    foreignMedia[host] = (foreignMedia[host] ?? 0) + 1;
  }
  await context.close();
  delete log.requests;
  return { viewport: `${view.viewport.width}x${view.viewport.height}`, motion, shots, sideways, ...probe, foreignMedia, ...log };
}

/* ------------------------------------------------------------ main */

const chromium = await loadChromium();
if (!chromium) {
  console.error('Playwright is not installed. In the project folder run:\n  npm i -D playwright && npx playwright install chromium');
  process.exit(2);
}
mkdirSync(outDir, { recursive: true });
const { url, server } = await resolveTarget(target);
let browser;
try {
  browser = await launch(chromium);
} catch (e) {
  console.error(`Could not start a browser (${String(e.message).split('\n')[0]}).\nRun: npx playwright install chromium`);
  server?.close();
  process.exit(2);
}

const results = [];
try {
  for (const view of VIEWS) {
    results.push(await run(browser, url, view, { stopsFor: stops, motion: 'no-preference', label: view.name }));
  }
  if (reduced) {
    for (const view of VIEWS) {
      results.push(await run(browser, url, view, { stopsFor: [0, 50, 100], motion: 'reduce', label: `reduced-${view.name}` }));
    }
  }
} finally {
  await browser.close();
  server?.close();
}

const reportPath = join(outDir, 'report.json');
writeFileSync(reportPath, JSON.stringify({ target, url, results }, null, 2));

/* ------------------------------------------------------------ summary */

let blocking = 0;
for (const r of results) {
  const tag = `${r.viewport}${r.motion === 'reduce' ? ' (reduced)' : ''}`;
  const issues = [];
  if (r.pageErrors.length) { issues.push(`${r.pageErrors.length} page error(s)`); blocking++; }
  if (r.consoleErrors.length) { issues.push(`${r.consoleErrors.length} console error(s)`); blocking++; }
  if (r.failedRequests.length) { issues.push(`${r.failedRequests.length} failed request(s)`); blocking++; }
  if (r.httpErrors.length) { issues.push(`${r.httpErrors.length} HTTP >=400`); blocking++; }
  if (r.brokenImages.length) { issues.push(`${r.brokenImages.length} broken image(s)`); blocking++; }
  const deadVideo = r.videos.filter((v) => v.error || v.readyState < 2);
  if (deadVideo.length) { issues.push(`${deadVideo.length} video(s) not ready`); blocking++; }
  if (r.sideways.sideways) { issues.push(`sideways scroll (${r.sideways.culprits.join(', ')})`); blocking++; }
  const same = r.shots.filter((s) => s.sameAsPrevious).map((s) => s.stop);
  const warnings = [];
  if (same.length) warnings.push(`unchanged at ${same.join(', ')}`);
  if (r.h1 && !r.h1.fontLoaded) warnings.push(`h1 font "${r.h1.font}" not loaded`);
  const foreign = Object.entries(r.foreignMedia).map(([h, n]) => `${h} (${n})`);
  if (foreign.length) warnings.push(`media from ${foreign.join(', ')}`);
  if (!r.reducedMotionRules) warnings.push('no prefers-reduced-motion rules');

  console.log(`${tag}  ${r.screens} screens  ${issues.length ? 'BLOCKED: ' + issues.join('; ') : 'ok'}${warnings.length ? '  [' + warnings.join('; ') + ']' : ''}`);
}
console.log(`report: ${reportPath}`);
process.exit(blocking ? 1 : 0);
