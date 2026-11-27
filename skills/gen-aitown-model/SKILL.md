---
name: gen-aitown-model
description: 写一个自包含的 ES Module：调用 createModel() 返回 AITown 可用的动画园区模型；只依赖 three@0.186，规范参数与内联工具原样复制，seek 纯函数、selfCheck 门禁。
version: 1-slim
---

# gen-aitown-model

写一个自包含的 ES Module，调用 `createModel()` 返回 AITown 可用的动画园区模型。
只依赖 three@0.186；§A 的 `AITOWN` 常量和 §C 的工具函数**原样复制**进你的文件；代码中引用参数名，不另写魔法数字。
文件必须完整可运行，不能出现 `...`、`// 省略`、`TODO`。

---

## 运行环境

宿主已提供：`WebGLRenderer`、scene/camera、`DirectionalLight`+`HemisphereLight`+PMREM 环境反射、软阴影、`NeutralToneMapping`（曝光 0.93）、每帧调用 `model.seek(t)`。
**你不能**：创建 renderer/scene/camera/方向光/环境光/雾；改曝光或色调映射；使用 `requestAnimationFrame`、`setTimeout`、`Math.random`；`fetch` 或加载任何 URL；import 下列以外的模块：

```js
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
```

坐标：米，原点在地块中心地坪（`+y` 向上，`+z` 为南，`+x` 为东，入口朝南）。

---

## §A 规范参数（原样复制到文件顶部）

```js
export const AITOWN = Object.freeze({
  spec: 'aitown-model/1',
  axes: { unit: 'metre', up: '+y', south: '+z', east: '+x', origin: 'lot-centre-ground' },
  grid: {
    cellMetres: 4, setbackMetres: 0.4,
    parkCap: { maxLong: 20, maxShort: 14, maxArea: 260 },
    recommended: [11, 8], entranceMinWidth: 3.6,
  },
  host: {
    toneMapping: 'Neutral', exposure: 0.93, environmentIntensity: 0.38,
    background: '#dfe6fa', ground: '#d5def7', fill: 1, sun: 2.2,
    sunDirection: [-0.78, 1, -0.36],
    shadow: { mapSize: 4096, bias: -0.0008, normalBias: 0.06, radius: 5 },
    camera: { azimuthDeg: 38, elevationDeg: 36, fovDeg: 28, viewport: [1440, 900] },
  },
  palette: {
    bg: '#dfe6fa', ground: '#d5def7', groundDeep: '#c3cff3', road: '#e6eaf8', lane: '#ffffff',
    bay: '#f2b33a', blue: '#3166ea', roof: '#4a85f0', blueDeep: '#2448c8', blueLight: '#8fb0f7',
    wall: '#7fa6f2', white: '#f6f8fd', panel: '#e9edf8', shade: '#c9d1ea', navy: '#1a2440',
    glass: '#22304f', yellow: '#f2b33a', yellowDeep: '#e0a02e', teal: '#21b3a3', orange: '#ff8a3d',
    green: '#7fdaa0', greenDeep: '#4fbf7d', trunk: '#b08a6a', red: '#e5484d', cardboard: '#e3b07a',
    soil: '#e2b07c', soilDeep: '#d39a62', concrete: '#c6c1b8', concreteWet: '#9a958d',
  },
  paletteNotes: {
    ground: '地坪浅薰衣草；路面浅色；标线白色与黄色；不铺大面积深色沥青',
    blue: '品牌主色', yellow: '仅作业机械与标线', orange: '少量点缀',
    green: '仅植物', navy: '轮胎/玻璃等深色件', red: '信号灯',
  },
  style: {
    lightShareMin: 0.55, brandShare: [0.25, 0.35], darkShareMax: 0.10, glowShareMax: 0.05,
    glassPerFacadeMax: 0.20, cornerRatio: [0.08, 0.20], buildingCornerRatio: [0.01, 0.04],
    exaggeration: [1.3, 1.5], bodyMaxM: 9, landmarkMaxM: 14, doorHeightM: 2.2, massLayers: 3,
  },
  material: {
    clearcoat: 0.35,
    rough: { paint: 0.48, matte: 0.6, coarse: 0.88, wet: 0.2, metal: 0.4 },
    metalness: { metal: 0.2 },
    glow: { low: 0.22, mid: 0.35, high: 0.9 },
    dayGlow: 0,
  },
  motion: { cycleSeconds: [20, 40], beatSeconds: [3, 6], anticipationRatio: 0.04, overshootMax: 0.03 },
  night: { maxPointLights: 8, minLightKinds: 3, color: '#ffd9a0' },
  budget: { heroTriangles: [8000, 15000], heroDraws: [30, 45], sceneTriangles: 130000, sceneDraws: 150 },
  people: 0,
  forbiddenNames: /(person|people|human|visitor|guest|staff|passenger|rider|figure|avatar|游客|人物|人形|店员|员工|乘客|行人)/i,
  residentAnimations: ['walk','sit','stand_idle','order_counter','browse_shelf','read_bench','play_equipment','queue_wait','delivery_pickup'],
});
```

