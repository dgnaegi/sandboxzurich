import * as THREE from 'three';

/**
 * Small mission system: a yellow beacon starts a mission; objectives are checkpoints (pink beacon) with an
 * optional time limit. Mission texts are placeholders until the campaign content arrives (TODO-PROGRAMM).
 */
export interface MissionDef { id: string; title: string; start: [number, number]; intro: string; points: [number, number][];
  limit?: number; reward: number; done: string; needsBike?: boolean }

export const MISSIONS: MissionDef[] = [
  { id: 'kurier', title: 'Velokurier', start: [770, -893], intro: 'Ein Labor wartet auf Proben. Bring das Paket ins Kasernenareal – mit dem Velo schaffst du es!',
    points: [[1108, -832]], limit: 110, reward: 120, done: 'Pünktlich geliefert. Velowege sind schneller als jedes Auto.', needsBike: true },
  { id: 'flyer', title: 'Flyer verteilen', start: [800, -560], intro: 'Verteile Flyer entlang der Langstrasse. (TODO-PROGRAMM)',
    points: [[828, -500], [855, -450], [770, -700], [745, -760]], limit: 180, reward: 60, done: 'Alle Flyer verteilt. Radikal sozial!' },
  { id: 'besichtigung', title: 'Wohnungsbesichtigung', start: [760, -700], intro: 'Besichtigung um 17:00 an der Langstrasse. Sei früh dort!',
    points: [[789, -641]], limit: 45, reward: 0, done: 'Du bist Nummer 147 in der Schlange. Die Wohnung ist schon weg.' },
];

const beaconGeo = new THREE.CylinderGeometry(1.1, 1.1, 30, 20, 1, true).translate(0, 15, 0);
const ringGeo = new THREE.RingGeometry(0.9, 1.25, 32).rotateX(-Math.PI / 2);
const mat = (c: number) => new THREE.MeshBasicMaterial({ color: c, transparent: true, opacity: 0.35, depthWrite: false, side: THREE.DoubleSide, fog: false });

export interface Blip { x: number; y: number; color: string }

export class Missions {
  readonly group = new THREE.Group();
  active: MissionDef | null = null;
  private step = 0;
  private timeLeft = 0;
  private startBeacons = new Map<string, THREE.Object3D>();
  private target = this.beacon(0xff3fa0);
  onText: (title: string, text: string, kind: 'start' | 'pass' | 'fail') => void = () => {};
  onReward: (chf: number, id: string) => void = () => {};

  constructor(private done: Set<string>, private ground: (x: number, y: number) => number) {
    for (const m of MISSIONS) {
      const b = this.beacon(0xf5c518);
      b.position.set(m.start[0], ground(m.start[0], m.start[1]), -m.start[1]);
      this.startBeacons.set(m.id, b);
      this.group.add(b);
    }
    this.target.visible = false;
    this.group.add(this.target);
  }

  private beacon(color: number) {
    const g = new THREE.Group();
    g.add(new THREE.Mesh(beaconGeo, mat(color)), new THREE.Mesh(ringGeo, mat(color)));
    return g;
  }

  blips(): Blip[] {
    if (this.active) { const [x, y] = this.active.points[this.step]; return [{ x, y, color: '#ff3fa0' }]; }
    return MISSIONS.map((m) => ({ x: m.start[0], y: m.start[1], color: this.done.has(m.id) ? '#9a9a9a' : '#f5c518' }));
  }

  hud(): string {
    if (!this.active) return '';
    const t = this.active.limit ? ` · ${Math.max(0, Math.ceil(this.timeLeft))} s` : '';
    return `${this.active.title}: ${this.step + 1}/${this.active.points.length}${t}`;
  }

  update(dt: number, px: number, py: number, onBike: boolean) {
    const now = performance.now() / 1000;
    for (const b of this.startBeacons.values()) b.visible = !this.active;
    this.group.children.forEach((o) => { o.rotation.y = now; });
    if (!this.active) {
      for (const m of MISSIONS) {
        if (Math.hypot(m.start[0] - px, m.start[1] - py) < 1.6) { this.begin(m); break; }
      }
      return;
    }
    const m = this.active;
    if (m.limit) {
      this.timeLeft -= dt;
      if (this.timeLeft <= 0) { this.onText('MISSION GESCHEITERT', 'Zu spät. Versuch es nochmals.', 'fail'); this.end(); return; }
    }
    const [tx, ty] = m.points[this.step];
    if (Math.hypot(tx - px, ty - py) < 2.2) {
      this.step++;
      if (this.step >= m.points.length) {
        this.done.add(m.id);
        this.onReward(m.reward, m.id);
        this.onText('MISSION ERFÜLLT', `${m.done}${m.reward ? `  +CHF ${m.reward}` : ''}`, 'pass');
        this.end();
        return;
      }
      this.placeTarget();
    }
    if (m.needsBike && !onBike && this.step === 0 && this.timeLeft < (m.limit ?? 0) - 8) { /* hint only once handled by intro */ }
  }

  private begin(m: MissionDef) {
    this.active = m; this.step = 0; this.timeLeft = m.limit ?? 0;
    this.onText(m.title.toUpperCase(), m.intro, 'start');
    this.placeTarget();
  }

  private placeTarget() {
    const [x, y] = this.active!.points[this.step];
    this.target.position.set(x, this.ground(x, y), -y);
    this.target.visible = true;
  }

  end() { this.active = null; this.target.visible = false; }
}
