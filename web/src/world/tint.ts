import * as THREE from 'three';
import type { Human, Model } from './humans';

/**
 * Runtime clothing recolour for the baked MakeHuman atlases (no extra textures): every vertex gets a zone mask from its bone weights and
 * rest height (shirt/jacket = torso + arms, trousers = pelvis + legs, shoes = feet), the fragment shader replaces the texel colour by
 * tint x (texel luma / zone mean luma), so folds, seams and stripes survive. Skin on bare forearms is spared (arm vertices with warm texels).
 * Material is cloned per person (uniforms differ); geometry and texture stay shared.
 */
const AUTUMN_TOPS = [0x1f2b45, 0x15171a, 0x4a5a2e, 0x9a7b4f, 0x7a2430, 0xb8862b, 0x6b7077, 0x1d4a36, 0xa5522a, 0xd8cdb6, 0x2c6a73, 0x8a2f2f, 0x3a3f66, 0xc9c4bb, 0x5a3b2a, 0xd9a2b0, 0x4f6f9a];
const TROUSERS = [0x2d4568, 0x1b1d22, 0x4b4f58, 0xb8aa8a, 0x55583a, 0x4a3828, 0x6a7fa3, 0x23262d, 0x7d6b50];
const SHOES = [0xf0f0ec, 0x16171a, 0x4a3426, 0x6d7074, 0x1f2a44, 0xb5482c, 0xd9d4c4];

interface Uniforms { uT0: THREE.IUniform<THREE.Color>; uT1: THREE.IUniform<THREE.Color>; uT2: THREE.IUniform<THREE.Color>; uAvg: THREE.IUniform<THREE.Vector3>; uAmt: THREE.IUniform<THREE.Vector3> }
interface TintState { u: Uniforms }
const state = new WeakMap<Human, TintState>();
const prepared = new WeakMap<Model, Vector3Avg>();
type Vector3Avg = THREE.Vector3;

const lin = (c: number) => Math.pow(c / 255, 2.2);

/** Zone attribute + zone mean luma, once per model (shared geometry). Returns false when the model has no skinned mesh. */
export function prepareTint(m: Model): boolean {
  if (prepared.has(m)) return true;
  let mesh: THREE.SkinnedMesh | null = null;
  m.scene.traverse((o) => { if ((o as THREE.SkinnedMesh).isSkinnedMesh && !mesh) mesh = o as THREE.SkinnedMesh; });
  const sm = mesh as THREE.SkinnedMesh | null;
  if (!sm) return false;
  m.scene.updateMatrixWorld(true);
  const g = sm.geometry, pos = g.attributes.position, si = g.attributes.skinIndex, sw = g.attributes.skinWeight, uv = g.attributes.uv;
  const role = sm.skeleton.bones.map((b) => {
    const n = b.name;
    if (/^(spine_0|clavicle|upperarm|lowerarm)/.test(n)) return /arm/.test(n) && !/^clavicle/.test(n) ? 4 : 1;     // 4 = arm (skin check), 1 = shirt
    if (/^(pelvis|thigh|calf)/.test(n)) return 2;
    if (/^(foot|ball)/.test(n)) return 3;
    return 0;                                                                                                     // head, neck, hands, fingers
  });
  const zone = new Float32Array(pos.count * 4), v = new THREE.Vector3(), h = m.height;
  for (let i = 0; i < pos.count; i++) {
    let sh = 0, tr = 0, fo = 0, arm = 0;
    for (let k = 0; k < 4; k++) {
      const w = sw.getComponent(i, k), r = role[si.getComponent(i, k)];
      if (r === 1) sh += w; else if (r === 4) { sh += w; arm += w; } else if (r === 2) tr += w; else if (r === 3) fo += w;
    }
    v.fromBufferAttribute(pos, i).applyMatrix4(sm.matrixWorld);
    const y = v.y / h;                                                                                            // 0 = sole, 1 = top of head
    const shoe = fo * (1 - Math.min(1, Math.max(0, (y - 0.045) / 0.03)));                                        // only the lowest ~7 cm count as shoe
    zone[i * 4] = Math.min(1, sh); zone[i * 4 + 1] = Math.min(1, tr + fo - shoe); zone[i * 4 + 2] = shoe; zone[i * 4 + 3] = arm;
  }
  g.setAttribute('aZone', new THREE.BufferAttribute(zone, 4));
  // zone mean luma from the atlas texels under the zone's vertices
  const avg = new THREE.Vector3(0.3, 0.3, 0.3), img = (sm.material as THREE.MeshStandardMaterial).map?.image as CanvasImageSource | undefined;
  try {
    if (img && uv) {
      const S = 256, c = document.createElement('canvas'); c.width = c.height = S;
      const cx = c.getContext('2d', { willReadFrequently: true })!; cx.drawImage(img, 0, 0, S, S);
      const d = cx.getImageData(0, 0, S, S).data, sum = [0, 0, 0], cnt = [0, 0, 0];
      for (let i = 0; i < pos.count; i++) {
        const px = Math.min(S - 1, Math.max(0, Math.floor(uv.getX(i) * S))), py = Math.min(S - 1, Math.max(0, Math.floor(uv.getY(i) * S))), o = (py * S + px) * 4;
        const L = 0.299 * lin(d[o]) + 0.587 * lin(d[o + 1]) + 0.114 * lin(d[o + 2]);
        for (let z = 0; z < 3; z++) if (zone[i * 4 + z] > 0.9 && (z > 0 || zone[i * 4 + 3] < 0.1)) { sum[z] += L; cnt[z]++; }
      }
      for (let z = 0; z < 3; z++) if (cnt[z] > 8) avg.setComponent(z, Math.max(0.02, sum[z] / cnt[z]));
    }
  } catch { /* tainted/unsupported image: keep defaults */ }
  prepared.set(m, avg);
  return true;
}

