import * as THREE from 'three';
import { carDay } from './cars';

/**
 * Light overlay for the traffic cars (one InstancedMesh per kind, no per-car objects): brake lights while braking
 * or queueing, indicators on turning cars, head and tail lights at dusk/night. Reads Traffic.positions().
 */
interface Pos { x: number; y: number; heading: number; kind: 'car' | 'bike'; len: number; v: number; id: number; brake: boolean; turn: number }

const CAP = 260;
const mk = (w: number, h: number, d: number, col: THREE.Color) => {
  const m = new THREE.InstancedMesh(new THREE.BoxGeometry(w, h, d), new THREE.MeshBasicMaterial({ color: col, toneMapped: false }), CAP);
  m.frustumCulled = false; m.count = 0;
  return m;
};

export class TrafficLights {
  private brake = mk(0.3, 0.1, 0.05, new THREE.Color(3, 0.1, 0.1));
  private tail = mk(0.3, 0.1, 0.05, new THREE.Color(0.9, 0.03, 0.04));
  private head = mk(0.32, 0.11, 0.05, new THREE.Color(2.4, 2.2, 1.7));
  private blink = mk(0.16, 0.08, 0.05, new THREE.Color(3, 1.6, 0));
  private n = [0, 0, 0, 0];

  constructor(scene: THREE.Scene) { scene.add(this.brake, this.tail, this.head, this.blink); }

  private put(m: THREE.InstancedMesh, k: number, c: number, s: number, x: number, y: number, z: number, lx: number, ly: number, lz: number) {
    const i = this.n[k]++;
    if (i >= CAP) { this.n[k] = CAP; return; }
    const a = m.instanceMatrix.array as Float32Array, o = i * 16;
    a[o] = c; a[o + 1] = 0; a[o + 2] = -s; a[o + 3] = 0; a[o + 4] = 0; a[o + 5] = 1; a[o + 6] = 0; a[o + 7] = 0;
    a[o + 8] = s; a[o + 9] = 0; a[o + 10] = c; a[o + 11] = 0;
    a[o + 12] = x + c * lx + s * lz; a[o + 13] = y + ly; a[o + 14] = z - s * lx + c * lz; a[o + 15] = 1;
  }

  update(cars: Pos[], time: number, night: number, ground: (x: number, y: number) => number, px: number, py: number) {
    this.n.fill(0);
    carDay.value = 1 - 0.85 * Math.min(1, Math.max(0, night));
    const dark = night > 0.3;
    for (const a of cars) {
      if (a.kind !== 'car' || (a.x - px) ** 2 + (a.y - py) ** 2 > 160 * 160) continue;
      const th = a.heading - Math.PI / 2, c = Math.cos(th), s = Math.sin(th), gy = ground(a.x, a.y) - 0.12, hl = a.len / 2 - 0.04;
      for (const sx of [-0.62, 0.62]) {
        if (a.brake || dark) this.put(a.brake ? this.brake : this.tail, a.brake ? 0 : 1, c, s, a.x, gy, -a.y, sx, 0.72, hl);
        if (dark) this.put(this.head, 2, c, s, a.x, gy, -a.y, sx, 0.68, -hl);
      }
      if (a.turn !== 0 && Math.floor(time * 3 + a.id * 0.37) % 2 === 0) {
        const lx = a.turn > 0 ? -0.74 : 0.74;
        this.put(this.blink, 3, c, s, a.x, gy, -a.y, lx, 0.7, -hl + 0.02);
        this.put(this.blink, 3, c, s, a.x, gy, -a.y, lx, 0.74, hl - 0.02);
      }
    }
    [this.brake, this.tail, this.head, this.blink].forEach((m, k) => { m.count = this.n[k]; m.instanceMatrix.needsUpdate = true; });
  }
}