---

## §B 导出接口

文件必须导出这五个名字（不能改名）：

| 导出 | 类型 |
|---|---|
| `AITOWN` | §A 常量 |
| `META` | 资产登记（见下） |
| `createModel(options?)` | 返回 `TownModel`，每次调用返回独立实例 |
| `selfCheck(model, opts?)` | §D 原文 |
| `liveModels()` | 返回当前存活实例数 |

### META（按场景填写）

```js
export const META = Object.freeze({
  id: 'morning-market',          // kebab-case，全局唯一，同时作为 model.object.name
  name: '巷口早市',
  type: 'scene',
  version: 1,
  brand: 'DAWNLANE',             // 虚构品牌
  lot: { size: [44, 32], footprint: [11, 8], groundY: 0 },  // size = footprint × 4
  needsRoad: true,
  entrances: [{ id: 'gate', at: [0, 0, 16], facing: 'south', clearWidth: 4.8 }],
  heroes: ['market-tricycle', 'market-awning-stall'],
  parts: ['market-lot', 'market-fence', 'market-gate'],
  referenceSeconds: 20,
  budgetEstimate: { estimate: true, triangles: 0, draws: 0 },
  residentBehavior: { enterable: false },
  // 允许居民进入时：
  // residentBehavior: {
  //   enterable: true, entranceAnchor: 'gate',
  //   waypoints: [{ id: 'bench_1', cx: 3, cz: 4, pause: 15 }],
  //   interactions: [{ id: 'bench_sit', cx: 3, cz: 4, animation: 'read_bench', loopable: true }],
  // }
  // animation 只能取 AITOWN.residentAnimations 中的值；cx/cz 为整数格坐标
});
```

### TownModel（createModel 返回值）

```ts
{
  object: THREE.Group;            // name = META.id；子节点 name 用 META.parts 中的部件 ID
  cycleSeconds: number;           // 在 AITOWN.motion.cycleSeconds 范围内
  referenceSeconds: number;       // 商品图取这一帧，= META.referenceSeconds
  sequence: { duration: number; stages: { id: string; label: string; start: number; end: number; focusActor?: string }[] };
  focus: Record<string, [number, number, number]>;  // 部件 ID → 本地米制镜头焦点
  anchors: Record<string, THREE.Vector3>;           // 至少包含 entrance
  seek(t: number): void;          // 纯函数，t 夹到 [0, cycleSeconds]
  setNight(k: number | boolean): void;  // 0/false=白天，1/true=夜晚
  readonly time: number;
  dispose(): void;                // 幂等
}
```

节点约定：会运动的节点设 `userData.moving = true`（标在最外层运动节点上）；贴花/透明件/发光灯泡设 `castShadow = false`；其他实体件 `castShadow = receiveShadow = true`。

---

## §C 内联工具（原样复制，可在后面追加自己的函数）

