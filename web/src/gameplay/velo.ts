/** Real cycling infrastructure (public/data/veloinfra.json): lookup "am I on a bike lane?" via a coarse grid. */
interface Line { k: 'weg' | 'streifen' | 'strasse'; p: number[][] }
const CELL = 20;

export class VeloInfra {
  lines: Line[] = [];
  private grid = new Map<string, [number[], number[], string][]>();

  async load(url = '/data/veloinfra.json') {
    this.lines = ((await (await fetch(url)).json()) as { lines: Line[] }).lines;
    for (const l of this.lines) for (let i = 0; i + 1 < l.p.length; i++) {
      const a = l.p[i], b = l.p[i + 1];
      for (let cx = Math.floor(Math.min(a[0], b[0]) / CELL) - 1; cx <= Math.floor(Math.max(a[0], b[0]) / CELL) + 1; cx++)
        for (let cy = Math.floor(Math.min(a[1], b[1]) / CELL) - 1; cy <= Math.floor(Math.max(a[1], b[1]) / CELL) + 1; cy++) {
          const k = `${cx},${cy}`;
          (this.grid.get(k) ?? this.grid.set(k, []).get(k)!).push([a, b, l.k]);
        }
    }
  }

  /** Kind of infrastructure within `r` metres of (x, y), or null. Lanes lie at the kerb, so r is generous. */
  at(x: number, y: number, r = 4.5): string | null {
    for (const [a, b, k] of this.grid.get(`${Math.floor(x / CELL)},${Math.floor(y / CELL)}`) ?? []) {
      const dx = b[0] - a[0], dy = b[1] - a[1], l2 = dx * dx + dy * dy || 1;
      const t = Math.max(0, Math.min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / l2));
      if (Math.hypot(x - (a[0] + t * dx), y - (a[1] + t * dy)) < r) return k;
    }
    return null;
  }
}
