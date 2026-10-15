import * as THREE from 'three';
import type { Human, HumanLib, Model } from './humans';
import { PedSpots } from './pedspots';

/**
 * Ambient pedestrians on sidewalk paths around the player. Composition follows Kreis 4 statistics
 * (research/npc_population.json): mostly 20–39, some older people (slower, cane/walker), children only
 * together with an adult, a few dog walkers; bags, backpacks and strollers attached at random.
 */
interface Ped {
  h: Human; path: number[][]; seg: number; t: number; dir: number; speed: number; x: number; y: number; tick: number;
  lateral: number; extras: THREE.Object3D[]; dog?: { obj: THREE.Object3D; mixer: THREE.AnimationMixer }; leader?: Ped;
}

/** Crowd hot spots (local metres): x, y, radius, weight by day, weight by night (Fri/Sat nightlife). */
const HOT: number[][] = [
  [731, -602, 190, 0.8, 1.0], [800, -760, 160, 0.8, 1.0], [786, -890, 150, 0.7, 0.9], [755, -945, 90, 0.5, 1.0], // Langstrasse, Helvetiaplatz, Kanzlei
  [1111, 42, 140, 0.6, 0.7], [-13, 150, 160, 0.8, 0.6], [718, 410, 100, 0.5, 0.8], [505, 215, 110, 0.5, 0.8], // Limmatplatz, Hardbrücke, Viadukt, Josefwiese
  [-2095, 704, 150, 0.8, 0.4], [-2285, 340, 120, 0.6, 0.4], [-495, -641, 120, 0.6, 0.4], [581, -1388, 120, 0.7, 0.4], // Altstetten, Albisriederplatz, Wiedikon
  [-1336, 239, 110, 0.5, 0.2], [1315, -640, 160, 0.8, 0.6], [393, -1202, 90, 0.5, 0.5], [-1003, 13, 130, 0.3, 0.5], // Letzipark, HB-Rand, Kalkbreite, Letzigrund
];
const AGE_W: [string, number][] = [['young', 0.56], ['mid', 0.33], ['old', 0.11]]; // adults only; children ride along

export class Pedestrians {
  readonly group = new THREE.Group();
  private peds: Ped[] = [];
  private pool = new Map<Model, Human[]>();
  private paths: number[][][] = [];
  private frame = 0;
  visRadius = 120;
  private player: [number, number] = [0, 0];
  /** Kindergartens/schools (local metres) and whether it is school-run time now (set by main). */
  schools: number[][] = [];
  schoolRun = false;
  /** People standing/sitting at benches, fountains, bars and construction sites (set via addSpots). */
  readonly spots: PedSpots;
  private hour = 12;
  private night = false;
  private hot = 0;

  constructor(private lib: HumanLib, public max: number, private height: (x: number, y: number) => number) {
    this.spots = new PedSpots(lib, this.group);
  }

  /** Tile meta with benches / fountains / signs / workers: static people (see pedspots.ts). */
  addSpots(meta: Parameters<PedSpots['add']>[0]) { this.spots.add(meta); }

  /** Game clock: minutes since midnight and weekday (0 = Monday). Drives density, nightlife and spot activity. */
  clock(minutes: number, weekday: number) {
    this.hour = (minutes / 60) % 24;
    this.night = (this.hour >= 22 || this.hour < 4) || (this.hour >= 19 && (weekday === 4 || weekday === 5));
    this.spots.hour = this.hour; this.spots.weekday = weekday;
  }

  /** 0..1: how busy the surroundings of (x, y) are right now (Langstrasse, stations, squares). */
  hotness(x: number, y: number): number {
    let best = 0;
    for (const [hx, hy, r, wd, wn] of HOT) {
      const d = Math.hypot(x - hx, y - hy);
      if (d < r) best = Math.max(best, (this.night ? wn : wd) * Math.pow(1 - d / r, 0.6));
    }
    return best;
  }

  addPaths(paths: number[][][]) { this.paths.push(...paths.filter((p) => p.length >= 2)); }

