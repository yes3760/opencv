// Tarayıcıdaki cilt görünümü demosu. Python'daki src/skin/ modülünün sadeleştirilmiş karşılığıdır:
// aynı bölgeler, aynı kalite kontrolleri ve aynı göstergeler. Saç ayrımı için tarayıcıda
// segmentasyon modeli yerine renk tutarlılığı yöntemi kullanılır.
import { FaceLandmarker } from "@mediapipe/tasks-vision";
import * as C from "./config";
import { imageToLab, viridis } from "./color";
import { REGIONS, CHEEK_LEFT_EDGE, CHEEK_RIGHT_EDGE } from "./faceRegions";
import { bbox, convexHull, dist, type Pose, type Pt } from "./geometry";
import { gaussianBlur, median, sharpness, toGray } from "./imageops";

export type Check = { name: string; ok: boolean; value: string; hint: string };
export type RegionStat = { deltaA: number; shine: number; texture: number; colorDiff: number; coverage: number };
export type SkinResult = {
  checks: Check[];
  ok: boolean;
  regions: Record<string, RegionStat>;
  cheekDeltaE: number | null;
  heatmap: HTMLCanvasElement | null;   // Δa* haritası, sabit aralık, ekran için aynalanmış
  regionPreview: HTMLCanvasElement | null;
  ms: number;
};

const idx = (conns: { start: number; end: number }[]) => [...new Set(conns.flatMap((c) => [c.start, c.end]))];
const EXCLUDE = [
  idx(FaceLandmarker.FACE_LANDMARKS_LEFT_EYE), idx(FaceLandmarker.FACE_LANDMARKS_RIGHT_EYE),
  idx(FaceLandmarker.FACE_LANDMARKS_LEFT_EYEBROW), idx(FaceLandmarker.FACE_LANDMARKS_RIGHT_EYEBROW),
  idx(FaceLandmarker.FACE_LANDMARKS_LIPS),
];

function canvas(w: number, h: number) {
  const c = document.createElement("canvas");
  c.width = w; c.height = h;
  return c;
}

function maskFrom(draw: (g: CanvasRenderingContext2D) => void, w: number, h: number): Uint8Array {
  const c = canvas(w, h);
  const g = c.getContext("2d", { willReadFrequently: true })!;
  g.fillStyle = "#fff"; g.strokeStyle = "#fff";
  draw(g);
  const d = g.getImageData(0, 0, w, h).data;
  const m = new Uint8Array(w * h);
  for (let i = 0; i < w * h; i++) m[i] = d[i * 4 + 3] > 127 ? 1 : 0;
  return m;
}

/**
 * source: video, canvas veya resim. points: yüz noktaları (kaynak pikselleri, aynalanmamış).
 */
