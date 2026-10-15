import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

/** Trams and buses on the real OSM lines (pipeline/transit.py). Positions are a pure function of game time. */
interface Stop { name: string; s: number }
interface LineJson { ref: string; mode: 'tram' | 'bus' | 'trolleybus'; colour: string; dir: number; pts: number[][]; stops: Stop[] }
interface Seg { s0: number; s1: number; t0: number; T: number; es: boolean; ee: boolean }
interface Line {
  ref: string; tram: boolean; pts: number[][]; cum: number[]; segs: Seg[]; trip: number; offset: number; len: number;
  pitch: number; mods: number; speed: number; label: THREE.Material;
}
export interface TransitCollider { x: number; y: number; heading: number; len: number; width: number }

const RANGE = 450, DWELL = 20, ROAD_DROP = 0.12;
const WHITE = new THREE.Color(0xe9ecef), BLUE = new THREE.Color(0x1d4f9c), DARK = new THREE.Color(0x15191e);

const box = (c: THREE.Color, w: number, h: number, d: number, x = 0, y = 0, z = 0) => {
  const g = new THREE.BoxGeometry(w, h, d).translate(x, y, z).toNonIndexed();
  const col = new Float32Array(g.attributes.position.count * 3);
  for (let i = 0; i < col.length; i += 3) { col[i] = c.r; col[i + 1] = c.g; col[i + 2] = c.b; }
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  g.deleteAttribute('uv');
  return g;
};
const merge = (g: THREE.BufferGeometry[]) => mergeGeometries(g)!;

/** Tram module (≈11.6 m long, front = -z). kind: 0 head, 1 mid, 2 tail. */
function tramModule(kind: number): THREE.BufferGeometry {
  const g = [
    box(WHITE, 2.4, 2.1, 11.6, 0, 1.75), box(WHITE, 2.2, 0.25, 11.2, 0, 2.9), box(BLUE, 2.42, 0.5, 11.62, 0, 0.75),
    box(DARK, 2.44, 0.95, 10.0, 0, 2.05), box(DARK, 2.0, 0.5, 2.6, 0, 0.35, -3.6), box(DARK, 2.0, 0.5, 2.6, 0, 0.35, 3.6),
    box(DARK, 2.0, 2.0, 0.5, 0, 1.9, -5.9), box(DARK, 2.0, 2.0, 0.5, 0, 1.9, 5.9), // bellows
  ];
  if (kind === 0) g.push(box(WHITE, 2.3, 1.6, 1.3, 0, 1.9, -6.2), box(DARK, 2.0, 0.9, 0.1, 0, 2.3, -6.9), box(BLUE, 2.32, 0.5, 1.32, 0, 0.75, -6.2));
  if (kind === 2) g.push(box(WHITE, 2.3, 1.6, 1.3, 0, 1.9, 6.2), box(DARK, 2.0, 0.9, 0.1, 0, 2.3, 6.9), box(BLUE, 2.32, 0.5, 1.32, 0, 0.75, 6.2));
  if (kind === 1) g.push(box(DARK, 1.6, 0.12, 1.4, 0, 3.12, 0), box(DARK, 0.06, 0.5, 0.06, 0.5, 3.35, 0.4), box(DARK, 0.06, 0.5, 0.06, -0.5, 3.35, 0.4));
  return merge(g);
}

/** Articulated trolleybus module (9 m, front = -z). kind: 0 front, 1 rear. */
function busModule(kind: number): THREE.BufferGeometry {
  const g = [
    box(WHITE, 2.55, 2.5, 8.8, 0, 1.75), box(BLUE, 2.57, 0.6, 8.82, 0, 0.8), box(DARK, 2.58, 0.95, 8.0, 0, 2.15),
    box(DARK, 0.3, 0.9, 0.9, 1.2, 0.45, -2.6), box(DARK, 0.3, 0.9, 0.9, -1.2, 0.45, -2.6),
    box(DARK, 0.3, 0.9, 0.9, 1.2, 0.45, 2.6), box(DARK, 0.3, 0.9, 0.9, -1.2, 0.45, 2.6),
  ];
  if (kind === 0) g.push(box(DARK, 2.3, 1.1, 0.1, 0, 2.2, -4.4), box(BLUE, 2.57, 0.45, 0.1, 0, 0.45, -4.4));
  else g.push(box(DARK, 0.04, 0.04, 6, 0.35, 3.15, 3).rotateX(-0.12), box(DARK, 0.04, 0.04, 6, -0.35, 3.15, 3).rotateX(-0.12),
    box(DARK, 2.0, 1.4, 0.6, 0, 1.9, 4.5));
  return merge(g);
}

