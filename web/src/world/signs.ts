import * as THREE from 'three';
import { buildStorefronts, type VenueSign } from './storefronts';
import { lookOf } from './storefront_style';
import { drawSignRow } from './storefront_sign';
import { applyBrand } from './brands';

/** Shop signs with real names (OSM), drawn into one canvas texture per tile. */
export type Sign = VenueSign;

const ROW = 96, TEXW = 1024;
/** Phones draw the sign canvas at half resolution: busy tiles (Langstrasse) reach 1024x8192 = 44 MB GPU each otherwise. */
const SCALE = matchMedia('(pointer: coarse)').matches ? 0.5 : 1;
/** Phones: shrink a loaded texture image to half size before its GPU upload (wildposters 2048² = 22 MB otherwise). */
function halveOnPhone(t: THREE.Texture) {
  const im = t.image as HTMLImageElement;
  if (SCALE === 1 || !im?.width) return;
  const c = document.createElement('canvas'); c.width = im.width * SCALE; c.height = im.height * SCALE;
  c.getContext('2d')!.drawImage(im, 0, 0, c.width, c.height);
  t.image = c; t.needsUpdate = true;
}

/** All sign materials, so the night factor can light them up like illuminated shop signs. */
const signMats = new Set<THREE.MeshLambertMaterial>();
/** Drop a shop-sign material from the night-glow list (tile unload). */
export const forgetSignMat = (m: THREE.Material) => { signMats.delete(m as THREE.MeshLambertMaterial); };
export function setSignNight(night: number) {
  for (const m of signMats) m.emissiveIntensity = 0.25 + night * (m.userData.neon ? 1.6 : 0.9);
}

/** Name signs (one mesh) plus the venue details of storefronts.ts (awnings, blade signs, props) as one group. */
export function buildSigns(signs: Sign[]): THREE.Object3D | null {
  const mesh = buildSignMesh(signs);
  if (!mesh) return null;
  const grp = new THREE.Group();
  grp.add(mesh, ...buildStorefronts(signs.filter((s) => !(s as { nf?: number }).nf))); // nf = plain wall plate (no awning / blade / props)
  return grp;
}

function buildSignMesh(signs: Sign[]): THREE.Mesh | null {
  if (!signs.length) return null;
  const c = document.createElement('canvas');
  const H = THREE.MathUtils.ceilPowerOfTwo(signs.length * ROW); // logical canvas height (uv space)
  c.width = TEXW * SCALE;
  c.height = H * SCALE;
  const g = c.getContext('2d')!;
  g.scale(SCALE, SCALE);
  const pos: number[] = [], uv: number[] = [], nrm: number[] = [], idx: number[] = [];
  signs.forEach((s, i) => {
    const look = applyBrand(lookOf(s), s);
    const y0 = i * ROW;
    drawSignRow(g, y0, TEXW, ROW, s, look);
    // sign width in metres follows the text length (about 0.3 m per glyph), capped by the facade
    const wm = (s as { big?: number }).big ? s.w : Math.max(1.6, Math.min(s.w, s.name.length * 0.3 + 0.6));
    // quad 0.15 m in front of the wall; outward normal = (ty, -tx)
    const ox = s.ty, oy = -s.tx, hw = wm / 2, hh = wm * ROW / TEXW / 2 * 1.6 * look.hf;
    const cx = s.x + ox * 0.15, cy = s.y + oy * 0.15;
    const corners = [[-hw, -hh], [hw, -hh], [hw, hh], [-hw, hh]];
    const b = pos.length / 3;
    for (const [u, v] of corners) {
      const x = cx + s.tx * u, y = cy + s.ty * u;
      pos.push(x, s.z + v, -y);
      nrm.push(ox, 0, -oy);
    }
    const v0 = 1 - (y0 + ROW) / H, v1 = 1 - y0 / H;
    uv.push(0, v0, 1, v0, 1, v1, 0, v1);
    idx.push(b, b + 1, b + 2, b, b + 2, b + 3);
  });
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  geo.setIndex(idx);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  if (SCALE < 1) tex.onUpdate = () => { c.width = c.height = 1; }; // phones: free the canvas pixels once on the GPU
  const mat = new THREE.MeshLambertMaterial({ map: tex, emissive: 0xffffff, emissiveMap: tex, emissiveIntensity: 0.25 });
  mat.userData.neon = signs.some((s) => ['bar', 'pub', 'nightclub'].includes(s.kind));
  signMats.add(mat);
  return new THREE.Mesh(geo, mat);
}

/** Alternative Linke posters: rows [x, y, z, tx, ty, variant, count], F4 portrait 0.895 x 1.28 m in a frame. */
let posterTex: THREE.Texture | null = null;
const POSTER_VARIANTS = 1;

