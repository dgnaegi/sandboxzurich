import * as THREE from 'three';
import { loadOgdExtras } from './ogd_extras';
import { catalogReady, setCatalogStopZ } from './catalog';

/** Real stop equipment from public/data/stops_equip.json (pipeline/stops_equip.py, VBZ infrastructure OGD, CC0).
 *  Shelters, benches, ticket machines, poster panels and departure displays at their real positions; one InstancedMesh per
 *  material (opaque boxes share one draw call). Stops without city data keep the generic fallback set from stops.ts. */
export interface StopDefault { x: number; y: number; z: number; lines: string[]; shelter: THREE.Group; o: THREE.Group }
interface Equip { sh: number[][]; bn: number[][]; df: number[][]; tk: number[][]; pl: number[][]; cov: number[][] }

/** Passenger information display (dark LED box: next departures as orange text). */
export function infoTex(lines: string[], half = false): THREE.Texture {
  const k = half ? 1 : 2;   // phones: half resolution (128x64 instead of 256x128)
  const c = document.createElement('canvas'); c.width = 128 * k; c.height = 64 * k;
  const g = c.getContext('2d')!; g.scale(k, k);
  g.fillStyle = '#07090c'; g.fillRect(0, 0, 128, 64);
  g.fillStyle = '#ffb347'; g.font = 'bold 15px monospace'; g.textAlign = 'left';
  lines.slice(0, 3).forEach((l, i) => { g.fillText(`${l.padEnd(3)} ${2 + i * 4 + (l.length * 3) % 5} min`, 8, 18 + i * 19); });
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

const MOBILE = typeof matchMedia !== 'undefined' && matchMedia('(pointer: coarse)').matches;
const UP = new THREE.Vector3(0, 1, 0);
const POSTER = [0xd9c9a3, 0x8fb0c9, 0xc96b5a, 0xe6dfcf, 0x6f9a7a, 0xd8b04a, 0x5d6f93, 0xe9e9e4].map((c) => new THREE.Color(c));
const WOOD = new THREE.Color(0x8a6a45), STEEL = new THREE.Color(0x7d848a), DARK = new THREE.Color(0x30353a), ROOF = new THREE.Color(0x5f666b);
const TICK = new THREE.Color(0x2c4a73), SCREEN = new THREE.Color(0xa9d4f5);

class Acc {
  mats: THREE.Matrix4[] = []; cols: THREE.Color[] = [];
  push(m: THREE.Matrix4, c?: THREE.Color) { this.mats.push(m); this.cols.push(c ?? STEEL); }
  mesh(geo: THREE.BufferGeometry, mat: THREE.Material, colored: boolean): THREE.InstancedMesh | null {
    if (!this.mats.length) return null;
    const im = new THREE.InstancedMesh(geo, mat, this.mats.length);
    this.mats.forEach((m, i) => { im.setMatrixAt(i, m); if (colored) im.setColorAt(i, this.cols[i]); });
    im.instanceMatrix.needsUpdate = true; im.matrixAutoUpdate = false;
    return im;
  }
}

/** Object frame: X along the face axis (azimuth az, clockwise from north, local y = north), Z = front (toward the track), Y up. */
function frame(x: number, y: number, z: number, az: number, side: number): THREE.Matrix4 {
  const a = (az * Math.PI) / 180, fx = Math.cos(a) * side, fz = Math.sin(a) * side;   // three: x = x, z = -y
  const f = new THREE.Vector3(fx, 0, fz), xa = new THREE.Vector3().crossVectors(UP, f);
  return new THREE.Matrix4().makeBasis(xa, UP, f).setPosition(x, z, -y);
}
const _l = new THREE.Matrix4(), _s = new THREE.Matrix4();
function part(fr: THREE.Matrix4, px: number, py: number, pz: number, sx: number, sy: number, sz: number): THREE.Matrix4 {
  return new THREE.Matrix4().multiplyMatrices(fr, _l.multiplyMatrices(_l.makeTranslation(px, py, pz), _s.makeScale(sx, sy, sz)));
}

export async function loadEquip(group: THREE.Group, defaults: StopDefault[], ground: (x: number, y: number) => number): Promise<void> {
  await Promise.resolve();   // buildStops returns and main adds the group to the scene first
  void loadOgdExtras(group.parent ?? group, ground);
  let eq: Equip;
  try { eq = await (await fetch('/data/stops_equip.json')).json(); } catch { return; }
  const cell = (x: number, y: number) => `${Math.floor(x / 40)},${Math.floor(y / 40)}`;
  const grid = new Map<string, number[][]>();
  for (const list of [eq.sh, eq.bn, eq.df, eq.tk, eq.pl, eq.cov]) for (const p of list) (grid.get(cell(p[0], p[1])) ?? grid.set(cell(p[0], p[1]), []).get(cell(p[0], p[1]))!).push(p);
  const covered = (x: number, y: number) => {
    for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++)
      for (const p of grid.get(cell(x + i * 40, y + j * 40)) ?? []) if (Math.hypot(p[0] - x, p[1] - y) < 40) return true;
    return false;
  };
  const disposables: { dispose(): void }[] = [];
  for (const d of defaults) if (covered(d.x, d.y)) {   // real data exists: drop the generic shelter
    d.o.remove(d.shelter);
    d.shelter.traverse((m) => { const me = m as THREE.Mesh; if (me.isMesh) { me.geometry.dispose(); const mat = me.material as THREE.MeshBasicMaterial; if (mat.map) { mat.map.dispose(); mat.dispose(); } } });
  }
  const zAt = (x: number, y: number) => {
    let best: StopDefault | null = null, bd = 25;
    for (const d of defaults) { const e = Math.hypot(d.x - x, d.y - y); if (e < bd && !Number.isNaN(d.z)) { bd = e; best = d; } }
    return best ? best.z : ground(x, y);
  };
  const cat = catalogReady();   // catalog models (world/catalog.ts) draw shelters, benches, ticket machines and displays
  if (cat) setCatalogStopZ(zAt);
  const box = new THREE.BoxGeometry(1, 1, 1), plane = new THREE.PlaneGeometry(1, 1);
  const solid = new THREE.MeshLambertMaterial({ color: 0xffffff });
  const glassM = new THREE.MeshLambertMaterial({ color: 0x9fb8c8, transparent: true, opacity: 0.35, depthWrite: false });
  const posterM = new THREE.MeshLambertMaterial({ color: 0xffffff, side: THREE.DoubleSide });
  const opaque = new Acc(), glassA = new Acc(), posters = new Acc();
  const dfi = new Map<string, THREE.Matrix4[]>();
  for (const [x, y, len, dep, az, s] of cat ? [] : eq.sh) {
    const z = zAt(x, y), fr = frame(x, y, z, az, s);
    opaque.push(part(fr, 0, 2.45, 0, len + 0.2, 0.08, dep + 0.3), ROOF);
    glassA.push(part(fr, 0, 1.25, -dep / 2, len, 1.9, 0.03));
    for (const px of [-len / 2 + 0.05, 0, len / 2 - 0.05]) opaque.push(part(fr, px, 1.2, -dep / 2, 0.06, 2.4, 0.06), STEEL);
    if (len >= 9) opaque.push(part(fr, 0, 1.2, -dep / 2, 0.06, 2.4, 0.06), STEEL);
  }
  for (const [x, y, az, s, kind] of eq.bn) {
    const z = zAt(x, y), fr = frame(x, y, z, az, s);
    if (cat && kind === 0) continue;
    if (kind === 1) {   // lean rail
      opaque.push(part(fr, 0, 0.9, 0, 1.0, 0.05, 0.12), STEEL); for (const px of [-0.4, 0.4]) opaque.push(part(fr, px, 0.45, 0, 0.04, 0.9, 0.04), STEEL);
    } else if (kind === 2) {   // single seat
      opaque.push(part(fr, 0, 0.45, 0, 0.5, 0.05, 0.4), WOOD, ); opaque.push(part(fr, 0, 0.22, 0, 0.06, 0.44, 0.06), STEEL);
    } else {   // bench with back rest
      opaque.push(part(fr, 0, 0.45, 0.05, 1.7, 0.05, 0.42), WOOD); opaque.push(part(fr, 0, 0.75, -0.17, 1.7, 0.3, 0.04), WOOD);
      for (const px of [-0.75, 0.75]) opaque.push(part(fr, px, 0.22, 0.05, 0.05, 0.44, 0.36), STEEL);
    }
  }
  (cat ? [] : eq.tk).forEach(([x, y, az, s], i) => {
    const z = zAt(x, y), fr = frame(x, y, z, az, s);
    opaque.push(part(fr, 0, 0.8, 0, 0.55, 1.6, 0.4), TICK); opaque.push(part(fr, 0, 1.25, 0.205, 0.4, 0.45, 0.01), SCREEN);
    opaque.push(part(fr, 0, 0.82, 0.205, 0.18, 0.14, 0.012), DARK); void i;
  });
  (cat ? [] : eq.pl).forEach(([x, y, az, s], i) => {
    const z = zAt(x, y), fr = frame(x, y, z, az, s), c = POSTER[(Math.round(x * 7 + y * 13) >>> 0) % POSTER.length];
    opaque.push(part(fr, 0, 1.15, 0, 1.2, 1.8, 0.07), DARK);
    posters.push(part(fr, 0, 1.15, 0.04, 1.04, 1.6, 1), c); posters.push(part(fr, 0, 1.15, -0.04, -1.04, 1.6, 1), c); void i;
  });
  const lineKey = (x: number, y: number) => {
    let best: StopDefault | null = null, bd = 45;
    for (const d of defaults) { const e = Math.hypot(d.x - x, d.y - y); if (e < bd) { bd = e; best = d; } }
    return best ? best.lines.slice(0, 3).join(',') : '';
  };
  // ceiling-hung displays need a roof: shelters / canopies within reach (VBZ flags some without one -> they floated); otherwise on a post
  const roofed = (x: number, y: number) => [...eq.sh, ...eq.cov].some((r) => Math.hypot(r[0] - x, r[1] - y) < Math.max(4, (r[2] ?? 0) / 2 + 1.5));
  for (const [x, y, az, ceil0] of eq.df) {
    const ceil = ceil0 && roofed(x, y);
    const z = zAt(x, y), fr = frame(x, y, z, az, 1), k = lineKey(x, y);
    if (!cat) opaque.push(part(fr, 0, ceil ? 2.12 : 2.25, 0, 0.62, 0.32, 0.1), DARK);
    if (!ceil) opaque.push(part(fr, 0, 1.1, 0, 0.06, 2.2, 0.06), STEEL);
    const arr = dfi.get(k) ?? dfi.set(k, []).get(k)!;
    if (cat) {   // catalog screen (H4 wall at 2.25 m, H5 ceiling-hung, centre 1.95 m): departure text plane over the atlas screen
      const cy = ceil ? 1.95 : 2.25;
      arr.push(part(fr, 0, cy, 0.055, 0.58, 0.38, 1), part(fr, 0, cy, -0.055, -0.58, 0.38, 1));
      continue;
    }
    arr.push(part(fr, 0, ceil ? 2.12 : 2.25, 0.055, 0.56, 0.26, 1), part(fr, 0, ceil ? 2.12 : 2.25, -0.055, -0.56, 0.26, 1));
  }
  // own group on the scene: main.ts toggles visibility of every child of the stops group by its (origin) position
  const eqGroup = new THREE.Group(); (group.parent ?? group).add(eqGroup);
  const add = (m: THREE.InstancedMesh | null) => { if (m) eqGroup.add(m); return m; };
  add(opaque.mesh(box, solid, true)); add(glassA.mesh(box, glassM, false)); add(posters.mesh(plane, posterM, true));
  for (const [k, mats] of dfi) {
    const tex = infoTex(k ? k.split(',') : ['1'], MOBILE), mat = new THREE.MeshBasicMaterial({ map: tex, side: THREE.DoubleSide });
    const im = new THREE.InstancedMesh(plane, mat, mats.length);
    mats.forEach((m, i) => im.setMatrixAt(i, m)); im.matrixAutoUpdate = false; eqGroup.add(im); disposables.push(tex, mat);
  }
  disposables.push(box, plane, solid, glassM, posterM);
  group.userData.dispose = () => { eqGroup.removeFromParent(); eqGroup.traverse((m) => (m as THREE.InstancedMesh).dispose?.()); for (const d of disposables) d.dispose(); };
}
