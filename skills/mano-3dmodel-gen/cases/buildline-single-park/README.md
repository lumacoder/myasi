# 案例：施工工地 · 单园区变体（buildline-single-park）

把 Buildline 施工工地从“作业散在园外”收成“只有一个园区”：搅拌站的加工与装填、两处房屋的砌筑全移入围栏内，
马路与树行截断至与园区等长，不再向外延伸。时间轴、机器、浇筑动画、灯光相机参数一律不动，只改布局布点。

## 从哪复现

- 基线：`~/workspace/3dmodel-gen-test/site-v1to1/`（Nyxera0x/simulator 源码 1:1 vendored，2026-11-24 审核 143/143 通过；
  基线 bundle md5 `91ca881fe6a98e7feb86bbcb07fc9923`）。基线本身不在本仓库内，复现时由使用者提供基线目录路径。
- 布局差量：本目录 `layout/`（`world.js`、`film.js` 两份改动后完整文件）。
- 构建脚本：本目录 `build.mjs`（用法见文件头注释）。它把基线复制到临时工作目录，用 `layout/` 的两文件
  覆盖基线同名文件，再跑基线自带的 `build.mjs`（与变体 `build.mjs` 字节一致）打包。
- 复现标准：构建出的 `web/assets/bundle.js` 须为 945,338 字节，md5 `3227049bb84cf7b8efaeb67ffd4e6e1a`；
  与变体 bundle 逐字节一致才算复现通过。
- 完整改动清单与量测依据：试跑项目 `~/workspace/3dmodel-gen-test/site-single-park/CHANGELOG.md`
  与 `~/workspace/3dmodel-gen-test/single-park-measurement.md`（不随 skill 分发，留试跑项目备查）。

## 线上页

- artifact slug：`shi-gong-gong-di-buildline-3d`（模型展示页，纯模型，零 DOM 覆盖层）。

## 它证明了 skill 的哪条能力

- §2 单园区布局规则：一个园区容纳全部作业，道路与绿植与园区等长、不外延（本案例是该规则的来源与基准）。
- §2 布局基准框：围栏/道路/大门/厂站/地块全部由地块矩形统一推导，只扩一侧、其余三界不动。
- §6 审核机制：变体 vs 基线逐帧比对 + 搬动区域允许集门禁 + 代码值核对 + OBB 碰撞扫查，
  审核 PASS 134/134、P0 127/127、失败 0 项（见 `review-report.md`）。
- §6 先 1:1 抄源码：变体只改两个布局文件，其余 17 个 vendored 文件 sha256 与源仓库一致。

## 目录

```
cases/buildline-single-park/
  brief.md          案例简报（6 行 + 单园区布局规则 + 验收标准）
  README.md         本文件
  layout/           布局差量源码（world.js、film.js，覆盖基线同名文件后构建）
  build.mjs         基线 + 差量 → 可发布页的构建脚本
  review-report.md  变体审核摘要（PASS 134/134、P0 127/127）
```

不含构建产物（bundle.js）与探针 PNG：仓库规则禁 build 产物；探针帧留在试跑项目里。
