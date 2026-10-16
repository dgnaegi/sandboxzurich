import * as THREE from 'three';
import { inRail } from './railzone';
import { FAMILY, type Human, type HumanLib, type Role } from './humans';

/** A clip family name (humans.FAMILY) or a single clip name. */
export const clipFor = (h: Human, a: string): string => (a in FAMILY ? h.pick(a as keyof typeof FAMILY, Math.random()) : h.has(a) ? a : 'idle');

/**
 * Standing / sitting people at fixed spots taken from the tile meta: benches (sitting), fountains (standing at the rim),
 * bars at night (smokers in front of the door), cafés/kiosks (looking at the phone) and construction workers
 * (hard hat + hi-vis vest, from pipeline/sites.py). Only the spots nearest to the player are populated, from a pool,
 * and the number of people is capped by the budget the crowd hands in (quality.peds based).
 */
type Kind = 'sit' | 'fount' | 'smoke' | 'cafe' | 'work';
/** ry = three rotation.y of the person (model faces local -z); (ax, ay) = unit axis in world for side-by-side offsets */
interface Spot { x: number; y: number; z: number; ry: number; ax: number; ay: number; kind: Kind; k: number; people: Human[]; gear: THREE.Object3D[][] }
/** the mocap pelvis sits ~5 cm above a 0.46 m bench seat */
const SIT_DROP = 0.05;
const face = (fx: number, fy: number) => Math.atan2(-fx, fy);

const BARS = new Set(['bar', 'pub', 'nightclub', 'biergarten', 'club', 'cocktail']);
const CAFES = new Set(['cafe', 'kiosk', 'bakery', 'ice_cream', 'fast_food', 'confectionery']);
const hash = (x: number, y: number) => Math.abs(Math.floor(x * 73.13 + y * 19.7 + x * y * 0.011)) % 1000;

export class PedSpots {
  private spots: Spot[] = [];
  private pool: Human[] = [];
  private live: Spot[] = [];
  private n = 0;
  private frame = 0;
  hour = 12;
  weekday = 0;
  visRadius = 75;
  /** hard cap for people on spots (set by the crowd every frame) */
  budget = 8;

  constructor(private lib: HumanLib, private parent: THREE.Group, private ground?: (x: number, y: number) => number) {}

  add(meta: { benches?: number[][]; fountains?: number[][]; signs?: { x: number; y: number; z: number; tx: number; ty: number; kind: string }[]; workers?: number[][] }) {
    const mk = (x: number, y: number, z: number, ry: number, ax: number, ay: number, kind: Kind, k: number) => !inRail(x, y) && this.spots.push({ x, y, z, ry, ax, ay, kind, k, people: [], gear: [] });
    // Bench rows [x, y, z, heading, type]: the sitter faces local -z of the bench (backrest at +z), pelvis on the seat.
    // Type 2/4 = table-bench combo (seats at local z = +-0.65 on both sides of the table, facing it); 6 = place bench,
    // 7 = place seat (heading already faces away from the backrest, see pipeline/places_detail.py)
    for (const [x, y, z, h, t] of meta.benches ?? []) {
      const k = hash(x, y), ry = -h + Math.PI / 2;
      if (k % 100 >= 60) continue;
      if (t === 2 || t === 4) {
        for (const s of [1, -1]) mk(x + Math.sin(ry) * 0.65 * s, y - Math.cos(ry) * 0.65 * s, z, s > 0 ? ry : ry + Math.PI, Math.cos(ry), Math.sin(ry), 'sit', k + (s > 0 ? 0 : 37));
      } else mk(x, y, z, ry, Math.cos(ry), Math.sin(ry), 'sit', k);
    }
    for (const [x, y, z] of meta.fountains ?? []) {
      const k = hash(x, y), a = (k % 628) / 100;
      if (k % 100 < 55) mk(x + Math.cos(a) * 1.4, y + Math.sin(a) * 1.4, z, face(-Math.cos(a), -Math.sin(a)), 1, 0, 'fount', k);
    }
    for (const s of meta.signs ?? []) {
      const k = hash(s.x, s.y), nx = s.ty, ny = -s.tx; // outward facade normal
      if (BARS.has(s.kind)) mk(s.x + nx * 1.4, s.y + ny * 1.4, s.z, face(s.tx, s.ty), s.tx, s.ty, 'smoke', k);
      else if (CAFES.has(s.kind) && k % 100 < 40) mk(s.x + nx * 1.1, s.y + ny * 1.1, s.z, face(nx, ny) + ((k % 7) - 3) * 0.12, 1, 0, 'cafe', k);
    }
    for (const [x, y, z, yaw] of meta.workers ?? []) mk(x, y, z, face(Math.cos(yaw), Math.sin(yaw)), 1, 0, 'work', hash(x, y));
  }