export function buildPosters(rows: number[][]): THREE.Object3D[] {
  if (!rows.length) return [];
  posterTex ??= Object.assign(new THREE.TextureLoader().load('/tex/posters.webp'), { colorSpace: THREE.SRGBColorSpace, anisotropy: 4 });
  const pos: number[] = [], uv: number[] = [], nrm: number[] = [], idx: number[] = [];
  const frames: number[] = [], fidx: number[] = [];
  const quad = (P: number[], I: number[], cx: number, cy: number, z: number, tx: number, ty: number, hw: number, hh: number, off: number, uvs?: number[]) => {
    const ox = ty, oy = -tx, b = P.length / 3;
    for (const [u, v] of [[-hw, -hh], [hw, -hh], [hw, hh], [-hw, hh]]) {
      P.push(cx + ox * off + tx * u, z + v, -(cy + oy * off + ty * u));
      if (P === pos) nrm.push(ox, 0, -oy);
    }
    if (uvs) uv.push(...uvs);
    I.push(b, b + 1, b + 2, b, b + 2, b + 3);
  };
  for (const [x, y, z, tx, ty, variant, count] of rows) {
    const n = count || 1, gap = 0.98;
    quad(frames, fidx, x, y, z, tx, ty, (n * gap) / 2 + 0.08, 0.74, 0.04);
    for (let k = 0; k < n; k++) {
      const c = (k - (n - 1) / 2) * gap, v = (variant + k) % POSTER_VARIANTS;
      const u0 = v / POSTER_VARIANTS, u1 = (v + 1) / POSTER_VARIANTS;
      quad(pos, idx, x + tx * c, y + ty * c, z, tx, ty, 0.4475, 0.64, 0.07, [u0, 0, u1, 0, u1, 1, u0, 1]);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  const f = new THREE.BufferGeometry();
  f.setAttribute('position', new THREE.Float32BufferAttribute(frames, 3));
  f.setIndex(fidx);
  f.computeVertexNormals();
  return [new THREE.Mesh(g, new THREE.MeshLambertMaterial({ map: posterTex })), new THREE.Mesh(f, new THREE.MeshLambertMaterial({ color: 0x2a2d30 }))];
}

/** Wild-posting walls (pasted real past events, own designs): rows [x, y, z, tx, ty, sheet, rot], 1.5 x 1.5 m RGBA pieces, 4x4 atlas. */
let wildTex: THREE.Texture | null = null;

export function buildWildPosters(rows: number[][]): THREE.Object3D[] {
  if (!rows.length) return [];
  wildTex ??= Object.assign(new THREE.TextureLoader().load('/tex/wildposters.webp', halveOnPhone), { colorSpace: THREE.SRGBColorSpace, anisotropy: 4 });
  const pos: number[] = [], uv: number[] = [], nrm: number[] = [], idx: number[] = [];
  rows.forEach(([x, y, z, tx, ty, sheet, rot], n) => {
    const ox = ty, oy = -tx, b = pos.length / 3, hw = 0.75, hh = 0.75, off = 0.05 + n * 0.0008;
    const c = Math.cos(rot), s = Math.sin(rot);
    for (const [u0, v0] of [[-hw, -hh], [hw, -hh], [hw, hh], [-hw, hh]]) {
      const u = u0 * c - v0 * s, v = u0 * s + v0 * c;
      pos.push(x + ox * off + tx * u, z + v, -(y + oy * off + ty * u));
      nrm.push(ox, 0, -oy);
    }
    const col = sheet % 4, row = Math.floor(sheet / 4);
    const a = col / 4, bb = (col + 1) / 4, t0 = 1 - (row + 1) / 4, t1 = 1 - row / 4;
    uv.push(a, t0, bb, t0, bb, t1, a, t1);
    idx.push(b, b + 1, b + 2, b, b + 2, b + 3);
  });
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  return [new THREE.Mesh(g, new THREE.MeshLambertMaterial({ map: wildTex, alphaTest: 0.5 }))];
}

/** Fictional graffiti tags on walls: rows [x, y, z, tx, ty, idx, scale]; 4x4 RGBA atlas. */
let graffitiTex: THREE.Texture | null = null;

export function buildGraffiti(rows: number[][]): THREE.Object3D[] {
  if (!rows.length) return [];
  graffitiTex ??= Object.assign(new THREE.TextureLoader().load('/tex/graffiti.png', halveOnPhone), { colorSpace: THREE.SRGBColorSpace, anisotropy: 4 });
  const pos: number[] = [], uv: number[] = [], nrm: number[] = [], idx: number[] = [];
  rows.forEach(([x, y, z, tx, ty, k, sc], n) => {
    const ox = ty, oy = -tx, b = pos.length / 3, h = 0.8 * sc, off = 0.035 + n * 0.0005;
    for (const [u, v] of [[-h, -h], [h, -h], [h, h], [-h, h]]) {
      pos.push(x + ox * off + tx * u, z + v, -(y + oy * off + ty * u)); nrm.push(ox, 0, -oy);
    }
    const c = k % 4, r = Math.floor(k / 4);
    uv.push(c / 4, 1 - (r + 1) / 4, (c + 1) / 4, 1 - (r + 1) / 4, (c + 1) / 4, 1 - r / 4, c / 4, 1 - r / 4);
    idx.push(b, b + 1, b + 2, b, b + 2, b + 3);
  });
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  return [new THREE.Mesh(g, new THREE.MeshLambertMaterial({ map: graffitiTex, transparent: true, depthWrite: false,
    polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }))];
}
