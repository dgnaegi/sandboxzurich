import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

/** Swiss traffic signs (SSV) and traffic lights. Rows: [x, y, z, heading, code|kind] in local metres (z = ground);
 *  heading = facing angle of the sign front in the local frame (x east, y north). Local -> Three: (x, z, -y).
 *  Signs: 2 draw calls per tile (merged posts + one atlas mesh). Signals: 2 (masts/housings + lamps, vertex-coloured). */
export type SignRow = [number, number, number, number, string];
export type SignalRow = [number, number, number, number, string];

const CELL = 128;
const RED = '#d4141c', BLUE = '#0a56a8', GREY = 0x8a8f94;
const CODES = ['speed30', 'speed50', 'zone30', 'zone30end', 'einbahn', 'einfahrt_verboten', 'fahrverbot', 'radweg', 'fussweg',
  'fussgaenger', 'vortritt', 'stop', 'parkieren', 'blauzone', 'sackgasse', 'halteverbot', 'begegnung', 'begegnungend', 'back'] as const;
const SIGN_SIZE = 0.62, BOTTOM = 2.2;

type G = CanvasRenderingContext2D;
const disc = (g: G, r: number, fill: string) => { g.fillStyle = fill; g.beginPath(); g.arc(64, 64, r, 0, 7); g.fill(); };
const ring = (g: G, num?: string) => {
  disc(g, 62, RED); disc(g, 45, '#fff');
  if (num) { g.fillStyle = '#111'; g.font = `700 ${num.length > 1 ? 50 : 60}px Arial, sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(num, 64, 68); }
};
const sq = (g: G, fill: string) => { g.fillStyle = '#fff'; g.beginPath(); g.roundRect(2, 2, 124, 124, 12); g.fill(); g.fillStyle = fill; g.beginPath(); g.roundRect(8, 8, 112, 112, 8); g.fill(); };
const walker = (g: G, cx: number, cy: number, s: number, col: string) => {
  g.fillStyle = col; g.strokeStyle = col; g.lineWidth = 7 * s; g.lineCap = 'round';
  g.beginPath(); g.arc(cx, cy - 22 * s, 7 * s, 0, 7); g.fill();
  g.beginPath(); g.moveTo(cx, cy - 12 * s); g.lineTo(cx - 2 * s, cy + 8 * s); g.lineTo(cx - 10 * s, cy + 28 * s);
  g.moveTo(cx - 2 * s, cy + 8 * s); g.lineTo(cx + 9 * s, cy + 28 * s);
  g.moveTo(cx - 12 * s, cy - 4 * s); g.lineTo(cx, cy - 8 * s); g.lineTo(cx + 12 * s, cy + 2 * s); g.stroke();
};
const text = (g: G, s: string, x: number, y: number, px: number, col: string) => { g.fillStyle = col; g.font = `700 ${px}px Arial, sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(s, x, y); };

const DRAW: Record<string, (g: G) => void> = {
  speed30: (g) => ring(g, '30'),
  speed50: (g) => ring(g, '50'),
  zone30: (g) => { sq(g, '#fff'); g.save(); g.translate(64, 52); g.scale(0.62, 0.62); g.translate(-64, -64); ring(g, '30'); g.restore(); text(g, 'ZONE', 64, 104, 24, '#111'); },
  zone30end: (g) => { DRAW.zone30(g); g.strokeStyle = '#222'; g.lineWidth = 6; g.beginPath(); for (const o of [-14, 0, 14]) { g.moveTo(112 + o, 14); g.lineTo(16 + o, 114); } g.stroke(); },
  einbahn: (g) => { sq(g, BLUE); g.fillStyle = '#fff'; g.beginPath(); g.moveTo(64, 20); g.lineTo(98, 62); g.lineTo(76, 62); g.lineTo(76, 108); g.lineTo(52, 108); g.lineTo(52, 62); g.lineTo(30, 62); g.fill(); },
  einfahrt_verboten: (g) => { disc(g, 62, RED); g.fillStyle = '#fff'; g.fillRect(20, 54, 88, 20); },
  fahrverbot: (g) => ring(g),
  radweg: (g) => {
    disc(g, 62, '#fff'); disc(g, 58, BLUE); g.strokeStyle = '#fff'; g.lineWidth = 6; g.lineCap = 'round';
    for (const x of [40, 88]) { g.beginPath(); g.arc(x, 78, 15, 0, 7); g.stroke(); }
    g.beginPath(); g.moveTo(40, 78); g.lineTo(58, 52); g.lineTo(80, 52); g.lineTo(88, 78); g.moveTo(58, 52); g.lineTo(66, 78); g.lineTo(40, 78); g.moveTo(66, 78); g.lineTo(80, 52); g.stroke();
  },
  fussweg: (g) => { disc(g, 62, '#fff'); disc(g, 58, BLUE); walker(g, 64, 64, 1.3, '#fff'); },
  fussgaenger: (g) => { sq(g, BLUE); g.fillStyle = '#fff'; g.beginPath(); g.moveTo(64, 16); g.lineTo(112, 104); g.lineTo(16, 104); g.fill(); g.fillStyle = BLUE; g.beginPath(); g.moveTo(64, 30); g.lineTo(100, 98); g.lineTo(28, 98); g.fill(); walker(g, 64, 74, 0.95, '#fff'); },
  vortritt: (g) => { g.fillStyle = RED; g.beginPath(); g.moveTo(4, 14); g.lineTo(124, 14); g.lineTo(64, 120); g.fill(); g.fillStyle = '#fff'; g.beginPath(); g.moveTo(26, 28); g.lineTo(102, 28); g.lineTo(64, 94); g.fill(); },
  stop: (g) => { const p = (r: number) => { g.beginPath(); for (let i = 0; i < 8; i++) { const a = Math.PI / 8 + i * Math.PI / 4; g.lineTo(64 + r * Math.cos(a), 64 + r * Math.sin(a)); } g.closePath(); }; g.fillStyle = '#fff'; p(66); g.fill(); g.fillStyle = RED; p(60); g.fill(); text(g, 'STOP', 64, 66, 36, '#fff'); },
  parkieren: (g) => { sq(g, BLUE); text(g, 'P', 64, 66, 88, '#fff'); },
  blauzone: (g) => { sq(g, BLUE); text(g, 'P', 64, 50, 64, '#fff'); disc(g, 0, '#fff'); g.fillStyle = '#fff'; g.fillRect(22, 84, 84, 26); text(g, 'BLAUE ZONE', 64, 98, 14, BLUE); },
  sackgasse: (g) => { sq(g, BLUE); g.fillStyle = '#fff'; g.fillRect(52, 36, 24, 74); g.fillStyle = RED; g.fillRect(30, 22, 68, 18); },
  halteverbot: (g) => { disc(g, 62, RED); disc(g, 52, BLUE); g.strokeStyle = RED; g.lineWidth = 12; g.beginPath(); g.moveTo(30, 30); g.lineTo(98, 98); g.moveTo(98, 30); g.lineTo(30, 98); g.stroke(); },
  begegnung: (g) => {
    sq(g, BLUE); walker(g, 44, 50, 0.95, '#fff'); walker(g, 66, 54, 0.7, '#fff');
    g.fillStyle = '#fff'; g.beginPath(); g.roundRect(70, 44, 38, 14, 4); g.fill(); g.fillStyle = BLUE; for (const x of [80, 98]) { g.beginPath(); g.arc(x, 60, 5, 0, 7); g.fill(); }
    g.fillStyle = '#fff'; for (const x of [80, 98]) { g.beginPath(); g.arc(x, 60, 3, 0, 7); g.fill(); }
    g.save(); g.translate(64, 88); g.scale(0.4, 0.4); g.translate(-64, -64); ring(g, '20'); g.restore();
  },
  begegnungend: (g) => { DRAW.begegnung(g); g.strokeStyle = '#222'; g.lineWidth = 6; g.beginPath(); for (const o of [-14, 0, 14]) { g.moveTo(112 + o, 14); g.lineTo(16 + o, 114); } g.stroke(); },
  back: (g) => { g.fillStyle = '#8d9297'; g.fillRect(0, 0, CELL, CELL); },
};

let signAtlas: THREE.CanvasTexture | null = null;
const COLS = 5, ROWS = Math.ceil(CODES.length / COLS);
function getAtlas(): THREE.CanvasTexture {
  if (signAtlas) return signAtlas;
  const c = document.createElement('canvas');
  c.width = THREE.MathUtils.ceilPowerOfTwo(COLS * CELL); c.height = THREE.MathUtils.ceilPowerOfTwo(ROWS * CELL);
  const g = c.getContext('2d')!;
  CODES.forEach((code, i) => { g.save(); g.translate((i % COLS) * CELL, Math.floor(i / COLS) * CELL); DRAW[code](g); g.restore(); });
  signAtlas = new THREE.CanvasTexture(c);
  signAtlas.colorSpace = THREE.SRGBColorSpace; signAtlas.anisotropy = 4;
  return signAtlas;
}
const cellUV = (i: number, tex: THREE.CanvasTexture, cols: number) => {
  const W = tex.image.width, H = tex.image.height, px = (i % cols) * CELL, py = Math.floor(i / cols) * CELL, e = 0.5;
  return [(px + e) / W, 1 - (py + CELL - e) / H, (px + CELL - e) / W, 1 - (py + e) / H]; // u0 v0 u1 v1
};

function boxAt(w: number, h: number, d: number, x: number, y: number, z: number, rotY: number, col: number): THREE.BufferGeometry {
  const b = new THREE.BoxGeometry(w, h, d);
  b.rotateY(rotY); b.translate(x, y, z);
  b.deleteAttribute('uv');
  const n = b.getAttribute('position').count, c = new THREE.Color(col), a = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) a.set([c.r, c.g, c.b], i * 3);
  b.setAttribute('color', new THREE.Float32BufferAttribute(a, 3));
  return b;
}
const facing = (h: number) => ({ nx: Math.cos(h), nz: -Math.sin(h) }); // normal in Three coordinates
/** rotation about Y that turns +Z (box front) to the normal */
const rotY = (h: number) => Math.atan2(Math.cos(h), -Math.sin(h));

