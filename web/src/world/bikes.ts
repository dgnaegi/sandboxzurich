import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { bike } from './vehicles';
import { CAR_PAINT, carMaterial } from './cars';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

/** Parked bikes as one InstancedMesh per tile so single bikes can be taken (stolen) and dropped elsewhere. */
export const BIKE_GEO = (() => {
  const tag = (g: THREE.BufferGeometry, c: THREE.Color, paint: number) => {
    g = g.index ? g.toNonIndexed() : g;
    for (const k of Object.keys(g.attributes)) if (k !== 'position' && k !== 'normal') g.deleteAttribute(k);
    const n = g.getAttribute('position').count;
    g.setAttribute('color', new THREE.BufferAttribute(new Float32Array(n * 3).map((_, i) => [c.r, c.g, c.b][i % 3]), 3));
    g.setAttribute('_paint', new THREE.BufferAttribute(new Float32Array(n).fill(paint), 1));
    return g;
  };
  return mergeGeometries([tag(bike.frame.clone(), new THREE.Color(1, 1, 1), 1), tag(bike.black.clone(), new THREE.Color(0x1d2226), 0)])!;
})();

/** Distant bikes: ~150-triangle stand-in (ring wheels, box frame) sharing the instance buffers of the detailed mesh. */
let LO: THREE.BufferGeometry | null = null;
function bikeLo(): THREE.BufferGeometry {
  if (LO) return LO;
  const ref = BIKE_MODELS.city ?? BIKE_GEO;
  ref.computeBoundingBox();
  const bb = ref.boundingBox!, c = new THREE.Vector3();
  bb.getCenter(c);
  const alongX = bb.max.x - bb.min.x >= bb.max.z - bb.min.z;
  const L = alongX ? bb.max.x - bb.min.x : bb.max.z - bb.min.z, H = bb.max.y - bb.min.y;
  const r = Math.min(0.35, H * 0.34), wx = L / 2 - r, y0 = bb.min.y;
  const tag = (g: THREE.BufferGeometry, col: number, paint: number) => {
    g = g.index ? g.toNonIndexed() : g;
    for (const k of Object.keys(g.attributes)) if (k !== 'position' && k !== 'normal') g.deleteAttribute(k);
    const n = g.getAttribute('position').count, cc = new THREE.Color(col);
    g.setAttribute('color', new THREE.BufferAttribute(new Float32Array(n * 3).map((_, i) => [cc.r, cc.g, cc.b][i % 3]), 3));
    g.setAttribute('_paint', new THREE.BufferAttribute(new Float32Array(n).fill(paint), 1));
    return g;
  };
  const parts: THREE.BufferGeometry[] = [];
  for (const sx of [-wx, wx]) for (const flip of [0, Math.PI]) {
    const g = new THREE.RingGeometry(r * 0.8, r, 10);
    g.rotateY(flip); g.translate(sx, y0 + r, 0);
    parts.push(tag(g, 0x1d2226, 0));
  }
  const box = (len: number, x: number, y: number, rot: number, col: number, paint: number, t = 0.04, d = 0.04) => {
    const g = new THREE.BoxGeometry(len, t, d);
    g.rotateZ(rot); g.translate(x, y, 0);
    parts.push(tag(g, col, paint));
  };
  box(wx * 1.25, 0, y0 + r * 1.45, 0.55, 0xffffff, 1);              // down tube
  box(wx * 1.1, wx * 0.05, y0 + r * 2.25, 0, 0xffffff, 1);          // top tube
  box(r * 1.6, -wx * 0.35, y0 + r * 1.7, Math.PI / 2, 0xffffff, 1); // seat tube
  box(0.22, -wx * 0.38, y0 + H * 0.86, 0, 0x1d2226, 0, 0.05, 0.1);  // saddle
  box(0.05, wx * 0.8, y0 + H * 0.92, 0, 0x1d2226, 0, 0.04, 0.56);   // handlebar
  LO = mergeGeometries(parts)!;
  if (!alongX) LO.rotateY(Math.PI / 2);
  LO.translate(c.x, 0, c.z);
  return LO;
}

export interface BikeSlot { mesh: THREE.InstancedMesh; i: number; x: number; y: number; z: number; h: number; color: THREE.Color; taken: boolean; type: string }

/** Realistic bike models (pipeline/bikes): geometry per type (+ *_lean on the kickstand), one shared material. */
export const BIKE_MODELS: Record<string, THREE.BufferGeometry> = {};
export let bikeModelMaterial: THREE.Material = carMaterial;
/** Axle and bottom-bracket positions per type (manifest `rig`), used to split the ridden bike into spinning parts. */
export const BIKE_RIG: Record<string, { rear: [number, number]; front: [number, number]; bb: [number, number] }> = {};
const MIX: [string, number][] = [['city', 34], ['trekking', 18], ['ebike', 13], ['road', 8], ['mtb', 8], ['rental', 8], ['kidseat', 7], ['cargo', 4]];

