/** Label pass of the city map: Kreis/quarter names, squares, parks, landmarks, stops and street names along the roads, collision free. */
import type { MapData, Named } from './map_data';
import type { Theme, View } from './map_render';
import { drawBlip, type BlipKind } from './map_blips';

export interface Jump { name: string; sub: string; x: number; y: number; yaw: number; built: boolean }
export interface PinHit { x: number; y: number; place: Jump }
export interface LabelOpts { dpr: number; kreise: Record<string, number[][]>; kreisAt?: Record<string, number[]>; jumps: Jump[]; pins: PinHit[] }

type Rect = [number, number, number, number];
const FONT = 'Barlow, system-ui, sans-serif';

class Placer {
  rects: Rect[] = [];
  free(r: Rect) { return !this.rects.some((o) => r[0] < o[2] && r[2] > o[0] && r[1] < o[3] && r[3] > o[1]); }
  take(r: Rect) { this.rects.push(r); }
}

function txt(g: CanvasRenderingContext2D, th: Theme, s: string, x: number, y: number, font: string, col: string, halo = 3, haloCol = th.halo) {
  g.font = font; g.textAlign = 'center'; g.textBaseline = 'middle'; g.lineJoin = 'round';
  g.strokeStyle = haloCol; g.lineWidth = halo; g.globalAlpha = 0.9; g.strokeText(s, x, y); g.globalAlpha = 1;
  g.fillStyle = col; g.fillText(s, x, y);
}

