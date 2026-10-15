/** Canvas renderer for the vector city map: shared by the radar (dark, rotating) and the big map (light). */
import type { MapData } from './map_data';

export interface View { cx: number; cy: number; s: number; rot: number; w: number; h: number }
export interface Theme {
  bg: string; land: string; dim: string; bld: string; bldLine: string; water: string; green: string; wood: string; sport: string;
  cemetery: string; play: string; allot: string; rail: string; plaza: string; roads: string[]; casing: string[]; railLine: string; tram: string;
  text: string; halo: string; kreis: string; play_: string; veloLane: string; veloPath: string; veloRoad: string;
}

export const LIGHT: Theme = {
  bg: '#e6e2d9', land: '#f4f0e6', dim: '#e6e2d9', bld: '#ddd6c9', bldLine: '#cbc2b1', water: '#a8cfe8', green: '#d3e6bb', wood: '#bfd9a5', sport: '#dcebc9',
  cemetery: '#c9dfb4', play: '#e2eccb', allot: '#dfe6c4', rail: '#e4e0ea', plaza: '#efe9dc',
  roads: ['#f4a65b', '#f8d46c', '#fff0a6', '#ffffff', '#ffffff', '#fbfaf6', '#f1e6ef', '#c9b79a'],
  casing: ['#c97a2c', '#cfab3c', '#d3c27a', '#c9c2b4', '#cfc8ba', '#d6d0c4', '#cdb8c8', '#c9b79a'],
  railLine: '#8d8a93', tram: '#b3262d', text: '#2f2a24', halo: '#fffdf6', kreis: '#8a5aa8', play_: '#e4007d',
  veloLane: '#1d86d6', veloPath: '#12a25e', veloRoad: '#7a4cc4',
};
export const DARK: Theme = {
  bg: '#1b2023', land: '#272f33', dim: '#1b2023', bld: '#48535a', bldLine: '#566269', water: '#2f628c', green: '#35573a', wood: '#2d4a33', sport: '#3b5e40',
  cemetery: '#34523a', play: '#3b5e40', allot: '#3c5238', rail: '#30343a', plaza: '#363f44',
  roads: ['#e0a458', '#e6cf7a', '#d9d29a', '#a9b3b8', '#97a2a7', '#6d777c', '#7d8589', '#6d777c'],
  casing: ['#6e4a1d', '#6e5b22', '#625e3a', '#3a4348', '#394246', '#333b3f', '#394246', '#394246'],
  railLine: '#7d838a', tram: '#ff6a6a', text: '#fff', halo: '#000', kreis: '#c9a7e0', play_: '#ff4fa0',
  veloLane: '#3fd0ff', veloPath: '#4be39a', veloRoad: '#b88cff',
};

const RW = [14, 12, 10, 8, 6, 3.2, 4.5, 1.4];     // road widths [m]
const RMIN = [3.4, 3, 2.6, 2.2, 1.8, 1, 1.3, 0.9]; // minimum widths [px]
const RSHOW = [0.04, 0.05, 0.07, 0.1, 0.17, 0.55, 0.35, 0.9]; // from this px/m on

export function applyView(g: CanvasRenderingContext2D, v: View, dpr: number) {
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  g.translate(v.w / 2, v.h / 2); g.rotate(v.rot); g.scale(v.s, -v.s); g.translate(-v.cx, -v.cy);
}

export function worldBounds(v: View): [number, number, number, number] {
  const c = Math.cos(-v.rot), s = Math.sin(-v.rot);
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
  for (const [sx, sy] of [[0, 0], [v.w, 0], [v.w, v.h], [0, v.h]]) {
    const dx = sx - v.w / 2, dy = sy - v.h / 2;
    const wx = v.cx + (dx * c - dy * s) / v.s, wy = v.cy - (dx * s + dy * c) / v.s;
    x0 = Math.min(x0, wx); x1 = Math.max(x1, wx); y0 = Math.min(y0, wy); y1 = Math.max(y1, wy);
  }
  return [x0, y0, x1, y1];
}

export interface DrawOpts { velo: boolean; boost?: number; kreise: number[][][]; playArea: number[][]; dpr: number }

function ring(g: CanvasRenderingContext2D, r: number[][]) {
  r.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y)));
  g.closePath();
}

