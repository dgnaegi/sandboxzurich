import * as THREE from 'three';
import type { Colliders } from '../player/collision';

/**
 * Knock-over objects (bins, bollards, bike racks, sign posts). The tile builders keep their merged meshes and describe each
 * knockable as a vertex range (`Mesh.userData.knock`). When a car drives into the circle (collision.ts), the range is collapsed
 * in the merged geometry (degenerate triangles) and a small proxy mesh with a copy of that range tips over / slides away
 * with a short animation. The proxy is a child of the same tile group, so unloading the tile disposes it; nothing is
 * kept globally, and the object stays down until the tile is rebuilt. Walkers and bikes never trigger this (they glide).
 */
export interface KnockRange { v0: number; vn: number; i0?: number; in?: number; mesh: THREE.Mesh }
export interface KnockRec {
  x: number; y: number; z: number; r: number;
  /** 1 = solid for walkers/bikes/NPC cars too (bins), 2 = only the player's car sees it (new colliders: bollards, racks, sign posts) */
  kind: 1 | 2;
  /** how it falls: pole = tips over, bin = tips and rolls a bit, flat = slides and lies down (racks) */
  type: 'pole' | 'bin' | 'flat';
  ranges: KnockRange[];
}

const FALL = 0.55;

function extract(m: THREE.Mesh, rg: KnockRange, px: number, py: number, pz: number): THREE.BufferGeometry {
  const src = m.geometry, g = new THREE.BufferGeometry();
  for (const name of Object.keys(src.attributes)) {
    const a = src.getAttribute(name) as THREE.BufferAttribute | THREE.InterleavedBufferAttribute;
    if ((a as THREE.InterleavedBufferAttribute).isInterleavedBufferAttribute) continue;
    const arr = (a.array as Float32Array).slice(rg.v0 * a.itemSize, (rg.v0 + rg.vn) * a.itemSize);
    if (name === 'position') for (let i = 0; i < arr.length; i += 3) { arr[i] -= px; arr[i + 1] -= py; arr[i + 2] -= pz; }
    g.setAttribute(name, new THREE.BufferAttribute(arr, a.itemSize, a.normalized));
  }
  if (src.index && rg.i0 !== undefined && rg.in !== undefined) {
    const idx = new Uint32Array(rg.in);
    for (let i = 0; i < rg.in; i++) idx[i] = src.index.getX(rg.i0 + i) - rg.v0;
    g.setIndex(new THREE.BufferAttribute(idx, 1));
  }
  g.computeBoundingSphere();
  return g;
}

/** Collapse a vertex range of a merged mesh into one point (the triangles vanish). */
function hide(rg: KnockRange) {
  const pos = rg.mesh.geometry.getAttribute('position') as THREE.BufferAttribute;
  const x = pos.getX(rg.v0), y = pos.getY(rg.v0), z = pos.getZ(rg.v0);
  for (let i = rg.v0; i < rg.v0 + rg.vn; i++) pos.setXYZ(i, x, y, z);
  pos.needsUpdate = true;
}

function topple(rec: KnockRec, dx: number, dy: number, speed: number) {
  const pivot = new THREE.Vector3(rec.x, rec.z, -rec.y);
  const dir = new THREE.Vector3(dx, 0, -dy);                 // fall direction in Three space
  const axis = new THREE.Vector3(-dy, 0, -dx).normalize();   // up x dir
  const tilt = rec.type === 'flat' ? 1.0 : Math.PI / 2 - 0.08, slide = Math.min(1.6, 0.25 + speed * 0.09) * (rec.type === 'bin' ? 1.4 : 1);
  const q = new THREE.Quaternion(), spin = rec.type === 'bin' ? (Math.random() < 0.5 ? -1 : 1) * 0.6 : 0;
  for (const rg of rec.ranges) {
    const geo = extract(rg.mesh, rg, pivot.x, pivot.y, pivot.z), parent = rg.mesh.parent;
    hide(rg);
    if (!parent) { geo.dispose(); continue; }
    const m = new THREE.Mesh(geo, rg.mesh.material);
    m.castShadow = rg.mesh.castShadow; m.receiveShadow = rg.mesh.receiveShadow; m.frustumCulled = false;
    m.position.copy(pivot);
    parent.add(m);
    const t0 = performance.now();
    const end = () => { m.onBeforeRender = () => {}; };
    m.onBeforeRender = () => {
      const u = Math.min(1, (performance.now() - t0) / 1000 / FALL), g = u * u;      // falls under gravity
      const bounce = u >= 1 ? 0 : Math.sin(u * Math.PI) * 0.03;                      // tiny settle
      q.setFromAxisAngle(axis, tilt * g);
      m.quaternion.copy(q);
      if (spin) m.quaternion.multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), spin * g));
      const s = slide * (1 - (1 - u) * (1 - u));
      m.position.set(pivot.x + dir.x * s, pivot.y + (rec.type === 'flat' ? 0.02 : 0.1) * g + bounce, pivot.z + dir.z * s);
      if (u >= 1) end();
    };
  }
}

/** Register the knockables found in a tile's object tree with the collider grid (key = tile name). Call after the tile's meshes exist. */
export function attachKnocks(key: string, root: THREE.Object3D, colliders: Colliders) {
  const rows: { row: number[]; fn: (dx: number, dy: number, speed: number) => void }[] = [];
  root.traverse((o) => {
    const list = o.userData.knock as KnockRec[] | undefined;
    if (!list) return;
    for (const rec of list) rows.push({ row: [rec.x, rec.y, rec.r, rec.kind], fn: (dx, dy, sp) => topple(rec, dx, dy, sp) });
  });
  if (rows.length) colliders.addKnockable(`${key}#knock`, rows);
}
export const knockKey = (name: string) => `${name}#knock`;
