// Sunumdaki "temel görüntü işleme" sahneleri için küçük JavaScript benzetimleri.
// Eğitimde aynı işlemler OpenCV (Python) ile yapılır; buradaki kod yalnızca gösterim içindir.

export function toGray(img: ImageData): Float32Array {
  const n = img.width * img.height, out = new Float32Array(n), d = img.data;
  for (let i = 0; i < n; i++) out[i] = 0.299 * d[i * 4] + 0.587 * d[i * 4 + 1] + 0.114 * d[i * 4 + 2];
  return out;
}

export function gaussianBlur(src: Float32Array, w: number, h: number, sigma: number): Float32Array {
  if (sigma <= 0) return src.slice();
  const r = Math.max(1, Math.ceil(sigma * 3));
  const k = new Float32Array(2 * r + 1);
  let sum = 0;
  for (let i = -r; i <= r; i++) { k[i + r] = Math.exp(-(i * i) / (2 * sigma * sigma)); sum += k[i + r]; }
  for (let i = 0; i < k.length; i++) k[i] /= sum;
  const tmp = new Float32Array(w * h), out = new Float32Array(w * h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    let acc = 0;
    for (let i = -r; i <= r; i++) acc += src[y * w + Math.min(w - 1, Math.max(0, x + i))] * k[i + r];
    tmp[y * w + x] = acc;
  }
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    let acc = 0;
    for (let i = -r; i <= r; i++) acc += tmp[Math.min(h - 1, Math.max(0, y + i)) * w + x] * k[i + r];
    out[y * w + x] = acc;
  }
  return out;
}

/** Otsu (1979): sınıflar arası varyansı en büyük yapan eşik. */
export function otsu(gray: Float32Array): number {
  const hist = new Array(256).fill(0);
  for (const v of gray) hist[Math.min(255, Math.max(0, Math.round(v)))]++;
  const total = gray.length;
  let sumAll = 0;
  for (let i = 0; i < 256; i++) sumAll += i * hist[i];
  let wB = 0, sumB = 0, best = 0, thr = 0;
  for (let t = 0; t < 256; t++) {
    wB += hist[t];
    if (!wB) continue;
    const wF = total - wB;
    if (!wF) break;
    sumB += t * hist[t];
    const mB = sumB / wB, mF = (sumAll - sumB) / wF;
    const between = wB * wF * (mB - mF) ** 2;
    if (between > best) { best = between; thr = t; }
  }
  return thr;
}

export const threshold = (g: Float32Array, t: number) => Uint8Array.from(g, (v) => (v > t ? 1 : 0));

function morph(src: Uint8Array, w: number, h: number, r: number, erode: boolean): Uint8Array {
  if (r <= 0) return src.slice();
  const out = new Uint8Array(w * h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    let v = erode ? 1 : 0;
    for (let dy = -r; dy <= r && (erode ? v === 1 : v === 0); dy++) for (let dx = -r; dx <= r; dx++) {
      if (dx * dx + dy * dy > r * r) continue;                 // elips (daire) çekirdek
      const xx = x + dx, yy = y + dy;
      const s = xx < 0 || yy < 0 || xx >= w || yy >= h ? 0 : src[yy * w + xx];
      if (erode && !s) { v = 0; break; }
      if (!erode && s) { v = 1; break; }
    }
    out[y * w + x] = v;
  }
  return out;
}
export const opening = (b: Uint8Array, w: number, h: number, r: number) => morph(morph(b, w, h, r, true), w, h, r, false);
export const closing = (b: Uint8Array, w: number, h: number, r: number) => morph(morph(b, w, h, r, false), w, h, r, true);

/** Bağlı bileşenler: beyaz bölgeleri sayar ve sınır piksellerini işaretler (kontur benzetimi). */
export function components(b: Uint8Array, w: number, h: number, minArea: number) {
  const labels = new Int32Array(w * h);
  let count = 0;
  const border = new Uint8Array(w * h);
  const stack: number[] = [];
  for (let i = 0; i < w * h; i++) {
    if (!b[i] || labels[i]) continue;
    const pixels: number[] = [];
    stack.push(i); labels[i] = -1;
    while (stack.length) {
      const p = stack.pop()!;
      pixels.push(p);
      const x = p % w, y = (p / w) | 0;
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const xx = x + dx, yy = y + dy;
        if (xx < 0 || yy < 0 || xx >= w || yy >= h) continue;
        const q = yy * w + xx;
        if (b[q] && !labels[q]) { labels[q] = -1; stack.push(q); }
      }
    }
    if (pixels.length < minArea) continue;
    count++;
    for (const p of pixels) {
      const x = p % w, y = (p / w) | 0;
      if (x === 0 || y === 0 || x === w - 1 || y === h - 1 || !b[p - 1] || !b[p + 1] || !b[p - w] || !b[p + w]) border[p] = 1;
    }
  }
  return { count, border };
}

/** Göreli netlik: Laplace varyansı / gri ton varyansı x 1000 (Python: skin/quality.py). */
export function sharpness(gray: Float32Array, w: number, h: number): number {
  let m = 0;
  for (const v of gray) m += v;
  m /= gray.length;
  let gv = 0;
  for (const v of gray) gv += (v - m) ** 2;
  gv /= gray.length;
  if (gv < 1e-6) return 0;
  const lap: number[] = [];
  for (let y = 1; y < h - 1; y++) for (let x = 1; x < w - 1; x++) {
    const i = y * w + x;
    lap.push(gray[i - 1] + gray[i + 1] + gray[i - w] + gray[i + w] - 4 * gray[i]);
  }
  let lm = 0;
  for (const v of lap) lm += v;
  lm /= lap.length;
  let lv = 0;
  for (const v of lap) lv += (v - lm) ** 2;
  lv /= lap.length;
  return (1000 * lv) / gv;
}

export function median(values: ArrayLike<number>): number {
  const arr = Array.from(values).sort((a, b) => a - b);
  if (!arr.length) return 0;
  const mid = arr.length >> 1;
  return arr.length % 2 ? arr[mid] : (arr[mid - 1] + arr[mid]) / 2;
}
