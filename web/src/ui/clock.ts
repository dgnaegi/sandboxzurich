/** Game clock (time of day, weekday, speed, pause) plus the HUD panel that opens when the clock is clicked or tapped. */
import { WEEKDAYS } from '../world/events';

const KEY = 'sbz-clock';
const QUICK: [string, number][] = [['Morgen', 7 * 60], ['Mittag', 12 * 60], ['Abend', 19 * 60], ['Nacht', 23 * 60]];
const RATES = [1, 10, 60];

export class GameClock {
  /** Minutes since midnight (0..1440) and weekday (0 = Mo). */
  min: number;
  day: number;
  /** Game minutes per real second (1, 10 or 60). */
  rate = 1;
  paused = false;
  onChange: () => void = () => {};

  /** `fixed`: start values come from the URL, so a saved choice is ignored. */
  constructor(min: number, day: number, fixed = false) {
    this.min = min; this.day = day;
    if (fixed) return;
    try {
      const d = JSON.parse(localStorage.getItem(KEY) ?? 'null');
      if (d && isFinite(d.min) && RATES.includes(d.rate)) { this.min = d.min; this.day = d.day % 7; this.rate = d.rate; this.paused = !!d.paused; }
    } catch { /* private mode */ }
  }

  tick(dt: number) {
    if (this.paused) return;
    this.min += dt * this.rate;
    while (this.min >= 1440) { this.min -= 1440; this.day = (this.day + 1) % 7; }
  }

  /** User choice: set time (and optionally weekday), remembered across reloads. */
  set(min: number, day = this.day) { this.min = ((min % 1440) + 1440) % 1440; this.day = day; this.commit(); }
  setRate(r: number) { this.rate = r; this.commit(); }
  setPaused(p: boolean) { this.paused = p; this.commit(); }

  private commit() {
    try { localStorage.setItem(KEY, JSON.stringify({ min: this.min, day: this.day, rate: this.rate, paused: this.paused })); } catch { /* ignore */ }
    this.onChange();
  }

  time(): string { return `${String(Math.floor(this.min / 60)).padStart(2, '0')}:${String(Math.floor(this.min % 60)).padStart(2, '0')}`; }
  label(): string { return `${WEEKDAYS[this.day]} ${this.time()}`; }
}

/** Make `#clock` a button that opens the time panel. */
export function bindClockPanel(clk: GameClock) {
  const el = document.getElementById('clock')!;
  el.setAttribute('role', 'button'); el.setAttribute('tabindex', '0'); el.setAttribute('aria-label', 'Uhrzeit einstellen');
  const panel = document.createElement('div');
  panel.id = 'clockpanel';
  panel.innerHTML = `
    <div class="cp-head"><b>Uhrzeit</b><span id="cp-time"></span><button id="cp-close" aria-label="Schliessen">✕</button></div>
    <input id="cp-slider" type="range" min="0" max="1439" step="5" aria-label="Uhrzeit" />
    <div class="cp-ticks"><span>0</span><span>6</span><span>12</span><span>18</span><span>24</span></div>
    <div class="cp-row" id="cp-days">${WEEKDAYS.map((d, i) => `<button data-day="${i}">${d}</button>`).join('')}</div>
    <div class="cp-row" id="cp-quick">${QUICK.map(([n, m]) => `<button data-min="${m}">${n}<small>${m / 60}:00</small></button>`).join('')}</div>
    <div class="cp-row"><button id="cp-pause"></button></div>
    <div class="cp-row" id="cp-rates">${RATES.map((r) => `<button data-rate="${r}">${r}×</button>`).join('')}</div>`;
  document.body.appendChild(panel);
  const $ = <T extends HTMLElement>(s: string) => panel.querySelector(s) as T;
  const slider = $<HTMLInputElement>('#cp-slider'), time = $('#cp-time'), pause = $('#cp-pause');
  let open = false;
  const sync = () => {
    el.textContent = clk.label();
    if (!open) return;
    time.textContent = clk.label();
    if (document.activeElement !== slider) slider.value = String(Math.floor(clk.min));
    panel.querySelectorAll<HTMLElement>('[data-day]').forEach((b) => b.classList.toggle('on', Number(b.dataset.day) === clk.day));
    panel.querySelectorAll<HTMLElement>('[data-rate]').forEach((b) => b.classList.toggle('on', Number(b.dataset.rate) === clk.rate));
    pause.textContent = clk.paused ? '▶ Zeit läuft weiter' : '⏸ Zeit anhalten';
    pause.classList.toggle('on', clk.paused);
  };
  const toggle = (on: boolean) => {
    open = on; panel.style.display = on ? 'block' : 'none';
    if (on) document.exitPointerLock?.();
    sync();
  };
  clk.onChange = sync;
  el.addEventListener('click', () => toggle(!open));
  el.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(!open); } });
  $('#cp-close').addEventListener('click', () => toggle(false));
  slider.addEventListener('input', () => clk.set(Number(slider.value)));
  slider.addEventListener('change', () => slider.blur());
  panel.addEventListener('click', (e) => {
    const b = (e.target as HTMLElement).closest('button');
    if (!b) return;
    if (b.dataset.day) clk.set(clk.min, Number(b.dataset.day));
    else if (b.dataset.min) clk.set(Number(b.dataset.min));
    else if (b.dataset.rate) clk.setRate(Number(b.dataset.rate));
    else if (b.id === 'cp-pause') clk.setPaused(!clk.paused);
    b.blur();
  });
  document.addEventListener('pointerdown', (e) => { if (open && !panel.contains(e.target as Node) && !el.contains(e.target as Node)) toggle(false); }, true);
  window.addEventListener('keydown', (e) => { if (open && e.code === 'Escape') toggle(false); });
  sync();
}
