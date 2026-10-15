import * as THREE from 'three';
import { actions, consumeLook } from '../input/actions';
import type { Tiles } from '../engine/tiles';
import type { Human } from '../world/humans';
import { bikeGeo, bikeModelMaterial, type BikeSlot } from '../world/bikes';
import { carMaterial } from '../world/cars';
import { rideBones, ridePose, type RideBones } from '../world/ridepose';

// close to the speeds the walk/run clips were authored for (humans.ts), so feet don't slide
const WALK = 1.7, RUN = 5.0, RADIUS = 0.35, ACCEL = 9, DECEL = 14;
const BIKE_MAX = 7.5, BIKE_SPRINT = 10.5, BIKE_ACC = 3.5, BIKE_BRAKE = 7;

/** Third-person player: walks, or rides a bike. Movement relative to camera when walking, steering on the bike. */
export class Player {
  x: number; y: number;
  yaw = 0; // camera yaw, 0 = looking north
  pitch = 0.22;
  heading = 0;
  speed = 0;
  riding: BikeSlot | null = null;
  /** Speed factor on the bike (e.g. 1.2 on cycle lanes). */
  boost = 1;
  readonly mesh = new THREE.Group();
  private camDist = 5.5;
  private z = 0;
  private bikeMesh: THREE.InstancedMesh<THREE.BufferGeometry, THREE.Material> = new THREE.InstancedMesh(bikeGeo('city'), carMaterial as THREE.Material, 1);
  private lastLook = 0;
  /** Smoothed walking velocity (m/s, world x/y). */
  private vx = 0; private vy = 0;
  private pedal = 0;
  private bones: RideBones;

  constructor(x: number, y: number, private tiles: Tiles, private body: Human) {
    this.x = x; this.y = y;
    this.z = tiles.ground(x, y);
    this.mesh.add(body.root);
    this.bikeMesh.setMatrixAt(0, new THREE.Matrix4());
    this.bikeMesh.visible = false;
    this.bikeMesh.castShadow = true;
    this.mesh.add(this.bikeMesh);
    this.bones = rideBones(body.root);
  }

  teleport(x: number, y: number, yaw: number) {
    this.x = x; this.y = y; this.yaw = yaw; this.heading = yaw; this.speed = 0; this.vx = this.vy = 0;
    this.z = this.tiles.groundAt(x, y, this.z);
  }

  mount(slot: BikeSlot) {
    this.riding = slot;
    this.x = slot.x; this.y = slot.y; this.heading = slot.h; this.speed = 0; this.vx = this.vy = 0;
    this.bikeMesh.geometry = bikeGeo(slot.type.replace('_lean', ''));
    this.bikeMesh.material = bikeModelMaterial;
    this.bikeMesh.setColorAt(0, slot.color);
    if (this.bikeMesh.instanceColor) this.bikeMesh.instanceColor.needsUpdate = true;
    this.bikeMesh.visible = true;
  }

  /** Get off; returns where the bike was left. */
  dismount(): { x: number; y: number; z: number; h: number; color: THREE.Color } | null {
    if (!this.riding) return null;
    const left = { x: this.x, y: this.y, z: this.z, h: this.heading, color: this.riding.color };
    this.riding = null;
    this.bikeMesh.visible = false;
    // step off to the right
    const nx = this.x + Math.cos(this.heading) * 0.8, ny = this.y - Math.sin(this.heading) * 0.8;
    if (!this.tiles.colliders.inside(nx, ny)) { this.x = nx; this.y = ny; }
    this.speed = 0;
    return left;
  }

