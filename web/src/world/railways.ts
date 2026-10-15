import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

/**
 * Railway layer: per-tile track/mast/platform meshes (pipeline/railways.py), catenary wires, station signs and
 * S-Bahn trains on the OSM tracks. Per tile: 1 mesh (world material) + 1 wire LineSegments + 1 sign mesh = 3 draw calls.
 * Train positions are a pure function of game time (like Transit).
 */
interface TileData { wr?: number[][]; sg?: number[][]; glb?: number }
interface RouteJson { name: string; dir: number; len: number; stops: { name: string; s: number }[]; pts: number[] }
interface RailJson { tile: number; stations: string[]; tiles: Record<string, TileData>; routes: RouteJson[] }
interface Seg { s0: number; s1: number; t0: number; T: number; es: boolean; ee: boolean }
interface Route { j: RouteJson; x: Float32Array; y: Float32Array; z: Float32Array; cum: Float32Array; segs: Seg[]; trip: number; offset: number; headway: number }
export interface RailCollider { x: number; y: number; heading: number; len: number; width: number }

const LOAD_R = 420, UNLOAD_R = 560, TRAIN_RANGE = 700, DWELL = 30, SPEED = 22, CARS = 5, CAR_L = 26.4, RAIL_TOP = 0.2, WIRE = 5.5 + 0.29, SPAN = 60;
const tpl = new THREE.Object3D(); tpl.rotation.order = 'YXZ';

