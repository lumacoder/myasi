// The toy construction site film: Buildline over plot P1, the batching plant and plots P2-P3, cut like
// the toy airport and plant. One camera at one angle (azimuth 38, elevation 36) that only pans and zooms. 0-7 s EX-07
// finishes the pit and loads TP-14; 7-13 TP-14 leaves and DZ-03 levels the floor; 13-16 the dropdown jumps to the
// plant, M-21 loads; 17.6-26 the camera rides M-21 to the site and down the ramp; 27-33.6 the pour; 34-40 the
// blockwork on P2 and P3; 40-43.7 home over the whole neighbourhood.
import * as THREE from 'three';
import {runSim} from '../kit/runtime.js';
import {TOY, createToyStage} from '../airport-shared/style.js';
import {createToyUI} from '../airport-shared/ui.js';
import {createSelection} from '../airport-shared/select.js';
import {thumb} from '../airport-shared/thumbs.js';
import {OPERATOR_AVATAR} from '../airport-shared/avatar.js';
import {DUR, T, buildWorld} from './world.js';
import {buildToyBulldozer, buildToyDumpTruck, buildToyExcavator, buildToyMixer} from './machines.js';
import {buildToyBatchingPlant, buildToyWalls} from './site.js';

const D2R = Math.PI / 180;
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const sm = (x) => {
  const u = clamp(x);
  return u * u * u * (u * (u * 6 - 15) + 10);
};
const ss = (a, b, t) => sm((t - a) / (b - a));
const lerp = (a, b, k) => a + (b - a) * k;
const fmt = (n) => Math.round(n).toLocaleString('en-US');

export const UI_WORDS = {
  brand: 'Buildline',
  search: 'Search plots, machines, pours, loads...',
  user: ['Mila Novak', 'Site Manager'],
  avatar: OPERATOR_AVATAR,
  kpis: [
    {ic: 'cube', k: 'Concrete today', key: 'a', v: '186 m³', d: '+27', s: 'Northbay Fields · 3 plots'},
    {ic: 'truck', k: 'Machines on site', key: 'b', v: '11', d: '+2', s: '3 trucks inbound'},
    {ic: 'clock', k: 'On schedule', key: 'c', v: '96.1%', d: '+1.2%', s: 'last 30 days · all plots'},
  ],
};

const CLICKS = [
  {t: 1.2, at: 'ex', card: 'ex'},
  {t: 5.2, at: 'tp', card: 'tp'},
  {t: 9.3, at: 'dozer', card: 'dozer'},
  {t: 13.0, ui: [1167, 37], drop: 'open'},
  {t: 14.1, ui: [930, 232], card: 'site'},
  {t: 16.1, at: 'mx', card: 'mx'},
  {t: 28.3, at: 'slab', card: 'slab'},
  {t: 33.8, ui: [1167, 37], drop: 'open'},
  {t: 34.9, ui: [930, 274], card: 'site'},
  {t: 40.0, ui: [1159, 275], tool: 6, card: 'site'},
];
export const FILM_CLICKS = CLICKS.map((c) => c.t);

const AZ = 38;
const EL = 36;
const KEYS = [
  {t: 0, x: -20, z: -4, d: 150},
  {t: 7.0, x: 12, z: 2, d: 114},
  {t: 12.8, x: 6, z: -2, d: 112},
  {t: 14.1, x: 6, z: -2, d: 112},
  {t: 15.8, x: -60, z: -10, d: 96},
  {t: 17.4, x: -60, z: -10, d: 94},
  {t: 22.4, x: 6, z: -36, d: 96},
  {t: 26.0, x: 2, z: -22, d: 96},
  {t: 27.4, x: 1, z: -10, d: 104},
  {t: 33.6, x: 0, z: -8, d: 100},
  {t: 34.9, x: 0, z: -8, d: 100},
  {t: 36.6, x: 27, z: -15.4, d: 90},
  {t: 40.0, x: 27, z: -15.4, d: 90},
  {t: 42.4, x: 22, z: -10, d: 250},
  {t: DUR, x: 20, z: -10, d: 244},
];
const SITES = {
  P1: ['P1', 'Northbay Fields · Plot 1', 'Foundation · 4 machines'],
  PL: ['BP', 'Batching plant', 'C30 · 2 mixers'],
  P2: ['P2', 'Northbay Fields · Plots 2-3', 'Blockwork · 2 crews'],
  N: ['N', 'Northbay Fields', '3 plots · 11 machines'],
};
const DROP = [['P1', 'Plot 1 · Foundation', 'pour today · 64%', 64], ['BP', 'Batching plant', 'C30 · 2 mixers', 72], ['P2', 'Plots 2-3 · Blockwork', 'ground floor · 86%', 86], ['P4', 'Plots 4-5', 'pegged out', 8], ['N', 'Northbay Fields', '3 plots active', 58]];