  update(dt: number, camera: THREE.PerspectiveCamera) {
    const look = consumeLook();
    if (look.yaw || look.pitch) this.lastLook = 0; else this.lastLook += dt;
    this.yaw += look.yaw;
    this.pitch = Math.min(1.2, Math.max(-0.25, this.pitch + look.pitch));
    const { x: mx, y: my } = actions.move;
    const ox = this.x, oy = this.y;

    if (this.riding) {
      const max = (actions.run ? BIKE_SPRINT : BIKE_MAX) * this.boost;
      if (my > 0.1) this.speed = Math.min(max * my, this.speed + BIKE_ACC * dt);
      else if (my < -0.1) this.speed = Math.max(-1.5, this.speed - BIKE_BRAKE * dt);
      else this.speed = Math.max(0, this.speed - 1.2 * dt);
      const turn = mx * (1.9 - Math.min(Math.abs(this.speed), 8) * 0.12) * dt * Math.sign(this.speed || 1);
      if (Math.abs(this.speed) > 0.3) this.heading += turn;
      const nx = this.x + Math.sin(this.heading) * this.speed * dt, ny = this.y + Math.cos(this.heading) * this.speed * dt;
      [this.x, this.y] = this.tiles.colliders.resolve(nx, ny, 0.45);
      if (Math.hypot(this.x - nx, this.y - ny) > 0.02) this.speed *= 0.6; // bumped into something
      // camera swings behind the bike unless the player is looking around
      if (this.lastLook > 1.2) { let d = this.heading - this.yaw; d = Math.atan2(Math.sin(d), Math.cos(d)); this.yaw += d * Math.min(1, dt * 2.5); }
    } else {
      const amount = Math.min(1, Math.hypot(mx, my));
      let tx = 0, ty = 0;
      if (amount > 0.05) {
        const s = Math.sin(this.yaw), c = Math.cos(this.yaw);
        const dx = my * s + mx * c, dy = my * c - mx * s, l = Math.hypot(dx, dy);
        const v = (actions.run ? RUN : WALK) * amount;
        tx = (dx / l) * v; ty = (dy / l) * v;
        let d = Math.atan2(dx, dy) - this.heading;
        d = Math.atan2(Math.sin(d), Math.cos(d));
        this.heading += d * Math.min(1, dt * 12);
      }
      // ease into and out of steps instead of jumping to full speed
      const k = Math.min(1, dt * (tx || ty ? ACCEL : DECEL));
      this.vx += (tx - this.vx) * k; this.vy += (ty - this.vy) * k;
      if (Math.hypot(this.vx, this.vy) > 0.01) {
        [this.x, this.y] = this.tiles.colliders.resolve(this.x + this.vx * dt, this.y + this.vy * dt, RADIUS);
        const mvx = (this.x - ox) / dt, mvy = (this.y - oy) / dt; // keep only what walls allowed
        this.vx = mvx; this.vy = mvy;
      }
      const v = Math.hypot(this.x - ox, this.y - oy) / dt;
      this.speed += (v - this.speed) * Math.min(1, dt * 10);
    }
    if (!this.tiles.inPlay(this.x, this.y)) { this.x = ox; this.y = oy; this.speed *= 0.3; } // fence: end of the playable map

    // animation: walking/running, or pedalling (walk clip, raised onto the saddle)
    if (this.riding) {
      this.body.setSpeed(0); // idle base pose, legs/arms overridden below
      this.body.root.position.set(0, 0.12, 0.1);
      this.body.root.rotation.x = 0;
    } else {
      this.body.setSpeed(this.speed);
      this.body.root.position.set(0, 0, 0);
      this.body.root.rotation.x = 0;
    }
    this.body.mixer.update(dt);
    if (this.riding) { this.pedal += this.speed * dt * 2.2; ridePose(this.bones, this.pedal); }
    this.z += (this.tiles.groundAt(this.x, this.y, this.z) - this.z) * Math.min(1, dt * 15);
    this.mesh.position.set(this.x, this.z, -this.y);
    this.mesh.rotation.y = -this.heading;
    this.mesh.rotation.z = this.riding ? -actions.move.x * Math.min(Math.abs(this.speed), 8) * 0.02 : 0;

    // camera: behind, pulled in front of walls
    const want = this.riding ? 6.5 : 5.5, cp0 = Math.cos(this.pitch) * want;
    const free = this.tiles.colliders.freeFraction(this.x, this.y, this.x - Math.sin(this.yaw) * cp0, this.y - Math.cos(this.yaw) * cp0);
    this.camDist += (Math.max(1.6, want * free - 0.3) - this.camDist) * Math.min(1, dt * (free < 1 ? 20 : 4));
    const target = new THREE.Vector3(this.x, this.z + 1.55, -this.y);
    const cp = Math.cos(this.pitch);
    camera.position.set(target.x - Math.sin(this.yaw) * cp * this.camDist, target.y + Math.sin(this.pitch) * this.camDist,
      target.z + Math.cos(this.yaw) * cp * this.camDist);
    camera.position.y = Math.max(camera.position.y, this.tiles.ground(camera.position.x, -camera.position.z) + 0.4);
    camera.lookAt(target);
  }
}
