import * as THREE from 'three';
import { CAR_GEO, carMaterial } from './cars';

/**
 * Registry of the parked cars (instances inside the tile meshes made in props.ts) so single cars can be taken
 * (stolen) and left behind again, and driven cars can bump into the rest. Slots of unloaded tiles are
 * recognised lazily (mesh no longer attached to the scene) and dropped when found.
 */
export interface CarSlot { mesh: THREE.InstancedMesh; i: number; x: number; y: number; z: number; h: number; type: string; color: THREE.Color; taken: boolean }

const CELL = 12;
const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), one = new THREE.Vector3(1, 1, 1), zero = new THREE.Vector3(0, 0, 0), Y = new THREE.Vector3(0, 1, 0);
const attached = (o: THREE.Object3D) => { let n: THREE.Object3D | null = o; while (n.parent) n = n.parent; return (n as THREE.Scene).isScene === true; };

class ParkedCars {
  private grid = new Map<string, CarSlot[]>();
  private dropped = new Map<string, { mesh: THREE.InstancedMesh; n: number }>();
  private scene: THREE.Scene | null = null;
  init(scene: THREE.Scene) { this.scene = scene; }

  add(s: CarSlot) {
    const k = `${Math.floor(s.x / CELL)},${Math.floor(s.y / CELL)}`;
    (this.grid.get(k) ?? this.grid.set(k, []).get(k)!).push(s);
  }

  /** Live slots within `r` metres (prunes slots of unloaded tiles). */
  near(x: number, y: number, r: number): CarSlot[] {
    const out: CarSlot[] = [], c = Math.ceil(r / CELL);
    const cx = Math.floor(x / CELL), cy = Math.floor(y / CELL);
    for (let i = cx - c; i <= cx + c; i++) for (let j = cy - c; j <= cy + c; j++) {
      const k = `${i},${j}`, list = this.grid.get(k);
      if (!list) continue;
      let dead = false;
      for (const s of list) {
        if (s.taken) continue;
        if (!s.mesh.parent || !attached(s.mesh)) { s.taken = true; dead = true; continue; }
        if (Math.hypot(s.x - x, s.y - y) <= r) out.push(s);
      }
      if (dead) { const keep = list.filter((s) => !s.taken); if (keep.length) this.grid.set(k, keep); else this.grid.delete(k); }
    }
    return out;
  }

  nearest(x: number, y: number, r = 3.2): CarSlot | null {
    let best: CarSlot | null = null, bd = r;
    for (const s of this.near(x, y, r + 2.5)) {
      // distance to the car body (centre line, ±length/2), not just its centre
      const L = carLength(s.type), fx = Math.sin(s.h), fy = Math.cos(s.h), dx = x - s.x, dy = y - s.y;
      const along = Math.max(-L / 2, Math.min(L / 2, dx * fx + dy * fy)), d = Math.hypot(dx - fx * along, dy - fy * along);
      if (d < bd) { bd = d; best = s; }
    }
    return best;
  }

  take(s: CarSlot) {
    s.taken = true;
    s.mesh.setMatrixAt(s.i, m4.compose(p.set(0, -100, 0), q.identity(), zero));
    s.mesh.instanceMatrix.needsUpdate = true;
  }

  /** Leave a car on the street (player gets out). */
  drop(type: string, color: THREE.Color, x: number, y: number, z: number, h: number) {
    if (!this.scene || !CAR_GEO[type]) return;
    let d = this.dropped.get(type);
    if (!d) {
      const mesh = new THREE.InstancedMesh(CAR_GEO[type], carMaterial, 24);
      mesh.count = 0; mesh.frustumCulled = false; mesh.castShadow = true;
      this.scene.add(mesh);
      d = { mesh, n: 0 };
      this.dropped.set(type, d);
    }
    const i = d.n++ % 24;
    d.mesh.setMatrixAt(i, m4.compose(p.set(x, z, -y), q.setFromAxisAngle(Y, -h), one));
    d.mesh.setColorAt(i, color);
    d.mesh.count = Math.min(24, d.n);
    d.mesh.instanceMatrix.needsUpdate = true;
    if (d.mesh.instanceColor) d.mesh.instanceColor.needsUpdate = true;
    // the slot reusing index i replaces an older dropped car of this type
    for (const list of this.grid.values()) for (const s of list) if (s.mesh === d.mesh && s.i === i) s.taken = true;
    this.add({ mesh: d.mesh, i, x, y, z, h, type, color, taken: false });
  }
}

export const carLength = (type: string) => {
  const g = CAR_GEO[type];
  if (!g) return 4.4;
  g.computeBoundingBox();
  return g.boundingBox!.max.z - g.boundingBox!.min.z;
};
export const parkedCars = new ParkedCars();
