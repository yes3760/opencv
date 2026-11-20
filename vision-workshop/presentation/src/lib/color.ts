// sRGB -> CIELAB (D65) dönüşümü. OpenCV'nin COLOR_BGR2LAB dönüşümüyle aynı formüller;
// burada değerler gerçek ölçekte döner: L* 0-100, a* ve b* yaklaşık -128..127.
const LIN = new Float32Array(256);
for (let i = 0; i < 256; i++) {
  const c = i / 255;
  LIN[i] = c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}
const f = (t: number) => (t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116);

export function rgbToLab(r: number, g: number, b: number): [number, number, number] {
  const R = LIN[r], G = LIN[g], B = LIN[b];
  const X = (0.412453 * R + 0.35758 * G + 0.180423 * B) / 0.950456;
  const Y = 0.212671 * R + 0.71516 * G + 0.072169 * B;
  const Z = (0.019334 * R + 0.119193 * G + 0.950227 * B) / 1.088754;
  const fy = f(Y);
  const L = Y > 0.008856 ? 116 * fy - 16 : 903.3 * Y;
  return [L, 500 * (f(X) - fy), 200 * (fy - f(Z))];
}

export type LabImage = { L: Float32Array; a: Float32Array; b: Float32Array; w: number; h: number };

export function imageToLab(img: ImageData): LabImage {
  const n = img.width * img.height;
  const L = new Float32Array(n), a = new Float32Array(n), b = new Float32Array(n);
  const d = img.data;
  for (let i = 0; i < n; i++) {
    const [l, aa, bb] = rgbToLab(d[i * 4], d[i * 4 + 1], d[i * 4 + 2]);
    L[i] = l; a[i] = aa; b[i] = bb;
  }
  return { L, a, b, w: img.width, h: img.height };
}

export function rgbToHsvOpenCV(r: number, g: number, b: number): [number, number, number] {
  // OpenCV 8 bit: H 0-179, S ve V 0-255
  const max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min;
  let h = 0;
  if (d > 0) {
    if (max === r) h = 60 * (((g - b) / d) % 6);
    else if (max === g) h = 60 * ((b - r) / d + 2);
    else h = 60 * ((r - g) / d + 4);
  }
  if (h < 0) h += 360;
  return [Math.round(h / 2), max === 0 ? 0 : Math.round((d / max) * 255), max];
}

/** Viridis renk haritasına yakın 6 duraklı ara değerleme (0-1 -> [r, g, b]). */
const VIRIDIS = [[68, 1, 84], [65, 68, 135], [42, 120, 142], [34, 168, 132], [122, 209, 81], [253, 231, 37]];
export function viridis(t: number): [number, number, number] {
  const x = Math.min(1, Math.max(0, t)) * (VIRIDIS.length - 1);
  const i = Math.min(VIRIDIS.length - 2, Math.floor(x)), u = x - i;
  const A = VIRIDIS[i], B = VIRIDIS[i + 1];
  return [A[0] + (B[0] - A[0]) * u, A[1] + (B[1] - A[1]) * u, A[2] + (B[2] - A[2]) * u];
}