/* ---------------------------------- signs ---------------------------------- */
export function buildTrafficSigns(rows: SignRow[]): THREE.Object3D[] {
  if (!rows.length) return [];
  const tex = getAtlas();
  const pos: number[] = [], uv: number[] = [], nrm: number[] = [], idx: number[] = [];
  const poles = new Map<string, { x: number; y: number; z: number; top: number }>();
  const level = new Map<string, number>();
  const back = cellUV(CODES.indexOf('back'), tex, COLS);
  for (const [x, y, z, h, code] of rows) {
    const ci = CODES.indexOf(code as never);
    if (ci < 0) continue;
    const pk = `${Math.round(x / 0.4)},${Math.round(y / 0.4)}`;
    const lk = `${pk}|${Math.round(h / (Math.PI / 4)) & 7}`;
    const lv = level.get(lk) ?? 0;
    level.set(lk, lv + 1);
    const cz = z + BOTTOM + SIGN_SIZE / 2 + lv * (SIGN_SIZE + 0.04);
    const p = poles.get(pk) ?? { x, y, z, top: 0 };
    p.top = Math.max(p.top, cz + SIGN_SIZE / 2 + 0.1); poles.set(pk, p);
    const nx = Math.cos(h), nz = -Math.sin(h), rx = nz, rz = -nx, hw = SIGN_SIZE / 2;
    const bx = x + nx * 0.06, bz = -y + nz * 0.06;
    const [u0, v0, u1, v1] = cellUV(ci, tex, COLS);
    for (const [f, uvs] of [[1, [u0, v0, u1, v1]], [-1, back]] as const) {
      const off = f === 1 ? 0 : -0.012, b0 = pos.length / 3;
      for (const [su, sv] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) {
        pos.push(bx + rx * hw * su * f + nx * off, cz + hw * sv, bz + rz * hw * su * f + nz * off);
        nrm.push(nx * f, 0, nz * f);
      }
      uv.push(uvs[0], uvs[1], uvs[2], uvs[1], uvs[2], uvs[3], uvs[0], uvs[3]);
      idx.push(b0, b0 + 1, b0 + 2, b0, b0 + 2, b0 + 3);
    }
  }
  const out: THREE.Object3D[] = [];
  if (!idx.length) return out;
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  geo.setIndex(idx);
  const mat = new THREE.MeshLambertMaterial({ map: tex, alphaTest: 0.5, emissive: 0xffffff, emissiveMap: tex, emissiveIntensity: 0.18 });
  out.push(new THREE.Mesh(geo, mat));
  const pg = mergeGeometries([...poles.values()].map((p) => boxAt(0.07, p.top - p.z, 0.07, p.x, (p.top + p.z) / 2, -p.y, 0, GREY)))!;
  out.push(new THREE.Mesh(pg, new THREE.MeshLambertMaterial({ vertexColors: true })));
  return out;
}