export function analyzeSkin(source: CanvasImageSource, srcW: number, srcH: number, faces: Pt[][],
                            pose: Pose | null): SkinResult {
  const t0 = performance.now();
  const checks: Check[] = [];
  const empty = (): SkinResult => ({ checks, ok: false, regions: {}, cheekDeltaE: null, heatmap: null,
                                    regionPreview: null, ms: performance.now() - t0 });
  checks.push({ name: "Tek yüz", ok: faces.length === 1, value: `${faces.length} yüz`,
                hint: "Analiz için kadrajda yalnızca bir kişi bulunmalı." });
  if (faces.length !== 1) return empty();
  const pts = faces[0];
  const widthFull = dist(pts[CHEEK_RIGHT_EDGE], pts[CHEEK_LEFT_EDGE]);
  checks.push({ name: "Yüz boyutu", ok: widthFull >= C.SKIN_MIN_FACE_WIDTH_PX,
                value: `${widthFull.toFixed(0)} px (en az ${C.SKIN_MIN_FACE_WIDTH_PX})`, hint: "Kameraya biraz yaklaşın." });
  const poseOk = !!pose && Math.abs(pose.yaw) <= C.SKIN_MAX_YAW_DEG && Math.abs(pose.pitch) <= C.SKIN_MAX_PITCH_DEG &&
    Math.abs(pose.roll) <= C.SKIN_MAX_ROLL_DEG;
  checks.push({ name: "Baş pozu", ok: poseOk,
                value: pose ? `dönüş ${pose.yaw.toFixed(0)}°, eğim ${pose.pitch.toFixed(0)}°, yatma ${pose.roll.toFixed(0)}°` : "ölçülemedi",
                hint: "Başınızı düz tutup doğrudan kameraya bakın." });

  // 1. Kesit ve ölçek: yüz genişliği 320 piksel olacak şekilde
  const b = bbox(pts);
  const mx = (b.x2 - b.x1) * 0.15, my = (b.y2 - b.y1) * 0.15;
  const x1 = Math.max(0, b.x1 - mx), y1 = Math.max(0, b.y1 - my);
  const x2 = Math.min(srcW, b.x2 + mx), y2 = Math.min(srcH, b.y2 + my);
  const s = C.SKIN_ANALYSIS_FACE_WIDTH / Math.max(widthFull, 1);
  const w = Math.max(8, Math.round((x2 - x1) * s)), h = Math.max(8, Math.round((y2 - y1) * s));
  const crop = canvas(w, h);
  const cg = crop.getContext("2d", { willReadFrequently: true })!;
  cg.drawImage(source, x1, y1, x2 - x1, y2 - y1, 0, 0, w, h);
  const img = cg.getImageData(0, 0, w, h);
  const P = pts.map((p) => ({ x: (p.x - x1) * s, y: (p.y - y1) * s }));

  // 2. Bölge maskeleri: çokgen, kenardan içeri çekme, göz/kaş/dudak dışlama
  const erode = Math.max(1, Math.round(C.SKIN_ANALYSIS_FACE_WIDTH * C.SKIN_ROI_EROSION_RATIO));
  const excl = maskFrom((g) => {
    g.lineWidth = erode * 4; g.lineJoin = "round";
    for (const group of EXCLUDE) {
      const hull = convexHull(group.map((i) => P[i]));
      g.beginPath(); hull.forEach((p, k) => (k ? g.lineTo(p.x, p.y) : g.moveTo(p.x, p.y))); g.closePath();
      g.fill(); g.stroke();
    }
  }, w, h);
  const lab = imageToLab(img);
  const L8 = Float32Array.from(lab.L, (v) => (v * 255) / 100);
  const raw: Record<string, Uint8Array> = {};
  for (const [name, ids] of Object.entries(REGIONS)) {
    raw[name] = maskFrom((g) => {
      g.beginPath(); ids.forEach((i, k) => (k ? g.lineTo(P[i].x, P[i].y) : g.moveTo(P[i].x, P[i].y))); g.closePath();
      g.fill();
      g.globalCompositeOperation = "destination-out";     // kenardan içeri çek (aşındırma)
      g.lineWidth = erode * 2; g.stroke();
    }, w, h);
    for (let i = 0; i < w * h; i++) if (excl[i]) raw[name][i] = 0;
  }
  // 3. Saç ve gölge: yüz ortancasından çok koyu pikseller atılır (renk tutarlılığı)
  const unionVals: number[] = [];
  for (let i = 0; i < w * h; i++) if (raw["alın"][i] || raw["sağ yanak"][i] || raw["sol yanak"][i]) unionVals.push(L8[i]);
  const medL = median(unionVals);
  const masks: Record<string, Uint8Array> = {};
  const coverage: Record<string, number> = {};
  for (const [name, m] of Object.entries(raw)) {
    let total = 0, kept = 0;
    const out = new Uint8Array(w * h);
    for (let i = 0; i < w * h; i++) if (m[i]) { total++; if (L8[i] > medL - 35) { out[i] = 1; kept++; } }
    masks[name] = out;
    coverage[name] = total ? kept / total : 0;
  }

  // 4. Kalite: netlik, pozlama, kapsama
  const fb = bbox(P);
  const fw = Math.max(1, Math.round(fb.x2 - fb.x1)), fh = Math.max(1, Math.round(fb.y2 - fb.y1));
  const sw = 256, sh = Math.max(8, Math.round((fh * 256) / fw));
  const sc = canvas(sw, sh);
  const sg = sc.getContext("2d", { willReadFrequently: true })!;
  sg.drawImage(crop, fb.x1, fb.y1, fw, fh, 0, 0, sw, sh);
  const sharp = sharpness(toGray(sg.getImageData(0, 0, sw, sh)), sw, sh);
  checks.push({ name: "Netlik", ok: sharp >= C.SKIN_MIN_SHARPNESS,
                value: `göreli netlik ${sharp.toFixed(0)} (en az ${C.SKIN_MIN_SHARPNESS})`, hint: "Hareketsiz durun; kamera merceğini silin." });
  const union: number[] = [];
  for (let i = 0; i < w * h; i++) if (masks["alın"][i] || masks["sağ yanak"][i] || masks["sol yanak"][i]) union.push(i);
  const lv = union.map((i) => L8[i]);
  const medianL = median(lv);
  const clipped = lv.filter((v) => v >= 250).length / Math.max(1, lv.length);
  const dark = lv.filter((v) => v <= 25).length / Math.max(1, lv.length);
  if (medianL < C.SKIN_MIN_MEDIAN_L || dark > C.SKIN_MAX_DARK_FRACTION)
    checks.push({ name: "Pozlama", ok: false, value: `ortanca L ${medianL.toFixed(0)}`, hint: "Ortam çok karanlık: yüzünüzü önden aydınlatın." });
  else if (medianL > C.SKIN_MAX_MEDIAN_L || clipped > C.SKIN_MAX_CLIPPED_FRACTION)
    checks.push({ name: "Pozlama", ok: false, value: `ortanca L ${medianL.toFixed(0)}, doymuş %${(clipped * 100).toFixed(0)}`, hint: "Aşırı ışık: doğrudan gelen ışıktan uzaklaşın." });
  else checks.push({ name: "Pozlama", ok: true, value: `ortanca L ${medianL.toFixed(0)}`, hint: "" });
  const validNames = Object.keys(coverage).filter((k) => coverage[k] >= C.SKIN_MIN_VALID_FRACTION);
  checks.push({ name: "Bölge kapsaması", ok: validNames.length >= 2,
                value: Object.entries(coverage).map(([k, v]) => `${k} %${(v * 100).toFixed(0)}`).join(", "),
                hint: "Saç, gözlük veya el bölgeleri örtüyor olabilir." });

  const preview = renderRegions(crop, masks, excl, w, h);
  const ok = checks.every((c) => c.ok);
  if (!ok) return { ...empty(), regionPreview: preview };

  // 5. Göstergeler
  const medA = median(union.map((i) => lab.a[i]));
  const chroma = Float32Array.from(lab.a, (a, i) => Math.hypot(a, lab.b[i]));
  const medChroma = median(union.map((i) => chroma[i]));
  const blurred = gaussianBlur(L8, w, h, 3);
  const detail2 = Float32Array.from(L8, (v, i) => (v - blurred[i]) ** 2);
  const energy = gaussianBlur(detail2, w, h, 2).map(Math.sqrt);
  const regions: Record<string, RegionStat> = {};
  const medians: Record<string, [number, number, number]> = {};
  for (const name of validNames) {
    const sel: number[] = [];
    for (let i = 0; i < w * h; i++) if (masks[name][i]) sel.push(i);
    const med: [number, number, number] = [median(sel.map((i) => lab.L[i])), median(sel.map((i) => lab.a[i])), median(sel.map((i) => lab.b[i]))];
    medians[name] = med;
    let da = 0, sh = 0, tx = 0, de = 0;
    for (const i of sel) {
      da += lab.a[i] - medA;
      if (L8[i] >= medianL + C.SPECULAR_DELTA_L && chroma[i] <= C.SPECULAR_CHROMA_RATIO * medChroma) sh++;
      tx += energy[i];
      de += Math.hypot(lab.L[i] - med[0], lab.a[i] - med[1], lab.b[i] - med[2]);
    }
    const n = Math.max(1, sel.length);
    regions[name] = { deltaA: da / n, shine: (sh / n) * 100, texture: tx / n, colorDiff: de / n, coverage: coverage[name] };
  }
  const cheekDeltaE = medians["sağ yanak"] && medians["sol yanak"]
    ? Math.hypot(...medians["sağ yanak"].map((v, k) => v - medians["sol yanak"][k]) as [number, number, number]) : null;

  // Isı haritası: Δa*, sabit aralık [-10, 10]; bölge dışı karartılır; ekran için aynalanır.
  const heat = canvas(w, h);
  const hg = heat.getContext("2d")!;
  const out = hg.createImageData(w, h);
  const [lo, hi] = C.REDNESS_RANGE;
  for (let i = 0; i < w * h; i++) {
    const inside = masks["alın"][i] || masks["sağ yanak"][i] || masks["sol yanak"][i];
    const r = img.data[i * 4], g = img.data[i * 4 + 1], bl = img.data[i * 4 + 2];
    if (inside) {
      const [cr, cgg, cb] = viridis((lab.a[i] - medA - lo) / (hi - lo));
      out.data[i * 4] = 0.4 * r + 0.6 * cr; out.data[i * 4 + 1] = 0.4 * g + 0.6 * cgg; out.data[i * 4 + 2] = 0.4 * bl + 0.6 * cb;
    } else {
      out.data[i * 4] = r * 0.4; out.data[i * 4 + 1] = g * 0.4; out.data[i * 4 + 2] = bl * 0.4;
    }
    out.data[i * 4 + 3] = 255;
  }
  hg.putImageData(out, 0, 0);
  const mirrored = canvas(w, h);
  const mg = mirrored.getContext("2d")!;
  mg.translate(w, 0); mg.scale(-1, 1); mg.drawImage(heat, 0, 0);
  return { checks, ok, regions, cheekDeltaE, heatmap: mirrored, regionPreview: preview, ms: performance.now() - t0 };
}