```js
// ── 取值与缓动 ────────────────────────────────────────────────────────────
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const sat   = (v) => clamp(v, 0, 1);
const lerp  = (a, b, t) => a + (b - a) * t;
const smooth = (v) => { const x = sat(v); return x * x * (3 - 2 * x); };
/** 大动作：先反向 a 预备，再越过终点 o 后回弹。 */
const anticipate = (v, a = 0.04, o = 0.02) => {
  const x = sat(v);
  if (x < 0.2) return -a * Math.sin((x / 0.2) * Math.PI);
  const y = smooth((x - 0.2) / 0.8);
  return y + o * Math.sin(y * Math.PI) * (1 - y) * 4;
};
/** 固定种子伪随机（禁止 Math.random）。 */
function rng(seed) {
  let s = seed | 0;
  return () => {
    s = (s + 0x6d2b79f5) | 0;
    let x = Math.imul(s ^ (s >>> 15), 1 | s);
    x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x;
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
}

// ── 闭式速度剖面：缓起 → 匀速 → 缓停 ────────────────────────────────────
const smoothIntegral = (u) => u * u * u - 0.5 * u * u * u * u;
/** t 时刻的累计位移或转角（闭式积分，seek 可任意跳转）。 */
function rampTravel(t, { start = 0, rampUp, cruise, rampDown, speed }) {
  const x = t - start;
  if (x <= 0) return 0;
  if (x < rampUp) return speed * rampUp * smoothIntegral(x / rampUp);
  const up = speed * rampUp * 0.5;
  if (x < rampUp + cruise) return up + speed * (x - rampUp);
  const mid = up + speed * cruise;
  const y = x - rampUp - cruise;
  if (y < rampDown) { const u = y / rampDown; return mid + speed * rampDown * (u - smoothIntegral(u)); }
  return mid + speed * rampDown * 0.5;
}
/** 整数圈对齐速度：在 rampUp/2 + cruise + rampDown/2 秒内正好转 n 圈。 */
const loopSpeed = (n, { rampUp, cruise, rampDown }) =>
  (2 * Math.PI * n) / (rampUp / 2 + cruise + rampDown / 2);

// ── 资源缓存 ─────────────────────────────────────────────────────────────
const SHARED = { mats: new Map(), tex: new Map(), geo: new Map() };
let LIVE = 0;
function releaseShared() {
  SHARED.mats.forEach((m) => m.dispose()); SHARED.mats.clear();
  SHARED.tex.forEach((t) => t.dispose());  SHARED.tex.clear();
  SHARED.geo.forEach((g) => g.dispose());  SHARED.geo.clear();
}
const cg = (key, make) => { let g = SHARED.geo.get(key); if (!g) SHARED.geo.set(key, g = make()); return g; };

// ── 材质 ─────────────────────────────────────────────────────────────────
// SHARED / glowMats 是模块级单例，所有实例共享。
// 结论：同一时刻只有一个实例（市场预览 ↔ 已放置）时完全正确；
//       若要支持两个实例同时存活，需要把 glowMats 移到实例内部。
const glowMats = new Set();
function toyMat(color, { rough = AITOWN.material.rough.matte, metal = 0, paint = false,
  emissive = null, glow = AITOWN.material.glow.low, opacity = 1 } = {}) {
  const key = [color, rough, metal, paint, emissive, glow, opacity].join('|');
  let m = SHARED.mats.get(key);
  if (!m) {
    const p = { color, roughness: rough, metalness: metal, transparent: opacity < 1, opacity };
    if (emissive) Object.assign(p, { emissive, emissiveIntensity: glow * AITOWN.material.dayGlow });
    m = paint
      ? new THREE.MeshPhysicalMaterial({ ...p, clearcoat: AITOWN.material.clearcoat, clearcoatRoughness: 0.4 })
      : new THREE.MeshStandardMaterial(p);
    if (emissive) { m.userData.glow = glow; glowMats.add(m); }
    SHARED.mats.set(key, m);
  }
  return m;
}
// 动态材质（seek 内直接修改属性的材质，如尾焰、呼吸灯）不能用 toyMat，
// 因为 toyMat 返回共享实例，修改会影响所有使用该颜色的网格。
// 做法：new THREE.MeshStandardMaterial(...)，推进本地 dynamicMats[]，在 dispose() 里 m.dispose()。
/** 贴花：polygonOffset 防闪烁，带贴花的网格设 castShadow = false。 */
function decalMat(map, { rough = 0.6 } = {}) {
  const key = 'decal|' + map.uuid + '|' + rough;
  let m = SHARED.mats.get(key); if (m) return m;
  m = new THREE.MeshStandardMaterial({ map, roughness: rough, transparent: true,
    polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
  SHARED.mats.set(key, m); return m;
}
function applyNightGlow(k) {
  for (const m of glowMats) m.emissiveIntensity = m.userData.glow * lerp(AITOWN.material.dayGlow, 1, k);
}

// ── Canvas 纹理（品牌字标、编号、招牌） ───────────────────────────────────
const FONT = "'PingFang SC','Noto Sans SC','Microsoft YaHei',system-ui,sans-serif";
function canvasTex(key, w, h, draw, { repeat = false } = {}) {
  let t = SHARED.tex.get(key); if (t) return t;
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  if (repeat) t.wrapS = t.wrapT = THREE.RepeatWrapping;
  SHARED.tex.set(key, t); return t;
}

// ── 几何 ─────────────────────────────────────────────────────────────────
const rbox = (w, h, d, r = Math.min(w, h, d) * 0.12, seg = 3) =>
  cg(`rbox|${w}|${h}|${d}|${r}`, () => new RoundedBoxGeometry(w, h, d, seg, Math.max(0.001, r)));
function roundedRect(w, h, r) {
  const s = new THREE.Shape(), x = -w / 2, y = -h / 2;
  s.moveTo(x+r,y); s.lineTo(x+w-r,y); s.quadraticCurveTo(x+w,y,x+w,y+r);
  s.lineTo(x+w,y+h-r); s.quadraticCurveTo(x+w,y+h,x+w-r,y+h);
  s.lineTo(x+r,y+h); s.quadraticCurveTo(x,y+h,x,y+h-r);
  s.lineTo(x,y+r); s.quadraticCurveTo(x,y,x+r,y); return s;
}
const extrude = (key, makeShape, depth, bevel = 0.04, curveSegs = 8) =>
  cg('ext|' + key, () => {
    const g = new THREE.ExtrudeGeometry(makeShape(), { depth: Math.max(0.001, depth - 2*bevel),
      bevelEnabled: bevel > 0, bevelThickness: bevel, bevelSize: bevel, bevelSegments: 2, curveSegments: curveSegs });
    g.translate(0, 0, -depth/2 + bevel); return g;
  });
const lathe = (key, pts, seg = 32) =>
  cg('lathe|' + key, () => new THREE.LatheGeometry(pts.map(([x,y]) => new THREE.Vector2(x,y)), seg));
const tube = (key, pts, r, seg = 48, radial = 10, closed = false) =>
  cg('tube|' + key, () => new THREE.TubeGeometry(
    new THREE.CatmullRomCurve3(pts.map((p) => new THREE.Vector3(...p)), closed), seg, r, radial, closed));
function catenary(a, b, sag, n = 16) {
  const out = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n;
    out.push([lerp(a[0],b[0],t), lerp(a[1],b[1],t) - sag*4*t*(1-t), lerp(a[2],b[2],t)]);
  } return out;
}

// ── 装配 ─────────────────────────────────────────────────────────────────
function mesh(geo, mat, parent, x=0, y=0, z=0, { rx=0, ry=0, rz=0, name='', shadow=true } = {}) {
  const m = new THREE.Mesh(geo, mat);
  m.position.set(x,y,z); m.rotation.set(rx,ry,rz);
  if (name) m.name = name; m.castShadow = shadow; m.receiveShadow = true;
  parent.add(m); return m;
}
/** 大量静止重复件（树、桩、灯柱）：一个 InstancedMesh 完成。 */
function instanced(geo, mat, transforms, parent, colors = null) {
  const im = new THREE.InstancedMesh(geo, mat, transforms.length);
  const o = new THREE.Object3D(), c = new THREE.Color();
  transforms.forEach(([x,y,z,ry=0,s=1], i) => {
    o.position.set(x,y,z); o.rotation.set(0,ry,0); o.scale.setScalar(s); o.updateMatrix();
    im.setMatrixAt(i, o.matrix);
    if (colors) im.setColorAt(i, c.set(colors[i % colors.length]));
  });
  im.castShadow = im.receiveShadow = true; parent.add(im); return im;
}
/** 两点之间的伸缩件（液压缸、拉杆、绳索）。 */
function rodBetween(parent, mat, r = 0.05) {
  const m = new THREE.Mesh(cg('rod|'+r, () => new THREE.CylinderGeometry(r,r,1,10).translate(0,0.5,0)), mat);
  m.castShadow = true; parent.add(m);
  const up = new THREE.Vector3(0,1,0), dir = new THREE.Vector3();
  return (a, b) => {
    dir.subVectors(b, a); const len = dir.length();
    m.position.copy(a); m.scale.set(1, Math.max(1e-4, len), 1);
    m.quaternion.setFromUnitVectors(up, dir.normalize());
  };
}
/** 按行驶距离转动车轮（轮轴沿本地 x 轴）。 */
const roller = (wheels, radius) => (d) => { for (const w of wheels) w.rotation.x = -d / radius; };
/** 合并 root 下全部永久静止网格（按材质分组），减少绘制次数。 */
function mergeStatic(root) {
  root.updateMatrixWorld(true);
  const inv = root.matrixWorld.clone().invert(), buckets = new Map(), done = [], made = [];
  root.traverse((o) => {
    if (!o.isMesh || o.isInstancedMesh || Array.isArray(o.material) || o.userData.moving) return;
    let g = (o.geometry.index ? o.geometry.toNonIndexed() : o.geometry.clone());
    for (const k of Object.keys(g.attributes)) if (!['position','normal','uv'].includes(k)) g.deleteAttribute(k);
    if (!g.attributes.normal) g.computeVertexNormals();
    if (!g.attributes.uv) g.setAttribute('uv', new THREE.Float32BufferAttribute(new Float32Array(g.attributes.position.count*2), 2));
    g.applyMatrix4(new THREE.Matrix4().multiplyMatrices(inv, o.matrixWorld));
    const key = o.material.uuid + '|' + o.castShadow;
    if (!buckets.has(key)) buckets.set(key, { mat: o.material, shadow: o.castShadow, list: [] });
    buckets.get(key).list.push(g); done.push(o);
  });
  for (const o of done) o.removeFromParent();
  for (const { mat, shadow, list } of buckets.values()) {
    const merged = mergeGeometries(list, false);
    list.forEach((g) => g.dispose());
    const m = new THREE.Mesh(merged, mat);
    m.castShadow = shadow; m.receiveShadow = true; root.add(m); made.push(merged);
  } return made;
}
```

