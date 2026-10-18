import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { ver } from '../engine/assetver';

/**
 * Tree models (pipeline/trees): per class 2 detail variants (lod 0), 1 simplified model (lod 1) and a baked impostor (tree_impostor.ts).
 * Models are normalised (height 1, crown diameter 1, foot at 0). Bark + foliage are merged into ONE geometry (1 draw call)
 * sharing the leaf atlas (bark UVs point at an opaque tile); attribute aLeaf (0 bark, 1 leaf) drives wind and autumn colour.
 * Class ids match pipeline/trees_dims.py.
 */
export const CLASSES = ['broadleaf', 'cherry', 'whiteblossom', 'plane', 'linden', 'maple', 'chestnut', 'birch', 'conifer', 'columnar',
  'robinia', 'ash', 'oak', 'beech', 'pine'];
/** Mid-October colour: [share of the crown that turns, hue 0 yellow .. 0.5 orange .. 1 red]. */
export const AUTUMN: [number, number][] = [[.25, .15], [.75, .65], [.5, .35], [.3, .2], [.5, .1], [.65, .55], [.5, .3], [.7, .05],
  [0, 0], [.45, .1], [.3, .1], [.25, .05], [.2, .45], [.5, .45], [0, 0]];
export type TreeModel = { geo: THREE.BufferGeometry; zb: number };
export const models: { lod0: TreeModel[]; lod1: TreeModel | null }[] = CLASSES.map(() => ({ lod0: [], lod1: null }));
export const atlas = new THREE.Texture();
export const treeTime = { value: 0 };
export const treeGust = { value: 1 };

const BARK_UV = [0.875, 0.625]; // centre of the opaque atlas tile (col 3, row 2)

function prepare(root: THREE.Object3D): THREE.BufferGeometry | null {
  const parts: THREE.BufferGeometry[] = [];
  root.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    const g = m.geometry.clone();
    const n = g.getAttribute('position').count, leaf = parts.length === 1;
    const c4 = g.getAttribute('color'), c3 = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) { c3[i * 3] = c4.getX(i); c3[i * 3 + 1] = c4.getY(i); c3[i * 3 + 2] = c4.getZ(i); }
    g.setAttribute('color', new THREE.BufferAttribute(c3, 3));
    if (!leaf) g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(n * 2).map((_, i) => BARK_UV[i & 1]), 2));
    g.setAttribute('aLeaf', new THREE.BufferAttribute(new Float32Array(n).fill(leaf ? 1 : 0), 1));
    // plain float normals/positions so merging works regardless of the glTF quantisation
    for (const k of ['position', 'normal', 'uv']) {
      const a = g.getAttribute(k), f = new Float32Array(a.count * a.itemSize);
      for (let i = 0; i < a.count; i++) for (let c = 0; c < a.itemSize; c++) f[i * a.itemSize + c] = [a.getX, a.getY, a.getZ][c].call(a, i);
      g.setAttribute(k, new THREE.BufferAttribute(f, a.itemSize));
    }
    parts.push(g);
  });
  return parts.length ? mergeGeometries(parts, false) : null;
}

/** variants: how many lod-0 variants per class to load (phones: 1, the field falls back to variant 0). */
export async function loadTrees(base = '/models/trees', variants = 2) {
  const manifest = (await (await fetch(`${base}/manifest.json`)).json()) as { cls: string; file: string; variant: number; lod: number; zb: number }[];
  const img = new Image();
  const loaded = new Promise<void>((res, rej) => { img.onload = () => res(); img.onerror = rej; });
  img.src = ver(`${base}/leaves.webp`);
  await loaded;
  atlas.image = img; atlas.flipY = false; atlas.colorSpace = THREE.SRGBColorSpace;
  atlas.generateMipmaps = true; atlas.minFilter = THREE.LinearMipmapLinearFilter; atlas.anisotropy = 4; atlas.needsUpdate = true;
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  await Promise.all(manifest.filter((e) => e.lod || e.variant < variants).map(async (e) => {
    const g = await loader.loadAsync(`${base}/${e.file}`);
    const geo = prepare(g.scene);
    const ci = CLASSES.indexOf(e.cls);
    if (!geo || ci < 0) return;
    const model = { geo, zb: e.cls === 'conifer' ? -1 : e.zb };
    if (e.lod) models[ci].lod1 = model; else models[ci].lod0[e.variant] = model;
  }));
}