const labelCache = new Map<string, THREE.Material>();
function labelMat(ref: string, colour: string): THREE.Material {
  let m = labelCache.get(ref);
  if (m) return m;
  const c = document.createElement('canvas'); c.width = 128; c.height = 48;
  const x = c.getContext('2d')!;
  x.fillStyle = '#05070a'; x.fillRect(0, 0, 128, 48);
  x.fillStyle = '#ffb347'; x.font = 'bold 36px monospace'; x.textAlign = 'center'; x.textBaseline = 'middle';
  x.fillText(ref, 64, 26);
  void colour;
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  m = new THREE.MeshBasicMaterial({ map: tex, side: THREE.FrontSide });
  labelCache.set(ref, m);
  return m;
}

const tpl = new THREE.Object3D();
tpl.rotation.order = 'YXZ';

interface SeqItem { module: string; rotateY180: number; z_center_from_front: number }
interface VehicleSpec { length: number; sequence: SeqItem[] }

export class Transit {
  /** Blender-built VBZ modules (pipeline/transit_models); falls back to box modules until loaded. */
  private modMesh = new Map<string, THREE.InstancedMesh>();
  private modLen = new Map<string, number>();
  private vehicles: Record<string, VehicleSpec> = {};
  readonly group = new THREE.Group();
  /** Game seconds per real second used to derive vehicle time (1 = vehicles move at real speed). */
  timeScale = 1;
  /** Seconds between vehicles per line and direction. */
  headway = 450;
  private lines: Line[] = [];
  private meshes: { tram: THREE.InstancedMesh[]; bus: THREE.InstancedMesh[] };
  private displays: THREE.Mesh[] = [];
  private nDisp = 0;
  private cols: TransitCollider[] = [];
  private vis = 0;

  constructor(scene: THREE.Scene, private ground: (x: number, y: number) => number) {
    const mat = new THREE.MeshLambertMaterial({ vertexColors: true });
    const mk = (g: THREE.BufferGeometry, n: number) => {
      const m = new THREE.InstancedMesh(g, mat, n);
      m.frustumCulled = false; m.count = 0; this.group.add(m);
      return m;
    };
    this.meshes = {
      tram: [0, 1, 2].map((k) => mk(tramModule(k), 24)),
      bus: [0, 1].map((k) => mk(busModule(k), 24)),
    };
    scene.add(this.group);
  }

  async loadModels(base = '/models/transit'): Promise<void> {
    const man = await (await fetch(`${base}/manifest.json`)).json() as { modules: Record<string, { file: string; length: number }>; vehicles: Record<string, VehicleSpec> };
    const loader = new GLTFLoader();
    const mat = new THREE.MeshLambertMaterial({ vertexColors: true });
    await Promise.all(Object.entries(man.modules).map(async ([name, m]) => {
      const g = await loader.loadAsync(`${base}/${m.file}`);
      const parts: THREE.BufferGeometry[] = [];
      g.scene.updateMatrixWorld(true);
      g.scene.traverse((o) => {
        const mesh = o as THREE.Mesh;
        if (!mesh.isMesh || (mesh.material as THREE.Material).name === 'display') return;
        let geo = mesh.geometry.clone().applyMatrix4(mesh.matrixWorld);
        geo = geo.index ? geo.toNonIndexed() : geo;
        // float32 for every attribute so parts with differently quantised data can be merged
        const out = new THREE.BufferGeometry(), n = geo.getAttribute('position').count;
        for (const [k, size] of [['position', 3], ['normal', 3], ['color', 3]] as const) {
          const a = geo.getAttribute(k), arr = new Float32Array(n * size);
          for (let i = 0; i < n; i++) for (let c = 0; c < size; c++) arr[i * size + c] = a ? a.getComponent(i, c) : 1;
          out.setAttribute(k, new THREE.BufferAttribute(arr, size));
        }
        parts.push(out);
      });
      const im = new THREE.InstancedMesh(mergeGeometries(parts)!, mat, 24);
      im.frustumCulled = false; im.count = 0; im.castShadow = true;
      this.group.add(im);
      this.modMesh.set(name, im); this.modLen.set(name, m.length);
    }));
    this.vehicles = man.vehicles;
    for (const m of [...this.meshes.tram, ...this.meshes.bus]) m.visible = false; // replaced by the models
  }

  async load(url = '/data/transit.json'): Promise<void> {
    const data = (await (await fetch(url)).json()) as { lines: LineJson[] };
    this.lines = data.lines.filter((l) => l.pts.length >= 2).map((l) => this.prep(l));
  }

