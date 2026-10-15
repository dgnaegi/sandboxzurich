import * as THREE from 'three';

/** Bridges and elevated roads/paths (pipeline/bridges.py -> tile meta "bridges").
 *  Deck rows: p = [[x, y, z]] local metres (z = top of the carriageway), g = terrain below, b = underside z,
 *  w = driving width, kind = road | foot | tram | rail. Piers: [x, y, zBottom, zTop, widthAcross, heading, kind].
 *  Local -> Three: (x, z, -y). One draw call per tile (vertex-coloured, flat shaded). */
export interface DeckRow { p: number[][]; g: number[]; b: number[]; w: number; kind: string; name: string }
export type PierRow = [number, number, number, number, number, number, string];
export interface BridgeRows { decks: DeckRow[]; piers: PierRow[] }

const mat = new THREE.MeshLambertMaterial({ vertexColors: true, side: THREE.DoubleSide });
const col = (hex: number) => new THREE.Color(hex);
const TOP: Record<string, THREE.Color> = { road: col(0x3c3d40), tram: col(0x3c3d40), foot: col(0x8d8a84), rail: col(0x4b4640) };
const CONC = col(0x9b988f), CONC_DARK = col(0x6f6d68), RAIL = col(0x5d6468), LINE = col(0xd8d4c4);
const PARAPET = 0.38, CURB = 0.3;

class Builder {
  pos: number[] = []; nor: number[] = []; clr: number[] = [];
  /** triangle a,b,c in local metres (x, y, z); normal from winding */
  tri(a: number[], b: number[], c: number[], k: THREE.Color) {
    const A = [a[0], a[2], -a[1]], B = [b[0], b[2], -b[1]], C = [c[0], c[2], -c[1]];
    const ux = B[0] - A[0], uy = B[1] - A[1], uz = B[2] - A[2], vx = C[0] - A[0], vy = C[1] - A[1], vz = C[2] - A[2];
    let nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    const l = Math.hypot(nx, ny, nz) || 1; nx /= l; ny /= l; nz /= l;
    for (const P of [A, B, C]) { this.pos.push(P[0], P[1], P[2]); this.nor.push(nx, ny, nz); this.clr.push(k.r, k.g, k.b); }
  }
  quad(a: number[], b: number[], c: number[], d: number[], k: THREE.Color) { this.tri(a, b, c, k); this.tri(a, c, d, k); }
  geometry(): THREE.BufferGeometry {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(this.pos, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(this.nor, 3));
    g.setAttribute('color', new THREE.Float32BufferAttribute(this.clr, 3));
    return g;
  }
}

/** Offset point of polyline vertex i by `o` metres to the left of travel direction, at height z. */
function offsets(p: number[][]): { nx: number[]; ny: number[] } {
  const nx: number[] = [], ny: number[] = [];
  for (let i = 0; i < p.length; i++) {
    const a = p[Math.max(0, i - 1)], b = p[Math.min(p.length - 1, i + 1)];
    let dx = b[0] - a[0], dy = b[1] - a[1];
    const l = Math.hypot(dx, dy) || 1; dx /= l; dy /= l;
    nx.push(-dy); ny.push(dx);
  }
  return { nx, ny };
}

