/** Pause menu (Esc / P / ☰): continue, map, quality, credits, imprint. */
export class Menu {
  open = false;
  private el = document.getElementById('menu')!;
  onMap: () => void = () => {};
  onQuality: (q: 'auto' | 'niedrig' | 'hoch') => void = () => {};
  onMute: (m: boolean) => void = () => {};
  private muted = false;
  private q: 'auto' | 'niedrig' | 'hoch' = 'auto';

  constructor() {
    const $ = (id: string) => document.getElementById(id)!;
    $('btn-menu').addEventListener('click', () => this.toggle(true));
    $('m-continue').addEventListener('click', () => this.toggle(false));
    $('m-map').addEventListener('click', () => { this.toggle(false); this.onMap(); });
    $('m-quality').addEventListener('click', () => {
      this.q = this.q === 'auto' ? 'niedrig' : this.q === 'niedrig' ? 'hoch' : 'auto';
      $('m-quality').textContent = `Grafik: ${this.q}`;
      this.onQuality(this.q);
    });
    $('m-sound').addEventListener('click', () => { this.muted = !this.muted; $('m-sound').textContent = `Ton: ${this.muted ? 'aus' : 'an'}`; this.onMute(this.muted); });
    for (const id of ['m-credits', 'm-imprint']) $(id).addEventListener('click', () => this.page(id === 'm-credits' ? 'credits' : 'imprint'));
    for (const b of document.querySelectorAll('.m-back')) b.addEventListener('click', () => this.page('main'));
    window.addEventListener('keydown', (e) => {
      if (e.code === 'KeyP' || (e.code === 'Escape' && !document.getElementById('bigmap')!.style.display.includes('block'))) this.toggle(!this.open);
    });
  }

  toggle(on: boolean) {
    this.open = on;
    this.el.style.display = on ? 'grid' : 'none';
    this.page('main');
    if (on) document.exitPointerLock?.();
  }

  private page(name: string) {
    for (const p of this.el.querySelectorAll<HTMLElement>('.m-page')) p.style.display = p.dataset.page === name ? 'block' : 'none';
  }
}
