/** Label pass of the city map: Kreis/quarter names, squares, parks, landmarks, stops and street names along the roads, collision free. */
import type { MapData, Named } from './map_data';
import type { Theme, View } from './map_render';

export interface Jump { name: string; sub: string; x: number; y: number; yaw: number; built: boolean }
export interface PinHit { x: number; y: number; place: Jump }
export interface LabelOpts { dpr: number; kreise: Record<string, number[][]>; jumps: Jump[]; pins: PinHit[] }

type Rect = [number, number, number, number];
const FONT = 'Barlow, system-ui, sans-serif';

class Placer {
  rects: Rect[] = [];
  free(r: Rect) { return !this.rects.some((o) => r[0] < o[2] && r[2] > o[0] && r[1] < o[3] && r[3] > o[1]); }
  take(r: Rect) { this.rects.push(r); }
}

function txt(g: CanvasRenderingContext2D, th: Theme, s: string, x: number, y: number, font: string, col: string, halo = 3) {
  g.font = font; g.textAlign = 'center'; g.textBaseline = 'middle'; g.lineJoin = 'round';
  g.strokeStyle = th.halo; g.lineWidth = halo; g.globalAlpha = 0.9; g.strokeText(s, x, y); g.globalAlpha = 1;
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

  // Kreis names (large, faint) when zoomed out
  if (s < 0.45) {
    g.globalAlpha = 0.55;
    for (const [name, ringPts] of Object.entries(o.kreise)) {
      let cx = 0, cy = 0; for (const [x, y] of ringPts) { cx += x; cy += y; }
      const [x, y] = sc(cx / ringPts.length, cy / ringPts.length);
      const size = Math.round(Math.min(28, Math.max(14, s * 110)));
      const f = `${size}px Anton, ${FONT}`;
      if (on(x, y, 0)) { const str = name.toUpperCase(); const w = tw(str, f); P.take(rectAt(x, y, w, size + 4)); txt(g, th, str, x, y, f, th.kreis, 3.5); }
    }
    g.globalAlpha = 1;
  }
  // jump points (pins)
  for (const p of o.jumps) {
    if (!p.built) continue;
    const [x, y] = sc(p.x, p.y);
    if (!on(x, y)) continue;
    g.fillStyle = th.play_; g.strokeStyle = '#fff'; g.lineWidth = 2;
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
    if (on(x, y)) label(x, y, q.name.toUpperCase(), `700 ${q.kind === 's' ? 13 : 11}px ${FONT}`, dark ? '#c9d2d6' : '#7a7466', 0, 6);
  }
  // squares, parks
  const green = dark ? '#8fd69a' : '#3e7a3c';
  for (const q of d.places) {
    if (q.kind !== 'q' && q.kind !== 'k') continue;
    if (s < (q.kind === 'q' ? 0.28 : 0.4)) continue;
    const [x, y] = sc(q.x, q.y);
    if (on(x, y)) label(x, y, q.name, `${q.kind === 'q' ? 700 : 600} ${q.kind === 'q' ? 12 : 11}px ${FONT}`, q.kind === 'q' ? th.text : green);
  }
  // landmarks, notable buildings
  const pk: Record<string, string> = { lm: '#e4007d', church: '#7a5a9a', hospital: '#d33', culture: '#c46a1a', civic: '#3a6fa8', school: '#3a8f6a', bld: '#8a8272' };
  const poiOrder = (a: Named, b: Named) => (a.kind === 'lm' ? 0 : 1) - (b.kind === 'lm' ? 0 : 1);
  for (const q of [...d.pois].sort(poiOrder)) {
    if (s < (q.kind === 'lm' ? 0.3 : q.kind === 'bld' ? 1.2 : 0.8)) continue;
    const [x, y] = sc(q.x, q.y);
    if (!on(x, y)) continue;
    const r = rectAt(x, y, 8, 8);
    if (!P.free(r)) continue;
    P.take(r); g.fillStyle = pk[q.kind] ?? '#888'; g.strokeStyle = '#fff'; g.lineWidth = 1.5;
    g.beginPath();
    if (q.kind === 'lm') { for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? 3.5 : 7; g.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); } g.closePath(); } else g.arc(x, y, 3.5, 0, 7);
    g.fill(); g.stroke();
    if (q.kind === 'lm' || s > 1) label(x, y, q.name, `600 ${q.kind === 'lm' ? 12 : 10}px ${FONT}`, q.kind === 'lm' ? pk.lm : th.text, 12, 1);
  }
  // tram stops and stations
  for (const q of d.stops) {
    if (s < (q.kind === 's' ? 0.12 : 0.35)) continue;
    const [x, y] = sc(q.x, q.y);
    if (!on(x, y)) continue;
    if (q.kind === 's') {
      g.fillStyle = '#e4002b'; g.strokeStyle = '#fff'; g.lineWidth = 2; g.beginPath(); g.roundRect(x - 7, y - 7, 14, 14, 3); g.fill(); g.stroke();
      g.fillStyle = '#fff'; g.font = `800 10px ${FONT}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('S', x, y + 0.5);
      P.take(rectAt(x, y, 16, 16));
      label(x, y, q.name.replace(/^Zürich /, ''), `800 12px ${FONT}`, th.tram, 17, 3);
    } else {
      g.fillStyle = '#fff'; g.strokeStyle = th.tram; g.lineWidth = 2.2; g.beginPath(); g.arc(x, y, 4.2, 0, 7); g.fill(); g.stroke();
      P.take(rectAt(x, y, 10, 10));
      if (s > 0.8) label(x, y, q.name, `600 10px ${FONT}`, th.tram, 11, 1);
    }
  }
  // street names along the roads
  const minCls = s >= 0.4 ? 6 : s >= 0.22 ? 3 : s >= 0.12 ? 2 : -1;
  if (minCls < 0 || !d.ready) return;
  const lines = d.labels.filter((l) => l.cls <= minCls || l.cls === 10).sort((a, b) => (a.cls === 10 ? -1 : a.cls) - (b.cls === 10 ? -1 : b.cls) || b.pts.length - a.pts.length);
  for (const l of lines) {
    const water = l.cls === 10;
    const size = water ? 13 : l.cls <= 1 ? 12 : l.cls <= 2 ? 11.5 : 10.5;
    const font = `${water ? 'italic ' : ''}${l.cls <= 3 || water ? 700 : 600} ${size}px ${FONT}`;
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
      txt(g, th, l.name, 0, 0, font, water ? (dark ? '#9fd2f5' : '#2b6a9a') : th.text, 3);
      g.restore();
      placed++;
      while (i < n - 2 && Lc[i] < Lc[j] + 260) i++;
      from = i;
    }
  }
}