function wireGeo(runs: number[][]): THREE.BufferGeometry {
  const v: number[] = [];
  for (const r of runs) {
    const n = r.length / 3;
    let s = 0, px = 0, py = 0, pc: number[] | null = null, pm: number[] | null = null;
    for (let i = 0; i < n; i++) {
      const x = r[i * 3] / 10, y = r[i * 3 + 1] / 10, z = r[i * 3 + 2] / 10;
      if (i > 0) s += Math.hypot(x - px, y - py);
      const a = Math.max(0, i - 1), b = Math.min(n - 1, i + 1);
      let tx = r[b * 3] - r[a * 3], ty = r[b * 3 + 1] - r[a * 3 + 1];
      const tl = Math.hypot(tx, ty) || 1; tx /= tl; ty /= tl;
      const f = (s % SPAN) / SPAN, zig = 0.2 * (Math.floor(s / SPAN) % 2 ? -1 : 1) * (1 - 2 * f);
      const zc = z + WIRE;
      const c = [x - ty * zig, zc, -(y + tx * zig)], m = [x, zc + 1.4 - (1 - (2 * f - 1) ** 2), -y];
      if (pc && pm) { v.push(...pc, ...c, ...pm, ...m); if (i % 3 === 1) v.push(...c, ...m); }
      pc = c; pm = m; px = x; py = y;
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(v, 3));
  return g;
}

export class Railways {
  readonly group = new THREE.Group();
  private data: RailJson | null = null;
  private tiles = new Map<string, THREE.Group>();
  private pending = new Set<string>();
  private loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  private wireMat = new THREE.LineBasicMaterial({ color: 0x2a2d31 });
  private signMat: THREE.MeshBasicMaterial | null = null;
  private routes: Route[] = [];
  private head: THREE.InstancedMesh | null = null;
  private mid: THREE.InstancedMesh | null = null;
  private cols: RailCollider[] = [];

  /** worldMat: the shared tile material (texture array); falls back to plain vertex colours. */
  constructor(scene: THREE.Scene, private worldMat?: THREE.Material, private reach = 1, private base = '/models/trains') {
    scene.add(this.group);
  }

  async load(): Promise<void> {
    this.data = await (await fetch('/data/rail.json')).json() as RailJson;
    this.routes = this.data.routes.map((r) => this.prep(r));
    this.signMat = new THREE.MeshBasicMaterial({ map: this.atlas(this.data.stations), side: THREE.DoubleSide });
    const man = await (await fetch(`${this.base}/manifest.json`)).json() as { modules: Record<string, { file: string }> };
    const mat = new THREE.MeshLambertMaterial({ vertexColors: true });
    const mk = async (name: string) => {
      const g = await this.loader.loadAsync(`${this.base}/${man.modules[name].file}`);
      const parts: THREE.BufferGeometry[] = [];
      g.scene.updateMatrixWorld(true);
      g.scene.traverse((o) => {
        const m = o as THREE.Mesh;
        if (!m.isMesh) return;
        const geo = (m.geometry.clone().applyMatrix4(m.matrixWorld));
        const ng = geo.index ? geo.toNonIndexed() : geo;
        const out = new THREE.BufferGeometry(), n = ng.getAttribute('position').count;
        for (const [k, size] of [['position', 3], ['normal', 3], ['color', 3]] as const) {
          const a = ng.getAttribute(k), arr = new Float32Array(n * size);
          for (let i = 0; i < n; i++) for (let c = 0; c < size; c++) arr[i * size + c] = a ? a.getComponent(i, c) : 1;
          out.setAttribute(k, new THREE.BufferAttribute(arr, size));
        }
        parts.push(out);
      });
      const im = new THREE.InstancedMesh(mergeGeometries(parts)!, mat, 32);
      im.frustumCulled = false; im.count = 0; im.castShadow = true;
      this.group.add(im);
      return im;
    };
    [this.head, this.mid] = await Promise.all([mk('sbahn_head'), mk('sbahn_mid')]);
  }

  /** Canvas atlas: row 0 = station clock (no logo), rows 1.. = name boards (white on blue). */
  private atlas(names: string[]): THREE.Texture {
    const c = document.createElement('canvas'); c.width = 512; c.height = 64 * (names.length + 1);
    const x = c.getContext('2d')!;
    x.fillStyle = '#f4f4f2'; x.beginPath(); x.arc(32, 32, 30, 0, 7); x.fill();
    x.strokeStyle = '#111'; x.lineWidth = 3; x.stroke();
    x.lineWidth = 2; for (let i = 0; i < 12; i++) { const a = i * Math.PI / 6; x.beginPath(); x.moveTo(32 + Math.sin(a) * 25, 32 - Math.cos(a) * 25); x.lineTo(32 + Math.sin(a) * 29, 32 - Math.cos(a) * 29); x.stroke(); }
    x.lineWidth = 4; x.beginPath(); x.moveTo(32, 32); x.lineTo(32 + Math.sin(1.9) * 15, 32 - Math.cos(1.9) * 15); x.stroke();
    x.lineWidth = 3; x.beginPath(); x.moveTo(32, 32); x.lineTo(32 + Math.sin(0.2) * 24, 32 - Math.cos(0.2) * 24); x.stroke();
    x.strokeStyle = '#d2191f'; x.lineWidth = 1.5; x.beginPath(); x.moveTo(32, 32); x.lineTo(32 + Math.sin(3.5) * 26, 32 - Math.cos(3.5) * 26); x.stroke();
    names.forEach((n, i) => {
      const y = 64 * (i + 1);
      x.fillStyle = '#12408f'; x.fillRect(0, y, 512, 64);
      x.fillStyle = '#fff'; x.font = 'bold 34px sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle';
      x.fillText(n, 256, y + 33, 490);
    });
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
    return t;
  }

  private signMesh(list: number[][]): THREE.Mesh {
    const n = this.data!.stations.length, H = n + 1;
    const pos: number[] = [], uv: number[] = [], idx: number[] = [];
    for (const [x, y, z, yaw, name, kind] of list) {
      const w = kind ? 0.75 : 1.9, h = kind ? 0.75 : 0.6;
      const px = -Math.sin(yaw) * w / 2, py = Math.cos(yaw) * w / 2;
      const v0 = kind ? 1 - 1 / H : 1 - (name + 2) / H, v1 = kind ? 1 : 1 - (name + 1) / H, u1 = kind ? 64 / 512 : 1;
      const b = pos.length / 3;
      pos.push(x - px, z - h, -(y - py), x + px, z - h, -(y + py), x + px, z, -(y + py), x - px, z, -(y - py));
      uv.push(0, v0, u1, v0, u1, v1, 0, v1);
      idx.push(b, b + 1, b + 2, b, b + 2, b + 3);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
    g.setIndex(idx);
    return new THREE.Mesh(g, this.signMat!);
  }

  private async loadTile(key: string) {
    const d = this.data!.tiles[key];
    const g = new THREE.Group();
    if (d.glb) {
      const gl = await this.loader.loadAsync(`${this.base}/tiles/r_${key}.glb`);
      gl.scene.traverse((o) => {
        const m = o as THREE.Mesh;
        if (!m.isMesh) return;
        m.material = this.worldMat ?? new THREE.MeshLambertMaterial({ vertexColors: true });
        m.receiveShadow = true; m.matrixAutoUpdate = false; m.updateMatrix();
      });
      g.add(gl.scene);
    }
    if (d.wr) g.add(new THREE.LineSegments(wireGeo(d.wr), this.wireMat));
    if (d.sg) g.add(this.signMesh(d.sg));
    this.group.add(g);
    this.tiles.set(key, g);
    this.pending.delete(key);
  }

  private streamTiles(px: number, py: number) {
    if (!this.data) return;
    const T = this.data.tile;
    for (const key of Object.keys(this.data.tiles)) {
      const [ix, iy] = key.split('_').map(Number);
      const dist = Math.hypot((ix + 0.5) * T - px, (iy + 0.5) * T - py);
      if (dist < LOAD_R * this.reach && !this.tiles.has(key) && !this.pending.has(key)) { this.pending.add(key); void this.loadTile(key); }
      else if (dist > UNLOAD_R * this.reach && this.tiles.has(key)) {
        const g = this.tiles.get(key)!;
        this.group.remove(g);
        g.traverse((o) => { const m = o as THREE.Mesh; if (m.geometry) m.geometry.dispose(); });
        this.tiles.delete(key);
      }
    }
  }

  private prep(j: RouteJson): Route {
    const n = j.pts.length / 3, x = new Float32Array(n), y = new Float32Array(n), z = new Float32Array(n), cum = new Float32Array(n);
    for (let i = 0; i < n; i++) {
      x[i] = j.pts[i * 3] / 10; y[i] = j.pts[i * 3 + 1] / 10; z[i] = j.pts[i * 3 + 2] / 10;
      if (i) cum[i] = cum[i - 1] + Math.hypot(x[i] - x[i - 1], y[i] - y[i - 1]);
    }
    const vlen = CARS * CAR_L, len = cum[n - 1];
    const wp = [{ s: 0, stop: false }, ...j.stops.map((s) => ({ s: s.s + vlen / 2, stop: true })), { s: len + vlen, stop: false }];
    const segs: Seg[] = [];
    let t = 0;
    for (let i = 0; i < wp.length - 1; i++) {
      const d = wp[i + 1].s - wp[i].s;
      if (d <= 0.5) continue;
      const es = wp[i].stop, ee = wp[i + 1].stop;
      const T = d / (SPEED * (es && ee ? 0.75 : es || ee ? 0.85 : 1));
      segs.push({ s0: wp[i].s, s1: wp[i + 1].s, t0: t, T, es, ee });
      t += T + (ee ? DWELL : 0);
    }
    let h = 0;
    for (const ch of j.name + j.dir) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
    const headway = j.name.includes('Wiedikon') ? 270 : 240;
    return { j, x, y, z, cum, segs, trip: t, offset: h % headway, headway };
  }

  private arc(R: Route, tau: number): number {
    if (tau < 0 || tau > R.trip) return -1;
    for (const g of R.segs) {
      if (tau > g.t0 + g.T) continue;
      if (tau < g.t0) return g.s0;
      const u = (tau - g.t0) / g.T;
      const f = g.es && g.ee ? (1 - Math.cos(Math.PI * u)) / 2 : g.es ? 1 - Math.cos((Math.PI * u) / 2) : g.ee ? Math.sin((Math.PI * u) / 2) : u;
      return g.s0 + (g.s1 - g.s0) * f;
    }
    return R.segs[R.segs.length - 1].s1;
  }

  /** Position (x, y, z) at arc length s; extrapolates linearly beyond the ends. */
  private sample(R: Route, s: number, o: number[]) {
    const { cum } = R, n = cum.length;
    let i = 0;
    if (s >= cum[n - 1]) i = n - 2;
    else if (s > 0) { let lo = 0, hi = n - 1; while (hi - lo > 1) { const m = (lo + hi) >> 1; if (cum[m] <= s) lo = m; else hi = m; } i = lo; }
    const sl = Math.max(1e-6, cum[i + 1] - cum[i]), t = (s - cum[i]) / sl;
    o[0] = R.x[i] + (R.x[i + 1] - R.x[i]) * t; o[1] = R.y[i] + (R.y[i + 1] - R.y[i]) * t; o[2] = R.z[i] + (R.z[i + 1] - R.z[i]) * t;
  }

  colliders(): RailCollider[] { return this.cols; }

  update(_dt: number, gameMinutes: number, px: number, py: number): void {
    this.streamTiles(px, py);
    if (!this.head || !this.mid) return;
    this.cols.length = 0;
    let nh = 0, nm = 0;
    const time = gameMinutes * 60, a = [0, 0, 0], b = [0, 0, 0], c = [0, 0, 0];
    for (const R of this.routes) {
      const k0 = Math.ceil((time - R.offset - R.trip) / R.headway), k1 = Math.floor((time - R.offset) / R.headway);
      for (let k = k0; k <= k1; k++) {
        const tip = this.arc(R, time - R.offset - k * R.headway);
        if (tip < 0) continue;
        this.sample(R, tip - (CARS * CAR_L) / 2, a);
        if (Math.hypot(a[0] - px, a[1] - py) > TRAIN_RANGE + CARS * CAR_L / 2) continue;
        for (let i = 0; i < CARS; i++) {
          const sc = tip - CAR_L / 2 - i * CAR_L;
          this.sample(R, sc, a); this.sample(R, sc + 9, b); this.sample(R, sc - 9, c);
          const dx = b[0] - c[0], dy = b[1] - c[1], dz = b[2] - c[2], hd = Math.hypot(dx, dy) || 1;
          const tail = i === CARS - 1;
          tpl.position.set(a[0], a[2] + RAIL_TOP, -a[1]);
          tpl.rotation.set(Math.atan2(dz, hd), Math.atan2(-dx, dy) + (tail ? Math.PI : 0), 0);
          if (tail) tpl.rotation.x = -tpl.rotation.x;
          tpl.updateMatrix();
          if (i === 0 || tail) { if (nh < 32) this.head.setMatrixAt(nh++, tpl.matrix); }
          else if (nm < 32) this.mid.setMatrixAt(nm++, tpl.matrix);
          this.cols.push({ x: a[0], y: a[1], heading: Math.atan2(dx, dy), len: CAR_L, width: 2.9 });
        }
      }
    }
    this.head.count = nh; this.mid.count = nm;
    this.head.instanceMatrix.needsUpdate = true; this.mid.instanceMatrix.needsUpdate = true;
  }
}
