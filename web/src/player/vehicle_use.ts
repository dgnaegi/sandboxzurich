import * as THREE from 'three';
import type { Tiles } from '../engine/tiles';
import type { HumanLib, Human } from '../world/humans';
import type { Traffic } from '../world/traffic';
import { parkedCars, carLength, type CarSlot } from '../world/parkedcars';
import { buildRig, initCarEnvironment } from './vehicle_model';
import { DriveCar, type Obb } from './drive';
import { enterDrive, exitDrive } from './vehicle_player';
import type { Player } from './player';
import type { Audio } from '../engine/audio';

/**
 * Taking and leaving cars: nearest parked car or car in traffic within reach, E to get in. The driver of a
 * moving car just gets out and walks off (no violence). Wiring for the later wanted stars: `onTheft`.
 */
type Target = { kind: 'parked'; d: number; slot: CarSlot } | { kind: 'traffic'; d: number };

export const REACH = 3.2;

export class CarUse {
  /** Hook for the wanted system (not active in the map phase): called with 'parked' or 'traffic' on every theft. */
  onTheft: ((kind: 'parked' | 'traffic') => void) | null = null;
  private busy = false;
  private leavers: { h: Human; t: number; dx: number; dy: number; x: number; y: number }[] = [];
  private scene: THREE.Scene;

  constructor(private player: Player, private tiles: Tiles, private traffic: Traffic, private humans: HumanLib,
    private audio: Audio, renderer: THREE.WebGLRenderer, scene: THREE.Scene, obstacles: () => Obb[], night: () => number) {
    this.scene = scene;
    initCarEnvironment(renderer);
    parkedCars.init(scene);
    player.drive.hooks = {
      obstacles,
      night,
      parked: (x, y, r) => parkedCars.near(x, y, r).map((s) => ({ x: s.x, y: s.y, fx: Math.sin(s.h), fy: Math.cos(s.h), hl: carLength(s.type) / 2, hw: 0.9 })),
      stopped: () => this.exit(),
    };
  }

  /** Closest car in reach (parked or driving), or null. */
  nearest(): Target | null {
    if (this.busy || this.player.driving || this.player.riding) return null;
    const { x, y } = this.player;
    const slot = parkedCars.nearest(x, y, REACH);
    const t = this.traffic.findCar(x, y, REACH);
    const sd = slot ? Math.hypot(slot.x - x, slot.y - y) : Infinity;
    if (t && (!slot || t.d < sd - 1)) return { kind: 'traffic', d: t.d };
    return slot ? { kind: 'parked', d: sd, slot } : null;
  }

  async enter(t: Target) {
    if (this.busy) return;
    this.busy = true;
    try {
      let type: string, color: THREE.Color, x: number, y: number, h: number, v = 0;
      if (t.kind === 'parked') {
        ({ type, color, x, y, h } = t.slot);
        parkedCars.take(t.slot);
      } else {
        const c = this.traffic.findCar(this.player.x, this.player.y, REACH, true);
        if (!c) return;
        ({ type, color, x, y, h, v } = c);
        this.spawnLeaver(x, y, h);
      }
      const rig = await buildRig(type, color);
      this.scene.add(rig.group);
      const car = new DriveCar(this.tiles, rig, type, color, x, y, h, v);
      car.onImpact = (s) => this.audio.carCrash(Math.min(1, s / 10));
      enterDrive(this.player, car);
      this.audio.carDoor();
      this.onTheft?.(t.kind);
    } finally { this.busy = false; }
  }

  /** E while driving: brake to a halt first if still rolling, then get out. */
  requestExit() {
    const car = this.player.driving;
    if (!car) return;
    if (Math.abs(car.speed) < 1) this.exit(); else this.player.drive.stopPending = true;
  }

  exit() {
    const car = this.player.driving;
    if (!car) return;
    const left = exitDrive(this.player);
    this.scene.remove(car.rig.group);
    car.rig.dispose();
    if (left) parkedCars.drop(car.type, car.color, left.x, left.y, left.z, left.h);
    this.audio.carDoor();
    this.audio.engine(0, 0, 0, false);
  }

  get driving() { return !!this.player.driving; }

  /** The driver who got out walks away from the road for a few seconds, then disappears. */
  private spawnLeaver(x: number, y: number, h: number) {
    const npcs = this.humans.npcs.filter((m) => m.age !== 'child');
    if (!npcs.length) return;
    const hum = this.humans.instance(npcs[Math.floor(Math.random() * npcs.length)]);
    const rx = Math.cos(h), ry = -Math.sin(h), px = x + rx * 1.4, py = y + ry * 1.4; // kerb-side door (right), walks off to the pavement
    hum.root.position.set(px, this.tiles.ground(px, py), -py);
    hum.root.rotation.y = -Math.atan2(rx, ry);
    hum.setSpeed(1.5);
    hum.root.traverse((o) => { o.frustumCulled = false; });
    this.scene.add(hum.root);
    this.leavers.push({ h: hum, t: 0, dx: rx, dy: ry, x: px, y: py });
  }

  update(dt: number) {
    for (const l of this.leavers) {
      l.t += dt;
      if (l.t < 0.8) { l.h.setSpeed(0); } else {
        l.h.setSpeed(1.5);
        [l.x, l.y] = this.tiles.colliders.resolve(l.x + l.dx * 1.5 * dt, l.y + l.dy * 1.5 * dt, 0.35);
        l.h.root.position.set(l.x, this.tiles.ground(l.x, l.y), -l.y);
        l.h.root.rotation.y = -Math.atan2(l.dx, l.dy);
      }
      l.h.mixer.update(dt);
    }
    for (let i = this.leavers.length - 1; i >= 0; i--) {
      if (this.leavers[i].t > 14) { this.scene.remove(this.leavers[i].h.root); this.leavers.splice(i, 1); }
    }
    const car = this.player.driving;
    if (car) this.audio.engine(car.rpm, Math.max(0, car.throttle), Math.abs(car.slip) + (car.braking ? Math.abs(car.speed) * 0.06 : 0), true, car.speed);
  }
}