  private prep(l: LineJson): Line {
    const tram = l.mode === 'tram';
    const speed = tram ? 8 : 7, mods = tram ? 3 : 2, pitch = tram ? 12.2 : 9.0;
    const vlen = tram ? 37 : 18.5;
    const cum = [0];
    for (let i = 1; i < l.pts.length; i++) cum.push(cum[i - 1] + Math.hypot(l.pts[i][0] - l.pts[i - 1][0], l.pts[i][1] - l.pts[i - 1][1]));
    const len = cum[cum.length - 1];
    // waypoints (front tip s): start, stops (platform centre), end of line + vehicle length
    const wp = [{ s: 0, stop: false }, ...l.stops.map((s) => ({ s: Math.min(len, s.s + vlen / 2), stop: true })), { s: len + vlen, stop: false }];
    const segs: Seg[] = [];
    let t = 0;
    for (let i = 0; i < wp.length - 1; i++) {
      const d = wp[i + 1].s - wp[i].s;
      if (d <= 0.5) continue;
      const es = wp[i].stop, ee = wp[i + 1].stop;
      const T = d / (speed * (es && ee ? 0.78 : es || ee ? 0.88 : 1));
      segs.push({ s0: wp[i].s, s1: wp[i + 1].s, t0: t, T, es, ee });
      t += T + (ee ? DWELL : 0);
    }
    let h = 0;
    for (const ch of l.ref + l.dir) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
    return { ref: l.ref, tram, pts: l.pts, cum, segs, trip: t, offset: h % this.headway, len, pitch, mods, speed, label: labelMat(l.ref, l.colour) };
  }

  /** Front-tip arc position at trip time tau (s), or -1 if not on the line. */
  private arc(L: Line, tau: number): number {
    if (tau < 0 || tau > L.trip) return -1;
    for (const g of L.segs) {
      if (tau > g.t0 + g.T) continue; // after this segment (dwell or later)
      if (tau < g.t0) return g.s0;
      const u = (tau - g.t0) / g.T;
      const f = g.es && g.ee ? (1 - Math.cos(Math.PI * u)) / 2 : g.es ? 1 - Math.cos((Math.PI * u) / 2) : g.ee ? Math.sin((Math.PI * u) / 2) : u;
      return g.s0 + (g.s1 - g.s0) * f;
    }
    return L.segs[L.segs.length - 1].s1;
  }

  private sample(L: Line, s: number, out: number[]) {
    const { pts, cum } = L;
    let i;
    if (s <= 0) i = 0;
    else if (s >= L.len) i = pts.length - 2;
    else { let lo = 0, hi = cum.length - 1; while (hi - lo > 1) { const m = (lo + hi) >> 1; if (cum[m] <= s) lo = m; else hi = m; } i = lo; }
    const a = pts[i], b = pts[i + 1], sl = Math.max(1e-6, cum[i + 1] - cum[i]);
    const t = (s - cum[i]) / sl; // may extrapolate beyond the ends
    out[0] = a[0] + (b[0] - a[0]) * t; out[1] = a[1] + (b[1] - a[1]) * t;
  }

  update(_dt: number, gameMinutes: number, px: number, py: number): void {
    const time = (gameMinutes * 60) / this.timeScale;
    this.cols.length = 0; this.nDisp = 0; this.vis = 0;
    const cn = { tram: [0, 0, 0], bus: [0, 0] };
    const modCount = new Map<string, number>();
    const p = [0, 0], q = [0, 0], r = [0, 0];
    for (const L of this.lines) {
      const k0 = Math.ceil((time - L.offset - L.trip) / this.headway), k1 = Math.floor((time - L.offset) / this.headway);
      for (let k = k0; k <= k1; k++) {
        const sh = this.arc(L, time - L.offset - k * this.headway);
        if (sh < 0) continue;
        this.sample(L, sh - (L.pitch * L.mods) / 2, p);
        if (Math.hypot(p[0] - px, p[1] - py) > RANGE) continue;
        this.vis++;
        const kinds = L.tram ? cn.tram : cn.bus;
        const im = L.tram ? this.meshes.tram : this.meshes.bus;
        const half = L.tram ? 6.1 : 4.5;
        const spec = this.modMesh.size ? this.vehicles[L.tram ? (k % 2 ? 'tram_flexity' : 'tram_cobra') : 'trolleybus'] : undefined;
        if (spec) { this.placeModels(L, sh, spec, modCount); continue; }
        for (let i = 0; i < L.mods; i++) {
          const sc = sh - (L.tram ? 7.0 : 5.0) - i * L.pitch + (L.tram ? 0.2 : 0.5);
          this.sample(L, sc, p); this.sample(L, sc + 4, q); this.sample(L, sc - 4, r);
          const hx = q[0] - r[0], hy = q[1] - r[1];
          const yaw = Math.atan2(-hx, hy);
          const hd = Math.hypot(hx, hy) || 1, ux = hx / hd, uy = hy / hd;
          const gf = this.ground(p[0] + ux * half, p[1] + uy * half), gb = this.ground(p[0] - ux * half, p[1] - uy * half);
          const gz = this.ground(p[0], p[1]) - ROAD_DROP;
          tpl.position.set(p[0], gz, -p[1]);
          tpl.rotation.set(Math.atan2(gf - gb, half * 2), yaw, 0);
          tpl.updateMatrix();
          const kind = L.tram ? (i === 0 ? 0 : i === L.mods - 1 ? 2 : 1) : (i === 0 ? 0 : 1);
          const mesh = im[kind];
          if (kinds[kind] < 24) mesh.setMatrixAt(kinds[kind]++, tpl.matrix);
          this.cols.push({ x: p[0], y: p[1], heading: Math.atan2(hy, hx), len: L.tram ? 11.6 : 8.8, width: L.tram ? 2.4 : 2.55 });
          if (i === 0 || i === L.mods - 1) this.display(L, tpl.matrix, i === 0);
        }
      }
    }
    for (const [name, im] of this.modMesh) { im.count = modCount.get(name) ?? 0; im.instanceMatrix.needsUpdate = true; }
    this.meshes.tram.forEach((m, i) => { m.count = cn.tram[i]; m.instanceMatrix.needsUpdate = true; });
    this.meshes.bus.forEach((m, i) => { m.count = cn.bus[i]; m.instanceMatrix.needsUpdate = true; });
    for (let i = this.nDisp; i < this.displays.length; i++) this.displays[i].visible = false;
  }

