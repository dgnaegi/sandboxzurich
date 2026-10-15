import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

/** Street-tree furniture (Zürich standard): 1.5 m tree pit with steel frame + slatted grate, plus 3 steel guard hoops (Schutzbügel)
 *  on the carriageway side where parking / traffic is next to the tree. Park trees have neither. One draw call each, near the player only. */
const col = (g: THREE.BufferGeometry, c: number) => {
  const k = new THREE.Color(c), n = g.getAttribute('position').count, a = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { a[i * 3] = k.r; a[i * 3 + 1] = k.g; a[i * 3 + 2] = k.b; }
  g.setAttribute('color', new THREE.BufferAttribute(a, 3));
  g.deleteAttribute('uv');
  return g;
};
const box = (w: number, h: number, d: number, x: number, y: number, z: number, c: number) =>
  col(new THREE.BoxGeometry(w, h, d).translate(x, y, z), c);

function pitGeo() {
  const S = 1.5, h = 0.035, parts: THREE.BufferGeometry[] = [];
  parts.push(box(S, h, .08, 0, h / 2, S / 2 - .04, 0x3b3e42), box(S, h, .08, 0, h / 2, -S / 2 + .04, 0x3b3e42),
    box(.08, h, S - .16, S / 2 - .04, h / 2, 0, 0x3b3e42), box(.08, h, S - .16, -S / 2 + .04, h / 2, 0, 0x3b3e42));
  parts.push(box(S - .16, h * .6, S - .16, 0, h * .3, 0, 0x2a241d)); // soil under the grate
  for (let i = -5; i <= 5; i++) parts.push(box(.03, h * .9, S - .16, i * .125, h * .45, 0, 0x4a4e52)); // slats
  parts.push(col(new THREE.CylinderGeometry(.16, .16, h * 1.2, 10).translate(0, h * .6, 0), 0x1a1612)); // trunk hole
  return mergeGeometries(parts, false)!;
}

function guardGeo() {
  const parts: THREE.BufferGeometry[] = [], steel = 0x30343a, H = .85, r = .022;
  const tube = (x: number, y: number, z: number, h: number, rotZ = 0, rotY = 0) => {
    const g = new THREE.CylinderGeometry(r, r, h, 6); g.rotateZ(rotZ); g.rotateY(rotY); g.translate(x, y, z); return col(g, steel);
  };
  const hoop = (cx: number, cz: number, ry: number) => {
    const c = Math.cos(ry), s = Math.sin(ry), hw = .45, g: THREE.BufferGeometry[] = [];
    for (const side of [-1, 1]) g.push(tube(cx + side * hw * c, H / 2, cz - side * hw * s, H));
    g.push(tube(cx, H, cz, hw * 2, Math.PI / 2, ry));
    return g;
  };
  parts.push(...hoop(0, .95, 0), ...hoop(.95, .1, Math.PI / 2), ...hoop(-.95, .1, Math.PI / 2));
  return mergeGeometries(parts, false)!;
}

export function buildGrates() {
  const group = new THREE.Group();
  const mat = new THREE.MeshLambertMaterial({ vertexColors: true });
  const make = (g: THREE.BufferGeometry, cap: number) => {
    const m = new THREE.InstancedMesh(g, mat, cap); m.frustumCulled = false; m.count = 0; group.add(m); return m;
  };
  const pits = make(pitGeo(), 160), guards = make(guardGeo(), 160);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), one = new THREE.Vector3(1, 1, 1), Y = new THREE.Vector3(0, 1, 0);
  return {
    group,
    set(list: { x: number; y: number; z: number; flags: number; rot: number }[]) {
      let a = 0, b = 0;
      for (const t of list) {
        if (a >= 160) break;
        q.setFromAxisAngle(Y, t.rot);
        m4.compose(p.set(t.x, t.z + .01, -t.y), q, one);
        pits.setMatrixAt(a++, m4);
        if (t.flags >= 2 && b < 160) guards.setMatrixAt(b++, m4);
      }
      pits.count = a; guards.count = b;
      pits.instanceMatrix.needsUpdate = guards.instanceMatrix.needsUpdate = true;
    },
  };
}
