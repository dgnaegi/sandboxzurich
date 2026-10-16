/** Railway land (Bahngebiet + track buffer, platforms and bridge decks excluded; pipeline/railzone.py): nobody walks or sits there. */
interface Zone { b: number[]; r: number[][][] }
let zones: Zone[] = [];

export async function loadRailZone(url = '/data/railzone.json'): Promise<void> {
  try { zones = ((await (await fetch(url)).json()) as { zones: Zone[] }).zones; } catch { zones = []; }
}

const inRing = (r: number[][], x: number, y: number) => {
  let c = false;
  for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
    const [xi, yi] = r[i], [xj, yj] = r[j];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
  }
  return c;
};

/** Is the local point (x, y) on railway land? */
export function inRail(x: number, y: number): boolean {
  for (const z of zones) {
    if (x < z.b[0] || x > z.b[2] || y < z.b[1] || y > z.b[3]) continue;
    let n = 0;
    for (const r of z.r) if (inRing(r, x, y)) n++;
    if (n & 1) return true;
  }
  return false;
}

/** Cut a path into the pieces that stay off railway land (sampled every ~2 m); pieces shorter than 8 m are dropped. */
export function clipPath(path: number[][]): number[][][] {
  if (!zones.length) return [path];
  const out: number[][][] = [];
  let cur: number[][] = [];
  const flush = () => { if (cur.length >= 2 && Math.hypot(cur[cur.length - 1][0] - cur[0][0], cur[cur.length - 1][1] - cur[0][1]) > 8) out.push(cur); cur = []; };
  for (let i = 0; i < path.length; i++) {
    const a = path[i];
    if (i > 0) {
      const p = path[i - 1], n = Math.max(1, Math.ceil(Math.hypot(a[0] - p[0], a[1] - p[1]) / 2));
      for (let k = 1; k < n; k++) {
        const q = [p[0] + ((a[0] - p[0]) * k) / n, p[1] + ((a[1] - p[1]) * k) / n];
        if (inRail(q[0], q[1])) flush(); else cur.push(q);
      }
    }
    if (inRail(a[0], a[1])) flush(); else cur.push(a);
  }
  flush();
  return out;
}