/* --------------------------------- signals --------------------------------- */
const CYCLE = 40, GREEN = 16, YELLOW = 2.5;
const axisOf = (h: number) => (Math.abs(Math.cos(h)) > 0.7071 ? 0 : 1);
/** 0 green, 1 yellow, 2 red for a given axis at time t (seconds); axis 1 is shifted by half a cycle. */
const phase = (axis: number, t: number) => { const s = (t + axis * CYCLE / 2) % CYCLE; return s < GREEN ? 0 : s < GREEN + YELLOW ? 1 : 2; };
const ON = [0xff2a1a, 0xffb400, 0x1fe56a], OFF = [0x3a0d0a, 0x3a2b00, 0x07301a];

interface Lamp { v0: number; axis: number; kind: string; idx: number } // idx: car 0 red,1 yellow,2 green; ped 0 red,1 green
interface Entry { mesh: THREE.Mesh; lamps: Lamp[]; seen: boolean }
const entries = new Set<Entry>();
let lastKey = -1;
let lampTex: THREE.CanvasTexture | null = null;
function getLampTex() {
  if (lampTex) return lampTex;
  const c = document.createElement('canvas'); c.width = 128; c.height = 64;
  const g = c.getContext('2d')!;
  g.fillStyle = '#fff'; g.beginPath(); g.arc(32, 32, 28, 0, 7); g.fill();
  walker(g, 96, 32, 0.9, '#fff');
  lampTex = new THREE.CanvasTexture(c); lampTex.colorSpace = THREE.SRGBColorSpace;
  return lampTex;
}