const REGION_RGB: Record<string, [number, number, number]> = {
  "alın": [45, 212, 191], "sağ yanak": [59, 130, 246], "sol yanak": [167, 139, 250],
};

function renderRegions(crop: HTMLCanvasElement, masks: Record<string, Uint8Array>, excl: Uint8Array, w: number, h: number) {
  const c = canvas(w, h);
  const g = c.getContext("2d")!;
  g.translate(w, 0); g.scale(-1, 1);              // ekranda ayna görüntüsü
  g.drawImage(crop, 0, 0);
  g.setTransform(1, 0, 0, 1, 0, 0);
  const img = g.getImageData(0, 0, w, h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const src = y * w + (w - 1 - x), i = (y * w + x) * 4;
    let tinted = false;
    for (const [name, m] of Object.entries(masks)) if (m[src]) {
      const [r, gg, b] = REGION_RGB[name];
      img.data[i] = img.data[i] * 0.5 + r * 0.5; img.data[i + 1] = img.data[i + 1] * 0.5 + gg * 0.5; img.data[i + 2] = img.data[i + 2] * 0.5 + b * 0.5;
      tinted = true;
    }
    if (!tinted && excl[src]) { img.data[i] *= 0.45; img.data[i + 1] *= 0.45; img.data[i + 2] *= 0.45; }
  }
  g.putImageData(img, 0, 0);
  return c;
}
