import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { tramModule, busModule, tramType, labelMat } from './transit_geo';

const RANGE = 450, DWELL = 20, ROAD_DROP = 0.12;

/** Trams and buses on the real OSM lines (pipeline/transit.py). Positions are a pure function of game time. */
export interface Stop { name: string; s: number }
interface LineJson { ref: string; mode: 'tram' | 'bus' | 'trolleybus'; colour: string; dir: number; pts: number[][]; stops: Stop[]; z?: (number | null)[] }
interface Seg { s0: number; s1: number; t0: number; T: number; es: boolean; ee: boolean }
export interface Line {
  ref: string; dest: string; stops: Stop[]; tram: boolean; pts: number[][]; cum: number[]; segs: Seg[]; trip: number; offset: number; len: number;
  pitch: number; mods: number; speed: number; label: THREE.Material; trolley: boolean;
  /** bridge deck height per point (null = terrain), from pipeline/transit.py */
  zs?: (number | null)[];
}
export interface TransitCollider { x: number; y: number; heading: number; len: number; width: number }
/** A scheduled vehicle the player can take (or the one left standing after leaving it). */
export interface VehicleHandle { key: string; li: number; k: number; tram: boolean; sh: number; v: number; spec: string; d: number; parked: boolean }
/** The vehicle driven by (or parked after) the player: drawn by Transit from line index + front-tip arc position. */
export interface Driven { li: number; key: string; s: number; spec: string; doors: boolean; active: boolean }

const tpl = new THREE.Object3D();
tpl.rotation.order = 'YXZ';

export interface SeqItem { module: string; rotateY180: number; z_center_from_front: number }
export interface VehicleSpec { length: number; sequence: SeqItem[] }