  nearest(x: number, y: number): { obj: THREE.Object3D; d: number } | null {
    let best: { obj: THREE.Object3D; d: number } | null = null;
    for (const p of this.peds) { const d = Math.hypot(p.x - x, p.y - y); if (!best || d < best.d) best = { obj: p.h.root, d }; }
    return best;
  }

  private model(age: string): Model {
    const list = this.lib.npcs.filter((m) => m.age === age);
    const src = list.length ? list : this.lib.npcs.filter((m) => m.age !== 'child');
    return src[Math.floor(Math.random() * src.length)];
  }

  private take(m: Model): Human {
    const h = this.pool.get(m)?.pop() ?? this.lib.instance(m);
    (h.root.userData as { model?: Model }).model = m;
    return h;
  }

  private release(p: Ped) {
    for (const e of p.extras) e.removeFromParent();
    if (p.dog) this.group.remove(p.dog.obj);
    this.group.remove(p.h.root);
    const m = (p.h.root.userData as { model: Model }).model;
    (this.pool.get(m) ?? this.pool.set(m, []).get(m)!).push(p.h);
  }

  private spawn(px: number, py: number): boolean {
    let cands = this.paths.filter((p) => Math.hypot(p[0][0] - px, p[0][1] - py) < 140);
    if (!cands.length || !this.lib.npcs.length) return false;
    if (this.hot > 0.15 && Math.random() < 0.6) { // busy places: walkers concentrate on the paths inside the hot zone
      const busy = cands.filter((p) => this.hotness(p[0][0], p[0][1]) > 0.25);
      if (busy.length) cands = busy;
    }
    let r = Math.random(), age = 'young';
    for (const [a, w] of AGE_W) { if (r < w) { age = a; break; } r -= w; }
    const m = this.model(age), h = this.take(m);
    const path = cands[Math.floor(Math.random() * cands.length)];
    const old = m.age === 'old';
    h.slow = old;
    const jog = !old && !this.night && Math.random() < (this.hour < 8 || (this.hour >= 17 && this.hour < 20) ? 0.07 : 0.025);
    const speed = jog ? 3.3 + Math.random() * 0.7 : old ? 0.7 + Math.random() * 0.3 : 1.05 + Math.random() * 0.55;
    h.setSpeed(speed);
    h.mixer.setTime(Math.random() * 2);
    this.group.add(h.root);
    const p: Ped = { h, path, seg: Math.floor(Math.random() * (path.length - 1)), t: Math.random(), dir: Math.random() < 0.5 ? 1 : -1,
      speed, x: path[0][0], y: path[0][1], tick: Math.floor(Math.random() * 3), lateral: 0, extras: [] };
    // accessories
    const add = (n: string) => { const o = this.lib.attach(h, n); if (o) p.extras.push(o); };
    const q = jog ? 1 : Math.random();
    if (old) { if (m.props.includes('walker') || q < 0.2) add('walker'); else if (m.props.includes('cane') || q < 0.55) add('cane'); }
    else if (q < 0.22) add('backpack'); else if (q < 0.37) add('shoulder_bag'); else if (q < 0.49) add('tote_bag');
    else if (q < 0.57) add(Math.random() < 0.5 ? 'shopping_bag' : 'shopping_bag_green'); else if (q < 0.61) add('stroller');
    if (Math.random() < 0.035) { // dog walker (Kreis 4: 1.75 dogs per 100 residents)
      const dog = this.lib.spawnFree(Math.random() < 0.5 ? 'dog_small' : 'dog_medium');
      if (dog) { p.dog = dog; this.group.add(dog.obj); add(dog.obj.name.includes('small') ? 'leash_small' : 'leash_medium'); }
    }
    this.peds.push(p);
    // friends walking together: pairs and threes, many more on a night out
    if (!old && !jog && Math.random() < (this.night ? 0.5 : 0.16 + 0.12 * this.hot)) {
      const n = Math.random() < 0.3 ? 2 : 1;
      for (let i = 0; i < n && this.peds.length < this.cap(); i++) {
        const fm = this.model(Math.random() < 0.8 ? 'young' : 'mid'), fh = this.take(fm);
        fh.setSpeed(speed); fh.mixer.setTime(Math.random() * 2); this.group.add(fh.root);
        this.peds.push({ ...p, h: fh, lateral: (i % 2 ? -1 : 1) * (0.75 + 0.2 * (i >> 1)), extras: [], dog: undefined, leader: p, tick: p.tick + i + 1 });
      }
    }
    // a child walking next to an adult (never alone)
    const kids = this.lib.npcs.filter((n) => n.age === 'child');
    const nearSchool = this.schoolRun && this.schools.some((sc) => Math.hypot(sc[0] - p.x, sc[1] - p.y) < 160);
    if (!old && kids.length && Math.random() < (nearSchool ? 0.45 : 0.09) && this.peds.length < this.cap()) {
      const km = kids[Math.floor(Math.random() * kids.length)], kh = this.take(km);
      kh.setSpeed(speed); this.group.add(kh.root);
      this.peds.push({ ...p, h: kh, lateral: 0.7, extras: [], dog: undefined, leader: p });
    }
    return true;
  }