export async function loadBikes(base = '/models/bikes') {
  const list = (await (await fetch(`${base}/manifest.json`)).json()) as { type: string; file: string; rig?: (typeof BIKE_RIG)[string] }[];
  for (const e of list) if (e.rig) BIKE_RIG[e.type] = e.rig;
  const loader = new GLTFLoader();
  let map: THREE.Texture | null = null;
  await Promise.all(list.map(async (e) => {
    const g = await loader.loadAsync(`${base}/${e.file}`);
    g.scene.updateMatrixWorld(true);
    g.scene.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      BIKE_MODELS[e.type] = m.geometry.clone().applyMatrix4(m.matrixWorld);
      map ??= (m.material as THREE.MeshStandardMaterial).map;
    });
  }));
  const mat = new THREE.MeshLambertMaterial({ vertexColors: true, map, alphaTest: 0.3, side: THREE.DoubleSide });
  mat.onBeforeCompile = (sh) => {
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nattribute float _paint;')
      .replace('#include <color_vertex>', 'vColor = vec4(1.0);\nvColor.rgb *= color.rgb;\n#ifdef USE_INSTANCING_COLOR\nvColor.rgb *= mix(vec3(1.0), instanceColor.rgb, step(0.5, _paint));\n#endif');
  };
  bikeModelMaterial = mat;
}

/** Deterministic bike type for a parked bike (mostly city/trekking, some e-bikes, few cargo). */
export function bikeType(key: number, lean: boolean): string {
  const total = MIX.reduce((a, [, w]) => a + w, 0);
  let k = (key * 2246822519 >>> 0) % total;
  for (const [t, w] of MIX) { if (k < w) return BIKE_MODELS[lean ? `${t}_lean` : t] ? (lean ? `${t}_lean` : t) : t; k -= w; }
  return 'city';
}
export const bikeGeo = (type: string) => BIKE_MODELS[type] ?? BIKE_GEO;

const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), one = new THREE.Vector3(1, 1, 1), zero = new THREE.Vector3(0, 0, 0), Y = new THREE.Vector3(0, 1, 0);

export class Bikes {
  private slots: BikeSlot[] = [];
  readonly dropped: THREE.InstancedMesh;
  private droppedCount = 0;

  constructor(scene: THREE.Scene) {
    this.dropped = new THREE.InstancedMesh(bikeGeo('city'), bikeModelMaterial, 64);
    this.dropped.count = 0;
    this.dropped.frustumCulled = false;
    scene.add(this.dropped);
  }

  /** Build instanced meshes (one per bike type) for a tile's rows [x, y, z, heading, colour]. */
  build(rows: number[][]): THREE.Object3D[] {
    if (!rows.length) return [];
    const byType = new Map<string, number[][]>();
    rows.forEach((r) => {
      const key = Math.abs(Math.floor(r[0] * 131 + r[1] * 71));
      const t = bikeType(key, key % 3 !== 0);
      (byType.get(t) ?? byType.set(t, []).get(t)!).push(r);
    });
    const out: THREE.Object3D[] = [];
    for (const [type, list] of byType) {
      const mesh = new THREE.InstancedMesh(bikeGeo(type), bikeModelMaterial, list.length);
      list.forEach((r, i) => {
        const color = CAR_PAINT[r[4] % CAR_PAINT.length];
        mesh.setMatrixAt(i, m4.compose(p.set(r[0], r[2], -r[1]), q.setFromAxisAngle(Y, -r[3]), one));
        mesh.setColorAt(i, color);
        this.slots.push({ mesh, i, x: r[0], y: r[1], z: r[2], h: r[3], color, taken: false, type });
      });
      mesh.computeBoundingSphere();
      const lo = new THREE.InstancedMesh(bikeLo(), carMaterial, list.length);
      lo.instanceMatrix = mesh.instanceMatrix; lo.instanceColor = mesh.instanceColor; // stolen bikes vanish in both
      lo.computeBoundingSphere();
      lo.visible = false;
      lo.name = 'bikes_lo';
      mesh.userData.lo = lo;
      out.push(mesh, lo);
    }
    return out;
  }

  /** Forget slots of an unloaded tile mesh. */
  forget(mesh: THREE.Object3D) { this.slots = this.slots.filter((s) => s.mesh !== mesh); }
  forgetAll(meshes: THREE.Object3D[]) { const set = new Set(meshes); this.slots = this.slots.filter((s) => !set.has(s.mesh)); }

  nearest(x: number, y: number, r = 2.2): BikeSlot | null {
    let best: BikeSlot | null = null, bd = r;
    for (const s of this.slots) {
      if (s.taken) continue;
      const d = Math.hypot(s.x - x, s.y - y);
      if (d < bd) { bd = d; best = s; }
    }
    return best;
  }

  take(s: BikeSlot) {
    s.taken = true;
    s.mesh.setMatrixAt(s.i, m4.compose(p.set(0, -100, 0), q.identity(), zero));
    s.mesh.instanceMatrix.needsUpdate = true;
  }

  /** Leave a bike on the street (player dismounts). */
  drop(x: number, y: number, z: number, h: number, color: THREE.Color) {
    const i = this.droppedCount++ % 64;
    this.dropped.setMatrixAt(i, m4.compose(p.set(x, z, -y), q.setFromAxisAngle(Y, -h), one));
    this.dropped.setColorAt(i, color);
    this.dropped.count = Math.min(64, this.droppedCount);
    this.dropped.instanceMatrix.needsUpdate = true;
    if (this.dropped.instanceColor) this.dropped.instanceColor.needsUpdate = true;
    this.slots.push({ mesh: this.dropped, i, x, y, z, h, color, taken: false, type: 'city' });
  }
}
