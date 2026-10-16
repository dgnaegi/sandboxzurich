/**
 * Quiet background hip-hop (CC BY instrumentals, see research/music.md). Streams via HTMLAudioElement -> MediaElementSource
 * (no pre-decoding; iOS ignores element.volume, so all levels go through GainNodes). Starts only after the first gesture
 * (the Audio engine creates the context), shuffled playlist, two elements for cross-fades. Not part of the start download.
 */
const BASE = `${import.meta.env.BASE_URL}audio/music/`;
export const TRACKS = [
  'audionautix-hiphop-no-vocal', 'nfaom-boom-bap', 'luode-hiphop-b-minor', 'audionautix-pool', 'luode-hop-hip-beat',
];
const FADE = 4;     // seconds of cross-fade at track start/end
const LEVEL = 0.22; // full user volume = this gain (city ambience stays on top)

interface Slot { el: HTMLAudioElement; g: GainNode; fade: number }

export class Music {
  private slots: Slot[] = [];
  private cur = -1;
  private order: string[] = [];
  private duckT = 0;
  private duckV = 1;
  private night = 0;
  private started = false;
  enabled = true;
  volume = 0.5;

  constructor(private ctx: AudioContext, private out: AudioNode) {}

  private shuffle() {
    const a = TRACKS.slice();
    for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
    if (a[0] === this.order[this.order.length - 1]) a.push(a.shift()!);
    this.order = a;
  }

  private slot(i: number): Slot {
    if (!this.slots[i]) {
      const el = new window.Audio(); el.preload = 'none'; el.crossOrigin = 'anonymous';
      el.setAttribute('playsinline', '');
      const g = this.ctx.createGain(); g.gain.value = 0;
      this.ctx.createMediaElementSource(el).connect(g).connect(this.out);
      el.addEventListener('ended', () => { if (this.slots[this.cur]?.el === el) this.next(); });
      el.addEventListener('error', () => { if (this.slots[this.cur]?.el === el) setTimeout(() => this.next(), 3000); });
      this.slots[i] = { el, g, fade: 0 };
    }
    return this.slots[i];
  }

  private next() {
    if (!this.enabled) return;
    if (!this.order.length) this.shuffle();
    const name = this.order.shift()!;
    const prev = this.slots[this.cur];
    this.cur = (this.cur + 1) % 2;
    const s = this.slot(this.cur);
    s.el.src = `${BASE}${name}.m4a`; s.fade = 0;
    s.el.play().catch(() => { /* blocked or offline: try again on the next gesture / switch */ });
    if (prev) prev.fade = -1; // fades out, then pauses
  }

  /** Called on user gesture / when the switch turns on. */
  start() {
    this.started = true;
    if (this.enabled && !(this.slots[this.cur]?.el.currentTime > 0 && !this.slots[this.cur].el.paused)) {
      const s = this.slots[this.cur];
      if (s && s.el.src && !s.el.ended) s.el.play().catch(() => {}); else this.next();
    }
  }

  /** Switch/slider changes apply at once (the game loop is paused while the menu is open). */
  setEnabled(on: boolean) {
    this.enabled = on;
    if (on) { if (this.started) this.start(); return; }
    for (const s of this.slots) { s.g.gain.value = 0; s.el.pause(); }
  }
  setVolume(v: number) {
    this.volume = Math.min(1, Math.max(0, v));
    const s = this.slots[this.cur]; if (s && this.enabled) s.g.gain.value = this.level() * s.fade;
  }
  private level() { return this.enabled ? LEVEL * this.volume * this.volume * (1 - 0.3 * this.night) * this.duckV : 0; }
  /** Short duck under loud events (crash, siren). */
  duck(seconds = 2.5) { this.duckT = Math.max(this.duckT, seconds); }
  /** Test hook: current state. */
  get state() { const s = this.slots[this.cur]; return { paused: !s || s.el.paused, gain: s?.g.gain.value ?? 0, time: s?.el.currentTime ?? 0, src: s?.el.src ?? '' }; }

  update(dt: number, night: number, loud: boolean) {
    this.night += (night - this.night) * Math.min(1, dt * 0.2);
    this.duckT = Math.max(0, this.duckT - dt);
    const dTarget = this.duckT > 0 || loud ? 0.4 : 1;
    this.duckV += (dTarget - this.duckV) * Math.min(1, dt * 2);
    const level = this.level();
    for (let i = 0; i < this.slots.length; i++) {
      const s = this.slots[i], playing = i === this.cur;
      if (s.fade >= 0 && playing) s.fade = Math.min(1, s.fade + dt / FADE); else if (!playing) s.fade = Math.max(-1, s.fade - dt / FADE);
      const f = playing ? s.fade : Math.max(0, 1 + s.fade);
      s.g.gain.setTargetAtTime(level * f, this.ctx.currentTime, 0.15);
      if (!playing && f <= 0 && !s.el.paused) s.el.pause();
    }
    const c = this.slots[this.cur];
    if (this.enabled && c && c.el.duration > 0 && c.el.currentTime > c.el.duration - FADE && !c.el.paused) this.next();
  }
}
