import type { Tiles } from '../engine/tiles';
import type { Landmarks3D } from '../world/landmarks3d';
import { inRail } from '../world/railzone';

/**
 * Free standing spots for spawns and map jumps: never inside buildings or landmark geometry, on railway land, over
 * water, on tram tracks or outside the fence. Spiral search from the wish point; pavement preferred over carriageway.
 */
const TRAM_CELL = 20, TRAM_HALF = 2.3;
const tramGrid = new Map<string, number[][]>();   // cell -> segments [ax, ay, bx, by]
let tramLoaded = false;

export async function loadTramTracks(url = '/data/transit.json'): Promise<void> {
  if (tramLoaded) return;
  tramLoaded = true;
  try {
    const d = (await (await fetch(url)).json()) as { lines: { mode: string; pts: number[][] }[] };
    for (const l of d.lines) {
      if (l.mode !== 'tram') continue;
      for (let i = 1; i < l.pts.length; i++) {
        const [ax, ay] = l.pts[i - 1], [bx, by] = l.pts[i], seg = [ax, ay, bx, by];
        for (let cx = Math.floor((Math.min(ax, bx) - TRAM_HALF) / TRAM_CELL); cx <= Math.floor((Math.max(ax, bx) + TRAM_HALF) / TRAM_CELL); cx++)
          for (let cy = Math.floor((Math.min(ay, by) - TRAM_HALF) / TRAM_CELL); cy <= Math.floor((Math.max(ay, by) + TRAM_HALF) / TRAM_CELL); cy++) {
            const k = `${cx},${cy}`;
            (tramGrid.get(k) ?? tramGrid.set(k, []).get(k)!).push(seg);
          }
      }
    }
  } catch { /* no transit data: tram check off */ }
}

/** On or next to a tram track (OSM centre line, +-2.3 m)? */
export function onTram(x: number, y: number): boolean {
  for (const [ax, ay, bx, by] of tramGrid.get(`${Math.floor(x / TRAM_CELL)},${Math.floor(y / TRAM_CELL)}`) ?? []) {
    const dx = bx - ax, dy = by - ay, l2 = dx * dx + dy * dy || 1, t = Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / l2));
    if (Math.hypot(x - ax - t * dx, y - ay - t * dy) < TRAM_HALF) return true;
  }
  return false;
}

export interface SpawnEnv { tiles: Tiles; landmarks: Landmarks3D }

/** Is (x, y) a legal standing spot? `quality` adds the pavement preference (not on a carriageway). */
export function validSpot(env: SpawnEnv, x: number, y: number, pavement = false): boolean {
  const t = env.tiles;
  if (!t.inPlay(x, y) || t.colliders.inside(x, y) || inRail(x, y) || onTram(x, y) || t.inWater(x, y)) return false;
  const [rx, ry] = t.colliders.resolve(x, y, 0.5);       // keep half a metre from walls
  if (Math.hypot(rx - x, ry - y) > 0.05) return false;
  if (pavement && t.onRoad(x, y)) return false;
  const gz = t.ground(x, y), fz = t.groundAt(x, y, gz + 1);
  if (t.bridges.heightAt(x, y, fz + 3.2, 1.3) !== null || t.ceilingAbove(x, y, fz, 4.5)) return false;   // deck / bridge right above the head
  return !env.landmarks.solidAt(x, y, fz);
}

/** Load what the checks need around (x, y), then return the nearest legal spot (the wish point itself if it is legal). */
export async function findSpot(env: SpawnEnv, x: number, y: number, maxR = 400): Promise<[number, number]> {
  await Promise.all([env.tiles.update(x, y), loadTramTracks(), env.landmarks.prepare(x, y)]);
  if (validSpot(env, x, y)) return [x, y];
  for (const pavement of [true, false]) {
    for (let r = 1; r <= maxR; r += Math.max(1, r * 0.04)) {
      const n = Math.max(6, Math.round((Math.PI * 2 * r) / 1.5));
      for (let k = 0; k < n; k++) {
        const a = (k / n) * Math.PI * 2 + r * 0.7, px = x + Math.cos(a) * r, py = y + Math.sin(a) * r;
        if (validSpot(env, px, py, pavement)) return [px, py];
      }
    }
  }
  return [x, y];
}