export function buildSignals(rows: SignalRow[]): THREE.Object3D[] {
  if (!rows.length) return [];
  const body: THREE.BufferGeometry[] = [];
  const poles = new Map<string, boolean>();
  const pos: number[] = [], uv: number[] = [], col: number[] = [], idx: number[] = [];
  const lamps: Lamp[] = [];
  const quad = (cx: number, cy: number, cz: number, nx: number, nz: number, s: number, uvr: number[], axis: number, kind: string, i: number) => {
    const rx = nz, rz = -nx, b0 = pos.length / 3, h = s / 2;
    for (const [su, sv] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) {
      pos.push(cx + rx * h * su, cy + h * sv, cz + rz * h * su);
      col.push(0.2, 0.05, 0.05);
    }
    uv.push(uvr[0], 0, uvr[1], 0, uvr[1], 1, uvr[0], 1);
    idx.push(b0, b0 + 1, b0 + 2, b0, b0 + 2, b0 + 3);
    lamps.push({ v0: b0, axis, kind, idx: i });
  };
  for (const [x, y, z, h, kind] of rows) {
    const { nx, nz } = facing(h), axis = axisOf(h), ry = rotY(h), px = x, pz = -y;
    const rx = nz, rz = -nx; // sideways
    const pk = `${Math.round(x / 0.5)},${Math.round(y / 0.5)}`;
    if (!poles.has(pk)) { poles.set(pk, true); body.push(boxAt(0.14, 3.4, 0.14, px, z + 1.7, pz, ry, 0x4b4f55)); }
    const side = kind === 'bike' ? 0.0 : 0.0;
    const cx = px + nx * 0.2 + rx * side, cz = pz + nz * 0.2 + rz * side;
    if (kind === 'car') {
      body.push(boxAt(0.34, 1.0, 0.26, cx, z + 3.0, cz, ry, 0x1d1f22));
      for (let i = 0; i < 3; i++) quad(cx + nx * 0.14, z + 3.3 - i * 0.3, cz + nz * 0.14, nx, nz, 0.22, [0, 0.5], axis, kind, i);
    } else if (kind === 'bike') {
      body.push(boxAt(0.26, 0.8, 0.22, cx + rx * 0.35, z + 2.3, cz + rz * 0.35, ry, 0x1d1f22));
      for (let i = 0; i < 3; i++) quad(cx + rx * 0.35 + nx * 0.12, z + 2.55 - i * 0.25, cz + rz * 0.35 + nz * 0.12, nx, nz, 0.17, [0, 0.5], axis, kind, i);
    } else {
      body.push(boxAt(0.3, 0.64, 0.22, cx, z + 2.4, cz, ry, 0x1d1f22));
      for (let i = 0; i < 2; i++) quad(cx + nx * 0.12, z + 2.57 - i * 0.3, cz + nz * 0.12, nx, nz, 0.24, [0.5, 1], axis, kind, i);
    }
  }
  const lg = new THREE.BufferGeometry();
  lg.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  lg.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  lg.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  lg.setIndex(idx);
  const lm = new THREE.Mesh(lg, new THREE.MeshBasicMaterial({ map: getLampTex(), vertexColors: true, alphaTest: 0.5 }));
  const bm = new THREE.Mesh(mergeGeometries(body)!, new THREE.MeshLambertMaterial({ vertexColors: true }));
  entries.add({ mesh: lm, lamps, seen: false });
  lastKey = -1;
  return [bm, lm];
}

