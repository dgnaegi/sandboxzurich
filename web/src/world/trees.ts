import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

/**
 * Trees from the Baumkataster rendered with leaf-card models (pipeline/trees): rows [x, y, z, cls, crown, height].
 * Models are normalised (height 1, crown 1); bark and leaves are separate primitives (leaves alpha-tested).
 * Spring: cherries bloom pink, apple/pear/hawthorn white, chestnuts carry white candles.
 */
const CLASSES = ['broadleaf', 'cherry', 'whiteblossom', 'plane', 'linden', 'maple', 'chestnut', 'birch', 'conifer', 'columnar'];
type Part = { geo: THREE.BufferGeometry; mat: THREE.Material };
let lib: Part[][][] = []; // [cls][variant] -> parts

export async function loadTrees(base = '/models/trees') {
  const manifest = (await (await fetch(`${base}/manifest.json`)).json()) as { cls: string; file: string; variant: number }[];
  const loader = new GLTFLoader();
  lib = CLASSES.map(() => []);
  await Promise.all(manifest.map(async (e) => {
    const g = await loader.loadAsync(`${base}/${e.file}`);
    const parts: Part[] = [];
    g.scene.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      const src = m.material as THREE.MeshStandardMaterial;
      // Lambert is cheaper than Standard and looks the same for foliage
      const mat = new THREE.MeshLambertMaterial({ map: src.map, vertexColors: true, alphaTest: src.alphaTest || 0,
        side: src.side, transparent: false });
      parts.push({ geo: m.geometry, mat });
    });
    lib[CLASSES.indexOf(e.cls)][e.variant] = parts;
  }));
}

const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), s = new THREE.Vector3(), Y = new THREE.Vector3(0, 1, 0);

// far LOD: one low-poly blob + trunk per tree (≈30 triangles), coloured per class
const FAR_COL = [0x4d7a35, 0xf0b0c6, 0xf2ece8, 0x7a9a48, 0x3f6b2c, 0x6b9a3a, 0x355f2a, 0x8fb04e, 0x2a4a2a, 0x4f7a34].map((c) => new THREE.Color(c));
const farGeo = (() => {
  const crown = new THREE.IcosahedronGeometry(0.5, 0).translate(0, 0.62, 0).toNonIndexed();
  const trunk = new THREE.CylinderGeometry(0.04, 0.05, 0.4, 5).translate(0, 0.2, 0).toNonIndexed();
  const col = (g: THREE.BufferGeometry, c: number) => { const n = g.getAttribute('position').count, a = new Float32Array(n * 3).fill(c); g.setAttribute('color', new THREE.BufferAttribute(a, 3)); return g; };
  for (const g of [crown, trunk]) g.deleteAttribute('uv');
  const merged = new THREE.BufferGeometry();
  const parts = [col(crown, 1), col(trunk, 0.35)];
  const pos = parts.flatMap((g) => Array.from(g.getAttribute('position').array as Float32Array));
  const nrm = parts.flatMap((g) => Array.from(g.getAttribute('normal').array as Float32Array));
  const clr = parts.flatMap((g) => Array.from(g.getAttribute('color').array as Float32Array));
  merged.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  merged.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
  merged.setAttribute('color', new THREE.Float32BufferAttribute(clr, 3));
  return merged;
})();
const farMat = new THREE.MeshLambertMaterial({ vertexColors: true, flatShading: true });

/** Cheap stand-in trees for distant tiles. */
export function buildFarTrees(rows: number[][]): THREE.Object3D[] {
  if (!rows.length) return [];
  const im = new THREE.InstancedMesh(farGeo, farMat, rows.length);
  rows.forEach((r, i) => {
    q.setFromAxisAngle(Y, r[0]);
    im.setMatrixAt(i, m4.compose(p.set(r[0], r[2], -r[1]), q, s.set(r[4], r[5], r[4])));
    im.setColorAt(i, FAR_COL[r[3] | 0] ?? FAR_COL[0]);
  });
  im.computeBoundingSphere();
  return [im];
}

export function buildTrees(rows: number[][], shadows: boolean): THREE.Object3D[] {
  if (!rows.length || !lib.length) return [];
  const groups = new Map<string, number[][]>();
  for (const r of rows) {
    const cls = Math.min(CLASSES.length - 1, Math.max(0, r[3] | 0));
    const variants = lib[cls].length || 1;
    const v = Math.floor(Math.abs(Math.sin(r[0] * 3.7 + r[1] * 1.3)) * 1000) % variants;
    const k = `${cls}_${v}`;
    (groups.get(k) ?? groups.set(k, []).get(k)!).push(r);
  }
  const out: THREE.Object3D[] = [];
  for (const [k, list] of groups) {
    const [cls, v] = k.split('_').map(Number);
    const parts = lib[cls][v] ?? lib[0][0];
    if (!parts) continue;
    for (const part of parts) {
      const im = new THREE.InstancedMesh(part.geo, part.mat, list.length);
      list.forEach((r, i) => {
        const jit = Math.abs(Math.sin(r[0] * 12.9898 + r[1] * 78.233)) % 1;
        q.setFromAxisAngle(Y, jit * 6.28);
        im.setMatrixAt(i, m4.compose(p.set(r[0], r[2], -r[1]), q, s.set(r[4], r[5], r[4])));
      });
      im.castShadow = shadows;
      im.computeBoundingSphere();
      out.push(im);
    }
  }
  return out;
}
