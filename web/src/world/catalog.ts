import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import type { Colliders } from '../player/collision';

/** Object catalog at runtime (pipeline/catalog/assign.py -> public/data/catalog.json, models in public/models/catalog/).
 *  Fountains (V1..V9) and stop equipment (H1..H7) as low-poly GLBs sharing one atlas. One InstancedMesh per variant and
 *  material (opaque / blend); only objects in chunks near the player are instanced, their collider circles are registered
 *  with the same chunk (and removed again). Row "o": [variant, x, y, yaw, sx, dy, kind]; kind 0 fountain, 1 stop object (platform z),
 *  2 kiosk with collider, 3 kiosk replacing a tile kiosk (details.ts skips it; the tile collider stays). */
const DIR = '/models/catalog';
const CHUNK = 64;
interface Row { v: string; x: number; y: number; yaw: number; sx: number; dy: number; kind: number }
interface VarInfo { file: string; radius: number }
interface Part { geo: THREE.BufferGeometry; blend: boolean }

let rows: Row[] = [];
let info: Record<string, VarInfo> = {};
const parts = new Map<string, Part[]>();
let atlas: THREE.Texture | null = null;
let ready = false;
const kiosks: Row[] = [];   // kind 3: queried by details.ts to drop the generic kiosk
const fountains = new Map<string, Row[]>();   // chunk key -> fountains (queried by props.ts / details.ts to drop the generic ones)
const key = (x: number, y: number) => `${Math.floor(x / CHUNK)},${Math.floor(y / CHUNK)}`;

/** Load catalog.json + GLBs once (phone: 256 px atlas). Never rejects: without catalog the generic objects stay. */
export async function loadCatalog(mobile: boolean): Promise<boolean> {
  if (new URLSearchParams(location.search).has('nocatalog')) return false;   // A/B for perf tests
  try {
    const [cat, idx] = await Promise.all([fetch('/data/catalog.json').then((r) => r.json()), fetch(`${DIR}/index.json`).then((r) => r.json())]);
    info = idx.variants;
    atlas = await new THREE.TextureLoader().loadAsync(`${DIR}/${mobile ? 'atlas_256.png' : 'atlas.png'}`);
    atlas.flipY = false; atlas.colorSpace = THREE.SRGBColorSpace; atlas.anisotropy = 4; atlas.generateMipmaps = true;
    const used = new Set<string>((cat.o as unknown[][]).map((r) => r[0] as string));
    const loader = new GLTFLoader();
    await Promise.all([...used].map(async (v) => {
      if (!info[v]) return;
      const g = await loader.loadAsync(`${DIR}/${info[v].file}`);
      const ps: Part[] = [];
      g.scene.updateMatrixWorld(true);
      g.scene.traverse((o) => {
        const m = o as THREE.Mesh;
        if (m.isMesh) ps.push({ geo: m.geometry, blend: (m.material as THREE.Material).transparent });
      });
      parts.set(v, ps);
    }));
    rows = (cat.o as number[][] & [string][]).map((r) => ({ v: r[0] as unknown as string, x: r[1], y: r[2], yaw: r[3], sx: r[4], dy: r[5], kind: r[6] }));
    rows = rows.filter((r) => parts.has(r.v));
    for (const r of rows) if (r.kind === 0) (fountains.get(key(r.x, r.y)) ?? fountains.set(key(r.x, r.y), []).get(key(r.x, r.y))!).push(r);
    for (const r of rows) if (r.kind === 3) kiosks.push(r);
    ready = true;
  } catch (e) { console.warn('catalog: not available, generic objects stay', e); ready = false; }
  return ready;
}

export const catalogReady = () => ready;
/** True when a catalog fountain stands within `r` metres: the generic fountain there is not drawn. */
export function catalogFountainNear(x: number, y: number, r = 3): boolean {
  if (!ready) return false;
  const cx = Math.floor(x / CHUNK), cy = Math.floor(y / CHUNK);
  for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++)
    for (const f of fountains.get(`${cx + i},${cy + j}`) ?? []) if (Math.hypot(f.x - x, f.y - y) <= r) return true;
  return false;
}

/** True when a catalog kiosk replaces the generic tile kiosk at (x, y). */
export function catalogKioskNear(x: number, y: number, r = 1.5): boolean {
  return ready && kiosks.some((k) => Math.hypot(k.x - x, k.y - y) <= r);
}