export function drawWorld(g: CanvasRenderingContext2D, d: MapData, v: View, th: Theme, o: DrawOpts) {
  const eff = v.s * (o.boost ?? 1), px = 1 / v.s; // px: world metres per screen pixel
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.fillStyle = th.bg; g.fillRect(0, 0, v.w * o.dpr, v.h * o.dpr);
  applyView(g, v, o.dpr);
  const [x0, y0, x1, y1] = worldBounds(v);
  // land inside the Kreise
  g.fillStyle = th.land; g.beginPath(); for (const r of o.kreise) ring(g, r); g.fill();
  const cells = d.ready ? d.visible(x0, y0, x1, y1) : [];
  const each = (layer: string, fn: (p: Path2D) => void) => { for (const c of cells) { const p = c.p.get(layer); if (p) fn(p); } };
  const fill = (layer: string, col: string) => { g.fillStyle = col; each(layer, (p) => g.fill(p, 'evenodd')); };
  g.lineJoin = 'round'; g.lineCap = 'round';
  fill('ar', th.rail); fill('ag', th.green); fill('aw', th.wood); fill('aa', th.allot); fill('ac', th.cemetery); fill('ap', th.play);
  fill('as', th.sport); fill('asq', th.plaza); fill('awater', th.water);
  g.strokeStyle = th.water;
  for (const [l, w, m] of [['w10', 16, 3], ['w11', 8, 2], ['w12', 2.5, 1]] as const) { g.lineWidth = Math.max(w, m * px); each(l, (p) => g.stroke(p)); }
  // underground (dashed, faint)
  if (eff > 0.25) {
    g.save(); g.globalAlpha = 0.7; g.strokeStyle = th.casing[3]; g.lineWidth = 1.2 * px; g.setLineDash([4 * px, 4 * px]);
    for (let c = 0; c < 5; c++) each('rt' + c, (p) => g.stroke(p));
    g.restore();
  }
  if (eff > 0.8) { g.fillStyle = th.bld; g.strokeStyle = th.bldLine; g.lineWidth = 0.8 * px; each('ab', (p) => { g.fill(p, 'evenodd'); g.stroke(p); }); }
  else fill('ab', th.bld);
  // roads, minor first; casing pass then fill pass
  for (let c = 7; c >= 0; c--) {
    if (eff < RSHOW[c]) continue;
    const w = Math.max(RW[c], RMIN[c] * px), cs = Math.max(1.2 * px, w * 0.18);
    g.strokeStyle = th.casing[c]; g.lineWidth = w + cs; each('r' + c, (p) => g.stroke(p));
    g.strokeStyle = th.roads[c]; g.lineWidth = w; each('r' + c, (p) => g.stroke(p));
  }
  // railways
  g.strokeStyle = th.railLine; g.lineWidth = Math.max(3, 2 * px);
  each('lr', (p) => g.stroke(p));
  if (eff > 0.3) { g.strokeStyle = th.land === LIGHT.land ? '#fff' : '#272f33'; g.lineWidth = Math.max(1.4, 1 * px); g.setLineDash([5 * px, 5 * px]); each('lr', (p) => g.stroke(p)); g.setLineDash([]); }
  if (eff > 0.5) { g.strokeStyle = th.railLine; g.lineWidth = 1 * px; each('ly', (p) => g.stroke(p)); }
  g.strokeStyle = th.tram; g.lineWidth = Math.max(2.2, 1.6 * px); each('lm', (p) => g.stroke(p));
  // bridges on top
  for (let c = 7; c >= 0; c--) {
    if (eff < RSHOW[c] || c > 5) continue;
    const w = Math.max(RW[c], RMIN[c] * px);
    g.strokeStyle = th.casing[c]; g.lineWidth = w + Math.max(2 * px, w * 0.35); each('rb' + c, (p) => g.stroke(p));
    g.strokeStyle = th.roads[c]; g.lineWidth = w; each('rb' + c, (p) => g.stroke(p));
  }
  // cycle infrastructure
  if (o.velo && d.velo) {
    g.lineWidth = Math.max(3, 2.4 * px);
    const col: Record<string, string> = { streifen: th.veloLane, weg: th.veloPath, strasse: th.veloRoad };
    for (const [k, p] of d.velo.p) { g.strokeStyle = col[k] ?? th.veloLane; g.globalAlpha = 0.9; g.stroke(p); }
    g.globalAlpha = 1;
  }
  // dim the outside of the Kreise
  g.fillStyle = th.dim; g.globalAlpha = 0.6; g.beginPath(); g.rect(x0 - 5000, y0 - 5000, x1 - x0 + 10000, y1 - y0 + 10000);
  for (const r of o.kreise) ring(g, r); g.fill('evenodd'); g.globalAlpha = 1;
}

/** Kreis borders and the playable area outline (world coordinates, call with the view transform active). */
export function drawBorders(g: CanvasRenderingContext2D, v: View, th: Theme, o: DrawOpts) {
  const px = 1 / v.s;
  g.lineJoin = 'round';
  g.strokeStyle = th.kreis; g.lineWidth = 2.4 * px; g.globalAlpha = 0.85; g.setLineDash([14 * px, 7 * px]);
  g.beginPath(); for (const r of o.kreise) ring(g, r); g.stroke(); g.setLineDash([]); g.globalAlpha = 1;
  g.beginPath(); ring(g, o.playArea);
  g.fillStyle = th.play_; g.globalAlpha = 0.035; g.fill(); g.globalAlpha = 1;
  g.strokeStyle = th.play_; g.lineWidth = 2.8 * px; g.stroke();
}
