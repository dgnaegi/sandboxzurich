import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

/** Zurich enamel signs. House numbers: rows [x, y, z, tx, ty, text]; street signs: rows [x, y, z, heading, text].
 *  Local (x east, y north, z up) -> Three (x, z, -y). Outward normal = (ty, -tx). One atlas texture + one mesh per type. */
export type NumberRow = [number, number, number, number, number, string];

const BLUE = '#12509a';
const FONT = (px: number) => `600 ${px}px "Barlow Condensed", "Arial Narrow", sans-serif`;

interface Cell { x: number; y: number; z: number; tx: number; ty: number; w: number; h: number; text: string; uw?: number }

function atlas(cells: Cell[], cw: number, ch: number, draw: (g: CanvasRenderingContext2D, text: string) => void): THREE.Object3D[] {
  if (!cells.length) return [];
  const cols = Math.min(cells.length, Math.floor(2048 / cw));
  const rowsN = Math.ceil(cells.length / cols);
  const c = document.createElement('canvas');
  c.width = THREE.MathUtils.ceilPowerOfTwo(cols * cw);
  c.height = THREE.MathUtils.ceilPowerOfTwo(rowsN * ch);
  const g = c.getContext('2d')!;
  const pos: number[] = [], nrm: number[] = [], uv: number[] = [], idx: number[] = [];
  cells.forEach((s, i) => {
    const px = (i % cols) * cw, py = Math.floor(i / cols) * ch;
    g.save();
    g.translate(px, py);
    g.beginPath();
    g.rect(0, 0, cw, ch);
    g.clip();
    draw(g, s.text);
    g.restore();
    const ox = s.ty, oy = -s.tx, hw = s.w / 2, hh = s.h / 2, b = pos.length / 3;
    for (const [u, v] of [[-hw, -hh], [hw, -hh], [hw, hh], [-hw, hh]]) {
      pos.push(s.x + s.tx * u, s.z + v, -(s.y + s.ty * u));
      nrm.push(ox, 0, -oy);
    }
    const u0 = px / c.width, u1 = (px + (s.uw ?? cw)) / c.width, v0 = 1 - (py + ch) / c.height, v1 = 1 - py / c.height;
    uv.push(u0, v0, u1, v0, u1, v1, u0, v1);
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
  const mat = new THREE.MeshLambertMaterial({ map: tex, emissive: 0xffffff, emissiveMap: tex, emissiveIntensity: 0.2, polygonOffset: true, polygonOffsetFactor: -1 });
  return [new THREE.Mesh(geo, mat)];
}

export function buildHouseNumbers(rows: NumberRow[]): THREE.Object3D[] {
  const W = 72, H = 56;
  const cells = rows.map(([x, y, z, tx, ty, text]) => ({ x, y, z, tx, ty, w: 0.18, h: 0.14, text }));
  return atlas(cells, W, H, (g, text) => {
    g.fillStyle = '#e8eef5';
    g.fillRect(0, 0, W, H);
    g.fillStyle = BLUE;
    g.fillRect(3, 3, W - 6, H - 6);
    g.fillStyle = '#fff';
    g.textAlign = 'center';
    g.textBaseline = 'middle';
    let px = 46;
    g.font = FONT(px);
    const tw = g.measureText(text).width;
    if (tw > W - 14) { px = Math.floor(px * (W - 14) / tw); g.font = FONT(px); }
    g.fillText(text, W / 2, H / 2 + 2);
  });
}

/** Street rows: [x, y, z, heading, name, plaque?, pole?]. Zurich enamel: dark blue, white rim + inset white line,
 *  panel length follows the name. Dedication plaque (white, blue text) hangs below. Pole signs are drawn on both sides. */
export type StreetRow = [number, number, number, number, string, string?, number?];
const PX_M = 330; // canvas px per metre on the name sign
function nameCells(rows: StreetRow[], g: CanvasRenderingContext2D): Cell[] {
  g.font = FONT(46);
  const cells: Cell[] = [];
  for (const [x, y, z, h, text, , pole] of rows) {
    const uw = Math.min(512, Math.ceil(g.measureText(text).width + 44));
    const tx = Math.cos(h), ty = Math.sin(h), w = uw / PX_M, hh = 66 / PX_M;
    cells.push({ x: x + ty * (pole ? 0.05 : 0), y: y - tx * (pole ? 0.05 : 0), z, tx, ty, w, h: hh, text, uw });
    if (pole) cells.push({ x: x - ty * 0.05, y: y + tx * 0.05, z, tx: -tx, ty: -ty, w, h: hh, text, uw });
  }
  return cells;
}
export function buildStreetSigns(rows: StreetRow[]): THREE.Object3D[] {
  if (!rows.length) return [];
  const W = 512, H = 66;
  const m = document.createElement('canvas').getContext('2d')!;
  const out = atlas(nameCells(rows, m), W, H, (g, text) => {
    g.font = FONT(46);
    const uw = Math.min(512, Math.ceil(g.measureText(text).width + 44));
    g.fillStyle = '#f4f4f0';
    g.fillRect(0, 0, uw, H);
    g.fillStyle = '#0f3f8c';
    g.fillRect(3, 3, uw - 6, H - 6);
    g.strokeStyle = '#eef2f8';
    g.lineWidth = 2;
    g.strokeRect(8, 8, uw - 16, H - 16);
    g.fillStyle = '#fff';
    g.textAlign = 'center';
    g.textBaseline = 'middle';
    g.fillText(text, uw / 2, H / 2 + 2, uw - 24);
  });
  // dedication plaques
  const PW = 512, PH = 150, plaques: Cell[] = [];
  for (const [x, y, z, h, , plaque, pole] of rows) {
    if (!plaque) continue;
    const tx = Math.cos(h), ty = Math.sin(h);
    for (const sgn of pole ? [1, -1] : [1]) {
      const o = pole ? 0.05 * sgn : 0;
      plaques.push({ x: x + ty * o, y: y - tx * o, z: z - 0.33, tx: tx * sgn, ty: ty * sgn, w: 0.66, h: 0.19, text: plaque });
    }
  }
  out.push(...atlas(plaques, PW, PH, (g, text) => {
    g.fillStyle = '#0f3f8c';
    g.fillRect(0, 0, PW, PH);
    g.fillStyle = '#f6f6f2';
    g.fillRect(4, 4, PW - 8, PH - 8);
    g.fillStyle = '#0f3f8c';
    g.textAlign = 'center';
    g.textBaseline = 'middle';
    const lines = text.split('\n').slice(0, 4);
    const lh = Math.min(34, (PH - 20) / lines.length);
    lines.forEach((ln, i) => {
      g.font = i === 0 ? FONT(lh * 0.95) : `500 ${Math.round(lh * 0.8)}px "Barlow Condensed", "Arial Narrow", sans-serif`;
      g.fillText(ln, PW / 2, PH / 2 + (i - (lines.length - 1) / 2) * lh, PW - 24);
    });
  }));
  // poles for free-standing signs (one merged mesh)
  const poles = rows.filter((r) => r[6]);
  if (poles.length) {
    const parts = poles.map(([x, y, z]) => {
      const len = 2.75;
      const c = new THREE.CylinderGeometry(0.03, 0.03, len, 6);
      c.translate(x, z - 2.6 + len / 2, -y);
      return c;
    });
    const geo = mergeGeometries(parts);
    parts.forEach((p) => p.dispose());
    out.push(new THREE.Mesh(geo, poleMat ??= new THREE.MeshLambertMaterial({ color: 0x8a8f94 })));
  }
  return out;
}
let poleMat: THREE.MeshLambertMaterial | undefined;
