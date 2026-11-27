#!/usr/bin/env node
// buildline-single-park 构建脚本：基线 + 布局差量 → 可发布页。
//
// 以变体 build.mjs 为底：变体 build.mjs 与基线 build.mjs 字节一致（diff 为空），
// 所以本脚本不重复打包逻辑，而是复用基线自带的 build.mjs，只做三步：
//   1. 把基线目录完整复制到临时工作目录（基线本身不动）；
//   2. 用 layout/world.js、layout/film.js 覆盖工作目录的同名文件；
//   3. 在工作目录跑 `node build.mjs`（esbuild IIFE，UI stub 插件与基线一致）。
//
// 用法：
//   node build.mjs <基线目录> [输出目录]
//   node build.mjs /path/to/site-v1to1 /path/to/out
//   BASELINE=/path/to/site-v1to1 node build.mjs [输出目录]
// 未给输出目录时，产物留在临时工作目录并打印其路径。
// 复现标准：输出 web/assets/bundle.js 须为 945,338 字节，
//   md5 3227049bb84cf7b8efaeb67ffd4e6e1a（与变体 bundle 逐字节一致）。
// 依赖与基线 build.mjs 相同：克隆 node_modules 里的 esbuild 0.28.1 + three 0.186.1
// （build.mjs 内 CLONE 为绝对路径，见基线 build.mjs）。
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const baseline = process.argv[2] || process.env.BASELINE;
const outDir = process.argv[3] || null;
if (!baseline) {
  console.error('用法: node build.mjs <基线目录> [输出目录]（或设 BASELINE 环境变量）');
  console.error('基线示例：~/workspace/3dmodel-gen-test/site-v1to1（Nyxera0x/simulator 1:1 vendored）');
  process.exit(2);
}
const BASE = path.resolve(baseline);
for (const f of ['build.mjs', 'src/entry.js', 'src/sims/site-shared/world.js', 'src/sims/site-shared/film.js']) {
  if (!fs.existsSync(path.join(BASE, f))) {
    console.error(`基线目录缺少 ${f}：${BASE}`);
    process.exit(2);
  }
}
// 差量应用前核对：layout 文件须与变体文件一致（sha256 见 review-report.md）。
const EXPECTED = {
  'world.js': '756ab238a8016c4cf1793faed2c7b81fc846beaed76b19e8cb2199775b625573',
  'film.js': '97aa9df9f8e232be9246992bd2d4dca45c87eafb885702a233a5b0a1bb211796',
};
for (const [name, sha] of Object.entries(EXPECTED)) {
  const got = createHash('sha256').update(fs.readFileSync(path.join(HERE, 'layout', name))).digest('hex');
  if (got !== sha) {
    console.error(`layout/${name} sha256 不符：${got}（期望 ${sha}），停止构建`);
    process.exit(1);
  }
}

const work = fs.mkdtempSync(path.join(os.tmpdir(), 'buildline-single-park-'));
execFileSync('cp', ['-r', `${BASE}/.`, work], {stdio: 'inherit'});
for (const name of ['world.js', 'film.js']) {
  fs.copyFileSync(path.join(HERE, 'layout', name), path.join(work, 'src', 'sims', 'site-shared', name));
}
console.log(`工作目录：${work}（基线已复制，layout 差量已覆盖）`);
execFileSync('node', ['build.mjs'], {cwd: work, stdio: 'inherit'});

const bundle = path.join(work, 'web', 'assets', 'bundle.js');
const buf = fs.readFileSync(bundle);
const md5 = createHash('md5').update(buf).digest('hex');
console.log(`bundle：${buf.length} 字节，md5 ${md5}`);
if (md5 === '3227049bb84cf7b8efaeb67ffd4e6e1a' && buf.length === 945338) {
  console.log('复现通过：与变体 bundle 逐字节一致');
} else {
  console.log('复现失败：与变体 bundle（945338 字节，md5 3227049bb84cf7b8efaeb67ffd4e6e1a）不一致');
  process.exit(1);
}
if (outDir) {
  const OUT = path.resolve(outDir);
  fs.mkdirSync(OUT, {recursive: true});
  execFileSync('cp', ['-r', path.join(work, 'web'), path.join(work, 'reference'), OUT], {stdio: 'inherit'});
  console.log(`产物已复制到：${OUT}`);
} else {
  console.log(`产物在工作目录：${work}/web（reference/ 同目录）`);
}