  private cap() { return Math.round(this.max * (1 + 0.45 * this.hot)); }

  update(dt: number, px: number, py: number) {
    this.player = [px, py];
    this.frame++;
    this.peds = this.peds.filter((p) => {
      const lead = p.leader ? this.peds.includes(p.leader) : true;
      const keep = lead && Math.hypot(p.x - px, p.y - py) < 170;
      if (!keep) this.release(p);
      return keep;
    });
    this.hot = this.hotness(px, py);
    // busy places get up to 45 % more people; people on spots (benches, bars, sites) share the same total
    const total = this.cap();
    this.spots.budget = Math.max(4, Math.round(total * 0.4));
    this.spots.update(dt, px, py);
    while (this.peds.length < Math.max(0, total - this.spots.count) && this.spawn(px, py));
    for (const p of this.peds) {
      if (p.leader) { p.seg = p.leader.seg; p.t = p.leader.t; p.dir = p.leader.dir; }
      else {
        const a = p.path[p.seg], b = p.path[p.seg + 1];
        const len = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
        p.t += (p.dir * p.speed * dt) / len;
        if (p.t > 1 || p.t < 0) {
          const next = p.seg + p.dir;
          if (next < 0 || next >= p.path.length - 1) { p.dir *= -1; p.t = Math.min(1, Math.max(0, p.t)); }
          else { p.seg = next; p.t = p.dir > 0 ? 0 : 1; }
        }
      }
      const c = p.path[p.seg], d = p.path[p.seg + 1];
      const hx = (d[0] - c[0]) * p.dir, hy = (d[1] - c[1]) * p.dir, hl = Math.hypot(hx, hy) || 1;
      p.x = c[0] + (d[0] - c[0]) * p.t + (hy / hl) * p.lateral;
      p.y = c[1] + (d[1] - c[1]) * p.t - (hx / hl) * p.lateral;
      // step aside around the player instead of walking through her
      const ax = p.x - this.player[0], ay = p.y - this.player[1], ad = Math.hypot(ax, ay);
      if (ad < 0.9 && ad > 1e-3) { p.x = this.player[0] + (ax / ad) * 0.9; p.y = this.player[1] + (ay / ad) * 0.9; }
      const heading = Math.atan2(hx, hy);
      p.h.root.position.set(p.x, this.height(p.x, p.y), -p.y);
      p.h.root.rotation.y = -heading;
      const dist = Math.hypot(p.x - px, p.y - py), far = dist > 45;
      p.h.root.visible = dist < this.visRadius;
      if (p.dog) {
        const dx = p.x + (hy / hl) * 0.6 + (hx / hl) * 0.9, dy = p.y - (hx / hl) * 0.6 + (hy / hl) * 0.9;
        p.dog.obj.position.set(dx, this.height(dx, dy), -dy); p.dog.obj.rotation.y = -heading;
        p.dog.obj.visible = p.h.root.visible;
        if (!far) p.dog.mixer.update(dt * p.speed);
      }
      if (!far) p.h.mixer.update(dt);
      else if ((this.frame + p.tick) % 3 === 0) p.h.mixer.update(dt * 3);
    }
  }
}
