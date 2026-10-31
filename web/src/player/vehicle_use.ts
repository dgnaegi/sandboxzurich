import * as THREE from 'three';
import type { Tiles } from '../engine/tiles';
import type { HumanLib, Human } from '../world/humans';
import type { Traffic } from '../world/traffic';
import { parkedCars, carLength, type CarSlot } from '../world/parkedcars';
import { buildRig, initCarEnvironment, preloadModel } from './vehicle_model';
import { DriveCar, type Obb, type Crash } from './drive';
import { CrashFx, bubble } from './crash_fx';
import { Wreck } from './crash_wreck';
import { enterDrive, exitDrive } from './vehicle_player';
import { StuckGuard, freeSpotFor } from './stuck';
import { actions } from '../input/actions';
import type { Player } from './player';
import type { Audio } from '../engine/audio';

/**
 * Taking and leaving cars: nearest parked car or car in traffic within reach, E to get in. The driver of a
 * moving car just gets out and walks off (no violence). Wiring for the later wanted stars: `onTheft`.
 * Also runs the stuck guard (player/stuck.ts) for the driven car.
 */
type Target = { kind: 'parked'; d: number; slot: CarSlot } | { kind: 'traffic'; d: number; type: string };

export const REACH = 3.2;
const touch = () => document.body.classList.contains('touch');

export class CarUse {
  /** Hook for the wanted system (not active in the map phase): called with 'parked' or 'traffic' on every theft. */
  onHint: ((text: string) => void) | null = null;
  onTheft: ((kind: 'parked' | 'traffic') => void) | null = null;
  /** Set by TransitUse: leaving a tram/bus is handled there. */
  transitExit: (() => void) | null = null;
  /** Set by main.ts: the bike or scooter the player was still on when the car became ready is left standing here. */
  onDismount: ((left: { x: number; y: number; z: number; h: number; color: THREE.Color; type: string }) => void) | null = null;
  /** Set by main.ts: legal ground for a car at (x, y) (fence, buildings, rails, water, landmarks); the stuck failsafe uses it. */
  legal: ((x: number, y: number) => boolean) | null = null;
  /** How often the stuck failsafe has moved the car (tests, stats). */
  rescues = 0;
  private busy = false;
  private guard = new StuckGuard();
  /** Drive model still downloading after E (the prompt says so). */
  get loading() { return this.busy; }
  private leavers: { h: Human; t: number; dx: number; dy: number; x: number; y: number; b?: THREE.Sprite }[] = [];
  /** Crashed cars standing around (shoved NPC/parked cars, abandoned wrecks); removed once far away. */
  wrecks: Wreck[] = [];
  private fx: CrashFx;
  private lampsOut = false;
  private hpEl = document.getElementById('carhp');
  private scene: THREE.Scene;