export function runToyBuildFilm() {
  return runSim({duration: DUR, fps: 60, theme: 'light', hud: {enabled: false, title: 'buildline', subtitle: ''}, director: {enabled: false}, watermark: ''}, async ({canvas, capture}) => {
    const app = document.getElementById('app');
    const st = createToyStage(canvas, {fov: 28});
    const W = buildWorld();
    st.scene.add(W.root);
    const ui = createToyUI(app, UI_WORDS);
    const sel = createSelection(st.scene, st);
    const fit = () => (app.style.transform = `scale(${Math.min(innerWidth / 1600, innerHeight / 900)})`);
    const resize = () => {
      fit();
      st.resize(1600, 900, capture ? devicePixelRatio || 1 : Math.min(devicePixelRatio || 1, 2));
    };
    resize();

    const exT = buildToyExcavator({number: '07'});
    exT.setPose({slew: 0, boom: 0.62, arm: -2.62, bucket: -2.2});
    const tpT = buildToyDumpTruck({number: '14'});
    tpT.setLoad(1);
    const TH = {
      ex: thumb(exT.group),
      tp: thumb(tpT.group),
      dozer: thumb(buildToyBulldozer({number: '03'}).group),
      mx: thumb(buildToyMixer({number: '21'}).group),
      plant: thumb(buildToyBatchingPlant().group, {pad: 0.95}),
      walls: thumb((() => {
        const w = buildToyWalls({w: 12, d: 9, h: 3.2, seed: 2});
        w.setBuilt(0.8);
        return w.group;
      })(), {pad: 0.95}),
    };

    const P = (o) => o.getWorldPosition(new THREE.Vector3());
    const keyCam = (t) => {
      let i = 0;
      while (i < KEYS.length - 2 && KEYS[i + 1].t <= t) i++;
      const a = KEYS[i];
      const b = KEYS[i + 1];
      const k = ss(a.t, b.t, t);
      const far = Math.hypot(b.x - a.x, b.z - a.z);
      const arc = far > 50 ? 0.3 * Math.sin(Math.PI * k) : 0;
      return {x: lerp(a.x, b.x, k), z: lerp(a.z, b.z, k), d: lerp(a.d, b.d, k) * (1 + arc)};
    };
    const camAt = (t) => {
      const c = keyCam(t);
      // the camera rides M-21 from the plant to the gate
      const w = ss(17.4, 18.6, t) * (1 - ss(21.2, 22.6, t));
      if (w > 0) {
        const p = P(W.objects.mx.group);
        c.x = lerp(c.x, p.x + 2, w);
        c.z = lerp(c.z, p.z + 3, w);
        c.d = lerp(c.d, 100, w);
      }
      return c;
    };

    const siteAt = (t) => (t < 14.1 ? 'P1' : t < 22.4 ? 'PL' : t < 34.9 ? 'P1' : t < 40.0 ? 'P2' : 'N');
    const poured = (t) => T.pourTo * ss(...T.pour, t);
    const mxState = (t) =>
      t < T.load[1] ? ['Loading', 'Batching plant · bay 1', 'in'] :
      t < T.drive[1] ? ['En route', 'To plot 1 · gate N', 'in'] :
      t < T.reverse[1] ? ['Reversing', 'Plot 1 · ramp', 'wait'] :
      t < T.pour[0] ? ['Setting up', 'Plot 1 · chute out', 'wait'] :
      t < T.pour[1] ? ['Pouring', `Plot 1 · ${Math.round(100 * poured(t))}% of slab`, 'go'] : ['Empty', 'Back to the plant', 'go'];
    const cardAt = (t, kind, t0) => {
      const pop = ss(t0, t0 + 0.35, t);
      const pc = (a, b) => clamp((t - a) / (b - a));
      if (kind === 'ex') {
        const dug = clamp((t - T.dig[0]) / (T.dig[1] - T.dig[0]));
        return {pop, thumb: TH.ex, org: 'AURORA BUILD · EARTHWORKS', title: 'EX-07', sub: 'Tracked excavator · 24 t', stat: t < T.exEnd ? 'Digging' : 'Done', statCls: t < T.exEnd ? 'in' : 'go', statText: `Plot 1 · pit ${Math.round(100 * dug)}% dug`, prog: dug, progText: `${(4 * dug).toFixed(1)} m`, rows: [['Pit', '40 × 28 × 4 m'], ['Dug', `${fmt(3200 * dug)} m³`], ['Loads out', `${fmt(150 + 4 * t)}`], ['Loading', 'TP-14', 1], ['Fuel', '58%']]};
      }
      if (kind === 'tp') {
        const leaving = t >= T.tLeave[0];
        return {pop, thumb: TH.tp, org: 'AURORA BUILD · HAULAGE', title: 'TP-14', sub: 'Tipper · 18 t', stat: leaving ? 'To the tip' : 'Loading', statCls: leaving ? 'in' : 'wait', statText: leaving ? 'Gate N2 · Northbay tip' : 'EX-07 · plot 1', prog: leaving ? pc(...T.tLeave) : clamp(t / T.tLeave[0]), progText: leaving ? `${Math.max(1, Math.round(T.tLeave[1] - t))} s` : `${Math.min(3, 1 + Math.floor((t + 1.35) / 4.6))}/3`, rows: [['Load', 'Spoil · 17.6 t'], ['Destination', 'Northbay tip · 6 km'], ['Trips today', '9'], ['ETA back', '14:40']]};
      }
      if (kind === 'dozer') {
        const lv = pc(...T.level);
        return {pop, thumb: TH.dozer, org: 'AURORA BUILD · EARTHWORKS', title: 'DZ-03', sub: 'Bulldozer · GPS grade', stat: lv < 1 ? 'Levelling' : 'Done', statCls: lv < 1 ? 'in' : 'go', statText: 'Plot 1 · pit floor −4.00 m', prog: lv, progText: `±${Math.max(1, Math.round(40 * (1 - lv)))} mm`, rows: [['Floor', '32 × 20 m'], ['Tolerance', '±10 mm'], ['Passes', `${Math.min(2, Math.floor(lv * 2) + 1)} / 2`], ['Next', 'Formwork · rebar']]};
      }
      if (kind === 'mx') {
        const [s, txt, cls] = mxState(t);
        return {pop, thumb: TH.mx, org: 'AURORA BUILD · CONCRETE', title: 'M-21', sub: 'Mixer truck · 9 m³ C30', stat: s, statCls: cls, statText: txt, prog: t < T.drive[0] ? pc(...T.load) : t < T.reverse[1] ? pc(T.drive[0], T.reverse[1]) : pc(...T.pour), progText: t < T.drive[0] ? `${(9 * pc(...T.load)).toFixed(1)} m³` : t < T.reverse[1] ? 'en route' : `${(9 * (1 - pc(...T.pour))).toFixed(1)} m³`, rows: [['Mix', 'C30/37 · slump S3'], ['Batched', '13:52'], ['Drum', t < T.load[1] ? '14 rpm · charging' : '2 rpm · agitating'], ['Pour', 'Plot 1 · slab', 1], ['Ticket', '#BT 20418']]};
      }
      if (kind === 'slab') {
        const k = poured(t);
        return {pop, thumb: TH.walls, org: 'PLOT 1 · FOUNDATION', title: 'Slab S1', sub: '30 × 20 × 0.6 m · C30', stat: t < T.pour[1] ? 'Pouring' : 'Curing', statCls: t < T.pour[1] ? 'in' : 'go', statText: `${Math.round(100 * k)}% poured · M-21`, prog: k, progText: `${fmt(360 * k)} m³`, rows: [['Volume', `${fmt(360 * k)} / 360 m³`], ['Mixers', '40 loads · 3 trucks'], ['Rebar', 'B500 · 2 layers'], ['Cure', '7 days']]};
      }
      const site = siteAt(t);
      if (site === 'PL') return {pop, thumb: TH.plant, org: 'BATCHING PLANT', title: 'Plant BP-1', sub: 'Northbay Fields · on site', stat: 'Batching', statCls: 'go', statText: 'C30 · 2 mixers queued', prog: 0.72, progText: '72%', rows: [['Output', '60 m³ / h'], ['Cement', '41 t · 2 silos'], ['Aggregate', '4 bins · 62%'], ['Today', '186 m³']]};
      if (site === 'P2') return {pop, thumb: TH.walls, org: 'PLOTS 2-3 · BLOCKWORK', title: 'Plots 2-3', sub: 'Ground floor · first floor', stat: 'Building', statCls: 'in', statText: '2 crews · 1 forklift', prog: 0.86, progText: '86%', rows: [['Blocks laid', fmt(4810 + 22 * t)], ['Plot 2', 'Ground floor · 86%'], ['Plot 3', 'First floor · 58%'], ['Next', 'Roof slab · Mon']]};
      return {pop, thumb: TH.ex, org: 'NORTHBAY FIELDS', title: site === 'N' ? 'Northbay Fields' : 'Plot 1', sub: site === 'N' ? '5 plots · 11 machines' : 'Foundation · 40 × 28 m', stat: 'On schedule', statCls: 'go', statText: '3 plots active · 2 ready', prog: 0.58, progText: '58%', rows: [['Concrete today', '186 m³'], ['Machines', '11 · 3 inbound'], ['Loads out', '154'], ['Next pour', 'Plot 2 · roof']]};
    };
    const selection = (t) => {
      let cur = {kind: 'site', t0: -1};
      for (const c of CLICKS) if (c.card && t >= c.t) cur = {kind: c.card, t0: c.t};
      return cur;
    };
    const SEL_OBJ = {ex: W.objects.ex.group, tp: W.objects.tp.group, dozer: W.objects.dozer.group, mx: W.objects.mx.group};
    const SEL_ANCHOR = {ex: 'ex', tp: 'tp', dozer: 'dozer', mx: 'mx', slab: 'slab'};
    const SEL_TEXT = (kind, t) => ({ex: ['EX-07', t < T.exEnd ? 'Digging' : 'Done'], tp: ['TP-14', t < T.tLeave[0] ? 'Loading' : 'To the tip'], dozer: ['DZ-03', t < T.level[1] ? 'Levelling' : 'Done'], mx: ['M-21', mxState(t)[0]], slab: ['Slab S1', `${Math.round(100 * poured(t))}% poured`]})[kind];
    const ROUTE = {tp: (t) => W.routes.tp(t), mx: (t) => W.routes.mx(t)};

    const proj = (v) => st.project(v);
    const targetOf = (c) => (c.ui ? c.ui : proj(W.anchors[c.at]()) ?? [800, 450]);
    const GLIDE = 1.0;
    const cursorAt = (t) => {
      let prev = [1050, 620];
      let hand = true;
      for (const c of CLICKS) {
        const target = targetOf(c);
        if (t < c.t - GLIDE) return {p: prev, hand};
        if (t < c.t) {
          const k = sm((t - (c.t - GLIDE)) / GLIDE);
          return {p: [lerp(prev[0], target[0], k), lerp(prev[1], target[1], k) - 16 * Math.sin(Math.PI * k)], hand: !c.ui};
        }
        prev = target;
        hand = !c.ui;
      }
      return {p: prev, hand};
    };
    const clickAt = (t) => {
      let v = 0;
      for (const c of CLICKS) if (t >= c.t && t < c.t + 0.7) v = Math.max(v, 1 - (t - c.t) / 0.7);
      return v;
    };
    const dropOpen = (t) => Math.max(ss(13.0, 13.3, t) * (1 - ss(14.15, 14.4, t)), ss(33.8, 34.1, t) * (1 - ss(34.95, 35.2, t)));
    const kpiFor = (site, t) => ({
      a: [`${fmt(186 + 360 * poured(t) * 0.1)} m³`, '+27', site === 'PL' ? 'batched · plant BP-1' : 'Northbay Fields · 3 plots'],
      b: ['11', '+2', '3 trucks inbound'],
      c: ['96.1%', '+1.2%', 'last 30 days · all plots'],
    });
    const trackFor = (t) => {
      const st2 = (a, b) => (t < a ? '' : t < b ? 'on' : 'done');
      const steps = [['Dig', 'EX-07', 'truck', st2(-1, T.exEnd)], ['Level', 'DZ-03', 'load', st2(T.exEnd, T.level[1])], ['Rebar', '2 layers', 'box', st2(T.level[1], T.rebar[1])], ['Pour', `${Math.round(100 * poured(t))}%`, 'truck', st2(T.rebar[1], 60)], ['Cure', '7 days', 'check', '']];
      const fill = t < T.exEnd ? 0.04 : t < T.level[1] ? 0.25 : t < T.rebar[1] ? 0.5 : 0.75;
      const [s, txt, cls] = t < T.drive[0] ? ['Digging', 'Plot 1 · pit', 'in'] : mxState(t);
      return {title: 'Pour Tracking', meta: 'Plot 1 · foundation slab S1', fill, steps, ship: {thumb: TH.mx, id: 'M-21 · 9 m³', to: 'To: Plot 1 · slab S1', stat: t < T.drive[0] ? 'Queued' : s, statCls: t < T.drive[0] ? 'wait' : cls, meta: t < T.drive[0] ? 'Batching plant · 14:02' : txt}};
    };
    const tableFor = (site, t) => {
      if (site === 'PL')
        return {tabs: [['Mixers', '2'], ['Loads', '40'], ['Silos', '2']], active: 0, site: 'Plant', rows: [
          {id: 'M-21', org: 'Plot 1', dot: TOY.blue, where: t < T.load[1] ? 'Bay 1' : 'To plot 1', stat: t < T.load[1] ? 'Loading' : 'En route', cls: 'in', p: 100 * clamp((t - T.load[0]) / (T.load[1] - T.load[0])), pt: `${(9 * clamp((t - T.load[0]) / (T.load[1] - T.load[0]))).toFixed(1)} m³`},
          {id: 'M-22', org: 'Plot 1', dot: TOY.blue, where: 'Queue', stat: 'Waiting', cls: 'wait', p: null, pt: 'next'},
          {id: 'M-17', org: 'Plot 2', dot: TOY.teal, where: 'Plot 2', stat: 'Pouring', cls: 'go', p: 70, pt: '6.3 m³'},
          {id: 'BP-1', org: 'Plant', dot: TOY.orange, where: 'Batching', stat: 'Running', cls: 'go', p: 72, pt: '60 m³/h'},
        ]};
      if (site === 'P2')
        return {tabs: [['Plots', '2'], ['Crews', '2'], ['Loads', '4']], active: 0, site: 'Plots 2-3', rows: [
          {id: 'P2', org: 'Ground floor', dot: TOY.blue, where: 'Blockwork', stat: 'Building', cls: 'in', p: 100 * lerp(0.32, 0.86, ss(...T.walls, t)), pt: `${Math.round(100 * lerp(0.32, 0.86, ss(...T.walls, t)))}%`},
          {id: 'P3', org: 'First floor', dot: TOY.blue, where: 'Blockwork', stat: 'Building', cls: 'in', p: 100 * lerp(0.12, 0.58, ss(...T.walls, t)), pt: `${Math.round(100 * lerp(0.12, 0.58, ss(...T.walls, t)))}%`},
          {id: 'FL-04', org: 'Forklift', dot: TOY.teal, where: 'Blocks', stat: 'Moving', cls: 'go', p: null, pt: 'pallet 6'},
          {id: 'FB-09', org: 'Flatbed', dot: TOY.orange, where: 'Plot 2', stat: 'Unloading', cls: 'wait', p: null, pt: '4 min'},
        ]};
      return {tabs: [['Machines', '6'], ['Trucks', '3'], ['Pours', '1']], active: 0, site: 'Plot 1', rows: [
        {id: 'EX-07', org: 'Excavator', dot: TOY.blue, where: 'East rim', stat: t < T.exEnd ? 'Digging' : 'Idle', cls: t < T.exEnd ? 'go' : 'wait', p: 100 * clamp((t - T.dig[0]) / (T.dig[1] - T.dig[0])), pt: `${Math.round(100 * clamp((t - T.dig[0]) / (T.dig[1] - T.dig[0])))}%`},
        {id: 'TP-14', org: 'Tipper', dot: TOY.blue, where: t < T.tLeave[0] ? 'At EX-07' : 'To the tip', stat: t < T.tLeave[0] ? 'Loading' : 'En route', cls: 'in', p: null, pt: t < T.tLeave[0] ? '2/3' : 'out'},
        {id: 'DZ-03', org: 'Dozer', dot: TOY.teal, where: 'Pit floor', stat: t < T.level[0] ? 'Waiting' : t < T.level[1] ? 'Levelling' : 'Done', cls: t < T.level[1] ? 'in' : 'go', p: 100 * clamp((t - T.level[0]) / (T.level[1] - T.level[0])), pt: t < T.level[1] ? 'grade' : 'done'},
        {id: 'M-21', org: 'Mixer', dot: TOY.orange, where: t < T.reverse[1] ? 'Inbound' : 'Ramp N', stat: mxState(t)[0], cls: mxState(t)[2], p: t < T.pour[0] ? null : 100 * poured(t), pt: t < T.pour[0] ? 'ETA' : `${Math.round(100 * poured(t))}%`},
      ]};
    };
    const underUI = ([x, y]) => (x > 1130 && y < 450) || (x > 1080 && y > 620) || (x < 1000 && y > 720) || (x < 780 && y < 185);
    const pinsAt = (t) => {
      const out = [];
      const pin = (v, a = 1) => {
        const s = proj(v);
        if (s && s[0] > 20 && s[0] < 1580 && s[1] > 80 && s[1] < 880 && !underUI(s)) out.push({kind: 'pin', x: s[0], y: s[1], a});
      };
      if (t < 1.2) pin(W.anchors.ex(), 1 - ss(0.9, 1.2, t));
      if (t > 22.6 && t < 28.3) pin(W.anchors.slab(), ss(22.6, 23, t) * (1 - ss(27.9, 28.3, t)));
      return out;
    };

    window.TOYBUILD = {st, W, camAt};
    return {
      resize,
      render(t) {
        W.pose(t);
        const s = selection(t);
        const site = siteAt(t);
        const obj = SEL_OBJ[s.kind];
        const fadeIn = ss(s.t0, s.t0 + 0.3, t);
        sel.box(obj ?? null, fadeIn);
        const rf = ROUTE[s.kind];
        sel.route(rf ? rf(t) : null, ss(s.t0, s.t0 + 0.9, t), 1);
        sel.update();
        const c = camAt(t);
        st.frame({tx: c.x, ty: -1, tz: c.z, az: AZ * D2R, el: EL * D2R, d: c.d, fov: 28, sx: -110, sy: 26});
        const tags = pinsAt(t);
        const ak = SEL_ANCHOR[s.kind];
        if (ak) {
          const a = proj(W.anchors[ak]());
          const [txt, sub] = SEL_TEXT(s.kind, t);
          if (a && !underUI(a)) tags.push({kind: 'sel', x: a[0], y: a[1], text: txt, sub, a: fadeIn});
        }
        const cur = cursorAt(t);
        let tool = -1;
        for (const cl of CLICKS) if (cl.tool != null && t >= cl.t && t < cl.t + 0.6) tool = cl.tool;
        ui.update({
          clock: `14:${String(2 + Math.floor(t / 6)).padStart(2, '0')}`,
          site: SITES[site],
          kpi: kpiFor(site, t),
          card: cardAt(t, s.kind, s.t0),
          track: trackFor(t),
          table: tableFor(site, t),
          drop: {open: dropOpen(t), sites: DROP, on: t < 20 ? 1 : 2},
          tool,
          tags,
          cursor: cur.p,
          hand: cur.hand,
          click: clickAt(t),
        });
        return {};
      },
    };
  });
}