function deck(B: Builder, d: DeckRow) {
  const p = d.p, n = p.length;
  if (n < 2) return;
  const { nx, ny } = offsets(p);
  const hw = d.w / 2, ow = hw + CURB;
  const at = (i: number, o: number, z: number) => [p[i][0] + nx[i] * o, p[i][1] + ny[i] * o, z];
  const top = TOP[d.kind] ?? TOP.road;
  const rail = d.kind === 'rail';
  for (let i = 0; i < n - 1; i++) {
    const j = i + 1, zi = p[i][2], zj = p[j][2], bi = d.b[i], bj = d.b[j];
    B.quad(at(i, -hw, zi), at(i, hw, zi), at(j, hw, zj), at(j, -hw, zj), top); // surface (winding: up)
    for (const s of [-1, 1]) {
      const sw = s * hw, so = s * ow;
      const q = (a: number[], b: number[], c: number[], e: number[], k: THREE.Color) => (s > 0 ? B.quad(a, b, c, e, k) : B.quad(e, c, b, a, k));
      // curb / parapet: inner face, top, outer face down to the underside
      q(at(i, sw, zi), at(j, sw, zj), at(j, sw, zj + PARAPET), at(i, sw, zi + PARAPET), CONC);
      q(at(i, sw, zi + PARAPET), at(j, sw, zj + PARAPET), at(j, so, zj + PARAPET), at(i, so, zi + PARAPET), CONC);
      q(at(i, so, zi + PARAPET), at(j, so, zj + PARAPET), at(j, so, bj), at(i, so, bi), CONC);
    }
    B.quad(at(i, ow, bi), at(i, -ow, bi), at(j, -ow, bj), at(j, ow, bj), CONC_DARK); // underside
  }
  if (!rail) railings(B, d, nx, ny, hw + CURB * 0.5);
  if (d.kind === 'road' && d.w >= 6) centreLine(B, d, nx, ny);
}

function railings(B: Builder, d: DeckRow, nx: number[], ny: number[], o: number) {
  const p = d.p;
  if (d.kind === 'rail') return;
  for (const s of [-1, 1]) {
    let acc = 0, nextPost = 0;
    for (let i = 0; i < p.length - 1; i++) {
      const j = i + 1, len = Math.hypot(p[j][0] - p[i][0], p[j][1] - p[i][1]);
      const at = (k: number, z: number) => [p[k][0] + nx[k] * o * s, p[k][1] + ny[k] * o * s, p[k][2] + z];
      for (const h of [0.75, 1.05]) B.quad(at(i, PARAPET + h - 0.04), at(j, PARAPET + h - 0.04), at(j, PARAPET + h + 0.03), at(i, PARAPET + h + 0.03), RAIL);
      // posts every ~2.5 m: two crossed thin quads
      while (nextPost <= acc + len) {
        const t = (nextPost - acc) / len;
        const x = p[i][0] + (p[j][0] - p[i][0]) * t + nx[i] * o * s, y = p[i][1] + (p[j][1] - p[i][1]) * t + ny[i] * o * s;
        const z = p[i][2] + (p[j][2] - p[i][2]) * t + PARAPET;
        const tx = (p[j][0] - p[i][0]) / len * 0.04, ty = (p[j][1] - p[i][1]) / len * 0.04;
        B.quad([x - tx, y - ty, z], [x + tx, y + ty, z], [x + tx, y + ty, z + 1.08], [x - tx, y - ty, z + 1.08], RAIL);
        nextPost += 2.5;
      }
      acc += len;
    }
  }
}

function centreLine(B: Builder, d: DeckRow, nx: number[], ny: number[]) {
  const p = d.p;
  let acc = 0;
  for (let i = 0; i < p.length - 1; i++) {
    const j = i + 1, len = Math.hypot(p[j][0] - p[i][0], p[j][1] - p[i][1]);
    if ((acc % 9) < 3) {
      const h = 0.07, z = 0.02;
      B.quad([p[i][0] - nx[i] * h, p[i][1] - ny[i] * h, p[i][2] + z], [p[i][0] + nx[i] * h, p[i][1] + ny[i] * h, p[i][2] + z],
        [p[j][0] + nx[j] * h, p[j][1] + ny[j] * h, p[j][2] + z], [p[j][0] - nx[j] * h, p[j][1] - ny[j] * h, p[j][2] + z], LINE);
    }
    acc += len;
  }
}

