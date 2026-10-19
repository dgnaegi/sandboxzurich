import { foliagePatch } from './foliage';
import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

/**
 * Courtyards, front gardens and private vegetation (pipeline/yards.py, research/yards.md): shrubs and hedges measured from the
 * nDSM + orthophoto, Mäuerchen/Zäune/low hedges along front gardens, bike sheds, clothes dryers, sandpits and garden tables in
 * courtyards, gravel strips along house walls. Few draw calls per tile: 3 instanced meshes (bushes, hedges, gravel), 3 for the
 * walls, 1 merged vertex-coloured mesh for the props. Handy LOD: half the bushes, no gravel and no table/shed detail.
 * Local (x, y, z) -> Three (x, z, -y); heading = CCW from east, object +x along it.
 */
export interface YardMeta {
  bushes?: number[][];  // x y z r h colour
  hedges?: number[][];  // x y z heading len width h colour
  walls?: number[][];   // type(0 wall, 1 fence, 2 hedge) x y z heading len
  props?: [string, number, number, number, number, number][];  // type x y z heading a
  gravel?: number[][];  // x y z heading len
}

let mobileLod = false;
export function setYardsMobile(m: boolean) { mobileLod = m; }

const GREENS = [0x4f6b3a, 0x5d7a40, 0x46603a, 0x6a8344, 0x7d8a3c, 0x66783a, 0x4c5f36, 0x56733f];   // 5/6 were olive/brown: smooth brown blobs on the street (2026-10-19)
const rnd = (x: number, y: number) => { const v = Math.sin(x * 127.1 + y * 311.7) * 43758.5453; return v - Math.floor(v); };

type G = THREE.BufferGeometry;
function paint(g: G, c: number): G {
  g = g.index ? g.toNonIndexed() : g;
  for (const k of Object.keys(g.attributes)) if (k !== 'position' && k !== 'normal') g.deleteAttribute(k);
  const n = g.getAttribute('position').count, cc = new THREE.Color(c), a = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) a.set([cc.r, cc.g, cc.b], i * 3);
  g.setAttribute('color', new THREE.BufferAttribute(a, 3));
  return g;
}
const B = (w: number, h: number, d: number, x: number, y: number, z: number, c: number): G => paint(new THREE.BoxGeometry(w, h, d).translate(x, y + h / 2, z), c);
const Y = (r: number, h: number, x: number, y: number, z: number, c: number, n = 6): G => paint(new THREE.CylinderGeometry(r, r, h, n).translate(x, y + h / 2, z), c);

const PROPS: Record<string, (a: number, x: number, y: number) => G[]> = {
  // Velounterstand: flat roof on four posts, rack rail underneath, two-three parked bikes as boxes
  bikeshed: (a) => {
    const p: G[] = [B(3.0, .08, 2.0, 0, 2.2, 0, 0x5b6468), B(.07, 2.2, .07, -1.4, 0, -.9, 0x3d4446), B(.07, 2.2, .07, 1.4, 0, -.9, 0x3d4446),
      B(.07, 2.2, .07, -1.4, 0, .9, 0x3d4446), B(.07, 2.2, .07, 1.4, 0, .9, 0x3d4446), B(2.8, .05, .05, 0, .55, .6, 0x777d80)];
    if (!mobileLod) for (let i = 0; i < 2 + (a % 2); i++) p.push(B(.05, .9, 1.6, -1 + i * .7, .05, .1, [0x2f4a7a, 0x8a2f2f, 0x3f6a4a][(i + a) % 3]));
    return p;
  },
  // Gartenhäuschen im Familiengarten: timber box, pitched roof, door, a = wall colour variant
  shed: (a) => [B(3, 2, 2.4, 0, 0, 0, [0x8a6a45, 0x6f8a6a, 0xb59a6a][a % 3]), paint(new THREE.CylinderGeometry(0, 1.9, 1.0, 4).rotateY(Math.PI / 4).scale(1.0, 1, .85).translate(0, 2.5, 0), 0x5a4a40),
    B(.7, 1.7, .05, -.6, 0, 1.22, 0x4a3a2a)],
  // Wäschespinne (rotary dryer): pole, four arms, a line
  drying: () => {
    const p: G[] = [Y(.03, 1.8, 0, 0, 0, 0x8a9094, 5)];
    for (let i = 0; i < 4; i++) { const g = B(1.5, .02, .02, 0, 1.75, 0, 0x8a9094); g.rotateY((i * Math.PI) / 4 + .4); p.push(g); }
    p.push(B(1.4, .01, 1.4, 0, 1.76, 0, 0xe6e2d8));
    return p;
  },
  // Sandkasten: timber frame with sand
  sandbox: () => [B(2.4, .22, .1, 0, 0, 1.15, 0x8a6a45), B(2.4, .22, .1, 0, 0, -1.15, 0x8a6a45), B(.1, .22, 2.4, 1.15, 0, 0, 0x8a6a45), B(.1, .22, 2.4, -1.15, 0, 0, 0x8a6a45),
    B(2.2, .16, 2.2, 0, 0, 0, 0xd9c590), B(.4, .25, .3, .3, .16, -.4, 0xd24a3a)],
  // Gartentisch with four stools; a = 1 adds a parasol
  table: (a) => {
    const p: G[] = [B(1.3, .05, .8, 0, .72, 0, 0x7b6a58), B(.06, .72, .06, -.55, 0, -.3, 0x55595c), B(.06, .72, .06, .55, 0, .3, 0x55595c)];
    for (const [sx, sz] of [[-.5, .6], [.5, .6], [-.5, -.6], [.5, -.6]]) p.push(B(.4, .45, .4, sx, 0, sz, 0xb5ac98));
    if (a) { p.push(Y(.02, 2.2, 0, 0, 0, 0x6d7377, 4)); p.push(paint(new THREE.ConeGeometry(1.3, .35, 8).translate(0, 2.35, 0), 0xc8553d)); }
    return p;
  },
};

