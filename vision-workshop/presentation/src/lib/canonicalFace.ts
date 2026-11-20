// MediaPipe'ın standart yüz modeli (Apache-2.0). Örnek gösterimlerde gerçek kişi
// görüntüsü yerine bu modelin döndürülmüş izdüşümü kullanılır.
import data from "../../../shared/canonical_face_478.json";
import type { Pt } from "./geometry";

const V = (data as { vertices: number[][] }).vertices;

export type ProjectOptions = {
  yaw?: number; pitch?: number; roll?: number; scale?: number; cx?: number; cy?: number;
};

/** Modeli döndürüp perspektifle 2B'ye yansıtır (Python: tests/conftest.py project). */
export function projectFace(o: ProjectOptions = {}): Pt[] {
  const { yaw = 0, pitch = 0, roll = 0, scale = 20, cx = 320, cy = 240 } = o;
  const [y, p, r] = [yaw, pitch, roll].map((d) => (d * Math.PI) / 180);
  const cyw = Math.cos(y), syw = Math.sin(y), cp = Math.cos(p), sp = Math.sin(p), cr = Math.cos(r), sr = Math.sin(r);
  return V.map(([x0, y0, z0]) => {
    // Ry
    let x = cyw * x0 + syw * z0, yy = y0, z = -syw * x0 + cyw * z0;
    // Rx
    const y1 = cp * yy - sp * z, z1 = sp * yy + cp * z; yy = y1; z = z1;
    // Rz
    const x2 = cr * x - sr * yy, y2 = sr * x + cr * yy; x = x2; yy = y2;
    const f = 60, d = 60;
    return { x: (f * x) / (d - z) * scale + cx, y: (-f * yy) / (d - z) * scale + cy };
  });
}

export const CANONICAL_COUNT = V.length;
