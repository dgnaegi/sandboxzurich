import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
/** Merge static meshes under `root` into one mesh per material (world transforms baked relative to root).
 *  Subtrees containing skinned meshes or bones (people, animated props) are left untouched. */
export function mergeStatic(root: THREE.Object3D): void {
  root.updateMatrixWorld(true);
  const inv = root.matrixWorld.clone().invert();
  const animated = new Set<THREE.Object3D>();
  root.traverse((o) => { if ((o as THREE.SkinnedMesh).isSkinnedMesh || (o as THREE.Bone).isBone) for (let q: THREE.Object3D | null = o; q && q !== root; q = q.parent) animated.add(q); });
  const byMat = new Map<THREE.Material, THREE.BufferGeometry[]>();
  const victims: THREE.Mesh[] = [];
  root.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh || animated.has(m) || (m as unknown as THREE.InstancedMesh).isInstancedMesh || Array.isArray(m.material)) return;
    for (let q: THREE.Object3D | null = m.parent; q && q !== root; q = q.parent) if (animated.has(q)) return;
    let g = m.geometry.index ? m.geometry.toNonIndexed() : m.geometry.clone();
    for (const k of Object.keys(g.attributes)) if (!['position', 'normal', 'uv'].includes(k)) g.deleteAttribute(k);
    if (!g.attributes.uv) g.setAttribute('uv', new THREE.Float32BufferAttribute(new Float32Array(g.attributes.position.count * 2), 2));
    g = g.applyMatrix4(new THREE.Matrix4().multiplyMatrices(inv, m.matrixWorld));
    (byMat.get(m.material) ?? byMat.set(m.material, []).get(m.material)!).push(g);
    victims.push(m);
  });
  for (const m of victims) m.parent?.remove(m);
  for (const [mat, list] of byMat) {
    const geo = mergeGeometries(list);
    list.forEach((g) => g.dispose());
    if (!geo) continue;
    const mesh = new THREE.Mesh(geo, mat);
    mesh.castShadow = true; mesh.receiveShadow = true;
    root.add(mesh);
  }
}
