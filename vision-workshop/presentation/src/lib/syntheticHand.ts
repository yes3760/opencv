// Örnek gösterimler için 21 noktalı sentetik el. Gerçek bir model çıktısı değildir.
import type { Pt } from "./geometry";

export type Curl = { thumb: number; index: number; middle: number; ring: number; pinky: number };

/** Tam bükülmede MCP, PIP ve DIP eklemlerindeki dönüş (radyan). */
const BEND = [1.0, 1.45, 1.0];

/** curl: 0 = düz, 1 = tamamen bükük. cx, cy: bilek; size: avuç boyu (piksel). */
export function syntheticHand(curl: Curl, cx: number, cy: number, size: number, tilt = 0): Pt[] {
  const pts: Pt[] = new Array(21);
  const rot = (x: number, y: number): Pt => {
    const c = Math.cos(tilt), s = Math.sin(tilt);
    return { x: cx + (x * c - y * s) * size, y: cy + (x * s + y * c) * size };
  };
  pts[0] = rot(0, 0);
  const fingers: [keyof Curl, number, number, number[]][] = [
    ["index", -0.32, -0.95, [0.42, 0.26, 0.2]],
    ["middle", -0.04, -1.0, [0.46, 0.29, 0.22]],
    ["ring", 0.22, -0.94, [0.42, 0.27, 0.2]],
    ["pinky", 0.45, -0.82, [0.33, 0.21, 0.17]],
  ];
  fingers.forEach(([name, bx, by, lens], k) => {
    const base = 5 + k * 4;
    let x = bx, y = by;
    pts[base] = rot(x, y);
    let ang = -Math.PI / 2 + bx * 0.25;            // parmak yönü (yukarı)
    const c = curl[name];
    for (let j = 0; j < 3; j++) {
      ang -= c * BEND[j];                           // avuç içine, başparmak tarafına kıvrılır
      const len = lens[j] * (1 - 0.3 * c);          // kameraya doğru bükülen parmak kısa görünür
      x += Math.cos(ang) * len;
      y += Math.sin(ang) * len;
      pts[base + j + 1] = rot(x, y);
    }
  });
  // başparmak: avucun yanından çıkar, bükülünce avuç içine döner
  let x = -0.28, y = -0.22, ang = -2.3;
  pts[1] = rot(x, y);
  const tl = [0.32, 0.26, 0.22];
  for (let j = 0; j < 3; j++) {
    ang += curl.thumb * 0.95;
    x += Math.cos(ang) * tl[j];
    y += Math.sin(ang) * tl[j];
    pts[2 + j] = rot(x, y);
  }
  return pts;
}

export const HAND_PAIRS: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4], [0, 5], [5, 6], [6, 7], [7, 8], [5, 9], [9, 10], [10, 11], [11, 12],
  [9, 13], [13, 14], [14, 15], [15, 16], [13, 17], [0, 17], [17, 18], [18, 19], [19, 20],
];
