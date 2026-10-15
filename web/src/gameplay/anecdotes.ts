/** Local stories (research/easter_eggs_testarea.md → public/data/anecdotes.json) shown once when passing by. */
interface Anecdote { id: string; title: string; text: string; x: number; y: number; r: number; kind?: string }
const KEY = 'sbz-anecdotes';

export class Anecdotes {
  private list: Anecdote[] = [];
  private seen = new Set<string>();
  private cooldown = 0;
  onShow: (a: Anecdote, n: number, total: number) => void = () => {};

  async load(url = '/data/anecdotes.json') {
    this.list = ((await (await fetch(url)).json()) as { anecdotes: Anecdote[] }).anecdotes;
    try { this.seen = new Set(JSON.parse(localStorage.getItem(KEY) ?? '[]')); } catch { /* private mode */ }
  }

  update(dt: number, px: number, py: number) {
    this.cooldown -= dt;
    if (this.cooldown > 0) return;
    for (const a of this.list) {
      if (this.seen.has(a.id) || Math.hypot(a.x - px, a.y - py) > a.r) continue;
      this.seen.add(a.id);
      try { localStorage.setItem(KEY, JSON.stringify([...this.seen])); } catch { /* ignore */ }
      this.cooldown = a.kind === 'street' ? 45 : 25; // street names are many: show them more sparsely
      this.onShow(a, this.seen.size, this.list.length);
      return;
    }
  }
}
