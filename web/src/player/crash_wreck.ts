import * as THREE from 'three';
import type { Tiles } from '../engine/tiles';
import type { Rig } from './vehicle_model';
import type { Obb } from './drive';
import type { CrashFx } from './crash_fx';

/**
 * A crashed car that is no longer driven: a shoved NPC/parked car or the player's own wreck. It slides and spins
 * until it stops (friction, walls), smokes by damage, stays as an obstacle and is removed once far from the player.
 * Whoever gets in the way is never hurt: pedestrians dodge, this is cars only.
 */
export class Wreck {
  vx = 0; vy = 0; spin = 0; z = 0;
  readonly hl: number; readonly hw: number;
  private pitch = 0; private roll = 0;
  constructor(private tiles: Tiles, readonly rig: Rig, readonly type: string, readonly color: THREE.Color,
    public x: number, public y: number, public h: number, public damage: number) {
    this.hl = rig.length / 2; this.hw = rig.width / 2;
    this.z = tiles.groundAt(x, y, tiles.ground(x, y));
    this.place();
  }

  get moving() { return Math.hypot(this.vx, this.vy) > 0.15 || Math.abs(this.spin) > 0.1; }

  obb(): Obb { return { x: this.x, y: this.y, fx: Math.sin(this.h), fy: Math.cos(this.h), hl: this.hl, hw: this.hw - 0.05, ref: this, vx: this.vx, vy: this.vy }; }

  /** Push from a hit at (px, py) with impulse (ix, iy) in m/s. */
  shove(ix: number, iy: number, px: number, py: number) {
    this.vx += ix; this.vy += iy;
    const cross = (px - this.x) * iy - (py - this.y) * ix;
    this.spin = Math.max(-2.4, Math.min(2.4, this.spin - cross * 0.12));
    this.damage = Math.min(1, this.damage + 0.25 + Math.hypot(ix, iy) * 0.03);
  }

  update(dt: number, fx: CrashFx) {
    if (this.moving) {
      const k = Math.exp(-dt * 1.8);
      this.vx *= k; this.vy *= k; this.spin *= Math.exp(-dt * 2.2);
      this.h += this.spin * dt;
      const [qx, qy] = this.tiles.colliders.resolve(this.x + this.vx * dt, this.y + this.vy * dt, this.hw);
      if (Math.hypot(qx - this.x - this.vx * dt, qy - this.y - this.vy * dt) > 0.02) { this.vx *= -0.2; this.vy *= -0.2; this.spin *= 0.5; }
      this.x = qx; this.y = qy;
      this.z += (this.tiles.groundAt(this.x, this.y, this.z) - this.z) * Math.min(1, dt * 10);
      this.place();
    }
    const lvl = this.damage < 0.5 ? 0 : this.damage < 0.85 ? 0.4 : 1;
    if (lvl) {
      const f = Math.sin(this.h), g = Math.cos(this.h), hz = -this.rig.hood.z;
      fx.smoke(this, this.x + f * hz, this.z + this.rig.hood.y, -(this.y + g * hz), lvl, dt);
    }
  }

  private place() {
    this.rig.group.position.set(this.x, this.z, -this.y);
    this.rig.group.rotation.set(this.pitch, -this.h, this.roll, 'YXZ');
  }
}
