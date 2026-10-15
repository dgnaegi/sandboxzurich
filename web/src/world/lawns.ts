import * as THREE from 'three';
import type { Human, HumanLib } from './humans';

/**
 * People on the grass (spots from the pipeline: [x, y, z, heading, kind]; 0 lying, 1 picnic, 2 chatting).
 * Only the spots nearest to the player are populated, from a pool of model instances.
 */
const BLANKETS = [0xc8443a, 0x2f6b9a, 0xe0b040, 0x3a8a5a, 0x8a4aa0].map((c) => new THREE.MeshLambertMaterial({ color: c }));
const blanketGeo = new THREE.BoxGeometry(2.0, 0.02, 1.5);

interface Spot { x: number; y: number; z: number; h: number; kind: number; obj: THREE.Group | null; people: Human[] }

export class Lawns {
  readonly group = new THREE.Group();
  private spots: Spot[] = [];
  private pool: Human[] = [];
  private k = 0;

  constructor(private lib: HumanLib, public max: number) {}

  add(rows: number[][]) {
    for (const [x, y, z, h, kind] of rows) this.spots.push({ x, y, z, h, kind, obj: null, people: [] });
  }

  private human(): Human { return this.pool.pop() ?? this.lib.instance(this.lib.adults[(this.k++ * 7) % this.lib.adults.length]); }

  private populate(s: Spot) {
    const g = new THREE.Group();
    g.position.set(s.x, s.z, -s.y);
    g.rotation.y = -s.h;
    const lie = (dx: number, dz: number, rot: number) => {
      const h = this.human(), w = new THREE.Group();
      h.root.rotation.set(Math.PI / 2, 0, 0); // on the back, head towards +z
      h.root.position.set(0, 0.12, -0.8);
      w.add(h.root); w.position.set(dx, 0, dz); w.rotation.y = rot;
      g.add(w); s.people.push(h);
    };
    const stand = (dx: number, dz: number, rot: number) => {
      const h = this.human();
      h.root.rotation.set(0, rot, 0); h.root.position.set(dx, 0, dz);
      h.play(Math.random() < 0.35 ? 'stand_phone' : 'idle', 0, Math.random() * 3); // many look at their phone
      g.add(h.root); s.people.push(h);
    };
    if (s.kind === 0) lie(0, 0, 0);
    else if (s.kind === 1) {
      const b = new THREE.Mesh(blanketGeo, BLANKETS[Math.floor(Math.abs(s.x * 7 + s.y)) % BLANKETS.length]);
      b.position.y = 0.02; g.add(b);
      lie(-0.5, 0, 0); lie(0.55, 0.1, Math.PI);
    } else { stand(0, 0, 0); stand(0.9, -0.6, -2.2); stand(-0.8, -0.7, 2.3); }
    for (const h of s.people) { h.root.position.y += 0; h.mixer.update(Math.random()); }
    this.group.add(g);
    s.obj = g;
  }

  private clear(s: Spot) {
    if (!s.obj) return;
    for (const h of s.people) { h.root.removeFromParent(); h.root.rotation.set(0, 0, 0); h.root.position.set(0, 0, 0); this.pool.push(h); }
    s.people = [];
    this.group.remove(s.obj);
    s.obj = null;
  }

  update(dt: number, px: number, py: number) {
    const near = this.spots.map((s) => ({ s, d: Math.hypot(s.x - px, s.y - py) })).filter((e) => e.d < 110).sort((a, b) => a.d - b.d);
    let budget = this.max;
    const keep = new Set<Spot>();
    for (const { s } of near) {
      const cost = s.kind === 0 ? 1 : s.kind === 1 ? 2 : 3;
      if (budget < cost) break;
      budget -= cost; keep.add(s);
    }
    for (const s of this.spots) {
      if (keep.has(s) && !s.obj) this.populate(s);
      else if (!keep.has(s) && s.obj) this.clear(s);
    }
    for (const s of keep) for (const h of s.people) h.mixer.update(dt);
  }
}
