import * as THREE from 'three';
import { hash, type Look, type ShopSign } from './storefront_style';

/** Pavement terrace (tables, chairs, parasols) and planter tubs in front of a venue, built from vertex-coloured quads. */
export interface QuadSink { quad(a: number[], b: number[], c: number[], d: number[], color: THREE.Color, glow?: number): void }
export type Pt = (u: number, v: number, h: number) => number[];

function bx(b: QuadSink, p: Pt, u: number, v: number, h0: number, du: number, dv: number, dh: number, c: THREE.Color) {
  const q = (x: number, y: number, z: number) => p(x, y, z);
  const A = q(u - du, v - dv, h0), B = q(u + du, v - dv, h0), C = q(u + du, v + dv, h0), D = q(u - du, v + dv, h0);
  const E = q(u - du, v - dv, h0 + dh), F = q(u + du, v - dv, h0 + dh), G = q(u + du, v + dv, h0 + dh), H = q(u - du, v + dv, h0 + dh);
  b.quad(E, F, G, H, c); b.quad(A, B, F, E, c); b.quad(B, C, G, F, c); b.quad(C, D, H, G, c); b.quad(D, A, E, H, c);
}

const CHAIRS = [0x2b2b2e, 0x7a5230, 0x3d5c4a, 0xb8a27a, 0x8a2f2a, 0x4a4f58];
const TOPS = [0xe8e4da, 0x2b2b2e, 0x9b7048, 0xcfc8b6];

function chair(b: QuadSink, p: Pt, u: number, v: number, back: number, col: THREE.Color) {  // back = +1/-1 along v, 0 = along u
  bx(b, p, u, v, 0.42, 0.2, 0.2, 0.04, col);
  for (const [cu, cv] of [[-0.17, -0.17], [0.17, -0.17], [-0.17, 0.17], [0.17, 0.17]]) bx(b, p, u + cu, v + cv, 0, 0.018, 0.018, 0.42, col);
  if (back) bx(b, p, u, v + back * 0.19, 0.46, 0.19, 0.015, 0.4, col);
}

function table(b: QuadSink, p: Pt, u: number, v: number, top: THREE.Color, leg: THREE.Color) {
  bx(b, p, u, v, 0.72, 0.34, 0.34, 0.035, top);
  bx(b, p, u, v, 0, 0.025, 0.025, 0.72, leg);
  bx(b, p, u, v, 0, 0.17, 0.17, 0.02, leg);
}

function parasol(b: QuadSink, p: Pt, u: number, v: number, r: number, col: THREE.Color, alt: THREE.Color) {
  bx(b, p, u, v, 0, 0.02, 0.02, 2.35, new THREE.Color(0x3a3a3e));
  const N = 8, top = p(u, v, 2.65);
  for (let i = 0; i < N; i++) {
    const a0 = i / N * Math.PI * 2, a1 = (i + 1) / N * Math.PI * 2;
    b.quad(p(u + Math.cos(a0) * r, v + Math.sin(a0) * r, 2.3), p(u + Math.cos(a1) * r, v + Math.sin(a1) * r, 2.3), top, top, i % 2 ? alt : col);
  }
}

/** depth = free pavement (m) between facade and kerb; returns true when something was placed. */
export function terrace(b: QuadSink, p: Pt, s: ShopSign, look: Look): boolean {
  const pd = s.pd ?? 3.0, depth = Math.min(2.5, pd - 1.5), h = hash(s.name);
  if (depth < 1.0) return false;
  const two = depth >= 1.9, span = Math.min(s.w - 0.4, 7.2), step = two ? 1.55 : 1.15;
  const n = Math.min(4, Math.floor(span / step));
  if (n < 1) return false;
  const chairC = new THREE.Color(CHAIRS[(h >>> 3) % CHAIRS.length]), topC = new THREE.Color(TOPS[(h >>> 6) % TOPS.length]);
  const leg = new THREE.Color(0x2b2b2e), pc = new THREE.Color(look.parasol), alt = look.stripes || h % 3 ? new THREE.Color(0xf0ece2) : pc;
  const shift = (h >>> 9) % 2 ? 0.3 : -0.3;
  for (let i = 0; i < n; i++) {
    const u = (i - (n - 1) / 2) * step + (n < 3 ? shift : 0);
    if (two) {
      table(b, p, u, 1.0, topC, leg);
      chair(b, p, u, 0.52, -1, chairC); chair(b, p, u, 1.48, 1, chairC);
      if (i % 2 === 0 && depth >= 2.2) parasol(b, p, u, 1.0, 1.15, pc, alt);
    } else {
      table(b, p, u, 0.6, topC, leg);
      chair(b, p, u - 0.5, 0.6, 0, chairC); chair(b, p, u + 0.5, 0.6, 0, chairC);
    }
  }
  return true;
}

/** Planter tubs left and right of the entrance zone. */
export function planters(b: QuadSink, p: Pt, s: ShopSign) {
  const h = hash(s.name), tub = new THREE.Color([0x3a3a3e, 0x7a4a2c, 0x8f8f88][h % 3]);
  const leaf = [0x2f6b34, 0x4a8a3a, 0x3a7a4a].map((c) => new THREE.Color(c));
  const e = Math.max(0.7, s.w / 2 - 0.5), us = h & 4 ? [-e, e] : [(h & 8) ? e : -e];
  us.forEach((u, i) => {
    bx(b, p, u, 0.4, 0, 0.27, 0.27, 0.5, tub);
    bx(b, p, u, 0.4, 0.5, 0.25, 0.25, 0.08, new THREE.Color(0x3b2a1c));
    const hh = 0.7 + ((h >> (i + 2)) & 3) * 0.28, c = leaf[(h >>> (i * 2)) % 3];
    bx(b, p, u, 0.4, 0.55, 0.22, 0.22, hh, c);
    bx(b, p, u + 0.04, 0.4, 0.75, 0.3, 0.12, hh * 0.6, leaf[(i + 1) % 3]);
  });
}
