import * as THREE from 'three';
import type { Human, HumanLib, Model } from './humans';

/**
 * Ambient pedestrians on sidewalk paths around the player. Composition follows Kreis 4 statistics
 * (research/npc_population.json): mostly 20–39, some older people (slower, cane/walker), children only
 * together with an adult, a few dog walkers; bags, backpacks and strollers attached at random.
 */
interface Ped {
  h: Human; path: number[][]; seg: number; t: number; dir: number; speed: number; x: number; y: number; tick: number;
  lateral: number; extras: THREE.Object3D[]; dog?: { obj: THREE.Object3D; mixer: THREE.AnimationMixer }; leader?: Ped;
}

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

  constructor(private lib: HumanLib, public max: number, private height: (x: number, y: number) => number) {}

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
    const cands = this.paths.filter((p) => Math.hypot(p[0][0] - px, p[0][1] - py) < 140);
    if (!cands.length || !this.lib.npcs.length) return false;
    let r = Math.random(), age = 'young';
    for (const [a, w] of AGE_W) { if (r < w) { age = a; break; } r -= w; }
    const m = this.model(age), h = this.take(m);
    const path = cands[Math.floor(Math.random() * cands.length)];
    const old = m.age === 'old';
    h.slow = old;
    const speed = old ? 0.7 + Math.random() * 0.3 : 1.05 + Math.random() * 0.55;
    h.setSpeed(speed);
    h.mixer.setTime(Math.random() * 2);
    this.group.add(h.root);
    const p: Ped = { h, path, seg: Math.floor(Math.random() * (path.length - 1)), t: Math.random(), dir: Math.random() < 0.5 ? 1 : -1,
      speed, x: path[0][0], y: path[0][1], tick: Math.floor(Math.random() * 3), lateral: 0, extras: [] };
    // accessories
    const add = (n: string) => { const o = this.lib.attach(h, n); if (o) p.extras.push(o); };
    const q = Math.random();
    if (old) { if (m.props.includes('walker') || q < 0.2) add('walker'); else if (m.props.includes('cane') || q < 0.55) add('cane'); }
    else if (q < 0.22) add('backpack'); else if (q < 0.37) add('shoulder_bag'); else if (q < 0.49) add('tote_bag');
    else if (q < 0.57) add(Math.random() < 0.5 ? 'shopping_bag' : 'shopping_bag_green'); else if (q < 0.61) add('stroller');
    if (Math.random() < 0.035) { // dog walker (Kreis 4: 1.75 dogs per 100 residents)
      const dog = this.lib.spawnFree(Math.random() < 0.5 ? 'dog_small' : 'dog_medium');
      if (dog) { p.dog = dog; this.group.add(dog.obj); add(dog.obj.name.includes('small') ? 'leash_small' : 'leash_medium'); }
    }
    this.peds.push(p);
    // a child walking next to an adult (never alone)
    const kids = this.lib.npcs.filter((n) => n.age === 'child');
    const nearSchool = this.schoolRun && this.schools.some((sc) => Math.hypot(sc[0] - p.x, sc[1] - p.y) < 160);
    if (!old && kids.length && Math.random() < (nearSchool ? 0.45 : 0.09) && this.peds.length < this.max) {
      const km = kids[Math.floor(Math.random() * kids.length)], kh = this.take(km);
      kh.setSpeed(speed); this.group.add(kh.root);
      this.peds.push({ ...p, h: kh, lateral: 0.7, extras: [], dog: undefined, leader: p });
    }
    return true;
  }

  update(dt: number, px: number, py: number) {
    this.player = [px, py];
    this.frame++;
    this.peds = this.peds.filter((p) => {
      const lead = p.leader ? this.peds.includes(p.leader) : true;
      const keep = lead && Math.hypot(p.x - px, p.y - py) < 170;
      if (!keep) this.release(p);
      return keep;
    });
    while (this.peds.length < this.max && this.spawn(px, py));
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
