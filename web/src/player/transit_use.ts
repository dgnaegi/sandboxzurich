import * as THREE from 'three';
import type { Tiles } from '../engine/tiles';
import type { Audio } from '../engine/audio';
import type { Transit, VehicleHandle } from '../world/transit';
import { consumeBell } from '../input/actions';
import { DriveCar, CAR_TUNE, type Obb, type Tune } from './drive';
import { TramCar } from './drive_tram';
import { buildBusRig } from './bus_rig';
import { enterDrive, exitDrive } from './vehicle_player';
import type { Player } from './player';

/**
 * Taking and leaving trams and buses (E, like cars). Trams run on their rails (TramCar), buses are DriveCar
 * physics with an articulated rig (bus_rig.ts). A taken trip is removed from the schedule (Transit.take); the
 * vehicle stays standing where it was left and goes back to the schedule once the player is far away.
 */
export const TRANSIT_REACH = 3.5;
const BUS_TUNE: Tune = { ...CAR_TUNE, acc: 2.2, turboAcc: 3, vmax: 14, turboVmax: 17, brake: 6.5, steer: 0.5, dmg: 0, gear: 1.7 };

export interface TransitTarget { kind: 'tram' | 'bus'; d: number; handle: VehicleHandle | null; bus: ParkedBus | null }
interface ParkedBus { car: DriveCar; key: string }

export class TransitUse {
  private parked: ParkedBus[] = [];
  private hud = document.getElementById('transithud');
  private hudKey = '';
  private hudT = 0;
  private busKey = '';
  private busLi = 0;

  constructor(private player: Player, private tiles: Tiles, private transit: Transit, private audio: Audio, private scene: THREE.Scene) {}

  /** Closest tram/bus (scheduled, or left standing by the player) in reach. */
  nearest(): TransitTarget | null {
    if (this.player.driving || this.player.riding) return null;
    const { x, y } = this.player;
    let best: TransitTarget | null = null;
    const h = this.transit.nearestVehicle(x, y, TRANSIT_REACH);
    if (h) best = { kind: h.tram ? 'tram' : 'bus', d: h.d, handle: h, bus: null };
    for (const b of this.parked) {
      let d = Math.hypot(b.car.x - x, b.car.y - y) - b.car.half.l - 1.3;
      for (const c of b.car.rig.tailCircles?.() ?? []) d = Math.min(d, Math.hypot(c.x - x, c.y - y) - 2.6);
      if (d < TRANSIT_REACH && (!best || d < best.d)) best = { kind: 'bus', d, handle: null, bus: b };
    }
    return best;
  }

  enter(t: TransitTarget) {
    if (t.bus) {
      this.parked.splice(this.parked.indexOf(t.bus), 1);
      this.busKey = t.bus.key; this.busLi = t.bus.car.rig.group.userData.li ?? 0;
      enterDrive(this.player, t.bus.car);
    } else if (t.handle && t.kind === 'tram') {
      const h = t.handle;
      this.transit.take(h);
      const car = new TramCar(this.transit, h.li, h.key, h.spec, h.sh, h.v);
      car.onImpact = (s) => this.audio.carCrash(Math.min(1, s / 14) * 0.6);
      enterDrive(this.player, car);
    } else if (t.handle) {
      const h = t.handle, p = [0, 0, 0, 0];
      this.transit.take(h);
      const rig = buildBusRig(this.transit, h.spec, h.li);
      rig.group.userData.li = h.li;
      this.transit.poseAt(h.li, h.sh - this.transit.moduleLength(this.transit.spec(h.spec)!.sequence[0].module) / 2, p);
      // the OSM line runs on the street axis: take the right-hand lane so oncoming traffic is not in the body
      const car = new DriveCar(this.tiles, rig, 'bus', new THREE.Color(0xffffff), p[0] + Math.cos(p[3]) * 1.6, p[1] - Math.sin(p[3]) * 1.6, p[3], h.v);
      car.tune = BUS_TUNE; car.cam = { dist: 13, h: 2.4 };
      car.onImpact = (s) => this.audio.carCrash(Math.min(1, s / 14) * 0.7);
      this.scene.add(rig.group);
      this.busKey = h.key; this.busLi = h.li;
      enterDrive(this.player, car);
    }
    document.body.classList.add('transit-drive');
    this.audio.carDoor();
  }

  /** Called when the player has come to a halt and gets out (right side, next to the doors). */
  exit() {
    const car = this.player.driving;
    if (!car) return;
    exitDrive(this.player, true);
    if (car instanceof TramCar) {
      const d = this.transit.driven;
      if (d) { d.active = false; d.doors = false; }
    } else this.parked.push({ car, key: this.busKey });
    document.body.classList.remove('transit-drive');
    if (this.hud) this.hud.style.display = 'none';
    this.hudKey = '';
    this.audio.carDoor();
    this.audio.engine(0, 0, 0, false);
  }

  isTransit(car: { isTram: boolean; type: string }) { return car.isTram || car.type === 'bus'; }

  /** Obstacles for the driven car/bus: buses left standing (body + trailer). */
  obstacles(): Obb[] {
    const out: Obb[] = [];
    for (const b of this.parked) {
      const c = b.car;
      out.push({ x: c.x, y: c.y, fx: Math.sin(c.h), fy: Math.cos(c.h), hl: c.half.l, hw: c.half.w });
      for (const t of c.rig.tailCircles?.() ?? []) out.push({ x: t.x, y: t.y, fx: 0, fy: 1, hl: 1.3, hw: 1.3 });
    }
    return out;
  }

  update(dt: number) {
    const car = this.player.driving;
    if (consumeBell() && car && this.isTransit(car)) { if (car.isTram) this.audio.tramBell(0.35); else this.audio.honk(); }
    for (let i = this.parked.length - 1; i >= 0; i--) {
      const b = this.parked[i];
      if (Math.hypot(b.car.x - this.player.x, b.car.y - this.player.y) < 300) continue;
      this.scene.remove(b.car.rig.group); b.car.rig.dispose();
      this.transit.release(b.key);
      this.parked.splice(i, 1);
    }
    if (!car || !this.hud || !this.isTransit(car)) return;
    this.hudT -= dt;
    if (this.hudT > 0) return;
    this.hudT = 0.1;
    const L = this.transit.line(car instanceof TramCar ? car.li : this.busLi), kmh = Math.round(Math.abs(car.speed) * 3.6);
    let sub = `${kmh} km/h`;
    if (car instanceof TramCar && car.stopName) {
      const d = Math.round(car.stopDist);
      sub = car.doorsOpen ? `Haltestelle ${car.stopName} · Türen offen` : `${d > 0 ? 'Nächste Haltestelle' : 'Letzte Haltestelle'} ${car.stopName} · ${Math.abs(d)} m · ${kmh} km/h`;
    }
    const key = `${L.ref}|${L.dest}|${sub}`;
    if (key === this.hudKey) return;
    this.hudKey = key;
    this.hud.innerHTML = `<b>${L.tram ? 'Tram' : 'Bus'} ${L.ref}</b>→ ${L.dest}<small>${sub}</small>`;
    this.hud.style.display = 'block';
  }
}
