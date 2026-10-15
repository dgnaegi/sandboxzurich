import * as THREE from 'three';
import type { Human, HumanLib } from '../world/humans';
import type { Colliders } from '../player/collision';
import { bikeGeo, bikeModelMaterial } from '../world/bikes';
import { rideBones, ridePose, type RideBones } from '../world/ridepose';

/**
 * Comic police (content guidelines: they catch you, nobody gets hurt). Officers are NPC models with a
 * high-vis vest and cap. With 0 stars two officers stroll near the player; with stars they run after him.
 * Caught → "Formular-Büro".
 */
interface Cop { h: Human; x: number; y: number; heading: number; wanderX: number; wanderY: number; bike: THREE.Object3D | null; bones: RideBones; pedal: number }

const copBikeColor = new THREE.Color(0xf4f4f2);

const vestMat = new THREE.MeshLambertMaterial({ color: 0xd8f020 });
const capMat = new THREE.MeshLambertMaterial({ color: 0x1b2440 });
const stripeMat = new THREE.MeshLambertMaterial({ color: 0xeeeeee });

function uniform(h: Human) {
  const spine = h.root.getObjectByName('spine_03') ?? h.root.getObjectByName('spine_02') ?? h.root.getObjectByName('spine_01');
  const head = h.root.getObjectByName('head');
  if (spine) {
    const vest = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.42, 0.27), vestMat);
    const stripe = new THREE.Mesh(new THREE.BoxGeometry(0.43, 0.05, 0.28), stripeMat);
    stripe.position.y = -0.08;
    vest.add(stripe);
    vest.position.y = 0.05;
    spine.add(vest);
  }
  if (head) {
    const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.115, 0.08, 12), capMat);
    const peak = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.015, 0.09), capMat);
    peak.position.set(0, -0.03, -0.12);
    cap.add(peak);
    cap.position.y = 0.16;
    head.add(cap);
  }
}

export class Police {
  readonly group = new THREE.Group();
  private cops: Cop[] = [];
  private pool: Human[] = [];
  private respawn = 0;
  private stars = 0;

  constructor(private lib: HumanLib, private colliders: Colliders, private ground: (x: number, y: number) => number) {}

  private spawn(px: number, py: number, near: number) {
    for (let tries = 0; tries < 20; tries++) {
      const a = Math.random() * Math.PI * 2, r = near + Math.random() * 30;
      const x = px + Math.cos(a) * r, y = py + Math.sin(a) * r;
      if (this.colliders.inside(x, y)) continue;
      let h = this.pool.pop();
      if (!h) { h = this.lib.instance(this.lib.adults[(this.cops.length * 5 + 3) % this.lib.adults.length]); uniform(h); }
      // from 2 stars on, every second officer comes on an e-bike (Stadtpolizei uses fast e-bikes)
      let bike: THREE.Object3D | null = null;
      const holder = new THREE.Group();
      holder.add(h.root);
      if (this.stars >= 2 && this.cops.length % 2 === 1) {
        const m = new THREE.InstancedMesh(bikeGeo('ebike'), bikeModelMaterial, 1);
        m.setMatrixAt(0, new THREE.Matrix4()); m.setColorAt(0, copBikeColor);
        holder.add(m); bike = m;
        h.root.position.set(0, 0.12, 0.1);
      }
      this.group.add(holder);
      this.cops.push({ h, x, y, heading: 0, wanderX: x, wanderY: y, bike, bones: rideBones(h.root), pedal: 0 });
      return;
    }
  }

  /** Distance of the closest officer to (x, y). */
  nearest(x: number, y: number): number {
    return this.cops.reduce((m, c) => Math.min(m, Math.hypot(c.x - x, c.y - y)), Infinity);
  }

  positions() { return this.cops.map((c) => ({ x: c.x, y: c.y })); }

  /** Returns true when an officer catches the player. */
  update(dt: number, px: number, py: number, stars: number): boolean {
    this.stars = stars;
    const want = stars === 0 ? 2 : Math.min(8, 2 + stars * 1.5);
    this.cops = this.cops.filter((c) => {
      const keep = Math.hypot(c.x - px, c.y - py) < 180;
      if (!keep) this.release(c);
      return keep;
    });
    this.respawn -= dt;
    if (this.cops.length < want && this.respawn <= 0) { this.spawn(px, py, stars ? 45 : 25); this.respawn = stars ? 2.5 : 6; }
    let caught = false;
    for (const c of this.cops) {
      let tx = c.wanderX, ty = c.wanderY, v = 1.2;
      if (stars > 0) { tx = px; ty = py; v = c.bike ? 8.2 + stars * 0.3 : 4.6 + stars * 0.25; }
      else if (Math.hypot(tx - c.x, ty - c.y) < 1) { c.wanderX = c.x + (Math.random() - 0.5) * 30; c.wanderY = c.y + (Math.random() - 0.5) * 30; }
      const dx = tx - c.x, dy = ty - c.y, d = Math.hypot(dx, dy);
      if (d > 0.6) {
        const step = Math.min(d, v * dt);
        [c.x, c.y] = this.colliders.resolve(c.x + (dx / d) * step, c.y + (dy / d) * step, 0.35);
        c.heading = Math.atan2(dx, dy);
        c.h.setSpeed(c.bike ? 0 : v);
        c.pedal += c.bike ? v * dt * 2.2 : 0;
      } else c.h.setSpeed(0);
      if (stars > 0 && Math.hypot(px - c.x, py - c.y) < 1.1) caught = true;
      const holder = c.h.root.parent!;
      holder.position.set(c.x, this.ground(c.x, c.y), -c.y);
      holder.rotation.y = -c.heading;
      c.h.mixer.update(dt);
      if (c.bike) ridePose(c.bones, c.pedal);
    }
    return caught;
  }

  private release(c: Cop) {
    const holder = c.h.root.parent!;
    this.group.remove(holder);
    holder.remove(c.h.root);
    c.h.root.position.set(0, 0, 0);
    this.pool.push(c.h);
  }

  clear() {
    for (const c of this.cops) this.release(c);
    this.cops = [];
  }
}
