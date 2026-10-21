import * as THREE from 'three';
import { actions } from '../input/actions';
import type { Player } from './player';
import type { Obb } from './drive';
import type { Driven } from './player';

/** Player-side glue for driving: input mapping, chase camera, entering/leaving. Called from Player.update. */
export interface DriveHooks {
  obstacles(): Obb[];
  parked(x: number, y: number, r: number): Obb[];
  night(): number;
  /** Called when a requested stop-and-get-out has come to a halt. */
  stopped(): void;
}
export interface DriveState { stopPending: boolean; camDist: number; shake: number; fov: number; hooks: DriveHooks | null; cam?: THREE.PerspectiveCamera }

const BASE_FOV = 60;

export function enterDrive(p: Player, car: Driven) {
  p.driving = car; p.riding = null;
  p.body.root.visible = false;
  p.x = car.x; p.y = car.y; p.z = car.z; p.heading = car.h; p.speed = car.speed;
  p.drive.stopPending = false; p.drive.camDist = car.cam.dist - 1; p.drive.fov = BASE_FOV;
  p.yaw = car.h; p.pitch = 0.2;
}

/** Get out on the driver's side (or any free side); returns where the car stands. */
export function exitDrive(p: Player, rightFirst = false): { x: number; y: number; z: number; h: number } | null {
  const car = p.driving;
  if (!car) return null;
  const h = car.h, rx = Math.cos(h), ry = -Math.sin(h), fx = Math.sin(h), fy = Math.cos(h), d = car.half.w + 0.75;
  const spots = [[-rx * d, -ry * d], [rx * d, ry * d], [-rx * d + fx * 1.4, -ry * d + fy * 1.4], [rx * d - fx * 1.4, ry * d - fy * 1.4], [-fx * (car.half.l + 0.8), -fy * (car.half.l + 0.8)]];
  if (rightFirst) { spots.unshift(spots[1]); spots.splice(2, 1); }
  let pick = spots[0];
  for (const s of spots) if (!p.tiles.colliders.inside(car.x + s[0], car.y + s[1])) { pick = s; break; }
  const left = { x: car.x, y: car.y, z: car.z, h };
  p.driving = null;
  p.body.root.visible = true;
  p.x = car.x + pick[0]; p.y = car.y + pick[1]; p.heading = h; p.speed = 0;
  p.z = p.tiles.groundAt(p.x, p.y, car.z);
  p.mesh.position.set(p.x, p.z, -p.y);
  p.drive.stopPending = false; p.drive.shake = 0;
  if (p.drive.cam) { p.drive.cam.fov = BASE_FOV; p.drive.cam.updateProjectionMatrix(); }
  return left;
}

export function driveStep(p: Player, dt: number, camera: THREE.PerspectiveCamera, look: { yaw: number; pitch: number }) {
  const car = p.driving!, st = p.drive, hooks = st.hooks;
  st.cam = camera;
  const kb = actions.kb, useKb = kb.x !== 0 || kb.y !== 0;
  let throttle = useKb ? kb.y : actions.move.y, steer = useKb ? kb.x : actions.move.x;
  if (Math.abs(throttle) < 0.08) throttle = 0;
  if (st.stopPending) { // E pressed while rolling: brake to a halt, then get out
    throttle = car.speed > 0.5 ? -1 : car.speed < -0.5 ? 1 : 0; steer *= 0.3;
    if (Math.abs(car.speed) < 0.6 && hooks) { hooks.stopped(); return; }
  }
  car.update(dt, { throttle, steer, turbo: actions.run && !st.stopPending }, hooks?.obstacles() ?? null, hooks?.parked ?? (() => []));
  car.lights(hooks?.night() ?? 0);
  p.x = car.x; p.y = car.y; p.z = car.z; p.heading = car.h; p.speed = car.speed;
  p.mesh.position.set(p.x, p.z, -p.y);
  p.mesh.rotation.set(0, -car.h, 0);
  // chase camera: swings behind the car unless the player looks around
  const sp = Math.abs(car.speed);
  if (look.yaw || look.pitch) p.lastLook = 0;
  if (p.lastLook > 1.0) {
    let d = car.h - p.yaw; d = Math.atan2(Math.sin(d), Math.cos(d));
    p.yaw += d * Math.min(1, dt * (1.8 + sp * 0.08));
    p.pitch += (0.2 - p.pitch) * Math.min(1, dt * 1.5);
  }
  const want = car.cam.dist + Math.min(car.isTram ? 2 : 3, sp * 0.12), cp0 = Math.cos(p.pitch) * want;
  const free = p.tiles.colliders.freeFraction(p.x, p.y, p.x - Math.sin(p.yaw) * cp0, p.y - Math.cos(p.yaw) * cp0);
  st.camDist += (Math.max(2.5, want * free - 0.4) - st.camDist) * Math.min(1, dt * (free < 1 ? 20 : 3));
  const ahead = Math.min(3, sp * 0.12) * Math.sign(car.speed || 1);
  const target = new THREE.Vector3(p.x + Math.sin(car.h) * ahead, p.z + car.cam.h, -(p.y + Math.cos(car.h) * ahead));
  const cp = Math.cos(p.pitch);
  camera.position.set(target.x - Math.sin(p.yaw) * cp * st.camDist, target.y + Math.sin(p.pitch) * st.camDist + 0.6,
    target.z + Math.cos(p.yaw) * cp * st.camDist);
  camera.position.y = Math.max(camera.position.y, p.tiles.ground(camera.position.x, -camera.position.z) + 0.5);
  if (car.impact > 0.02) {
    const k = car.impact * 0.35;
    camera.position.x += (Math.random() - 0.5) * k; camera.position.y += (Math.random() - 0.5) * k; camera.position.z += (Math.random() - 0.5) * k;
  }
  camera.lookAt(target);
  const fov = BASE_FOV + Math.min(14, sp * 0.45);
  st.fov += (fov - st.fov) * Math.min(1, dt * 3);
  if (Math.abs(camera.fov - st.fov) > 0.05) { camera.fov = st.fov; camera.updateProjectionMatrix(); }
}