function pier(B: Builder, r: PierRow) {
  const [x, y, zb, zt, w, hd, kind] = r;
  const along = kind === 'foot' ? 0.5 : 0.75, across = w / 2;
  const c = Math.cos(hd), s = Math.sin(hd);
  const corner = (a: number, b: number, z: number) => [x + c * a - s * b, y + s * a + c * b, z];
  const cs: [number, number][] = [[-along, -across], [along, -across], [along, across], [-along, across]];
  for (let k = 0; k < 4; k++) {
    const [a0, b0] = cs[k], [a1, b1] = cs[(k + 1) % 4];
    B.quad(corner(a0, b0, zb), corner(a1, b1, zb), corner(a1, b1, zt), corner(a0, b0, zt), CONC_DARK);
  }
}

/** Meshes for one tile: a single vertex-coloured mesh with decks, parapets, railings and piers. */
export function buildBridges(rows: BridgeRows | undefined | null): THREE.Object3D[] {
  if (!rows || (!rows.decks?.length && !rows.piers?.length)) return [];
  const B = new Builder();
  for (const d of rows.decks ?? []) deck(B, d);
  for (const r of rows.piers ?? []) pier(B, r);
  const m = new THREE.Mesh(B.geometry(), mat);
  m.castShadow = false; m.receiveShadow = true; m.name = 'bridges';
  return [m];
}

/** Walkable decks, spatially hashed. heightAt returns the deck height only for a player standing on / just above it. */
export class BridgeIndex {
  private cell = 8;
  private grid = new Map<string, { d: DeckRow; i: number }[]>();
  private byKey = new Map<string, string[]>();

  add(rows: BridgeRows | undefined | null, key = ''): void {
    if (!rows) return;
    const cells: string[] = [];
    for (const d of rows.decks ?? []) {
      if (d.kind === 'rail') continue; // not walkable
      const r = d.w / 2 + 1;
      for (let i = 0; i < d.p.length - 1; i++) {
        const a = d.p[i], b = d.p[i + 1];
        const x0 = Math.floor((Math.min(a[0], b[0]) - r) / this.cell), x1 = Math.floor((Math.max(a[0], b[0]) + r) / this.cell);
        const y0 = Math.floor((Math.min(a[1], b[1]) - r) / this.cell), y1 = Math.floor((Math.max(a[1], b[1]) + r) / this.cell);
        for (let cx = x0; cx <= x1; cx++) for (let cy = y0; cy <= y1; cy++) {
          const k = cx + ',' + cy;
          let l = this.grid.get(k);
          if (!l) this.grid.set(k, (l = []));
          l.push({ d, i });
          cells.push(k);
        }
      }
    }
    this.byKey.set(key, cells);
    if (key) this.owners.set(key, rows);
  }

  private owners = new Map<string, BridgeRows>();

  /** Remove the decks of a tile that was unloaded (same key as in add). */
  remove(key: string): void {
    const rows = this.owners.get(key);
    if (!rows) return;
    const dead = new Set(rows.decks);
    for (const k of new Set(this.byKey.get(key) ?? [])) {
      const l = this.grid.get(k)?.filter((e) => !dead.has(e.d));
      if (l && l.length) this.grid.set(k, l); else this.grid.delete(k);
    }
    this.byKey.delete(key); this.owners.delete(key);
  }

  /** Deck height at (x, y) if it lies on a deck and |zPlayer - deck| < reach (default 1.5 m); else null (terrain applies). */
  heightAt(x: number, y: number, zPlayer: number, reach = 1.5): number | null {
    const l = this.grid.get(Math.floor(x / this.cell) + ',' + Math.floor(y / this.cell));
    if (!l) return null;
    let best: number | null = null, bd = reach;
    for (const { d, i } of l) {
      const a = d.p[i], b = d.p[i + 1];
      const dx = b[0] - a[0], dy = b[1] - a[1], len2 = dx * dx + dy * dy || 1;
      const t = Math.max(0, Math.min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / len2));
      const px = a[0] + dx * t - x, py = a[1] + dy * t - y;
      if (px * px + py * py > (d.w / 2 + 0.3) ** 2) continue;
      const z = a[2] + (b[2] - a[2]) * t, dz = Math.abs(zPlayer - z);
      if (dz < bd) { bd = dz; best = z; }
    }
    return best;
  }
}
