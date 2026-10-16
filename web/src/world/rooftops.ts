import * as THREE from 'three';

/** Rooftop furniture (pipeline/rooftops.py): dormers, roof windows, solar panels, lift/vent boxes, terraces, antennas.
 *  Row: [type 0 box | 1 gable prism, x, y, z(bottom), w, d, h, azimuth(downslope, rad), slope(rad), colour]. Two instanced meshes per chunk. */
export type RoofRow = number[];

const PALETTE = [
  0x1c2a45, 0x2c3a4a, 0xcdc8bc, 0x969ba0, 0xe1dacd, 0x6e7378, 0x964b37, 0xbec3c8, 0x466437, 0x46484b, 0x96734f, 0x8c8478,
].map((h) => new THREE.Color(h));

let boxGeo: THREE.BufferGeometry | null = null, prismGeo: THREE.BufferGeometry | null = null, mat: THREE.Material | null = null;
function geos() {
  if (!boxGeo) { boxGeo = new THREE.BoxGeometry(1, 1, 1); boxGeo.translate(0, 0.5, 0); }
  if (!prismGeo) {
    // triangle in x/y (apex at x=0,y=1), extruded along z in [-0.5, 0.5]
    const v = [-0.5, 0, -0.5, 0.5, 0, -0.5, 0, 1, -0.5, -0.5, 0, 0.5, 0.5, 0, 0.5, 0, 1, 0.5];
    const idx = [0, 2, 1, 3, 4, 5, 0, 3, 5, 0, 5, 2, 1, 2, 5, 1, 5, 4, 0, 1, 4, 0, 4, 3];
    prismGeo = new THREE.BufferGeometry();
    prismGeo.setAttribute('position', new THREE.Float32BufferAttribute(v, 3));
    prismGeo.setIndex(idx);
    prismGeo.computeVertexNormals();
  }
  if (!mat) mat = new THREE.MeshLambertMaterial();
  return { boxGeo, prismGeo, mat };
}

export interface RoofChunk { g: THREE.Group; x: number; y: number }
const CHUNK = 100;

/** Build per-100 m chunks (distance-cullable). Instance matrices and colours only; geometry/material are shared module singletons. */
export function buildRooftops(rows: RoofRow[] | undefined, shadows: boolean): RoofChunk[] {
  if (!rows?.length) return [];
  const { boxGeo: bg, prismGeo: pg, mat: m } = geos();
  const cells = new Map<string, RoofRow[]>();
  for (const r of rows) {
    const k = `${Math.floor(r[1] / CHUNK)},${Math.floor(r[2] / CHUNK)}`;
    (cells.get(k) ?? cells.set(k, []).get(k)!).push(r);
  }
  const out: RoofChunk[] = [];
  const q = new THREE.Quaternion(), e = new THREE.Euler(0, 0, 0, 'YXZ'), p = new THREE.Vector3(), s = new THREE.Vector3(), M = new THREE.Matrix4();
  for (const [k, list] of cells) {
    const [cx, cy] = k.split(',').map(Number);
    const g = new THREE.Group();
    for (const type of [0, 1]) {
      const rs = list.filter((r) => r[0] === type);
      if (!rs.length) continue;
      const im = new THREE.InstancedMesh(type ? pg : bg, m, rs.length);
      rs.forEach((r, i) => {
        e.set(r[8], r[7] + Math.PI / 2, 0);
        q.setFromEuler(e);
        p.set(r[1], r[3], -r[2]);
        s.set(r[4], r[6], r[5]);
        im.setMatrixAt(i, M.compose(p, q, s));
        im.setColorAt(i, PALETTE[r[9]] ?? PALETTE[3]);
      });
      im.instanceMatrix.needsUpdate = true;
      if (im.instanceColor) im.instanceColor.needsUpdate = true;
      im.computeBoundingSphere();
      im.castShadow = shadows && list.length < 400;
      im.receiveShadow = false;
      im.name = 'rooftops';
      g.add(im);
    }
    out.push({ g, x: (cx + 0.5) * CHUNK, y: (cy + 0.5) * CHUNK });
  }
  return out;
}