/** Forget traffic-light meshes of tiles that left the scene (called on tile unload). */
export function purgeSignals(): void {
  for (const e of entries) {
    let n: THREE.Object3D | null = e.mesh;
    while (n?.parent) n = n.parent;
    if (e.mesh.parent && !(n as THREE.Scene).isScene) entries.delete(e);
  }
}

/** Call once per frame with elapsed seconds; recolours lamps only when a phase changes. */
export function updateSignals(t: number): void {
  const s0 = phase(0, t), s1 = phase(1, t), key = s0 * 3 + s1;
  if (key === lastKey) return;
  lastKey = key;
  const st = [s0, s1];
  for (const e of entries) {
    if (e.mesh.parent) e.seen = true;
    else if (e.seen) { entries.delete(e); continue; }
    const attr = e.mesh.geometry.getAttribute('color') as THREE.BufferAttribute, c = new THREE.Color();
    for (const l of e.lamps) {
      const s = st[l.axis];
      const lit = l.kind === 'ped' ? (l.idx === 1 ? s === 0 : s !== 0) : s === l.idx;
      const code = l.kind === 'ped' ? [0xff2a1a, 0x1fe56a][l.idx] : ON[l.idx];
      const dim = l.kind === 'ped' ? [0x3a0d0a, 0x07301a][l.idx] : OFF[l.idx];
      c.setHex(lit ? code : dim);
      for (let k = 0; k < 4; k++) attr.setXYZ(l.v0 + k, c.r, c.g, c.b);
    }
    attr.needsUpdate = true;
  }
}
