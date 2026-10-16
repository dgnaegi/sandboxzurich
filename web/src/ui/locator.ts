/** HUD location: real Quartier polygons (Stadt Zürich OGD), named squares/hubs and nearest street (OSM). Data: pipeline/districts.py. */
interface Quartier { k: number; q: string; ring: number[][] }
interface Square { n: string; ring?: number[][]; x?: number; y?: number; r?: number }
interface Hub { n: string; x: number; y: number; r: number }
interface Street { n: string; p: number[][] }
interface Data { quartiere: Quartier[]; streets: Street[]; squares: Square[]; hubs: Hub[] }

const CELL = 50;

function inside(ring: number[][], x: number, y: number): boolean {
  let c = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i], [xj, yj] = ring[j];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
  }
  return c;
}

function segDist(px: number, py: number, a: number[], b: number[]): number {
  const dx = b[0] - a[0], dy = b[1] - a[1], l = dx * dx + dy * dy;
  const t = l ? Math.max(0, Math.min(1, ((px - a[0]) * dx + (py - a[1]) * dy) / l)) : 0;
  return Math.hypot(px - a[0] - t * dx, py - a[1] - t * dy);
}

export class Locator {
  private d: Data = { quartiere: [], streets: [], squares: [], hubs: [] };
  private grid = new Map<number, [number, number, number][]>(); // cell -> [street index, segment index]
  ready = false;

  async load(url = '/data/districts.json') {
    try {
      this.d = await (await fetch(url)).json();
    } catch { return; }
    this.d.streets.forEach((s, si) => s.p.forEach((_, i) => {
      if (i === 0) return;
      const a = s.p[i - 1], b = s.p[i];
      const x0 = Math.floor(Math.min(a[0], b[0]) / CELL), x1 = Math.floor(Math.max(a[0], b[0]) / CELL);
      const y0 = Math.floor(Math.min(a[1], b[1]) / CELL), y1 = Math.floor(Math.max(a[1], b[1]) / CELL);
      for (let cx = x0; cx <= x1; cx++) for (let cy = y0; cy <= y1; cy++) {
        const k = cx * 100003 + cy;
        (this.grid.get(k) ?? this.grid.set(k, []).get(k)!).push([si, i, 0]);
      }
    }));
    this.ready = true;
  }

  /** «KREIS 4 · LANGSTRASSE» from the official Quartier polygons. */
  kreis(x: number, y: number): string | null {
    const q = this.d.quartiere.find((p) => inside(p.ring, x, y));
    return q ? `KREIS ${q.k} · ${q.q.toUpperCase()}` : null;
  }

  /** Named square or transit hub the point lies on (precise, no fallback). */
  square(x: number, y: number): string | null {
    for (const s of this.d.squares) {
      if (s.ring ? inside(s.ring, x, y) : Math.hypot(x - s.x!, y - s.y!) < (s.r ?? 30)) return s.n;
    }
    let best: Hub | null = null, bd = Infinity;
    for (const h of this.d.hubs) {
      const dd = Math.hypot(x - h.x, y - h.y);
      if (dd < h.r && dd < bd) { bd = dd; best = h; }
    }
    return best ? best.n : null;
  }

  street(x: number, y: number, maxD = 35): string | null {
    let best: string | null = null, bd = maxD;
    const cx = Math.floor(x / CELL), cy = Math.floor(y / CELL);
    for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++) {
      for (const [si, seg] of this.grid.get((cx + i) * 100003 + cy + j) ?? []) {
        const s = this.d.streets[si], dd = segDist(x, y, s.p[seg - 1], s.p[seg]);
        if (dd < bd) { bd = dd; best = s.n; }
      }
    }
    return best;
  }
}
