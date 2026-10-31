import type { Tiles } from '../engine/tiles';
import type { DriveCar } from './drive';

/**
 * Stuck detection and the failsafe for the driven car.
 *
 * "Stuck" is deliberately strict, all of these at once for a while:
 *   1. the player keeps asking for movement (throttle or reverse held),
 *   2. the car gets nowhere: everywhere it has been in the last 3 s fits in a 2.5 m pocket (the bounding box of
 *      its path; bouncing back and forth between a tree and a wall stays inside such a box, a slow U-turn or a
 *      crawl along a facade does not), measured once at least 2 s of path exist,
 *   3. recent contact: pushed by a wall, post, tree, car or the fence within the last 0.6 s, or wedged so that the
 *      pushes cancel out. A bouncing car is only in contact every few frames, hence the memory.
 * Waiting at a light, idling or a slow U-turn never satisfy all three. Bouncing hard (three or more impacts within
 * a second) counts double, so a car ping-ponging in a pocket is freed sooner.
 *   WARN   after 2.5 s of stuckness: hint (try reverse; rescue follows)
 *   RESCUE after 5 s:              the car is set down on the nearest legal free spot on the same height level
 * Letting go of the controls, or getting free, lets the clock run down again at the same rate it filled.
 * From the moment the throttle goes down in a trap that is about 4.5 s to the hint and 7 s to the rescue.
 */
const WARN = 2.5, RESCUE = 5.0, WINDOW = 3.0, MIN_SPAN = 2.0, POCKET = 2.5, CONTACT_MEMORY = 0.6, BOUNCE_HITS = 3;

export class StuckGuard {
  private t = 0;
  private clock = 0;
  private warned = false;
  private contactT = 0;
  private impacts: number[] = [];
  private trail: { t: number; x: number; y: number }[] = [];

  /** Call from the car's onImpact. */
  impact() { this.impacts.push(this.clock); }
  reset() { this.t = 0; this.warned = false; this.contactT = 0; this.impacts.length = 0; this.trail.length = 0; }
  /** Seconds of continuous stuckness so far (0 when free); tests and HUD. */
  get seconds() { return this.t; }

  /** Once per frame while driving. `wants` = the player is pushing the throttle or reverse. */
  update(dt: number, car: Pick<DriveCar, 'x' | 'y' | 'touching' | 'pinned'>, wants: boolean): 'warn' | 'rescue' | null {
    this.clock += dt;
    this.trail.push({ t: this.clock, x: car.x, y: car.y });
    while (this.trail.length > 1 && this.trail[0].t < this.clock - WINDOW) this.trail.shift();
    while (this.impacts.length && this.impacts[0] < this.clock - 1) this.impacts.shift();
    this.contactT = car.touching || car.pinned ? CONTACT_MEMORY : Math.max(0, this.contactT - dt);
    const span = this.clock - this.trail[0].t;
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    for (const p of this.trail) { if (p.x < x0) x0 = p.x; if (p.x > x1) x1 = p.x; if (p.y < y0) y0 = p.y; if (p.y > y1) y1 = p.y; }
    const pocket = Math.hypot(x1 - x0, y1 - y0);
    const stuck = wants && span >= MIN_SPAN && pocket < POCKET && this.contactT > 0;
    if (!stuck) {
      this.t = Math.max(0, this.t - dt);
      if (this.t === 0) this.warned = false;
      return null;
    }
    this.t += dt * (this.impacts.length >= BOUNCE_HITS ? 2 : 1);
    if (this.t >= RESCUE) { this.reset(); return 'rescue'; }
    if (this.t >= WARN && !this.warned) { this.warned = true; return 'warn'; }
    return null;
  }
}

/**
 * Nearest spot where the car fits: six probe points of its footprint are clear of buildings, posts and trees at
 * the car's height level, on legal ground (fence, rails, water, landmarks via `legal`), and the ground there is
 * within 1.2 m of the car's height so a car on a bridge stays on the bridge and one below stays below. Rings of
 * 3 to 30 m; spots on the carriageway are preferred, then any legal spot. The heading points away from the trap
 * first, then keeps the car's own heading. Null if nothing fits within 30 m.
 */
export function freeSpotFor(car: DriveCar, tiles: Tiles, legal: (x: number, y: number) => boolean): { x: number; y: number; h: number } | null {
  const z = car.z, hl = car.half.l, hw = car.half.w;
  const elevated = tiles.onElevatedDeck(car.x, car.y, z);
  const fits = (x: number, y: number, h: number) => {
    const fx = Math.sin(h), fy = Math.cos(h), rx = fy, ry = -fx;
    for (const o of [-hl + 0.4, 0, hl - 0.4]) for (const l of [-hw + 0.2, hw - 0.2]) {
      const px = x + fx * o + rx * l, py = y + fy * o + ry * l;
      if (!tiles.inPlay(px, py)) return false;
      if (!elevated && !legal(px, py)) return false;   // on a deck the ground rules below (rail land, buildings) do not apply
      const [qx, qy] = tiles.resolveSolid(px, py, 0.6, z);
      if (Math.hypot(qx - px, qy - py) > 0.02) return false;
      if (Math.abs(tiles.groundAt(px, py, z) - z) > 1.2) return false;
    }
    return true;
  };
  for (const road of [true, false]) {
    for (const r of [3, 4.5, 6, 8, 10.5, 13, 16, 20, 25, 30]) {
      const n = Math.max(8, Math.round(r * 2.2));
      for (let k = 0; k < n; k++) {
        const a = (k / n) * Math.PI * 2 + r, x = car.x + Math.cos(a) * r, y = car.y + Math.sin(a) * r;
        if (road && !tiles.onRoad(x, y)) continue;
        for (const h of [Math.atan2(Math.cos(a), Math.sin(a)), car.h]) if (fits(x, y, h)) return { x, y, h };
      }
    }
  }
  return null;
}