const GLSL_COMMON = `
attribute vec4 iTree; attribute float aLeaf;
uniform float uTime; uniform float uGust; uniform float uZb;
varying float vAut; varying vec3 vAutCol;`;
const GLSL_VERT = `
vec3 transformed = vec3( position );
float yy = position.y;
if (uZb > 0.0) {   // real crown base (Kronenansatz) from the data: stretch trunk / crown around the model's own base
  float b = iTree.x;
  yy = yy < uZb ? yy * (b / uZb) : b + (yy - uZb) * (1.0 - b) / (1.0 - uZb);
  transformed.y = yy;
}
float ph = iTree.w * 6.2831;
float sway = aLeaf * smoothstep(0.15, 1.0, yy);
transformed.x += sway * (sin(uTime * 1.25 + ph + yy * 2.0) * 0.011 + sin(uTime * 3.7 + ph * 1.7 + position.x * 9.0 + position.z * 7.0) * 0.0035 * uGust);
transformed.z += sway * cos(uTime * 1.05 + ph) * 0.008;
float blot = 0.5 + 0.5 * sin(position.x * 8.0 + iTree.w * 40.0) * sin(position.z * 8.0 + iTree.w * 17.0 + position.y * 3.0);
vAut = clamp(iTree.y * aLeaf * (0.5 + 0.9 * blot), 0.0, 1.0);
vec3 cy = vec3(.92, .74, .14), co = vec3(.84, .42, .08), cr = vec3(.66, .13, .10);
vec3 ac = iTree.z < 0.5 ? mix(cy, co, iTree.z * 2.0) : mix(co, cr, (iTree.z - 0.5) * 2.0);
vAutCol = ac * ac;`;
const GLSL_FRAG = `
#include <color_fragment>
{ float lum = dot(diffuseColor.rgb, vec3(.3, .55, .15));
  diffuseColor.rgb = mix(diffuseColor.rgb, vAutCol * (0.3 + lum * 2.8), vAut); }`;

/** Lambert material with crown-base remap, wind and autumn tint (instance attribute iTree = base, autumn amount, hue, phase). */
export function treeMaterial(zb: number, imp: THREE.Texture | null = null): THREE.MeshLambertMaterial {
  const impostor = !!imp;
  const mat = new THREE.MeshLambertMaterial({ map: imp ?? atlas, vertexColors: !impostor, alphaTest: .5, side: THREE.DoubleSide });
  mat.customProgramCacheKey = () => (impostor ? 'treeimp' : 'tree');
  mat.onBeforeCompile = (sh) => {
    sh.uniforms.uTime = treeTime; sh.uniforms.uGust = treeGust; sh.uniforms.uZb = { value: zb };
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>' + GLSL_COMMON)
      .replace('#include <begin_vertex>', impostor ? 'vec3 transformed = vec3( position );' + IMP_VERT : GLSL_VERT);
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying float vAut; varying vec3 vAutCol;')
      .replace('#include <color_fragment>', GLSL_FRAG);
    if (impostor) {
      sh.vertexShader = sh.vertexShader.replace('attribute vec4 iTree;', 'attribute vec4 iTree; attribute float iCls;')
        .replace('#include <beginnormal_vertex>', 'vec3 objectNormal = vec3(0.0, 1.0, 0.0);')
        .replace('#include <uv_vertex>', '#include <uv_vertex>\nvMapUv = (vec2(mod(iCls, 4.0), floor(iCls / 4.0)) + uv) * 0.25;')
        .replace('#include <project_vertex>', `vec4 org = modelViewMatrix * instanceMatrix * vec4(0.0, 0.0, 0.0, 1.0);
vec4 mvPosition = org + vec4(position.x * instanceMatrix[0][0], position.y * instanceMatrix[1][1], 0.0, 0.0);
gl_Position = projectionMatrix * mvPosition;`);
    }
  };
  return mat;
}
const IMP_VERT = `
vAut = iTree.y * (0.55 + 0.7 * fract(iTree.w * 7.0)) * step(0.5, aLeaf + 1.0);
vec3 cy = vec3(.92, .74, .14), co = vec3(.84, .42, .08), cr = vec3(.66, .13, .10);
vec3 ac = iTree.z < 0.5 ? mix(cy, co, iTree.z * 2.0) : mix(co, cr, (iTree.z - 0.5) * 2.0);
vAutCol = ac * ac;`;
