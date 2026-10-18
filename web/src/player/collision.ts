/** 2D collision of a circle against building footprints (local metres), via a uniform grid. */
type Ring = number[][];
const CELL = 25;

export class Colliders {
  private grid = new Map<string, Ring[]>();
  private circles = new Map<string, number[][]>();        // cell -> [x, y, r] (trunks, poles, bins, benches)
  private circleRows = new Map<string, { cell: string; row: number[] }[]>();   // tile -> what it registered (for unloading)

  /** Register solid circles [x, y, r] of a tile (small obstacles; only checked near the player). */
  addCircles(key: string, rows: number[][]) {
    this.removeCircles(key);
    const mine: { cell: string; row: number[] }[] = [];
    for (const row of rows) {
      const cell = `${Math.floor(row[0] / CELL)},${Math.floor(row[1] / CELL)}`;
      (this.circles.get(cell) ?? this.circles.set(cell, []).get(cell)!).push(row);
      mine.push({ cell, row });
    }
    this.circleRows.set(key, mine);
  }

  removeCircles(key: string) {
    const mine = this.circleRows.get(key);
    if (!mine) return;
    const gone = new Set(mine.map((m) => m.row));
    for (const cell of new Set(mine.map((m) => m.cell))) {
      const l = this.circles.get(cell)!.filter((r) => !gone.has(r));
      if (l.length) this.circles.set(cell, l); else this.circles.delete(cell);
    }
    this.circleRows.delete(key);
  }

  /** Push the circle (x, y, rad) out of nearby solid circles. */
  resolveCircles(x: number, y: number, rad: number): [number, number] {
    const cx = Math.floor(x / CELL), cy = Math.floor(y / CELL);
    for (let pass = 0; pass < 2; pass++) {   // move2: two passes so a pole next to a wall/another pole cannot trap
      let moved = false;
      for (let i = cx - 1; i <= cx + 1; i++) for (let j = cy - 1; j <= cy + 1; j++) {
        for (const c of this.circles.get(`${i},${j}`) ?? []) {
          const dx = x - c[0], dy = y - c[1], m = rad + c[2];
          if (Math.abs(dx) >= m || Math.abs(dy) >= m) continue;
          const d = Math.hypot(dx, dy);
          if (d < m) { const k = d > 1e-4 ? m / d : 0; if (k) { x = c[0] + dx * k; y = c[1] + dy * k; } else x += m; moved = true; }
        }
      }
      if (!moved) break;
    }
    return [x, y];
  }

  /** move2: distance along (hx, hy) to the nearest solid circle whose edge reaches into a corridor of half width `hw` (bumper to centre), Infinity if none within `maxD`. */
  circleAhead(x: number, y: number, hx: number, hy: number, maxD: number, hw: number): number {
    let best = Infinity;
    const x1 = x + hx * maxD, y1 = y + hy * maxD, c0x = Math.floor((Math.min(x, x1) - 1) / CELL), c1x = Math.floor((Math.max(x, x1) + 1) / CELL);
    const c0y = Math.floor((Math.min(y, y1) - 1) / CELL), c1y = Math.floor((Math.max(y, y1) + 1) / CELL);
    for (let i = c0x; i <= c1x; i++) for (let j = c0y; j <= c1y; j++) for (const c of this.circles.get(`${i},${j}`) ?? []) {
      const dx = c[0] - x, dy = c[1] - y, f = dx * hx + dy * hy, l = -dx * hy + dy * hx;
      if (f > 0 && f < best && f < maxD + c[2] && Math.abs(l) < hw + c[2]) best = f - c[2];
    }
    return best;
  }

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

  /** Inside a footprint that is larger than a parked car (building, not a car-sized box)? */
  insideBuilding(x: number, y: number): boolean {
    return !!this.grid.get(`${Math.floor(x / CELL)},${Math.floor(y / CELL)}`)?.some((r) => {
      if (!pointInRing(x, y, r)) return false;
      let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
      for (const [px, py] of r) { x0 = Math.min(x0, px); y0 = Math.min(y0, py); x1 = Math.max(x1, px); y1 = Math.max(y1, py); }
      return Math.max(x1 - x0, y1 - y0) > 7;
    });
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
