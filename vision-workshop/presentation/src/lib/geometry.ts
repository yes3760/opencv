export type Pt = { x: number; y: number };

export const dist = (a: Pt, b: Pt) => Math.hypot(a.x - b.x, a.y - b.y);

/** b noktasındaki açı (derece). Düz bir parmakta 180'e yaklaşır. */
export function angleDeg(a: Pt, b: Pt, c: Pt): number {
  const v1x = a.x - b.x, v1y = a.y - b.y, v2x = c.x - b.x, v2y = c.y - b.y;
  const d = Math.hypot(v1x, v1y) * Math.hypot(v2x, v2y);
  if (d < 1e-9) return 0;
  const cos = Math.min(1, Math.max(-1, (v1x * v2x + v1y * v2y) / d));
  return (Math.acos(cos) * 180) / Math.PI;
}

export function earOf(p: Pt[], idx: number[]): number {
  const [p1, p2, p3, p4, p5, p6] = idx.map((i) => p[i]);
  const w = dist(p1, p4);
  return w < 1e-6 ? 0 : (dist(p2, p6) + dist(p3, p5)) / (2 * w);
}

export type Pose = { pitch: number; yaw: number; roll: number };

/** 4x4 dönüşüm matrisinden yaklaşık Euler açıları (Python: head_pose_from_matrix).
 *  Matrisin satır mı sütun öncelikli mi saklandığı öteleme değerinin yerinden anlaşılır. */
export function poseFromMatrix(data: number[]): Pose {
  const rowMajor = Math.abs(data[3]) + Math.abs(data[7]) + Math.abs(data[11]) >
    Math.abs(data[12]) + Math.abs(data[13]) + Math.abs(data[14]);
  const r = (i: number, j: number) => (rowMajor ? data[i * 4 + j] : data[j * 4 + i]);
  const deg = 180 / Math.PI;
  return {
    pitch: Math.atan2(r(2, 1), r(2, 2)) * deg,
    yaw: Math.asin(Math.max(-1, Math.min(1, -r(2, 0)))) * deg,
    roll: Math.atan2(r(1, 0), r(0, 0)) * deg,
  };
}

/** Normalize (0-1) noktaları piksele çevirir; aynalama istenirse x ekseni çevrilir. */
export function toPixels(lms: { x: number; y: number }[], w: number, h: number, mirror = false): Pt[] {
  return lms.map((p) => ({ x: (mirror ? 1 - p.x : p.x) * w, y: p.y * h }));
}

export function bbox(pts: Pt[]) {
  let x1 = Infinity, y1 = Infinity, x2 = -Infinity, y2 = -Infinity;
  for (const p of pts) {
    x1 = Math.min(x1, p.x); y1 = Math.min(y1, p.y); x2 = Math.max(x2, p.x); y2 = Math.max(y2, p.y);
  }
  return { x1, y1, x2, y2 };
}

/** Dışbükey zarf (Andrew'un monoton zincir algoritması). */
export function convexHull(points: Pt[]): Pt[] {
  const pts = [...points].sort((a, b) => a.x - b.x || a.y - b.y);
  if (pts.length < 3) return pts;
  const cross = (o: Pt, a: Pt, b: Pt) => (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
  const lower: Pt[] = [];
  for (const p of pts) {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) lower.pop();
    lower.push(p);
  }
  const upper: Pt[] = [];
  for (let i = pts.length - 1; i >= 0; i--) {
    const p = pts[i];
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) upper.pop();
    upper.push(p);
  }
  return lower.slice(0, -1).concat(upper.slice(0, -1));
}