  /** Place each module of a vehicle along the line; front tip at arc position sh. */
  private placeModels(L: Line, sh: number, spec: VehicleSpec, count: Map<string, number>) {
    const p = [0, 0], q = [0, 0], r = [0, 0];
    spec.sequence.forEach((it, i) => {
      const im = this.modMesh.get(it.module), len = this.modLen.get(it.module) ?? 6;
      if (!im) return;
      const sc = sh - it.z_center_from_front, half = len / 2;
      this.sample(L, sc, p); this.sample(L, sc + half, q); this.sample(L, sc - half, r);
      const hx = q[0] - r[0], hy = q[1] - r[1], hd = Math.hypot(hx, hy) || 1, ux = hx / hd, uy = hy / hd;
      const gf = this.ground(p[0] + ux * half, p[1] + uy * half), gb = this.ground(p[0] - ux * half, p[1] - uy * half);
      tpl.position.set(p[0], this.ground(p[0], p[1]) - ROAD_DROP, -p[1]);
      tpl.rotation.set(Math.atan2(gf - gb, len), Math.atan2(-hx, hy) + (it.rotateY180 ? Math.PI : 0), 0, 'YXZ');
      tpl.updateMatrix();
      const n = count.get(it.module) ?? 0;
      if (n < 24) { im.setMatrixAt(n, tpl.matrix); count.set(it.module, n + 1); }
      this.cols.push({ x: p[0], y: p[1], heading: Math.atan2(hy, hx), len, width: L.tram ? 2.4 : 2.55 });
      const last = i === spec.sequence.length - 1;
      if (i === 0 || (last && L.tram)) this.displayAt(L, tpl.matrix, half - 0.25, L.tram ? 2.85 : 2.75);
    });
  }

  private displayAt(L: Line, m: THREE.Matrix4, zFront: number, y: number) {
    let d = this.displays[this.nDisp];
    if (!d) {
      d = new THREE.Mesh(new THREE.PlaneGeometry(1.5, 0.45)); d.matrixAutoUpdate = false; d.frustumCulled = false;
      this.group.add(d); this.displays.push(d);
    }
    this.nDisp++;
    d.visible = true; d.material = L.label;
    d.matrix.copy(m).multiply(new THREE.Matrix4().makeTranslation(0, y, -zFront)).multiply(new THREE.Matrix4().makeRotationY(Math.PI));
  }

  private display(L: Line, m: THREE.Matrix4, front: boolean) {
    let d = this.displays[this.nDisp];
    if (!d) {
      const g = new THREE.PlaneGeometry(1.5, 0.56);
      d = new THREE.Mesh(g); d.matrixAutoUpdate = false; d.frustumCulled = false;
      this.group.add(d); this.displays.push(d);
    }
    this.nDisp++;
    d.visible = true; d.material = L.label;
    if (!L.tram && !front) { d.visible = false; return; } // bus rear end has no display
    const zOff = (L.tram ? 6.95 : 4.46) * (front ? -1 : 1);
    const loc = new THREE.Matrix4().makeTranslation(0, L.tram ? 2.3 : 2.5, zOff);
    if (front) loc.multiply(new THREE.Matrix4().makeRotationY(Math.PI));
    d.matrix.copy(m).multiply(loc);
  }

  colliders(): TransitCollider[] { return this.cols; }

  /** Number of vehicles rendered in the last update (for debugging). */
  get visible(): number { return this.vis; }
}
