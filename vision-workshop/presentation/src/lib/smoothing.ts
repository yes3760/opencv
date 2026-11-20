import type { Pt } from "./geometry";

/** Üstel hareketli ortalama: yeni = alpha * ölçüm + (1 - alpha) * eski */
export class EMA {
  value: Pt | null = null;
  constructor(public alpha: number) {}
  update(m: Pt): Pt {
    this.value = this.value === null ? { ...m } : {
      x: this.alpha * m.x + (1 - this.alpha) * this.value.x,
      y: this.alpha * m.y + (1 - this.alpha) * this.value.y,
    };
    return this.value;
  }
  reset() { this.value = null; }
}

/** Hıza göre kendini ayarlayan filtre (Casiez vd., CHI 2012). */
export class OneEuro {
  private x: Pt | null = null;
  private dx: Pt = { x: 0, y: 0 };
  private t = 0;
  constructor(public minCutoff = 1.0, public beta = 0.02, public dCutoff = 1.0) {}
  private alpha(cutoff: number, dt: number) {
    const tau = 1 / (2 * Math.PI * cutoff);
    return 1 / (1 + tau / dt);
  }
  update(m: Pt, tSec: number): Pt {
    if (this.x === null) { this.x = { ...m }; this.t = tSec; return this.x; }
    const dt = Math.max(tSec - this.t, 1e-3);
    const ad = this.alpha(this.dCutoff, dt);
    this.dx = { x: ad * (m.x - this.x.x) / dt + (1 - ad) * this.dx.x, y: ad * (m.y - this.x.y) / dt + (1 - ad) * this.dx.y };
    const cutoff = this.minCutoff + this.beta * Math.hypot(this.dx.x, this.dx.y);
    const a = this.alpha(cutoff, dt);
    this.x = { x: a * m.x + (1 - a) * this.x.x, y: a * m.y + (1 - a) * this.x.y };
    this.t = tSec;
    return this.x;
  }
  reset() { this.x = null; }
}