export class Transit {
  /** Blender-built VBZ modules (pipeline/transit_models); falls back to box modules until loaded. */
  private modMesh = new Map<string, THREE.InstancedMesh>();
  private modLen = new Map<string, number>();
  private vehicles: Record<string, VehicleSpec> = {};
  readonly group = new THREE.Group();
  private nightU = { value: 0 };
  /** 0..1 night amount (lit interiors). */
  set night(v: number) { this.nightU.value = v; }
  /** Called when a tram/bus near the player pulls away from a stop (audio bell). */
  onBell: (() => void) | null = null;
  private bellT = 0;
  private modDoors = new Map<string, { r: number[]; l: number[] }>();
  private doorMesh!: THREE.InstancedMesh;
  private paxBody!: THREE.InstancedMesh;
  private paxHead!: THREE.InstancedMesh;
  private nDoor = 0;
  private nPax = 0;
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
  /** Trips taken out of the schedule (`li:k`), the driven/parked one, and vehicles near the player (pooled). */
  private taken = new Set<string>();
  driven: Driven | null = null;
  private near: { li: number; k: number; sh: number }[] = [];
  private nNear = 0;
  private lastTime = 0;

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
    this.doorMesh = new THREE.InstancedMesh(new THREE.PlaneGeometry(1.2, 1.9).translate(0, 1.3, 0),
      new THREE.MeshBasicMaterial({ color: 0xf2e6c0, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2 }), 48);
    this.paxBody = new THREE.InstancedMesh(new THREE.BoxGeometry(0.38, 0.95, 0.24).translate(0, 0.95, 0), new THREE.MeshLambertMaterial({ color: 0xffffff }), 48);
    this.paxHead = new THREE.InstancedMesh(new THREE.BoxGeometry(0.2, 0.22, 0.2).translate(0, 1.55, 0), new THREE.MeshLambertMaterial({ color: 0xd9a88a }), 48);
    for (const m of [this.doorMesh, this.paxBody, this.paxHead]) { m.frustumCulled = false; m.count = 0; this.group.add(m); }
    scene.add(this.group);
  }

  async loadModels(base = '/models/transit'): Promise<void> {
    const man = await (await fetch(`${base}/manifest.json`)).json() as { modules: Record<string, { file: string; length: number }>; vehicles: Record<string, VehicleSpec> };
    const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
    for (const [n, m] of Object.entries(man.modules as Record<string, { doors_r?: number[]; doors_l?: number[] }>)) this.modDoors.set(n, { r: m.doors_r ?? [], l: m.doors_l ?? [] });
    const mat = new THREE.MeshLambertMaterial({ vertexColors: true });
    // night: dark window panels glow warm (lit interior)
    mat.onBeforeCompile = (sh) => {
      sh.uniforms.uTrNight = this.nightU;
      sh.fragmentShader = 'uniform float uTrNight;\n' + sh.fragmentShader.replace('#include <color_fragment>',
        '#include <color_fragment>\nfloat trWin = step(1.35 * vColor.r, vColor.b) * step(0.09, vColor.b) * step(vColor.b, 0.4) * step(vColor.r, 0.15);\n')
        .replace('#include <opaque_fragment>', 'outgoingLight += trWin * uTrNight * vec3(0.95, 0.78, 0.45) * 0.38;\n#include <opaque_fragment>');
    };
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
    return { ref: l.ref, dest: l.stops.length ? l.stops[l.stops.length - 1].name : '', stops: l.stops, tram, pts: l.pts, cum, segs, trip: t, offset: h % this.headway, len, pitch, mods, speed, label: labelMat(l.ref, l.stops.length ? l.stops[l.stops.length - 1].name : ''), trolley: l.mode === 'trolleybus', zs: l.z };
  }

  /** Front-tip arc position at trip time tau (s), or -1 if not on the line. */
  private dwellU = -1;
  private arc(L: Line, tau: number): number {
    this.dwellU = -1;
    if (tau < 0 || tau > L.trip) return -1;
    let prev: Seg | null = null;
    for (const g of L.segs) {
      if (tau > g.t0 + g.T) { prev = g; continue; } // after this segment (dwell or later)
      if (tau < g.t0) { if (prev && prev.ee) this.dwellU = (tau - prev.t0 - prev.T) / DWELL; return g.s0; }
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
    const z0 = L.zs?.[i], z1 = L.zs?.[i + 1];   // deck height on bridges, NaN = terrain
    out[2] = z0 == null && z1 == null ? NaN : z0 == null ? z1! : z1 == null ? z0 : z0 + (z1 - z0) * Math.min(1, Math.max(0, t));
  }

  update(_dt: number, gameMinutes: number, px: number, py: number): void {
    const time = (gameMinutes * 60) / this.timeScale;
    this.cols.length = 0; this.nNear = 0; this.lastTime = time; this.nDisp = 0; this.vis = 0; this.nDoor = 0; this.nPax = 0; this.bellT -= _dt;
    const cn = { tram: [0, 0, 0], bus: [0, 0] };
    const modCount = new Map<string, number>();
    const p = [0, 0, NaN], q = [0, 0, NaN], r = [0, 0, NaN];
    for (let li = 0; li < this.lines.length; li++) {
      const L = this.lines[li];
      const k0 = Math.ceil((time - L.offset - L.trip) / this.headway), k1 = Math.floor((time - L.offset) / this.headway);
      for (let k = k0; k <= k1; k++) {
        if (this.taken.size && this.taken.has(`${li}:${k}`)) continue;
        const sh = this.arc(L, time - L.offset - k * this.headway);
        if (sh < 0) continue;
        this.sample(L, sh - (L.pitch * L.mods) / 2, p);
        if (Math.hypot(p[0] - px, p[1] - py) > RANGE) continue;
        this.vis++;
        if (Math.hypot(p[0] - px, p[1] - py) < 70 && this.nNear < 16) {
          const nr = this.near[this.nNear] ?? (this.near[this.nNear] = { li: 0, k: 0, sh: 0 });
          nr.li = li; nr.k = k; nr.sh = sh; this.nNear++;
        }
        const kinds = L.tram ? cn.tram : cn.bus;
        const im = L.tram ? this.meshes.tram : this.meshes.bus;
        const half = L.tram ? 6.1 : 4.5;
        const spec = this.modMesh.size ? this.vehicles[this.specName(L, k)] : undefined;
        if (spec) { this.placeModels(L, sh, spec, modCount, this.dwellU, px, py); continue; }
        for (let i = 0; i < L.mods; i++) {
          const sc = sh - (L.tram ? 7.0 : 5.0) - i * L.pitch + (L.tram ? 0.2 : 0.5);
          this.sample(L, sc, p); this.sample(L, sc + 4, q); this.sample(L, sc - 4, r);
          const hx = q[0] - r[0], hy = q[1] - r[1];
          const yaw = Math.atan2(-hx, hy);
          const hd = Math.hypot(hx, hy) || 1, ux = hx / hd, uy = hy / hd;
          const deck = !Number.isNaN(p[2]);
          const gf = deck ? q[2] : this.ground(p[0] + ux * half, p[1] + uy * half), gb = deck ? r[2] : this.ground(p[0] - ux * half, p[1] - uy * half);
          const gz = deck ? p[2] : this.ground(p[0], p[1]) - ROAD_DROP;
          tpl.position.set(p[0], gz, -p[1]);
          tpl.rotation.set(deck ? (Number.isNaN(gf + gb) ? 0 : Math.atan2(gf - gb, 8)) : Math.atan2(gf - gb, half * 2), yaw, 0);
          tpl.updateMatrix();
          const kind = L.tram ? (i === 0 ? 0 : i === L.mods - 1 ? 2 : 1) : (i === 0 ? 0 : 1);
          const mesh = im[kind];
          if (kinds[kind] < 24) mesh.setMatrixAt(kinds[kind]++, tpl.matrix);
          this.cols.push({ x: p[0], y: p[1], heading: Math.atan2(hy, hx), len: L.tram ? 11.6 : 8.8, width: L.tram ? 2.4 : 2.55 });
          if (i === 0 || i === L.mods - 1) this.display(L, tpl.matrix, i === 0);
        }
      }
    }
    this.updateDriven(modCount, px, py);
    this.doorMesh.count = this.nDoor; this.doorMesh.instanceMatrix.needsUpdate = true;
    this.paxBody.count = this.paxHead.count = this.nPax;
    this.paxBody.instanceMatrix.needsUpdate = this.paxHead.instanceMatrix.needsUpdate = true;
    if (this.paxBody.instanceColor) this.paxBody.instanceColor.needsUpdate = true;
    for (const [name, im] of this.modMesh) { im.count = modCount.get(name) ?? 0; im.instanceMatrix.needsUpdate = true; }
    this.meshes.tram.forEach((m, i) => { m.count = cn.tram[i]; m.instanceMatrix.needsUpdate = true; });
    this.meshes.bus.forEach((m, i) => { m.count = cn.bus[i]; m.instanceMatrix.needsUpdate = true; });
    for (let i = this.nDisp; i < this.displays.length; i++) this.displays[i].visible = false;
  }

  specName(L: Line, k: number): string { return L.tram ? tramType(L.ref, k) : L.trolley ? 'trolleybus' : 'bus_gelenk'; }
  spec(name: string): VehicleSpec | undefined { return this.vehicles[name]; }
  line(li: number): Line { return this.lines[li]; }
  /** Geometry of a Blender module (shared; do not dispose) for rigs that carry it around, e.g. the driven bus. */
  moduleGeometry(name: string): THREE.BufferGeometry | undefined { return this.modMesh.get(name)?.geometry; }
  moduleLength(name: string): number { return this.modLen.get(name) ?? 6; }
  labelMaterial(li: number): THREE.Material { return this.lines[li].label; }

  private static readonly PA = [0, 0, NaN];
  private static readonly PB = [0, 0, NaN];
  /** Pose at arc position s: out = [x, y, z (deck height or terrain), compass heading]. */
  poseAt(li: number, s: number, out: number[]) {
    const L = this.lines[li], a = Transit.PA, b = Transit.PB;
    this.sample(L, s, a); this.sample(L, s + 1.5, b);
    this.sample(L, s - 1.5, out);
    out[3] = Math.atan2(b[0] - out[0], b[1] - out[1]);
    out[0] = a[0]; out[1] = a[1]; out[2] = Number.isNaN(a[2]) ? this.ground(a[0], a[1]) - ROAD_DROP : a[2];
  }

  /** Nearest rendered vehicle whose body is within `reach` metres of (x, y), or the one parked by the player. */
  nearestVehicle(x: number, y: number, reach: number): VehicleHandle | null {
    let best: VehicleHandle | null = null, bd = reach + 1.3; // 1.3 = half vehicle width
    const p = [0, 0, NaN];
    const dist = (L: Line, sh: number, len: number) => {
      let m = Infinity;
      for (let o = 0.5; o < len; o += 3) { this.sample(L, sh - o, p); m = Math.min(m, Math.hypot(p[0] - x, p[1] - y)); }
      return m;
    };
    for (let i = 0; i < this.nNear; i++) {
      const r = this.near[i], L = this.lines[r.li], name = this.specName(L, r.k), len = this.vehicles[name]?.length ?? (L.tram ? 37 : 18.5);
      const d = dist(L, r.sh, len);
      if (d >= bd) continue;
      bd = d;
      const tau = this.lastTime - L.offset - r.k * this.headway, v = (this.arc(L, tau + 0.5) - this.arc(L, tau - 0.5));
      best = { key: `${r.li}:${r.k}`, li: r.li, k: r.k, tram: L.tram, sh: r.sh, v: v > 0 && v < 20 ? v : 0, spec: name, d: d - 1.3, parked: false };
    }
    const dr = this.driven;
    if (dr && !dr.active) {
      const L = this.lines[dr.li], len = this.vehicles[dr.spec]?.length ?? 37, d = dist(L, dr.s, len);
      if (d < bd) best = { key: dr.key, li: dr.li, k: 0, tram: L.tram, sh: dr.s, v: 0, spec: dr.spec, d: d - 1.3, parked: true };
    }
    return best;
  }

  /** Remove the trip from the schedule (the caller now draws and drives it). */
  take(h: VehicleHandle) { if (!h.parked) this.taken.add(h.key); }
  /** Give the trip back to the schedule once it is far away. */
  release(key: string) { this.taken.delete(key); if (this.driven?.key === key) this.driven = null; }

  private updateDriven(modCount: Map<string, number>, px: number, py: number) {
    const d = this.driven;
    if (!d) return;
    const spec = this.vehicles[d.spec];
    if (!spec || !this.modMesh.size) return;
    if (!d.active) { // left standing: give the trip back once the player is far away
      const q = [0, 0, NaN];
      this.sample(this.lines[d.li], d.s - 10, q);
      if (Math.hypot(q[0] - px, q[1] - py) > 300) { this.release(d.key); return; }
    }
    const n0 = this.cols.length;
    this.vis++;
    this.placeModels(this.lines[d.li], d.s, spec, modCount, d.doors ? 0.3 : -1, px, py);
    if (d.active) this.cols.length = n0; // the player's own vehicle is no obstacle for itself
  }

  /** Place each module of a vehicle along the line; front tip at arc position sh. */
  private placeModels(L: Line, sh: number, spec: VehicleSpec, count: Map<string, number>, du: number, px: number, py: number) {
    const p = [0, 0, NaN], q = [0, 0, NaN], r = [0, 0, NaN];
    spec.sequence.forEach((it, i) => {
      const im = this.modMesh.get(it.module), len = this.modLen.get(it.module) ?? 6;
      if (!im) return;
      const sc = sh - it.z_center_from_front, half = len / 2;
      this.sample(L, sc, p); this.sample(L, sc + half, q); this.sample(L, sc - half, r);
      const hx = q[0] - r[0], hy = q[1] - r[1], hd = Math.hypot(hx, hy) || 1, ux = hx / hd, uy = hy / hd;
      const deck = !Number.isNaN(p[2]);
      const gf = deck ? q[2] : this.ground(p[0] + ux * half, p[1] + uy * half), gb = deck ? r[2] : this.ground(p[0] - ux * half, p[1] - uy * half);
      tpl.position.set(p[0], deck ? p[2] : this.ground(p[0], p[1]) - ROAD_DROP, -p[1]);
      tpl.rotation.set(deck && Number.isNaN(gf + gb) ? 0 : Math.atan2(gf - gb, len), Math.atan2(-hx, hy) + (it.rotateY180 ? Math.PI : 0), 0, 'YXZ');
      tpl.updateMatrix();
      const n = count.get(it.module) ?? 0;
      if (n < 24) { im.setMatrixAt(n, tpl.matrix); count.set(it.module, n + 1); }
      this.cols.push({ x: p[0], y: p[1], heading: Math.atan2(hy, hx), len, width: L.tram ? 2.4 : 2.55 });
      if (du > 0.06 && du < 0.94) this.openDoors(it, tpl.matrix, du, Math.hypot(p[0] - px, p[1] - py) < 90);
      else if (du >= 0.94 && this.bellT <= 0 && L.tram && Math.hypot(p[0] - px, p[1] - py) < 45) { this.bellT = 6; this.onBell?.(); }
      const last = i === spec.sequence.length - 1;
      if (i === 0 || (last && L.tram)) this.displayAt(L, tpl.matrix, half - 0.25, L.tram ? 2.85 : 2.75);
    });
  }

  private static readonly TMP = new THREE.Matrix4();
  private static readonly TQ = new THREE.Quaternion();
  private static readonly TS = new THREE.Vector3(1, 1, 1);
  private static readonly TV = new THREE.Vector3();
  /** Lit door openings on the right side and a few passengers stepping off (first half) or on (second half). */
  private openDoors(it: SeqItem, m: THREE.Matrix4, du: number, near: boolean) {
    const d = this.modDoors.get(it.module); if (!d) return;
    const flip = !!it.rotateY180, list = flip ? d.l : d.r, hx = it.module.startsWith('bus') || it.module.startsWith('trolley') ? 1.29 : 1.2;
    const side = flip ? -1 : 1, T = Transit.TMP, Q = Transit.TQ, V = Transit.TV;
    for (const zd of list) {
      if (this.nDoor >= 48) return;
      const zz = flip ? -zd : zd;  // flipped module: local z mirrored when expressed in vehicle frame is handled by matrix; keep local coords
      void zz;
      const lz = zd, lx = side * (hx + 0.02);
      T.copy(m).multiply(new THREE.Matrix4().makeTranslation(lx, 0, lz)).multiply(new THREE.Matrix4().makeRotationY(Math.PI / 2));
      this.doorMesh.setMatrixAt(this.nDoor++, T);
      if (!near || this.nPax >= 47) continue;
      const out = du < 0.5, u = out ? du / 0.5 : (1 - du) / 0.5;      // 0 at door, 1 at waiting spot
      const dist = 0.3 + Math.min(1, Math.max(0, u)) * 2.2, lat = (lz > 0 ? 0.5 : -0.5) * Math.min(1, u) + (this.nPax % 2 ? 0.2 : -0.2);
      const k = Math.abs(Math.sin(lz * 12.9 + this.nDoor)) ;
      if (k < 0.25) continue;
      V.set(side * (hx + dist), 0, lz + lat).applyMatrix4(m);
      Q.identity(); T.compose(V, Q, Transit.TS);
      this.paxBody.setMatrixAt(this.nPax, T); this.paxHead.setMatrixAt(this.nPax, T);
      this.paxBody.setColorAt(this.nPax, Transit.PAX.setHSL((k * 7) % 1, 0.35, 0.3 + 0.25 * k));
      this.nPax++;
    }
  }
  private static readonly PAX = new THREE.Color();

  private displayAt(L: Line, m: THREE.Matrix4, zFront: number, y: number) {
    let d = this.displays[this.nDisp];
    if (!d) {
      d = new THREE.Mesh(new THREE.PlaneGeometry(1.7, 0.64)); d.matrixAutoUpdate = false; d.frustumCulled = false;
      this.group.add(d); this.displays.push(d);
    }
    this.nDisp++;
    d.visible = true; d.material = L.label;
    d.matrix.copy(m).multiply(new THREE.Matrix4().makeTranslation(0, y, -zFront)).multiply(new THREE.Matrix4().makeRotationY(Math.PI));
  }

  private display(L: Line, m: THREE.Matrix4, front: boolean) {
    let d = this.displays[this.nDisp];
    if (!d) {
      const g = new THREE.PlaneGeometry(1.7, 0.64);
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
