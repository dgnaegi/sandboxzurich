import type * as THREE from 'three';

/**
 * Automatic quality governor: measures the frame rate and steps quality down when it drops below the target
 * (30 fps phones, 55 fps PC), and slowly back up when there is headroom. Order of steps: AO off (PC),
 * pixel ratio, detail radius, pedestrian count.
 */
export class Quality {
  pixelRatio: number;
  detailRadius: number;
  peds: number;
  post: boolean;
  private acc = 0;
  private frames = 0;
  private good = 0;
  level = 0;

  constructor(private renderer: THREE.WebGLRenderer, private mobile: boolean, hasPost: boolean) {
    this.pixelRatio = renderer.getPixelRatio();
    this.detailRadius = mobile ? 260 : 380;
    this.peds = mobile ? 16 : 36;
    this.post = hasPost;
  }

  private forced: string = 'auto';

  /** Menu override: 'niedrig' = phone-like settings, 'hoch' = full detail, 'auto' = governor. */
  force(q: 'auto' | 'niedrig' | 'hoch') {
    this.forced = q;
    if (q === 'niedrig') { this.post = false; this.pixelRatio = 0.85; this.detailRadius = 200; this.peds = 10; }
    if (q === 'hoch') { this.pixelRatio = Math.min(devicePixelRatio, 2); this.detailRadius = 380; this.peds = 36; }
    this.renderer.setPixelRatio(this.pixelRatio);
  }

  /** Call once per frame with the real (unclamped) frame time. */
  tick(dt: number) {
    if (this.forced !== 'auto') return;
    this.acc += dt; this.frames++;
    if (this.acc < 2) return;
    const fps = this.frames / this.acc;
    this.acc = 0; this.frames = 0;
    const target = this.mobile ? 30 : 55;
    if (fps < target - 3) { this.down(); this.good = 0; }
    else if (fps > target + 8 && this.level > 0 && ++this.good >= 5) { this.up(); this.good = 0; }
  }

  private down() {
    if (this.post) this.post = false;
    else if (this.pixelRatio > 0.75) this.pixelRatio = Math.max(0.75, this.pixelRatio - 0.25);
    else if (this.detailRadius > 180) this.detailRadius -= 40;
    else if (this.peds > 6) this.peds -= 4;
    else return;
    this.level++;
    this.renderer.setPixelRatio(this.pixelRatio);
  }

  private up() {
    if (this.peds < (this.mobile ? 16 : 36)) this.peds += 4;
    else if (this.detailRadius < (this.mobile ? 260 : 380)) this.detailRadius += 40;
    else if (this.pixelRatio < (this.mobile ? 1.25 : Math.min(devicePixelRatio, 2))) this.pixelRatio += 0.25;
    this.level--;
    this.renderer.setPixelRatio(this.pixelRatio);
  }
}