  constructor(private player: Player, private tiles: Tiles, private traffic: Traffic, private humans: HumanLib,
    private audio: Audio, renderer: THREE.WebGLRenderer, scene: THREE.Scene, obstacles: () => Obb[], night: () => number) {
    this.scene = scene;
    this.fx = new CrashFx(scene);
    initCarEnvironment(renderer);
    parkedCars.init(scene);
    player.drive.hooks = {
      obstacles: () => [...obstacles(), ...this.wrecks.map((w) => w.obb())],
      night,
      parked: (x, y, r) => parkedCars.near(x, y, r).map((s) => ({ x: s.x, y: s.y, fx: Math.sin(s.h), fy: Math.cos(s.h), hl: carLength(s.type) / 2, hw: 0.9, ref: s })),
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
    const pick: Target | null = t && (!slot || t.d < sd - 1) ? { kind: 'traffic', d: t.d, type: t.type } : slot ? { kind: 'parked', d: sd, slot } : null;
    if (pick) void preloadModel(pick.kind === 'parked' ? pick.slot.type : pick.type);   // warm the cache while the prompt shows, so E is instant on most connections
    return pick;
  }

  /**
   * E on a car. The drive model may still have to come over the network (seconds on a slow connection), so the
   * order is: wait for the model, then take the car and sit down in one go. Until then the car stays where it is
   * and the player keeps walking; if they moved out of reach, got into a tram or bus, or the car drove off, nothing
   * happens. (Before, the car vanished at once and the player was teleported back onto it when the download
   * finished; a scooter mounted in between stayed glued to the figure.)
   */
  async enter(t: Target) {
    if (this.busy || this.player.driving) return;
    this.busy = true;
    try {
      const p = this.player;
      let type = t.kind === 'parked' ? t.slot.type : t.type;
      for (let round = 0; round < 3; round++) {
        await preloadModel(type);   // the only real wait
        if (p.driving) return;
        const far = (x: number, y: number) => Math.hypot(x - p.x, y - p.y) > REACH + 1.2;
        let color: THREE.Color, x: number, y: number, h: number, v = 0;
        if (t.kind === 'parked') {
          const s = t.slot;
          if (s.taken || far(s.x, s.y)) return;   // walked away, or the car was shoved meanwhile
          ({ color, x, y, h } = s);
          parkedCars.take(s);
        } else {
          const c = this.traffic.findCar(p.x, p.y, REACH + 1.2);
          if (!c) return;   // drove off
          if (c.type !== type) { type = c.type; continue; }   // another car is the nearest now: its model first
          this.traffic.findCar(p.x, p.y, REACH + 1.2, true);
          ({ color, x, y, h, v } = c);
          this.spawnLeaver(x, y, h);
        }
        // from here on no frame passes: the model is cached, buildRig only awaits a resolved promise
        const rig = await buildRig(type, color);
        this.scene.add(rig.group);
        const car = new DriveCar(this.tiles, rig, type, color, x, y, h, v);
        car.onImpact = (s) => { this.guard.impact(); this.audio.carCrash(Math.min(1, s / 14), car.dead); };
        car.onCrash = (c) => this.crashed(car, c);
        this.lampsOut = false;
        if (p.riding) { const left = p.dismount(); if (left) this.onDismount?.(left); }   // got onto a bike/scooter while the model loaded: leave it standing here
        this.guard.reset();
        enterDrive(p, car);
        this.audio.carDoor();
        this.onTheft?.(t.kind);
        // parked in a row: the next car is right in front -> tell about reverse gear
        if (t.kind === 'parked' && parkedCars.near(x + Math.sin(h) * 3.6, y + Math.cos(h) * 3.6, 1.3).some((c) => c !== t.slot)) this.onHint?.(touch() ? 'Vorne blockiert: Stick nach unten = rückwärts' : 'Vorne blockiert: S / ↓ = rückwärts');
        return;
      }
    } finally { this.busy = false; }
  }

  /** Stuck failsafe (player/stuck.ts): set the car down on the nearest free legal spot, facing away from the trap. */
  private rescue(car: DriveCar) {
    const spot = freeSpotFor(car, this.tiles, (x, y) => this.legal?.(x, y) ?? this.tiles.inPlay(x, y));
    if (!spot) { this.onHint?.(touch() ? 'Festgefahren: E = aussteigen' : 'Festgefahren: E zum Aussteigen'); return; }
    car.place(spot.x, spot.y, spot.h);
    this.player.yaw = spot.h;
    this.rescues++;
    this.onHint?.('Freigestellt.');
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
    if (car.isTram || car.type === 'bus') { this.transitExit?.(); return; }
    const left = exitDrive(this.player);
    if (left && car.damage > 0.08) { // damaged cars stay as they are (dents, smoke) instead of becoming a fresh parked car
      this.addWreck(new Wreck(this.tiles, car.rig, car.type, car.color, car.x, car.y, car.h, car.damage));
    } else {
      this.scene.remove(car.rig.group);
      car.rig.dispose();
      if (left) parkedCars.drop(car.type, car.color, left.x, left.y, left.z, left.h);
    }
    if (this.hpEl) this.hpEl.style.display = 'none';
    this.audio.carDoor();
    this.audio.engine(0, 0, 0, false);
  }

  private addWreck(w: Wreck) {
    this.wrecks.push(w);
    while (this.wrecks.length > 10) this.dropWreck(this.wrecks[0]);
  }

  private dropWreck(w: Wreck) {
    this.scene.remove(w.rig.group); w.rig.dispose(); this.fx.forget(w);
    this.wrecks.splice(this.wrecks.indexOf(w), 1);
  }

  /** The driven car hit something: dent, sparks, glass/lamps, and shove whatever we hit (cars only). */
  private crashed(car: DriveCar, c: Crash) {
    const fx = Math.sin(car.h), fy = Math.cos(car.h), rx = fy, ry = -fx;
    const dx = c.px - car.x, dy = c.py - car.y, s = Math.min(1, c.strength / 14);
    const ox = c.nx, oy = c.ny; // out of the obstacle, into us: the body is pushed this way
    if (c.damage > 0) car.rig.dent(dx * rx + dy * ry, -(dx * fx + dy * fy), ox * rx + oy * ry, -(ox * fx + oy * fy), 0.05 + 0.2 * s);
    if (-(dx * fx + dy * fy) < -car.half.l * 0.3 && c.strength > 9) this.lampsOut = true; // hard front hit breaks the head lamps
    car.rig.setDamage(car.damage, this.lampsOut || car.damage > 0.5);
    const gz = car.z + 0.6;
    this.fx.sparks(c.px, gz, -c.py, Math.round(2 + 10 * s), -ox, oy);
    if (c.strength > 12) this.audio.glass();
    // whatever we hit is pushed away and turns; its driver gets out and grumbles
    const o = c.obb;
    if (!o || c.strength < 3.5) return;
    const ix = -ox * c.strength * 0.85 + car.vx * 0.25, iy = -oy * c.strength * 0.85 + car.vy * 0.25;
    if (o.ref instanceof Wreck) { o.ref.shove(ix, iy, c.px, c.py); return; }
    if (o.id !== undefined) {
      const t = this.traffic.findCar(c.px, c.py, 1.4, true);
      if (t) { this.spawnLeaver(t.x, t.y, t.h, true); void this.spawnWreck(t.type, t.color, t.x, t.y, t.h, ix + Math.sin(t.h) * t.v * 0.5, iy + Math.cos(t.h) * t.v * 0.5, c); }
    } else if (o.ref && typeof o.ref === 'object' && 'mesh' in (o.ref as object)) {
      const slot = o.ref as CarSlot;
      if (slot.taken) return;
      parkedCars.take(slot);
      void this.spawnWreck(slot.type, slot.color, slot.x, slot.y, slot.h, ix, iy, c);
    }
  }

  private async spawnWreck(type: string, color: THREE.Color, x: number, y: number, h: number, ix: number, iy: number, c: Crash) {
    const rig = await buildRig(type, color);
    this.scene.add(rig.group);
    const w = new Wreck(this.tiles, rig, type, color, x, y, h, 0.15);
    w.shove(ix, iy, c.px, c.py);
    rig.setDamage(w.damage, false);
    // dent where it was hit, in its own frame
    const fx = Math.sin(h), fy = Math.cos(h), dx = c.px - x, dy = c.py - y;
    rig.dent(dx * fy - dy * fx, -(dx * fx + dy * fy), -c.nx * fy + c.ny * fx, (c.nx * fx + c.ny * fy), 0.18);
    this.addWreck(w);
  }

  get driving() { return !!this.player.driving; }

  /** The driver who got out walks away from the road for a few seconds, then disappears. */
  private spawnLeaver(x: number, y: number, h: number, angry = false) {
    const npcs = this.humans.npcs.filter((m) => m.age !== 'child');
    if (!npcs.length) return;
    const hum = this.humans.instance(npcs[Math.floor(Math.random() * npcs.length)]);
    const rx = Math.cos(h), ry = -Math.sin(h), px = x + rx * 1.4, py = y + ry * 1.4; // kerb-side door (right), walks off to the pavement
    hum.root.position.set(px, this.tiles.ground(px, py), -py);
    hum.root.rotation.y = -Math.atan2(rx, ry);
    hum.setSpeed(1.5);
    hum.root.traverse((o) => { o.frustumCulled = false; });
    this.scene.add(hum.root);
    let b: THREE.Sprite | undefined;
    if (angry) { b = bubble(['Spinnst du?!', 'Pass doch auf!', 'Mein Auto!', 'Sag mal, geht\'s noch?'][Math.floor(Math.random() * 4)]); hum.root.add(b); }
    this.leavers.push({ h: hum, t: 0, dx: rx, dy: ry, x: px, y: py, b });
  }

  update(dt: number) {
    for (const l of this.leavers) {
      l.t += dt;
      if (l.b && l.t > 5) { l.h.root.remove(l.b); l.b.material.map?.dispose(); l.b.material.dispose(); l.b = undefined; }
      if (l.t < (l.b ? 2.5 : 0.8)) { l.h.setSpeed(0); } else {
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
    if (car) this.audio.engine(car.rpm, Math.max(0, car.throttle), Math.abs(car.slip) + (car.braking ? Math.abs(car.speed) * 0.06 : 0), !car.dead, car.speed);
    // stuck guard: throttle held, no progress, in contact -> hint, then set the car free (trams run on rails, dead cars say "aussteigen" already)
    if (car && !car.isTram && !car.dead) {
      const r = this.guard.update(dt, car, Math.abs(actions.kb.y || actions.move.y) > 0.3);
      if (r === 'warn') this.onHint?.(touch() ? 'Festgefahren? Stick nach unten = rückwärts. Sonst stellen wir dich gleich frei.' : 'Festgefahren? S / ↓ = rückwärts. Sonst stellen wir dich gleich frei.');
      else if (r === 'rescue') this.rescue(car);
    } else this.guard.reset();
    // smoke from the bonnet: light from ~50 %, heavy from ~85 %
    if (car && car.rig && car.type !== 'bus') {
      const lvl = car.damage < 0.5 ? 0 : car.damage < 0.85 ? 0.4 : 1, hz = -car.rig.hood.z, f = Math.sin(car.h), g = Math.cos(car.h);
      this.fx.smoke(car, car.x + f * hz, car.z + car.rig.hood.y, -(car.y + g * hz), lvl, dt);
      if (this.hpEl) {
        this.hpEl.style.display = 'flex';
        const hp = 1 - car.damage, bar = this.hpEl.querySelector('i') as HTMLElement;
        bar.style.width = `${Math.round(hp * 100)}%`; bar.style.background = hp > 0.5 ? '#4caf50' : hp > 0.25 ? '#f5c518' : '#e53935';
      }
    }
    for (let i = this.wrecks.length - 1; i >= 0; i--) {
      const w = this.wrecks[i];
      w.update(dt, this.fx);
      if (!w.moving && Math.hypot(w.x - this.player.x, w.y - this.player.y) > 160) this.dropWreck(w);
    }
    this.fx.update(dt);
  }
}