---

## §D selfCheck（原样复制）

```js
export function selfCheck(model, { step = 0.25 } = {}) {
  const issues = [];
  const [W, D] = META.lot.size, m = AITOWN.grid.setbackMetres, T = model.cycleSeconds;
  const root = model.object;
  const pose = (t) => { model.seek(t); root.updateMatrixWorld(true); };
  const refresh = (o) => o.traverse((c) => { if (c.isInstancedMesh) c.computeBoundingBox(); });
  const box = new THREE.Box3(), env = new THREE.Box3(), all = new THREE.Box3();
  const movers = [];
  root.traverse((o) => { if (o.userData.moving) movers.push(o); });
  if (!movers.length) issues.push('没有节点标记 userData.moving，无法计算扫掠包络');

  for (let t = 0; t <= T + 1e-9; t += step) {
    pose(Math.min(t, T));
    for (const mo of movers) { refresh(mo); env.union(box.setFromObject(mo)); }
    refresh(root); all.union(box.setFromObject(root));
  }
  const lim = { minX: -W/2+m, maxX: W/2-m, minZ: -D/2+m, maxZ: D/2-m };
  const r2 = (v) => Math.round(v*100)/100;
  const envelope = movers.length ? { minX:r2(env.min.x), maxX:r2(env.max.x), minZ:r2(env.min.z), maxZ:r2(env.max.z) } : null;
  if (envelope && (env.min.x<lim.minX||env.max.x>lim.maxX||env.min.z<lim.minZ||env.max.z>lim.maxZ))
    issues.push(`活动件扫掠越过退界线：${JSON.stringify(envelope)}，允许 ${JSON.stringify(lim)}`);
  if (all.min.x<-W/2-1e-3||all.max.x>W/2+1e-3||all.min.z<-D/2-1e-3||all.max.z>D/2+1e-3) issues.push('模型超出地块');
  if (all.min.y < -0.02) issues.push(`有部件低于地坪：minY=${r2(all.min.y)}`);

  const fp = [Math.ceil(W/AITOWN.grid.cellMetres), Math.ceil(D/AITOWN.grid.cellMetres)];
  if (fp[0]!==META.lot.footprint[0]||fp[1]!==META.lot.footprint[1]) issues.push(`footprint 应为 ${fp}`);
  const cap = AITOWN.grid.parkCap;
  if (Math.max(...fp)>cap.maxLong||Math.min(...fp)>cap.maxShort||fp[0]*fp[1]>cap.maxArea) issues.push('超出园区格数上限');
  for (const e of META.entrances) {
    if (Math.abs(e.at[2]-D/2)>0.5) issues.push(`入口 ${e.id} 不在南边线上`);
    if (e.clearWidth<AITOWN.grid.entranceMinWidth) issues.push(`入口 ${e.id} 净宽不足`);
    if (envelope&&env.max.z>D/2-2&&env.min.x<e.at[0]+e.clearWidth/2&&env.max.x>e.at[0]-e.clearWidth/2)
      issues.push(`活动件进入入口 ${e.id} 通道`);
  }

  const snap = () => { const a=[]; root.traverse((o) => { a.push(...o.matrixWorld.elements,o.visible?1:0); if(o.isInstancedMesh) a.push(...o.instanceMatrix.array); }); return a; };
  const diff = (a,b) => { if(a.length!==b.length) return Infinity; let d=0; for(let i=0;i<a.length;i++) d=Math.max(d,Math.abs(a[i]-b[i])); return d; };
  pose(T*0.37); const s1=snap(); pose(T*0.91); pose(T*0.05); pose(T*0.37);
  if (diff(s1,snap())>1e-6) issues.push('seek 不是纯函数：跳转后同一时刻姿态不一致');
  pose(0); const a0=snap(); pose(T);
  if (diff(a0,snap())>1e-3) issues.push('seek(0) 与 seek(cycleSeconds) 姿态不一致，循环会跳变');

  const ref = model.referenceSeconds ?? T/2; pose(ref);
  let triangles=0, draws=0, points=0;
  root.traverse((o) => {
    if (AITOWN.forbiddenNames.test(o.name)) issues.push(`疑似人物部件：${o.name}`);
    if (o.isLight) { if (o.isPointLight||o.isSpotLight) points++; else issues.push(`不允许 ${o.type}`); }
    if (!(o.isMesh||o.isLine||o.isPoints)||!o.visible) return;
    const g=o.geometry, n=g.index?g.index.count:g.attributes.position.count;
    if (o.isMesh) triangles += (n/3)*(o.isInstancedMesh?o.count:1);
    draws += Array.isArray(o.material)?Math.max(1,g.groups.length):1;
  });
  if (triangles>AITOWN.budget.sceneTriangles) issues.push(`三角形 ${triangles} 超限`);
  if (draws>AITOWN.budget.sceneDraws) issues.push(`绘制次数 ${draws} 超限`);
  if (points>AITOWN.night.maxPointLights) issues.push(`点光源 ${points} 盏超限`);
  model.setNight(0); pose(ref);
  root.traverse((o) => { if ((o.isPointLight||o.isSpotLight)&&o.visible&&o.intensity>1e-6) issues.push(`白天点光源未关闭：${o.name||o.uuid}`); });

  const before = liveModels(); const probe = createModel(); probe.dispose(); probe.dispose();
  if (liveModels()!==before) issues.push('dispose 后实例计数没有回落');
  if (probe.object.parent) issues.push('dispose 后模型仍挂在父节点');

  return { ok: issues.length===0, footprint: fp, envelope, triangles: Math.round(triangles), draws, pointLights: points, issues };
}
export const liveModels = () => LIVE;
```