function mkInst(geo: G, mat: THREE.Material, n: number): THREE.InstancedMesh {
  const m = new THREE.InstancedMesh(geo, mat, n);
  m.frustumCulled = true; m.castShadow = false;
  return m;
}

export function buildYards(meta: YardMeta | undefined, shadows: boolean): THREE.Object3D[] {
  if (!meta) return [];
  const out: THREE.Object3D[] = [];
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), s = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0), col = new THREE.Color();
  const step = mobileLod ? 2 : 1;

  const bush = (meta.bushes ?? []).filter((_, i) => i % step === 0);
  if (bush.length) {
    const bm = new THREE.MeshLambertMaterial({ color: 0xffffff }); foliagePatch(bm, 'inst', mobileLod);   // leafy look like the hedges
    const im = mkInst(new THREE.IcosahedronGeometry(1, 2), bm, bush.length);
    bush.forEach(([x, y, z, r, h, c], i) => {
      q.setFromAxisAngle(up, rnd(x, y) * 6.28);
      im.setMatrixAt(i, m.compose(p.set(x, z + h * .42, -y), q, s.set(r, h * .5, r)));
      im.setColorAt(i, col.setHex(GREENS[c % GREENS.length]).offsetHSL(0, 0, (rnd(y, x) - .5) * .06));
    });
    im.receiveShadow = shadows; out.push(im);
  }
  const hed = (meta.hedges ?? []).filter((_, i) => i % step === 0);
  if (hed.length) {
    const hm = new THREE.MeshLambertMaterial({ color: 0xffffff }); foliagePatch(hm, 'inst', mobileLod); // look3
    const im = mkInst(new THREE.BoxGeometry(1, 1, 1, 10, 3, 2), hm, hed.length);
    hed.forEach(([x, y, z, hd, len, w, h, c], i) => {
      q.setFromAxisAngle(up, hd);
      im.setMatrixAt(i, m.compose(p.set(x, z + h / 2, -y), q, s.set(len, h, w)));
      im.setColorAt(i, col.setHex(GREENS[c % 4]));
    });
    im.receiveShadow = shadows; out.push(im);
  }
  const wl = [[], [], []] as number[][][];
  for (const r of meta.walls ?? []) wl[r[0]]?.push(r);
  const wallGeo: G[] = [new THREE.BoxGeometry(1, 1, 1), (() => { // metal fence: rails + 9 bars on a unit length
    const a: G[] = [new THREE.BoxGeometry(1, .04, .04).translate(0, .95, 0), new THREE.BoxGeometry(1, .04, .04).translate(0, .2, 0)];
    for (let i = 0; i < 9; i++) a.push(new THREE.BoxGeometry(.012, 1, .03).translate(-.5 + i / 8, .5, 0));
    return mergeGeometries(a.map((g) => g.toNonIndexed().deleteAttribute('uv') as G))!; })(), new THREE.BoxGeometry(1, 1, 1, 10, 3, 2)]; // look3: hedge walls segmented
  const wallCol = [0xcfc8b8, 0x2f3a36, 0x4a6a36], wallH = [.45, 1, .9], wallW = [.22, 1, .6];
  wl.forEach((rows, t) => {
    if (!rows.length) return;
    const wm = new THREE.MeshLambertMaterial({ color: wallCol[t] }); if (t === 2) foliagePatch(wm, 'inst', mobileLod); // look3
    const im = mkInst(wallGeo[t], wm, rows.length);
    rows.forEach(([, x, y, z, hd, len], i) => {
      q.setFromAxisAngle(up, hd);
      if (t === 1) im.setMatrixAt(i, m.compose(p.set(x, z, -y), q, s.set(len, 1, 1)));
      else im.setMatrixAt(i, m.compose(p.set(x, z + wallH[t] / 2 - .03, -y), q, s.set(len, wallH[t], wallW[t])));
    });
    im.receiveShadow = shadows; out.push(im);
  });
  const gr = mobileLod ? [] : meta.gravel ?? [];
  if (gr.length) {
    const im = mkInst(new THREE.BoxGeometry(1, .03, 1), new THREE.MeshLambertMaterial({ color: 0xb4ab9a }), gr.length);
    gr.forEach(([x, y, z, hd, len], i) => im.setMatrixAt(i, m.compose(p.set(x, z + .02, -y), q.setFromAxisAngle(up, hd), s.set(len, 1, .9))));
    im.receiveShadow = shadows; out.push(im);
  }
  const parts: G[] = [];
  for (const [t, x, y, z, hd, a] of meta.props ?? []) {
    const f = PROPS[t];
    if (!f || (mobileLod && t === 'table')) continue;
    m.compose(p.set(x, z, -y), q.setFromAxisAngle(up, hd), s.set(1, 1, 1));
    for (const g of f(a, x, y)) parts.push(g.applyMatrix4(m));
  }
  if (parts.length) {
    const mesh = new THREE.Mesh(mergeGeometries(parts, false)!, new THREE.MeshLambertMaterial({ vertexColors: true }));
    mesh.receiveShadow = shadows; mesh.castShadow = shadows && !mobileLod;
    for (const g of parts) g.dispose();
    out.push(mesh);
  }
  return out;
}
