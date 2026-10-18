import * as THREE from 'three';
import { nightUniform } from '../engine/materials';
import { registerLights } from './night_lights';
import { hash, lookOf, mix, type ShopSign } from './storefront_style';
import { planters, terrace } from './storefront_terrace';

/**
 * Per-tile details for ground-floor venues (rows = tile meta `signs`): coloured awnings, neon blade signs with the real
 * venue name, standing tables at bars, beer fridges at kiosks, bikes at bike shops, fruit crates at greengrocers, and
 * coloured light pools on the pavement in front of bars/clubs at night.
 * Everything of a tile is merged into one vertex-coloured mesh (1 draw call) + one additive "spill" mesh.
 * Facade frame: u = along the wall (sign tangent), v = outward, h = height above the pavement (sign z - 3.45).
 */
export type VenueSign = ShopSign;

const NEON = ['#ff3caa', '#28e6dc', '#ff3caa', '#ffb43c', '#8c64ff'];
const BARS = ['bar', 'pub', 'nightclub', 'biergarten'];

/** Shared material: vertex colour x label atlas, `aGlow` = share of the colour that is self-lit at night. */
let mat: THREE.MeshLambertMaterial | null = null;
function material(): THREE.MeshLambertMaterial {
  if (mat) return mat;
  mat = new THREE.MeshLambertMaterial({ vertexColors: true, side: THREE.DoubleSide });
  mat.onBeforeCompile = (sh) => {
    sh.uniforms.night = nightUniform;
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nattribute float aGlow;\nvarying float vGlow;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvGlow = aGlow;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform float night;\nvarying float vGlow;')
      .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += diffuseColor.rgb * vGlow * night * 1.7;');
  };
  mat.customProgramCacheKey = () => 'storefronts';
  return mat;
}

let spillMat: THREE.MeshBasicMaterial | null = null;
function spillMaterial(): THREE.MeshBasicMaterial {
  if (spillMat) return spillMat;
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d')!, gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, 'rgba(255,255,255,0.9)'); gr.addColorStop(0.5, 'rgba(255,255,255,0.35)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  spillMat = new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(c), vertexColors: true, transparent: true, depthWrite: false,
    blending: THREE.AdditiveBlending, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
  spillMat.onBeforeCompile = (sh) => {
    sh.uniforms.night = nightUniform;
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nuniform float night;')
      .replace('#include <color_fragment>', '#include <color_fragment>\ndiffuseColor.a *= night * 0.55;');
  };
  spillMat.customProgramCacheKey = () => 'storefront-spill';
  return spillMat;
}