---

## 建模要求

**先不动笔，输出 Brief：**

```
场景：<名称>（品牌：<虚构名>）  基调：<一句话情绪>
主画面：<谁 → 对什么 → 做什么 → 结果>
故事链：<3–5 步>
地块：<w×d m = cw×cd 格>；占地预检：长边≤20 格、短边≤14 格、面积≤260 格²；入口在南边（z = d/2），净宽≥3.6 m
主角 2–3 个（会动的设备/地标）+ 配角（入口、主路、休憩、服务、围护各一件以上）
节拍表：起止秒 | 执行者 ID | setter 取值 | 物料位置 | 交接锚点
风格锁：色面分布（浅色≥55%/品牌色25–35%/深色≤10%/发光≤5%）；材质；圆角取值；比例
```

**硬性规则（违反任何一条不合格）：**

1. 主角必须程序化建模：用车床 `lathe`、圆角挤出 `extrude`、`rbox`、放样管 `tube` 组合；禁止用一堆矩形 `BoxGeometry` 拼主角。
2. 园区零人物：不放任何人形几何或贴片；节点名不匹配 `AITOWN.forbiddenNames`。
3. `seek(t)` 是纯函数：同一 t 总返回同一姿态，可任意跳转和倒放；连续运动用 `rampTravel`，不累加帧时间；`seek(0)` 与 `seek(cycleSeconds)` 画面一致。如果 `setNight` 内部依赖当前时间（如在 `seek` 里混合夜间光照与动效），必须在 `setNight` 末尾调用 `seek(currentTime)` 保持一致性。
4. 颜色只用 `AITOWN.palette` 或注明来源的 `SCENE_COLORS`；仅当场景需要调色板之外的颜色时才定义 `SCENE_COLORS`，不需要时不要定义空对象；绿色只给植物，黄色只给作业机械与标线。
5. 活动件全周期 XZ 扫掠在地块内，离边 ≥ `AITOWN.grid.setbackMetres`，不进入入口通道。
6. `dispose()` 幂等；最后一个实例释放时调 `releaseShared()`；退出再进入不泄漏。`InstancedMesh.dispose()` 只释放实例矩阵属性，不释放几何（几何在 `SHARED.geo` 里，由 `releaseShared()` 统一清理）。
7. 不靠删细节换性能：先 `mergeStatic` 合并静态件，再 `instanced` 实例化重复件。
8. **`userData.moving` 只标在最顶层的运动祖先上**：`selfCheck` 用 `setFromObject` 遍历子树，中间层不需要重复标记。同一运动子树内的子节点（起竖摇臂、吊舱、液压缸）不用单独标。
9. **动态材质不能用 `toyMat`**：在 `seek()` 内直接修改 `emissiveIntensity`、`opacity` 或 `scale` 的材质（尾焰、呼吸灯、蒸汽透明度），必须用 `new THREE.MeshStandardMaterial(...)` 独立创建，推进本地 `dynamicMats[]`，并在 `dispose()` 中释放。用 `toyMat` 创建的是共享实例，修改会影响所有使用该颜色的网格。
10. **`budgetEstimate` 要往高估**：这个值进入宿主的部署前检查。低估会让检查通过但 `selfCheck` 实测三角形数超限。估算原则：先列出所有几何（球、车床件、`rbox`、`tube`），取每件的三角面数，乘以实例数，求和后上调 20% 作为填报值。

