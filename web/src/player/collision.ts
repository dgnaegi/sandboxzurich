/** 2D collision of a circle against building footprints (local metres), via a uniform grid. */
type Ring = number[][];
const CELL = 25;

export class Colliders {
  private grid = new Map<string, Ring[]>();

  add(rings: Ring[]) {
    for (const r of rings) {
      let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
      for (const [x, y] of r) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
      for (let cx = Math.floor(x0 / CELL); cx <= Math.floor(x1 / CELL); cx++)
        for (let cy = Math.floor(y0 / CELL); cy <= Math.floor(y1 / CELL); cy++) {
          const k = `${cx},${cy}`;
          (this.grid.get(k) ?? this.grid.set(k, []).get(k)!).push(r);
        }
    }
  }

  /** True if local (x, y) lies inside any footprint. */
  inside(x: number, y: number): boolean {
    return !!this.grid.get(`${Math.floor(x / CELL)},${Math.floor(y / CELL)}`)?.some((r) => pointInRing(x, y, r));
  }

  /** Fraction (0..1) of the segment a→b that is free before entering a footprint. */
  freeFraction(ax: number, ay: number, bx: number, by: number, steps = 24): number {
    for (let i = 1; i <= steps; i++) {
      const t = i / steps;
      if (this.inside(ax + (bx - ax) * t, ay + (by - ay) * t)) return (i - 1) / steps;
    }
    return 1;
  }

  /** Push the circle (x, y, radius) out of every footprint it overlaps. Returns corrected position. */
  resolve(x: number, y: number, rad: number): [number, number] {
    for (let pass = 0; pass < 3; pass++) {
      const rings = this.grid.get(`${Math.floor(x / CELL)},${Math.floor(y / CELL)}`);
      if (!rings) break;
      let moved = false;
      for (const r of rings) {
        const inside = pointInRing(x, y, r);
        let best = Infinity, bx = 0, by = 0;
        for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
          const [ax, ay] = r[j], [qx, qy] = r[i];
          const dx = qx - ax, dy = qy - ay, l2 = dx * dx + dy * dy || 1;
          const t = Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / l2));
          const px = ax + t * dx, py = ay + t * dy, d = Math.hypot(x - px, y - py);
          if (d < best) { best = d; bx = px; by = py; }
        }
        if (!inside && best >= rad) continue;
        const nx = (x - bx) / (best || 1), ny = (y - by) / (best || 1);
        const s = inside ? -1 : 1;
        x = bx + s * nx * rad; y = by + s * ny * rad;
        moved = true;
      }
      if (!moved) break;
    }
    return [x, y];
  }
}

function pointInRing(x: number, y: number, r: Ring): boolean {
  let c = false;
  for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
    const [xi, yi] = r[i], [xj, yj] = r[j];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
  }
  return c;
}
