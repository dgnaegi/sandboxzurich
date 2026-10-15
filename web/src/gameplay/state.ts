/** Persistent player state (money, wanted level, finished missions) in localStorage, plus HUD binding. */
export interface SaveData { money: number; missions: string[]; x?: number; y?: number }

const KEY = 'gtz-save';

export class GameState {
  money = 312.4;
  stars = 0;
  missions = new Set<string>();
  private starTimer = 0;
  onChange: () => void = () => {};

  load(): SaveData | null {
    try {
      const d = JSON.parse(localStorage.getItem(KEY) ?? 'null') as SaveData | null;
      if (d) { this.money = d.money; this.missions = new Set(d.missions); }
      return d;
    } catch { return null; }
  }

  save(x: number, y: number) {
    try { localStorage.setItem(KEY, JSON.stringify({ money: this.money, missions: [...this.missions], x, y })); } catch { /* private mode */ }
  }

  addMoney(v: number) { this.money = Math.max(0, Math.round((this.money + v) * 100) / 100); this.onChange(); }

  wanted(n: number) {
    this.stars = Math.max(0, Math.min(5, n));
    this.starTimer = 0;
    this.onChange();
  }

  /** Stars fade one by one when no police officer is close for a while. */
  tick(dt: number, policeNear: boolean) {
    if (this.stars === 0) return;
    this.starTimer = policeNear ? 0 : this.starTimer + dt;
    if (this.starTimer > 20) { this.stars--; this.starTimer = 0; this.onChange(); }
  }
}

/** Bind the top-right HUD to the state. */
export function bindHud(st: GameState) {
  const money = document.getElementById('money')!, stars = document.querySelectorAll('#stars i');
  st.onChange = () => {
    money.textContent = `CHF ${st.money.toLocaleString('de-CH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    stars.forEach((e, i) => e.classList.toggle('on', i < st.stars));
    document.body.classList.toggle('wanted', st.stars > 0);
  };
  st.onChange();
}
