import * as THREE from 'three';
import { AUTUMN, CLASSES, models, treeMaterial, treeTime } from './trees';
import { IMP_H, IMP_W, IMP_Y0, bakeImpostors } from './tree_impostor';
import { buildGrates } from './tree_grates';

/**
 * All trees of all loaded tiles in one field, re-bucketed by distance to the player (every ~0.25 s / 4 m):
 * LOD0 detailed leaf-card model (2 variants), LOD1 simplified model, LOD2 camera-facing impostor (ONE draw call for all classes).
 * Rows: [x, y, z, cls, crown, height, crown-base fraction, flags (1 street tree, 2 +guard), pit angle].
 */
type Tree = { x: number; y: number; z: number; cls: number; crown: number; h: number; base: number; flags: number; rot: number;
  v: number; aut: number; hue: number; ph: number; row: number[] };
const hash = (x: number, y: number, k: number) => { const s = Math.sin(x * 12.9898 + y * 78.233 + k * 37.719) * 43758.5453; return s - Math.floor(s); };
const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), sc = new THREE.Vector3(), Y = new THREE.Vector3(0, 1, 0);

class Pool {
  mesh: THREE.InstancedMesh | null = null; cap = 0; attr!: THREE.InstancedBufferAttribute; extra?: THREE.InstancedBufferAttribute;
  constructor(readonly geo: THREE.BufferGeometry, readonly mat: THREE.Material, readonly group: THREE.Group, readonly shadow: boolean, readonly withCls = false) {}
  ensure(n: number) {
    if (n <= this.cap && this.mesh) return;
    if (this.mesh) { this.group.remove(this.mesh); this.mesh.dispose(); }
    this.cap = Math.max(24, Math.ceil(n * 1.4));
    this.attr = new THREE.InstancedBufferAttribute(new Float32Array(this.cap * 4), 4);
    this.attr.setUsage(THREE.DynamicDrawUsage);
    this.geo.setAttribute('iTree', this.attr);
    if (this.withCls) { this.extra = new THREE.InstancedBufferAttribute(new Float32Array(this.cap), 1); this.geo.setAttribute('iCls', this.extra); }
    this.mesh = new THREE.InstancedMesh(this.geo, this.mat, this.cap);
    this.mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    this.mesh.frustumCulled = false;
    this.mesh.castShadow = this.shadow;
    this.mesh.count = 0;
    this.group.add(this.mesh);
  }
  set(i: number, t: Tree, imp = false) {
    const m = this.mesh!;
    if (imp) {
      p.set(t.x, t.z + IMP_Y0 * t.h, -t.y); sc.set(t.crown * IMP_W, t.h * IMP_H, 1); q.identity();
      this.extra!.setX(i, t.cls);
    } else {
      p.set(t.x, t.z, -t.y); sc.set(t.crown, t.h, t.crown); q.setFromAxisAngle(Y, hash(t.x, t.y, 1) * 6.283);
    }
    m.setMatrixAt(i, m4.compose(p, q, sc));
    this.attr.setXYZW(i, t.base, t.aut, t.hue, t.ph);
  }
  done(n: number) {
    const m = this.mesh!; m.count = n; m.instanceMatrix.needsUpdate = true; this.attr.needsUpdate = true;
    if (this.extra) this.extra.needsUpdate = true;
  }
}

export class TreeField {
  readonly group = new THREE.Group();
  nearR = 60; midR = 150; farR = 420;
  private tiles = new Map<string, Tree[]>();
  private all: Tree[] = [];
  private dirty = true;
  private px = 1e9;
  private py = 1e9;
  private last = 0;
  private pools = new Map<string, Pool>();
  private imp: Pool | null = null;
  private grates = buildGrates();
  shadows = false;
  private variants = 2;   // phones: 1 detail variant per class (fewer draw calls)

  constructor() { this.group.name = 'treefield'; this.group.add(this.grates.group); }

  /** Bake the impostor sheet (needs the renderer). */
  init(renderer: THREE.WebGLRenderer, mobile: boolean, shadows: boolean) {
    this.shadows = shadows; this.variants = mobile ? 1 : 2;
    this.nearR = mobile ? 55 : 90; this.midR = mobile ? 140 : 210; this.farR = mobile ? 380 : 520;
    const tex = bakeImpostors(renderer);
    const g = new THREE.PlaneGeometry(1, 1).translate(0, 0.5, 0);
    this.imp = new Pool(g, treeMaterial(0, tex), this.group, false, true);
  }

  add(tile: string, rows: number[][]) {
    this.tiles.set(tile, rows.map((r) => {
      const cls = Math.min(CLASSES.length - 1, Math.max(0, r[3] | 0));
      const [ab, hb] = AUTUMN[cls];
      return { x: r[0], y: r[1], z: r[2], cls, crown: r[4], h: r[5], base: r[6] ?? .3, flags: r[7] ?? 0, rot: r[8] ?? 0, row: r,
        v: Math.floor(hash(r[0], r[1], 2) * 2), aut: Math.min(.95, ab * (.25 + 1.3 * hash(r[0], r[1], 3))),
        hue: Math.min(1, Math.max(0, hb + (hash(r[0], r[1], 4) - .5) * .5)), ph: hash(r[0], r[1], 5) };
    }));
    this.dirty = true;
  }
  remove(tile: string) { if (this.tiles.delete(tile)) this.dirty = true; }

  private pool(key: string, cls: number, v: number, lod: number): Pool | null {
    let pl = this.pools.get(key);
    if (!pl) {
      const m = lod ? models[cls].lod1 ?? models[cls].lod0[0] : models[cls].lod0[v] ?? models[cls].lod0[0];
      if (!m) return null;
      pl = new Pool(m.geo.clone(), treeMaterial(m.zb), this.group, !lod && this.shadows);
      this.pools.set(key, pl);
    }
    return pl;
  }

  update(x: number, y: number) {
    treeTime.value = performance.now() / 1000;
    const now = performance.now();
    if (!this.dirty && (Math.hypot(x - this.px, y - this.py) < 4 || now - this.last < 250)) return;
    if (this.dirty) { this.all = [...this.tiles.values()].flat(); this.dirty = false; }
    this.px = x; this.py = y; this.last = now;
    const buckets = new Map<string, Tree[]>(), far: Tree[] = [], pit: Tree[] = [];
    const r0 = this.nearR ** 2, r1 = this.midR ** 2, r2 = this.farR ** 2;
    for (const t of this.all) {
      const d = (t.x - x) ** 2 + (t.y - y) ** 2;
      if (d > r2) continue;
      if (d < r0) {
        const k = `${t.cls}_${t.v % this.variants}_0`;
        (buckets.get(k) ?? buckets.set(k, []).get(k)!).push(t);
        if (t.flags && d < 45 * 45) pit.push(t);
      } else if (d < r1) {
        const k = `${t.cls}_0_1`;
        (buckets.get(k) ?? buckets.set(k, []).get(k)!).push(t);
      } else far.push(t);
    }
    for (const [k, list] of buckets) {
      const [cls, v, lod] = k.split('_').map(Number);
      const pl = this.pool(k, cls, v, lod);
      if (!pl) continue;
      pl.ensure(list.length);
      list.forEach((t, i) => pl.set(i, t));
      pl.done(list.length);
    }
    for (const [k, pl] of this.pools) if (!buckets.has(k) && pl.mesh) pl.mesh.count = 0;
    if (this.imp) {
      this.imp.ensure(far.length || 1);
      far.forEach((t, i) => this.imp!.set(i, t, true));
      this.imp.done(far.length);
    }
    this.grates.set(pit);
  }
}

export const treeField = new TreeField();