  private active(s: Spot): boolean {
    const h = this.hour, night = h >= 22 || h < 6, p = s.k % 100;
    switch (s.kind) {
      case 'sit': return night ? p < 12 : h >= 8 && p < 60;
      case 'fount': return h >= 9 && h < 22;
      case 'cafe': return h >= 7 && h < 20;
      case 'smoke': return h >= 18 || h < 3 ? p < (this.weekday >= 4 && this.weekday <= 5 ? 90 : 55) : false;
      case 'work': return this.weekday <= 4 && ((h >= 7 && h < 12) || (h >= 13 && h < 17));
    }
  }

  private take(role: Role = 'any'): Human {
    const h = this.pool.pop() ?? this.lib.instance(this.lib.adults[(this.n++ * 7) % this.lib.adults.length]);
    this.lib.dress(h, role);
    return h;
  }

  /** A construction worker spot (active or not) lies within `r` m of (x, y). */
  workNear(x: number, y: number, r: number): boolean { return this.spots.some((s) => s.kind === 'work' && Math.abs(s.x - x) < r && Math.abs(s.y - y) < r); }

  private place(h: Human, x: number, y: number, z: number, ry: number, snap = false) {
    h.root.position.set(x, snap && this.ground ? this.ground(x, y) : z, -y);   // sign-based spots carry the sign height: snap to terrain
    h.root.rotation.set(0, ry, 0);
    this.parent.add(h.root);
  }

  private populate(s: Spot) {
    /** Deterministic 0..1 per spot and person, so a spot looks the same every time it is rebuilt. */
    const rnd = (i: number) => ((s.k * 7 + i * 131 + 17) % 100) / 100;
    const person = (off: number, ry: number, anim: string, i = 0, role: Role = 'any') => {
      const h = this.take(role);
      h.play(clipFor(h, anim), 0);
      s.people.push(h);
      this.place(h, s.x + s.ax * off, s.y + s.ay * off, s.z, ry, s.kind === 'smoke' || s.kind === 'cafe');
      return h;
    };
    /** Standing around: weight shifts, arms crossed, hands in pockets, looking around, texting, phoning. */
    const loiter = (i: number, wait = false) => {
      const r = rnd(i);
      return r < 0.28 ? 'phone' : r < 0.4 ? 'call' : wait ? 'wait' : 'idle';
    };
    if (s.kind === 'sit') {
      const n = 1 + (s.k % 3 === 0 ? 1 : 0);
      for (let i = 0; i < n; i++) {
        const off = (i - (n - 1) / 2) * 0.9 + (n === 1 ? ((s.k % 5) - 2) * 0.12 : 0);
        const h0 = this.take(), fam = n === 2 ? 'sitTalk' : 'sit';
        h0.play(h0.pick(fam, rnd(i)), 0, Math.random() * 4);
        s.people.push(h0);
        // a pair on one bench turns towards each other (talking); alone: slightly random posture
        this.place(h0, s.x + s.ax * off, s.y + s.ay * off, s.z - SIT_DROP, s.ry + (n === 2 ? (i ? 0.4 : -0.4) : (rnd(5) - 0.5) * 0.3));
      }
    } else if (s.kind === 'smoke') { person(-0.5, s.ry, 'talk', 0); person(0.5, s.ry + Math.PI, rnd(2) < 0.7 ? 'listen' : 'talk2', 1); }
    else if (s.kind === 'work') person(0, s.ry + (s.k % 5) * 0.15, s.k % 4 === 0 ? 'call' : s.k % 3 === 0 ? 'wait' : 'idle', 0, 'builder');   // hard hat + hi-vis from humankit
    else if (s.kind === 'cafe') person(0, s.ry, rnd(0) < 0.45 ? 'phone' : loiter(0, true));
    else person(0, s.ry, loiter(0));
  }

  private clear(s: Spot) {
    for (const g of s.gear) for (const o of g) o.removeFromParent();
    s.gear = [];
    for (const h of s.people) { h.root.removeFromParent(); h.root.rotation.set(0, 0, 0); this.pool.push(h); }
    s.people = [];
  }

  get count() { return this.live.reduce((n, s) => n + s.people.length, 0); }

  update(dt: number, px: number, py: number) {
    this.frame++;
    if (this.frame % 20 === 1) {
      const cost = (s: Spot) => (s.kind === 'sit' ? 1 + (s.k % 3 === 0 ? 1 : 0) : s.kind === 'smoke' ? 2 : 1);
      const near = this.spots.filter((s) => Math.abs(s.x - px) < this.visRadius && Math.abs(s.y - py) < this.visRadius && this.active(s))
        .map((s) => ({ s, d: Math.hypot(s.x - px, s.y - py) })).filter((e) => e.d < this.visRadius).sort((a, b) => a.d - b.d);
      let left = this.budget;
      const keep = new Set<Spot>();
      for (const { s } of near) { const c = cost(s); if (left < c) continue; left -= c; keep.add(s); }
      for (const s of this.live) if (!keep.has(s)) this.clear(s);
      let built = 0;
      for (const s of keep) if (!s.people.length && built++ < 2) this.populate(s);
      this.live = [...keep].filter((s) => s.people.length);
    }
    for (const s of this.live) {
      if (Math.hypot(s.x - px, s.y - py) > 35) continue; // far: frozen
      for (const h of s.people) h.mixer.update(dt);
    }
  }
}