function attach(h: Human, m: Model): TintState | null {
  const avg = prepared.get(m);
  if (!avg) return null;
  let st = state.get(h);
  if (st) return st;
  const u: Uniforms = { uT0: { value: new THREE.Color() }, uT1: { value: new THREE.Color() }, uT2: { value: new THREE.Color() }, uAvg: { value: avg.clone() }, uAmt: { value: new THREE.Vector3() } };
  h.root.traverse((o) => {
    const sm = o as THREE.SkinnedMesh;
    if (!sm.isSkinnedMesh) return;
    const mat = (sm.material as THREE.MeshStandardMaterial).clone();
    mat.onBeforeCompile = (sh) => {
      Object.assign(sh.uniforms, u);
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute vec4 aZone; varying vec4 vZone;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvZone = aZone;');
      sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec4 vZone; uniform vec3 uT0, uT1, uT2, uAvg, uAmt;')
        .replace('#include <map_fragment>', `#include <map_fragment>
        {
          float L = dot(diffuseColor.rgb, vec3(0.299, 0.587, 0.114));
          float warm = (diffuseColor.r - diffuseColor.b) / (diffuseColor.r + diffuseColor.g + diffuseColor.b + 1e-4);
          float bare = vZone.w * smoothstep(0.16, 0.28, warm);              // bare forearm skin
          vec3 zn = smoothstep(0.47, 0.53, vZone.xyz);                      // hard edge jacket / trousers / shoes
          vec3 c = diffuseColor.rgb;
          c = mix(c, uT0 * clamp(L / uAvg.x, 0.3, 2.2), zn.x * uAmt.x * (1.0 - bare));
          c = mix(c, uT1 * clamp(L / uAvg.y, 0.3, 2.2), zn.y * uAmt.y);
          c = mix(c, uT2 * clamp(L / uAvg.z, 0.3, 2.2), zn.z * uAmt.z);
          diffuseColor.rgb = c;
        }`);
    };
    mat.customProgramCacheKey = () => 'humanTint';
    sm.material = mat;
  });
  st = { u }; state.set(h, st);
  return st;
}

const pick = <T,>(a: T[], r: number) => a[Math.floor(r * a.length) % a.length];

/** Random autumn outfit colours for a person (null = keep the baked look). `m` = the figure's model. Cheap: only uniforms change. */
export function dress(h: Human, m: Model, keep = 0.25) {
  if (m.age === 'child' || !prepareTint(m)) return;
  const st = attach(h, m);
  if (!st) return;
  const r = Math.random, u = st.u;
  u.uAmt.value.set(r() < keep ? 0 : 1, r() < keep + 0.1 ? 0 : 1, r() < 0.35 ? 0 : 1);
  u.uT0.value.set(pick(AUTUMN_TOPS, r())); u.uT1.value.set(pick(TROUSERS, r())); u.uT2.value.set(pick(SHOES, r()));
}
