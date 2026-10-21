import * as THREE from 'three';
import type { Transit } from '../world/transit';
import type { Rig } from './vehicle_model';

/**
 * Rig of the driven (articulated) bus built from the transit Blender modules: the front module is the car body
 * (DriveCar physics), the joint and rear module hang on a trailer that follows the hitch (pull kinematics:
 * the rear axle always points at the hitch, so it cuts the corner like the real thing).
 * The trailer has no collision of its own (only avoid-circles for traffic), see DECISIONS.
 */
export interface BusRig extends Rig { follow(x: number, y: number, h: number): void; tailCircles(): { x: number; y: number; r: number }[] }

export function buildBusRig(transit: Transit, specName: string, li: number): BusRig {
  const spec = transit.spec(specName)!;
  const group = new THREE.Group(), trailer = new THREE.Group();
  const mat = new THREE.MeshLambertMaterial({ vertexColors: true });
  const first = spec.sequence[0], hitch = transit.moduleLength(first.module) / 2; // joint behind the front module
  group.add(trailer); trailer.position.set(0, 0, hitch);
  spec.sequence.forEach((it, i) => {
    const geo = transit.moduleGeometry(it.module);
    if (!geo) return;
    const m = new THREE.Mesh(geo, mat);
    m.castShadow = true;
    m.rotation.y = it.rotateY180 ? Math.PI : 0;
    m.position.z = i === 0 ? 0 : it.z_center_from_front - first.z_center_from_front - hitch;
    (i === 0 ? group : trailer).add(m);
  });
  const label = new THREE.Mesh(new THREE.PlaneGeometry(1.7, 0.64), transit.labelMaterial(li));
  label.position.set(0, 2.75, -(hitch - 0.25)); label.rotation.y = Math.PI;
  group.add(label);

  const rear = spec.sequence[spec.sequence.length - 1], D = rear.z_center_from_front - first.z_center_from_front - hitch; // hitch -> rear module centre
  const tail = [{ x: 0, y: 0, r: 1.5 }, { x: 0, y: 0, r: 1.5 }];
  let rx = 0, ry = 0, ready = false;
  return {
    group, length: transit.moduleLength(first.module), width: 2.55, wheelR: 0.5, wheelbase: 5.7, hood: new THREE.Vector3(0, 1, -4),
    setWheels() {}, setLights() {}, dent() {}, setDamage() {},
    follow(x, y, h) {
      const fx = Math.sin(h), fy = Math.cos(h), hx = x - fx * hitch, hy = y - fy * hitch;
      if (!ready) { rx = hx - fx * D; ry = hy - fy * D; ready = true; }
      let dx = hx - rx, dy = hy - ry;
      const d = Math.hypot(dx, dy) || 1;
      dx /= d; dy /= d;
      rx = hx - dx * D; ry = hy - dy * D;
      trailer.rotation.y = h - Math.atan2(dx, dy);
      tail[0].x = hx - dx * 2.2; tail[0].y = hy - dy * 2.2;
      tail[1].x = rx; tail[1].y = ry;
    },
    tailCircles: () => tail,
    dispose() { mat.dispose(); label.geometry.dispose(); },
  };
}
