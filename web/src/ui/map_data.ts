/** Vector city map data (pipeline/mapdata.py -> /data/map/vec.json), bucketed into 250 m cells of Path2D for fast culling. */
export type Pt = [number, number];
export interface Named { name: string; x: number; y: number; kind: string }
export interface LabelLine { name: string; cls: number; pts: Float32Array }
export interface Cell { p: Map<string, Path2D> }

const CELL = 250;
const key = (i: number, j: number) => i * 4096 + j + 2048;

export class MapData {
  cells = new Map<number, Cell>();
  labels: LabelLine[] = [];
  stops: Named[] = [];
  places: Named[] = [];
  pois: Named[] = [];
  velo: Cell | null = null;
  ready = false;

  private add(layer: string, flat: ArrayLike<number>, closed: boolean) {
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    for (let i = 0; i < flat.length; i += 2) {
      const x = flat[i], y = flat[i + 1];
      if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
    }
    for (let i = Math.floor(x0 / CELL); i <= Math.floor(x1 / CELL); i++) {
      for (let j = Math.floor(y0 / CELL); j <= Math.floor(y1 / CELL); j++) {
        const k = key(i, j);
        let c = this.cells.get(k);
        if (!c) this.cells.set(k, c = { p: new Map() });
        let p = c.p.get(layer);
        if (!p) c.p.set(layer, p = new Path2D());
        p.moveTo(flat[0], flat[1]);
        for (let n = 2; n < flat.length; n += 2) p.lineTo(flat[n], flat[n + 1]);
        if (closed) p.closePath();
      }
    }
  }

  private static dec(flat: number[], ox: number, oy: number, q: number): Float32Array {
    const out = new Float32Array(flat.length);
    let x = 0, y = 0;
    for (let i = 0; i < flat.length; i += 2) {
      x += flat[i]; y += flat[i + 1];
      out[i] = x / q + ox; out[i + 1] = y / q + oy;
    }
    return out;
  }

  async load(url = '/data/map/vec.json') {
    const d = await (await fetch(url)).json();
    const { ox, oy, q } = d;
    for (const [kind, arr] of Object.entries<number[][] | number[][][]>(d.areas)) {
      for (const a of arr as (number[] | number[][])[]) {
        const rings = (typeof a[0] === 'number' ? [a] : a) as number[][];
        // holes are extra sub-paths of the same layer path; the renderer fills evenodd
        for (const r of rings) this.add('a' + kind, MapData.dec(r, ox, oy, q), true);
      }
    }
    for (const [cls, arr] of Object.entries<[number, number[]][]>(d.roads)) {
      for (const [fl, flat] of arr) {
        const layer = Number(cls) >= 10 ? 'w' + cls : (fl & 1 ? 'rt' : fl & 2 ? 'rb' : 'r') + cls;
        this.add(layer, MapData.dec(flat, ox, oy, q), false);
      }
    }
    for (const [cls, fl, flat] of d.rails as [number, number, number[], string][]) {
      this.add(fl & 1 ? 'lt' : fl & 4 ? 'ly' : cls === 1 ? 'lm' : 'lr', MapData.dec(flat, ox, oy, q), false);
    }
    this.labels = (d.labels as [string, number, number[]][]).map(([name, cls, f]) => ({ name, cls, pts: MapData.dec(f, ox, oy, q) }));
    const nm = (a: [string, number, number, string][]): Named[] => a.map(([name, x, y, kind]) => ({ name, x, y, kind }));
    this.stops = nm(d.stops); this.places = nm(d.places); this.pois = nm(d.pois);
    this.ready = true;
  }

  /** Cycle infrastructure (existing game data, play area only). */
  async loadVelo(url = '/data/veloinfra.json') {
    if (this.velo) return;
    const d = await (await fetch(url)).json() as { lines: { k: string; p: Pt[] }[] };
    const cell: Cell = { p: new Map() };
    for (const l of d.lines) {
      let p = cell.p.get(l.k);
      if (!p) cell.p.set(l.k, p = new Path2D());
      l.p.forEach(([x, y], i) => (i ? p!.lineTo(x, y) : p!.moveTo(x, y)));
    }
    this.velo = cell;
  }

  /** Cells overlapping a world rectangle. */
  visible(x0: number, y0: number, x1: number, y1: number): Cell[] {
    const out: Cell[] = [];
    for (let i = Math.floor(x0 / CELL); i <= Math.floor(x1 / CELL); i++) {
      for (let j = Math.floor(y0 / CELL); j <= Math.floor(y1 / CELL); j++) {
        const c = this.cells.get(key(i, j));
        if (c) out.push(c);
      }
    }
    return out;
  }
}