class Builder {
  pos: number[] = []; nrm: number[] = []; uv: number[] = []; col: number[] = []; glow: number[] = []; idx: number[] = [];
  /** quad from 4 corners (three coords, CCW seen from the front); uv rect [u0, v0, u1, v1] in the label atlas */
  quad(a: number[], b: number[], c: number[], d: number[], color: THREE.Color, glow = 0, uv: number[] = [0.01, 0.99, 0.01, 0.99]) {
    const n = new THREE.Vector3(b[0] - a[0], b[1] - a[1], b[2] - a[2]).cross(new THREE.Vector3(d[0] - a[0], d[1] - a[1], d[2] - a[2])).normalize();
    const base = this.pos.length / 3;
    for (const p of [a, b, c, d]) { this.pos.push(...p); this.nrm.push(n.x, n.y, n.z); this.col.push(color.r, color.g, color.b); this.glow.push(glow); }
    this.uv.push(uv[0], uv[1], uv[2], uv[1], uv[2], uv[3], uv[0], uv[3]);
    this.idx.push(base, base + 1, base + 2, base, base + 2, base + 3);
  }
  mesh(m: THREE.Material, glow = true): THREE.Mesh | null {
    if (!this.idx.length) return null;
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(this.pos, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(this.nrm, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(this.uv, 2));
    g.setAttribute('color', new THREE.Float32BufferAttribute(this.col, 3));
    if (glow) g.setAttribute('aGlow', new THREE.Float32BufferAttribute(this.glow, 1));
    g.setIndex(this.idx);
    return new THREE.Mesh(g, m);
  }
}

/** Facade frame -> three coordinates. */
function frame(s: VenueSign) {
  const ox = s.ty, oy = -s.tx, gz = s.z - 3.45;
  return (u: number, v: number, h: number) => [s.x + s.tx * u + ox * v, gz + h, -(s.y + s.ty * u + oy * v)];
}
type Pt = (u: number, v: number, h: number) => number[];

function box(b: Builder, p: Pt, u: number, v: number, h0: number, du: number, dv: number, dh: number, c: THREE.Color, glow = 0, glowFront = false) {
  const [a, bb, cc, d, e, f, g, hh] = [[u - du, v - dv, h0], [u + du, v - dv, h0], [u + du, v + dv, h0], [u - du, v + dv, h0],
    [u - du, v - dv, h0 + dh], [u + du, v - dv, h0 + dh], [u + du, v + dv, h0 + dh], [u - du, v + dv, h0 + dh]].map((q) => p(q[0], q[1], q[2]));
  b.quad(e, f, g, hh, c, 0);                       // top
  b.quad(a, d, cc, bb, c, 0);                      // bottom
  b.quad(a, bb, f, e, c, 0);                       // side towards the wall
  b.quad(bb, cc, g, f, c, 0);                      // +u
  b.quad(cc, d, hh, g, c, glowFront ? glow : 0);   // outward front
  b.quad(d, a, e, hh, c, 0);                       // -u
}

function awning(b: Builder, p: Pt, u0: number, u1: number, c: THREE.Color, striped: boolean, h0 = 2.85) {
  const white = new THREE.Color(0xf0ece2), n = Math.max(2, Math.round((u1 - u0) / 0.32)), du = (u1 - u0) / n;
  const shade = c.clone().multiplyScalar(0.82);
  for (let i = 0; i < n; i++) {
    const col = striped && i % 2 ? white : c, a = u0 + i * du, e = a + du;
    b.quad(p(a, 0.05, h0), p(e, 0.05, h0), p(e, 1.15, h0 - 0.5), p(a, 1.15, h0 - 0.5), col);          // sloped cloth
    b.quad(p(a, 1.15, h0 - 0.5), p(e, 1.15, h0 - 0.5), p(e, 1.17, h0 - 0.74), p(a, 1.17, h0 - 0.74), striped ? col : shade); // valance
  }
}

/** Ground-floor facade colour as pilasters at the wall ends + stall riser (only for venues with photo notes). */
function framing(b: Builder, p: Pt, s: VenueSign, fc: string) {
  if (s.w > 8.6) return;
  const col = new THREE.Color(fc), riser = new THREE.Color(mix(fc, '#000000', 0.18)), e = s.w / 2 + 0.3, v = 0.05;
  for (const sg of [-1, 1]) b.quad(p(sg * e, v, 0), p(sg * (e - 0.38), v, 0), p(sg * (e - 0.38), v, 3.9), p(sg * e, v, 3.9), col);
  b.quad(p(-e, v, 0), p(e, v, 0), p(e, v, 0.42), p(-e, v, 0.42), riser);
}

function standingTable(b: Builder, p: Pt, u: number, v: number) {
  const metal = new THREE.Color(0x30343a), top = new THREE.Color(0x9b7048), N = 8;
  const ring = (r: number, h: number) => Array.from({ length: N }, (_, i) => p(u + Math.cos(i / N * 6.283) * r, v + Math.sin(i / N * 6.283) * r, h));
  const t0 = ring(0.36, 1.05), t1 = ring(0.36, 1.1), l0 = ring(0.035, 0), l1 = ring(0.035, 1.05);
  for (let i = 0; i < N; i++) {
    const j = (i + 1) % N;
    b.quad(t0[i], t0[j], t1[j], t1[i], top);
    b.quad(l0[i], l0[j], l1[j], l1[i], metal);
    b.quad(t1[i], t1[j], p(u, v, 1.1), p(u, v, 1.1), top);
  }
  box(b, p, u, v, 0, 0.2, 0.2, 0.02, metal);
}

function bike(b: Builder, p: Pt, u: number, v: number, c: THREE.Color) {
  const dark = new THREE.Color(0x1c1c20), R = 0.33, N = 10, w = 0.025;
  const bar = (u0: number, h0: number, u1: number, h1: number, col: THREE.Color, t = 0.03) => {
    const dx = u1 - u0, dh = h1 - h0, L = Math.hypot(dx, dh), nu = -dh / L * t, nh = dx / L * t;
    b.quad(p(u0 - nu, v, h0 - nh), p(u1 - nu, v, h1 - nh), p(u1 + nu, v, h1 + nh), p(u0 + nu, v, h0 + nh), col);
  };
  for (const cu of [u - 0.5, u + 0.5]) {
    for (let i = 0; i < N; i++) {
      const a0 = i / N * 6.283, a1 = (i + 1) / N * 6.283;
      bar(cu + Math.cos(a0) * R, R + Math.sin(a0) * R, cu + Math.cos(a1) * R, R + Math.sin(a1) * R, dark, w);
    }
  }
  bar(u - 0.5, R, u - 0.05, R + 0.28, c); bar(u - 0.05, R + 0.28, u + 0.5, R, c); bar(u - 0.5, R, u + 0.12, R + 0.5, c);
  bar(u + 0.12, R + 0.5, u - 0.05, R + 0.28, c); bar(u + 0.12, R + 0.5, u + 0.5, R, c); bar(u + 0.5, R, u + 0.4, R + 0.55, c);
  bar(u + 0.35, R + 0.58, u + 0.48, R + 0.58, dark, 0.02);
}

function crates(b: Builder, p: Pt, u: number, rnd: number) {
  const wood = new THREE.Color(0x93693a), fruit = [0xd22b1e, 0xf09a1e, 0x72a031, 0xf5d83c, 0x7a2a66, 0x3e8f3a];
  for (let i = 0; i < 4; i++) {
    const cu = u + (i - 1.5) * 0.62, f = new THREE.Color(fruit[(rnd >> (i * 3)) % fruit.length]);
    box(b, p, cu, 0.6, 0, 0.27, 0.19, 0.28, wood);
    box(b, p, cu, 0.6, 0.28, 0.24, 0.16, 0.07, f);
    if (i % 2 === 0) { box(b, p, cu, 0.6, 0.28, 0.27, 0.19, 0.26, wood); box(b, p, cu, 0.6, 0.54, 0.24, 0.16, 0.07, new THREE.Color(fruit[(rnd >> (i * 2 + 1)) % fruit.length])); }
  }
}

/** Neon / illuminated label atlas: one 512x64 row per label. */
function labelAtlas(rows: { text: string; color: string; bg?: string; cross?: boolean }[]) {
  // phones draw at half resolution (busy Langstrasse tiles reach 512x4096); uvs use the logical height H
  const S = matchMedia('(pointer: coarse)').matches ? 0.5 : 1, H = THREE.MathUtils.ceilPowerOfTwo(rows.length * 64 + 8);
  const c = document.createElement('canvas'); c.width = 512 * S; c.height = H * S;
  const g = c.getContext('2d')!;
  g.scale(S, S);
  g.fillStyle = '#fff'; g.fillRect(0, 0, 8, 8);
  rows.forEach((r, i) => {
    const y = 8 + i * 64;
    g.fillStyle = r.bg ?? '#120d1a'; g.fillRect(0, y, 512, 64);
    g.strokeStyle = r.color; g.lineWidth = 3; g.shadowColor = r.color; g.shadowBlur = 10; g.strokeRect(5, y + 5, 502, 54);
    g.fillStyle = r.color; g.textAlign = 'center'; g.textBaseline = 'middle';
    if (r.cross) {
      g.fillRect(236, y + 12, 40, 40); g.fillRect(222, y + 26, 68, 12);
    } else {
      let size = 40; const t = r.text.toUpperCase();
      g.font = `700 ${size}px "Barlow Condensed", "Arial Narrow", sans-serif`;
      const w = g.measureText(t).width;
      if (w > 470) { size = Math.floor(size * 470 / w); g.font = `700 ${size}px "Barlow Condensed", "Arial Narrow", sans-serif`; }
      g.fillText(t, 256, y + 33);
    }
    g.shadowBlur = 0;
  });
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  return { tex: t, h: H };
}

export function buildStorefronts(signs: VenueSign[] | undefined): THREE.Object3D[] {
  if (!signs?.length) return [];
  const shopPts: number[] = [];
  const b = new Builder(), spill = new Builder(), labels: { text: string; color: string; bg?: string; cross?: boolean }[] = [];
  const blades: { p: Pt; u: number; row: number; color: string }[] = [];
  for (const s of signs) {
    const h = hash(s.name), p = frame(s), k = s.kind, wide = Math.min(s.w, 5.2), look = lookOf(s);
    const isBar = BARS.includes(k);
    {   // window light on the pavement in front (night_lights): bars neon-coloured, other open shops warm white
      const lit = isBar || ((['restaurant', 'fast_food', 'convenience', 'kiosk', 'pharmacy', 'tobacco'].includes(k) ? 0.8 : 0.35) > (h % 100) / 100);
      if (lit) {
        const q = p(0, 1.3, 1.4), nc = isBar ? new THREE.Color(look.neon ?? NEON[(h >>> 2) % NEON.length]) : new THREE.Color(1, 0.8, 0.5);
        const k2 = isBar ? 1.0 : 0.7;
        shopPts.push(q[0], q[1], q[2], isBar ? 8 : 6.5, nc.r * k2, nc.g * k2, nc.b * k2);
      }
    }
    if (look.fc) framing(b, p, s, look.fc);
    if (look.aw && wide > 2.4 && s.pd !== undefined && s.pd >= 0.9) awning(b, p, -wide / 2, wide / 2, new THREE.Color(look.aw), look.stripes);
    const edge = s.w / 2 - 0.35;
    if (look.blade || isBar || k === 'pharmacy' || (!s.v && ((k === 'restaurant' && h % 3 === 0) || (k === 'fast_food' && h % 2 === 1)))) {
      const real = look.blade || !!s.v;
      const color = k === 'pharmacy' ? '#32dc82' : real ? look.fg : k === 'restaurant' ? '#ffd28c' : k === 'fast_food' ? '#ff5a46' : NEON[(h >>> 2) % NEON.length];
      labels.push({ text: s.name, color, bg: real && look.blade ? look.bg : undefined, cross: k === 'pharmacy' });
      blades.push({ p, u: h % 2 ? edge : -edge, row: labels.length - 1, color });
    }
    if (look.seat) terrace(b, p, s, look);
    if (look.plants) planters(b, p, s);
    if (isBar) {
      if (!look.seat) for (const sx of [-1, 1]) if (h >> (4 + (sx > 0 ? 1 : 0)) & 1) standingTable(b, p, sx * Math.max(0.9, s.w / 2 - 0.9), 1.3);
      const col = new THREE.Color(look.neon ?? NEON[(h >>> 2) % NEON.length]);
      const r = k === 'nightclub' ? 2.6 : 1.9;
      spill.quad(p(-r * 1.4, 0.1, 0.06), p(r * 1.4, 0.1, 0.06), p(r * 1.4, 0.1 + r * 2, 0.06), p(-r * 1.4, 0.1 + r * 2, 0.06), col, 0, [0, 0, 1, 1]);
    }
    if (k === 'kiosk' || k === 'convenience' || k === 'tobacco') {
      const u = s.w / 2 - 0.55;
      box(b, p, -u, 0.45, 0, 0.38, 0.32, 1.85, new THREE.Color(0xe8ecef));
      box(b, p, -u, 0.45, 0.25, 0.3, 0.33, 1.4, new THREE.Color(0x9cc8ea), 1, true);
    }
    if (k === 'bicycle') {
      const cols = [0xd22b1e, 0x1f5fb8, 0xf0aa1e, 0x2d8a5a, 0x222226];
      for (let i = 0; i < 3 && (i + 1) * 1.45 < s.w; i++) bike(b, p, (i - 1) * 1.45, 0.9 + (i % 2) * 0.12, new THREE.Color(cols[(h >> (i * 2)) % cols.length]));
    }
    if (k === 'greengrocer' || (k === 'florist' && h % 2 === 0)) crates(b, p, 0, h >> 3);
  }
  const out: THREE.Object3D[] = [];
  if (labels.length) {
    const { tex, h: ah } = labelAtlas(labels);
    for (const bl of blades) {
      const { p, u } = bl, y0 = 8 + bl.row * 64, v0 = 1 - (y0 + 64) / ah, v1 = 1 - y0 / ah, dark = new THREE.Color(0x2a2d30);
      // blade sign hangs from a bracket, perpendicular to the wall, text reads along the street side
      b.quad(p(u, 0.1, 3.35), p(u, 1.25, 3.35), p(u, 1.25, 2.9), p(u, 0.1, 2.9), new THREE.Color(1, 1, 1), 1, [0, v1, 1, v0]);
      box(b, p, u, 0.65, 3.36, 0.01, 0.6, 0.025, dark);
    }
    const m = material().clone();
    m.map = tex;
    m.onBeforeCompile = material().onBeforeCompile;
    m.customProgramCacheKey = () => 'storefronts';
    const mesh = b.mesh(m);
    if (mesh) out.push(mesh);
  } else {
    const mesh = b.mesh(material());
    if (mesh) out.push(mesh);
  }
  if (shopPts.length) { const owner = new THREE.Object3D(); registerLights(owner, shopPts); out.push(owner); }
  const sp = spill.mesh(spillMaterial(), false);
  if (sp) { sp.renderOrder = 2; out.push(sp); }
  return out;
}