/** Height of the stop platform at (x, y); set by stops_equip.ts once its data is in (stop objects wait for it). */
let stopZ: ((x: number, y: number) => number) | null = null;
export function setCatalogStopZ(fn: (x: number, y: number) => number) { stopZ = fn; }

export class CatalogLayer {
  readonly group = new THREE.Group();
  private meshes = new Map<string, THREE.InstancedMesh[]>();
  private chunks = new Map<string, Row[]>();
  private active = new Set<string>();
  private lx = 1e9; private ly = 1e9; private hadStopZ = false;
  private mats: THREE.Material[] = [];
  private opaque: THREE.MeshLambertMaterial; private blend: THREE.MeshLambertMaterial;

  constructor(scene: THREE.Scene, private ground: (x: number, y: number) => number, private colliders: Colliders, private radius: number) {
    this.opaque = new THREE.MeshLambertMaterial({ map: atlas });
    this.blend = new THREE.MeshLambertMaterial({ map: atlas, transparent: true, depthWrite: false, side: THREE.DoubleSide });
    this.mats.push(this.opaque, this.blend);
    for (const r of rows) (this.chunks.get(key(r.x, r.y)) ?? this.chunks.set(key(r.x, r.y), []).get(key(r.x, r.y))!).push(r);
    const count = new Map<string, number>();
    for (const r of rows) count.set(r.v, (count.get(r.v) ?? 0) + 1);
    for (const [v, n] of count) {
      const ims = parts.get(v)!.map((p) => {
        const im = new THREE.InstancedMesh(p.geo, p.blend ? this.blend : this.opaque, n);
        im.count = 0; im.frustumCulled = false; im.matrixAutoUpdate = false; im.renderOrder = p.blend ? 1 : 0; im.visible = false;
        this.group.add(im);
        return im;
      });
      this.meshes.set(v, ims);
    }
    scene.add(this.group);
  }

  /** Call every frame: re-instances (cheap, a few hundred objects) after the player moved 16 m. */
  update(px: number, py: number) {
    const sz = stopZ !== null;
    if (Math.hypot(px - this.lx, py - this.ly) < 16 && sz === this.hadStopZ) return;
    this.lx = px; this.ly = py; this.hadStopZ = sz;
    const m = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), s = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0);
    const per = new Map<string, number>();
    const now = new Set<string>();
    const r = this.radius, c0x = Math.floor((px - r) / CHUNK), c1x = Math.floor((px + r) / CHUNK), c0y = Math.floor((py - r) / CHUNK), c1y = Math.floor((py + r) / CHUNK);
    for (let cx = c0x; cx <= c1x; cx++) for (let cy = c0y; cy <= c1y; cy++) {
      const k = `${cx},${cy}`, list = this.chunks.get(k);
      if (!list) continue;
      now.add(k);
      for (const o of list) {
        if (Math.hypot(o.x - px, o.y - py) > r) continue;
        if (o.kind === 1 && !sz) continue;
        const z = (o.kind === 1 ? stopZ!(o.x, o.y) : this.ground(o.x, o.y)) + o.dy;
        m.compose(p.set(o.x, z, -o.y), q.setFromAxisAngle(up, o.yaw), s.set(o.sx, 1, 1));
        const ims = this.meshes.get(o.v)!, n = per.get(o.v) ?? 0;
        for (const im of ims) im.setMatrixAt(n, m);
        per.set(o.v, n + 1);
      }
      if (!this.active.has(k)) {   // chunk enters the radius: register its fountain colliders (whole chunk)
        const solids = list.filter((o) => o.kind === 0 || o.kind === 2).map((o) => [o.x, o.y, o.kind === 2 ? Math.min(info[o.v].radius, 1.7) : info[o.v].radius]);
        if (solids.length) this.colliders.addCircles(`catalog_${k}`, solids);
      }
    }
    for (const k of this.active) if (!now.has(k)) this.colliders.removeCircles(`catalog_${k}`);
    this.active = now;
    for (const [v, ims] of this.meshes) {
      const n = per.get(v) ?? 0;
      for (const im of ims) { im.count = n; im.visible = n > 0; im.instanceMatrix.needsUpdate = true; }
    }
  }

  dispose() {
    for (const k of this.active) this.colliders.removeCircles(`catalog_${k}`);
    this.group.removeFromParent();
    for (const ims of this.meshes.values()) for (const im of ims) im.dispose();
    for (const m of this.mats) m.dispose();
  }
}