export function drawLabels(g: CanvasRenderingContext2D, d: MapData, v: View, th: Theme, o: LabelOpts) {
  const { s } = v, dark = th.text === '#fff';
  g.setTransform(o.dpr, 0, 0, o.dpr, 0, 0);
  const c = Math.cos(v.rot), sn = Math.sin(v.rot);
  const sc = (x: number, y: number): [number, number] => {
    const dx = (x - v.cx) * s, dy = -(y - v.cy) * s;
    return [v.w / 2 + dx * c - dy * sn, v.h / 2 + dx * sn + dy * c];
  };
  const on = (x: number, y: number, m = 20) => x > -m && y > -m && x < v.w + m && y < v.h + m;
  const P = new Placer();
  o.pins.length = 0;
  const rectAt = (x: number, y: number, w: number, h: number): Rect => [x - w / 2, y - h / 2, x + w / 2, y + h / 2];
  const tw = (str: string, font: string) => { g.font = font; return g.measureText(str).width; };
  const label = (x: number, y: number, str: string, font: string, col: string, dy = 0, pad = 2) => {
    const w = tw(str, font) + pad * 2, h = parseInt(font.replace(/^\D*/, '')) + 3 + pad;
    const r = rectAt(x, y + dy, w, h);
    if (!P.free(r)) return false;
    P.take(r); txt(g, th, str, x, y + dy, font, col); return true;
  };

  // Kreis names: chunky GTA district titles with a heavy black outline
  if (s < 0.6) {
    for (const [name, ringPts] of Object.entries(o.kreise)) {
      let cx = 0, cy = 0; for (const [x, y] of ringPts) { cx += x; cy += y; }
      const at = o.kreisAt?.[name] ?? [cx / ringPts.length, cy / ringPts.length];   // anchor inside the play area (build_map.kreis_anchor)
      const [x, y] = sc(at[0], at[1]);
      const [num, nm = ''] = name.split(' · ');
      const size = Math.round(Math.min(30, Math.max(18, s * 130))), sub = Math.round(size * 0.5);
      const f1 = `${size}px Anton, ${FONT}`, f2 = `${sub}px Anton, ${FONT}`;
      if (!on(x, y, 0)) continue;
      const w = Math.max(tw(num, f1), tw(nm.toUpperCase(), f2));
      P.take(rectAt(x, y, w + 8, size + sub + 8));
      g.globalAlpha = 0.72 * (s > 0.4 ? Math.max(0.35, (0.6 - s) / 0.2) : 1);   // background titles, calmer than streets/blips
      txt(g, th, num, x, y - sub * 0.55, f1, th.kreis, size * 0.28, '#0d0b08');
      if (nm) txt(g, th, nm.toUpperCase(), x, y + size * 0.5, f2, th.kreis, sub * 0.3, '#0d0b08');
      g.globalAlpha = 1;
    }
  }
  // jump points (pins)
  for (const p of o.jumps) {
    if (!p.built) continue;
    const [x, y] = sc(p.x, p.y);
    if (!on(x, y)) continue;
    g.fillStyle = th.play_; g.strokeStyle = '#15110c'; g.lineWidth = 2;
    g.beginPath(); g.arc(x, y, 6, 0, 7); g.fill(); g.stroke();
    o.pins.push({ x, y, place: p });
    P.take(rectAt(x, y, 16, 16));
    label(x, y, p.name, `800 13px ${FONT}`, th.play_, 16, 3);
  }
  // quarters
  for (const q of d.places) {
    if (q.kind !== 's' && q.kind !== 'u') continue;
    if (!(s > 0.12 && s < 0.7)) continue;
    const [x, y] = sc(q.x, q.y);
    if (on(x, y)) label(x, y, q.name.toUpperCase(), `700 ${q.kind === 's' ? 13 : 11}px ${FONT}`, dark ? '#c9d2d6' : '#6f6a56', 0, 6);
  }
  // squares, parks
  const green = dark ? '#8fd69a' : '#2f6a31';
  for (const q of d.places) {
    if (q.kind !== 'q' && q.kind !== 'k') continue;
    if (s < (q.kind === 'q' ? 0.28 : 0.4)) continue;
    const [x, y] = sc(q.x, q.y);
    if (on(x, y)) label(x, y, q.name, `${q.kind === 'q' ? 700 : 600} ${q.kind === 'q' ? 12 : 11}px ${FONT}`, q.kind === 'q' ? th.text : green);
  }
  // landmarks (always blip + label), minor POIs only when blip and label both fit (no anonymous dark dots), big buildings as plain text
  const poiOrder = (a: Named, b: Named) => (a.kind === 'lm' ? 0 : 1) - (b.kind === 'lm' ? 0 : 1);
  for (const q of [...d.pois].sort(poiOrder)) {
    const lm = q.kind === 'lm', bld = q.kind === 'bld';
    if (s < (lm ? 0.2 : bld ? 1.5 : 0.9)) continue;
    const [x, y] = sc(q.x, q.y);
    if (!on(x, y)) continue;
    if (bld) { label(x, y, q.name, `italic 600 10.5px ${FONT}`, dark ? '#c9d2d6' : '#6f6a56', 0, 1); continue; }
    const br = lm ? (s > 0.5 ? 10.5 : 8.5) : 6.5;
    const font = `${lm ? 700 : 600} ${lm ? 12.5 : 10.5}px ${FONT}`, ly = br + (lm ? 8 : 7);
    const w = tw(q.name, font) + 2, r = rectAt(x, y, br * 2 + 2, br * 2 + 2);
    const lr = rectAt(x, y + ly, w, 14);
    if (!P.free(r)) continue;
    const lrFree = P.free(lr);
    if (!lm && !lrFree) continue;   // minor blip without a readable name is dropped
    P.take(r); drawBlip(g, q.kind as BlipKind, x, y, br);
    if (lrFree) { P.take(lr); txt(g, th, q.name, x, y + ly, font, th.text); }
  }
  // tram stops and stations
  for (const q of d.stops) {
    if (s < (q.kind === 's' ? 0.12 : 0.5)) continue;
    const [x, y] = sc(q.x, q.y);
    if (!on(x, y)) continue;
    const st = q.kind === 's', br = st ? 8.5 : 5.5;
    P.take(rectAt(x, y, br * 2 + 2, br * 2 + 2)); drawBlip(g, st ? 'station' : 'stop', x, y, br);
    if (st) label(x, y, q.name.replace(/^Zürich /, ''), `800 12px ${FONT}`, th.tram, br + 8, 3);
    else if (s > 0.9) label(x, y, q.name, `600 10px ${FONT}`, th.tram, br + 7, 1);
  }
  // street names along the roads
  const minCls = s >= 0.4 ? 6 : s >= 0.22 ? 3 : s >= 0.12 ? 2 : -1;
  if (minCls < 0 || !d.ready) return;
  const lines = d.labels.filter((l) => l.cls <= minCls || l.cls === 10).sort((a, b) => (a.cls === 10 ? -1 : a.cls) - (b.cls === 10 ? -1 : b.cls) || b.pts.length - a.pts.length);
  for (const l of lines) {
    const water = l.cls === 10;
    const size = water ? 13 : l.cls <= 1 ? 12 : l.cls <= 2 ? 11.5 : 10.5;
    const font = `${water ? 'italic ' : ''}${l.cls <= 1 || water ? 700 : 600} ${size}px ${FONT}`;
    const w = tw(l.name, font) + 6;
    // project and collect lengths
    const n = l.pts.length / 2, X = new Float32Array(n), Y = new Float32Array(n), Lc = new Float32Array(n);
    for (let i = 0; i < n; i++) {
      const [x, y] = sc(l.pts[i * 2], l.pts[i * 2 + 1]); X[i] = x; Y[i] = y;
      if (i) Lc[i] = Lc[i - 1] + Math.hypot(x - X[i - 1], y - Y[i - 1]);
    }
    if (Lc[n - 1] < w) continue;
    let placed = 0, from = 0;
    for (let i = from; i < n - 1 && placed < 2; i++) {
      let j = i + 1;
      while (j < n && Lc[j] - Lc[i] < w) j++;
      if (j >= n) break;
      // clip the window to the text length along the polyline
      const ax = X[i], ay = Y[i], bx = X[j], by = Y[j], len = Math.hypot(bx - ax, by - ay);
      let ok = len > 0.9 * (Lc[j] - Lc[i]);
      for (let k = i + 1; ok && k < j; k++) ok = Math.abs((bx - ax) * (ay - Y[k]) - (ax - X[k]) * (by - ay)) / len < Math.max(2.5, 0.07 * w);
      const mx = (ax + bx) / 2, my = (ay + by) / 2;
      if (!ok || !on(mx, my, -4)) continue;
      let ang = Math.atan2(by - ay, bx - ax);
      if (ang > Math.PI / 2) ang -= Math.PI; else if (ang < -Math.PI / 2) ang += Math.PI;
      // collision with the rotated box approximated by its bounding box
      const hw = (Math.abs(Math.cos(ang)) * w + Math.abs(Math.sin(ang)) * size) / 2, hh = (Math.abs(Math.sin(ang)) * w + Math.abs(Math.cos(ang)) * size) / 2;
      const r: Rect = [mx - hw, my - hh, mx + hw, my + hh];
      if (!P.free(r)) continue;
      P.take(r);
      g.save(); g.translate(mx, my); g.rotate(ang);
      txt(g, th, l.name, 0, 0, font, water ? (dark ? '#9fd2f5' : '#d6ecfa') : dark ? th.text : '#4f4a3c', water && !dark ? 2.5 : 3, water && !dark ? '#1e5680' : th.halo);
      g.restore();
      placed++;
      while (i < n - 2 && Lc[i] < Lc[j] + 260) i++;
      from = i;
    }
  }
}