**主角每个都要达到：**

- **L1 剪影**：3/4 俯视缩到 50 px 仍能认出；有曲线轮廓；底部、间隙、洞口能透光。
- **L2 结构**：近景能看出组成部分；大体块分三层；接地件多件式；空腔内面深一级。
- **L3 识别**：用 `canvasTex` 画品牌字标或编号贴花；≥2 种灯；≥3 件功能小件（把手、格栅、铭牌、仪表、管线）。
- **L4 动作**：至少一组联动（液压缸跟臂、物料跟容器）用 `rodBetween` 在同一个 setter 里求解。

---

## 输出顺序

1. **Brief + 节拍表 + 风格锁**
2. **完整模块代码**（一个代码块，第一行注释写文件名 `<META.id>.js`，包含 §A §C §D 原文；`createModel` 内部可拆分为 `buildXxx(root)` 子函数，特别是有 3 个以上主角时）
3. **selfCheck 结果**（能运行就贴 JSON，不能就写「未运行」并给出 `budgetEstimate` 估算依据——列出每类几何的面数 × 实例数，求和后上调 20%）
4. **每个主角的 L1–L4 自评**（各一句，说明落在哪些部件上）
5. **自查清单**（每条回答「是」或「否 + 原因」）：
   1. 只用了 §C 允许的三行 import？
   2. 没有 renderer/相机/方向光/环境光/动画循环/计时器/`Math.random`/网络加载？
   3. `seek` 纯函数，首尾一致，倒放无漂移？如果 `setNight` 依赖当前时间，末尾调用了 `seek(currentTime)`？
   4. 颜色全来自 `AITOWN.palette` 或注明来源的 `SCENE_COLORS`（无需新颜色则不定义该常量）？
   5. 零人物，节点名未命中 `forbiddenNames`？
   6. 活动件扫掠在退界线内，入口通道畅通？`userData.moving` 只标在最顶层运动祖先上？
   7. 每个主角 L1–L4 都有落点？
   8. 点光源 ≤ 8 盏，白天强度为 0？
   9. `dispose` 幂等，最后一个实例调了 `releaseShared()`；动态材质（`seek` 内修改属性的）单独 `new` 并在 `dispose` 里 `.dispose()`？
   10. `META.id`、`object.name`、文件名三者一致（文件名用 `<META.id>.js`，连字符不改成下划线）？

篇幅不够时先交 1 个主角 + 最少量地块/围栏/入口，标题写**「样件」**，质检通过后再补。

---

**← 在这一行后面写你的场景需求**
