import { useEffect, useMemo, useRef, useState } from "react";
import { FaceLandmarker } from "@mediapipe/tasks-vision";
import { CameraStage, type LiveFrame } from "../components/CameraStage";
import { Header } from "../components/Header";
import { Slider, Toggle } from "../components/Control";
import { prepCanvas } from "../components/useCanvas";
import { projectFace } from "../lib/canonicalFace";
import { rgbToLab } from "../lib/color";
import * as C from "../lib/config";
import { REGIONS } from "../lib/faceRegions";
import { convexHull, poseFromMatrix, toPixels, type Pose, type Pt } from "../lib/geometry";
import { FACE_CONTOURS, FACE_TESSELATION } from "../lib/mediapipe";
import { analyzeSkin, type SkinResult } from "../lib/skin";
import type { SceneProps } from "./types";

const REGION_COLORS: Record<string, string> = { "alın": "#2dd4bf", "sağ yanak": "#3b82f6", "sol yanak": "#a78bfa" };
const idx = (conns: { start: number; end: number }[]) => [...new Set(conns.flatMap((c) => [c.start, c.end]))];
const EXCLUDE = [FaceLandmarker.FACE_LANDMARKS_LEFT_EYE, FaceLandmarker.FACE_LANDMARKS_RIGHT_EYE, FaceLandmarker.FACE_LANDMARKS_LEFT_EYEBROW,
  FaceLandmarker.FACE_LANDMARKS_RIGHT_EYEBROW, FaceLandmarker.FACE_LANDMARKS_LIPS].map(idx);

function path(g: CanvasRenderingContext2D, pts: Pt[]) {
  g.beginPath(); pts.forEach((p, k) => (k ? g.lineTo(p.x, p.y) : g.moveTo(p.x, p.y))); g.closePath();
}

/* ------------------------------------------------------------------ 16 */
const STEPS = ["Yüz ağı", "Alın ve yanak çokgenleri", "Göz, kaş ve dudak dışlanır", "Kenardan içeri çekilir", "Saç örten bölge atılır"];

export function Bolgeler({ meta, index }: SceneProps) {
  const ref = useRef<HTMLCanvasElement>(null);
  const [step, setStep] = useState(4);
  const [hair, setHair] = useState(true);
  const [coverage, setCoverage] = useState<Record<string, number>>({});
  const W = 640, H = 600;
  const pts = useMemo(() => projectFace({ scale: 25, cx: W / 2, cy: H / 2 + 10 }), []);
  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const g = prepCanvas(c, W, H);
    g.fillStyle = "#0a1120"; g.fillRect(0, 0, W, H);
    g.strokeStyle = "rgba(148,163,184,0.22)"; g.lineWidth = 0.8; g.beginPath();
    for (const e of FACE_TESSELATION) { g.moveTo(pts[e.start].x, pts[e.start].y); g.lineTo(pts[e.end].x, pts[e.end].y); }
    g.stroke();
    g.strokeStyle = "rgba(45,212,191,0.5)"; g.lineWidth = 1.2; g.beginPath();
    for (const e of FACE_CONTOURS) { g.moveTo(pts[e.start].x, pts[e.start].y); g.lineTo(pts[e.end].x, pts[e.end].y); }
    g.stroke();
    if (step < 1) return;
    // Bölgeleri ayrı bir tuvalde maskele, sonra boyayarak göster
    const erode = 6;
    const cov: Record<string, number> = {};
    const hairPoly = [pts[338], pts[297], pts[332], pts[284], { x: pts[284].x + 40, y: pts[284].y - 30 }, { x: pts[10].x + 10, y: pts[10].y - 60 }];
    for (const [name, ids] of Object.entries(REGIONS)) {
      const m = document.createElement("canvas"); m.width = W; m.height = H;
      const mg = m.getContext("2d", { willReadFrequently: true })!;
      mg.fillStyle = REGION_COLORS[name]; mg.strokeStyle = "#000";
      path(mg, ids.map((i) => pts[i])); mg.fill();
      const before = countAlpha(mg, W, H);
      mg.globalCompositeOperation = "destination-out";
      if (step >= 3) { mg.lineWidth = erode * 2; path(mg, ids.map((i) => pts[i])); mg.stroke(); }
      if (step >= 2) for (const grp of EXCLUDE) { const hull = convexHull(grp.map((i) => pts[i])); mg.lineWidth = erode * 4; path(mg, hull); mg.fill(); mg.stroke(); }
      const afterGeom = countAlpha(mg, W, H);
      if (step >= 4 && hair) { path(mg, hairPoly); mg.fill(); }
      cov[name] = afterGeom ? countAlpha(mg, W, H) / afterGeom : 0;
      void before;
      g.globalAlpha = 0.6; g.drawImage(m, 0, 0); g.globalAlpha = 1;
      g.strokeStyle = REGION_COLORS[name]; g.lineWidth = 1.5; path(g, ids.map((i) => pts[i])); g.stroke();
    }
    if (step >= 2) {
      g.fillStyle = "rgba(2,6,15,0.55)";
      for (const grp of EXCLUDE) { const hull = convexHull(grp.map((i) => pts[i])); g.lineWidth = erode * 4; g.strokeStyle = "rgba(2,6,15,0.55)"; path(g, hull); g.fill(); g.stroke(); }
    }
    if (step >= 4 && hair) {
      g.save(); path(g, hairPoly); g.clip();
      g.strokeStyle = "rgba(245,158,11,0.75)"; g.lineWidth = 2;
      for (let x = -H; x < W; x += 12) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x + H, H); g.stroke(); }
      g.restore();
      g.fillStyle = "#fcd34d"; g.font = "15px JetBrains Mono"; g.fillText("saç (örnek maske)", hairPoly[4].x - 120, hairPoly[4].y - 10);
    }
    g.fillStyle = "#9aa7b8"; g.font = "16px Inter";
    g.fillText("sağ yanak", pts[123].x - 90, pts[123].y + 4); g.fillText("sol yanak", pts[352].x + 14, pts[352].y + 4);
    setCoverage(cov);
  }, [step, hair, pts]);
  return (
    <>
      <Header meta={meta} index={index} />
      <div className="split" style={{ marginTop: 4 }}>
        <div className="col">
          <ol className="points" style={{ fontSize: 21 }}>
            {STEPS.map((s, i) => (
              <li key={s} style={{ color: i <= step ? "var(--text)" : "var(--dim)", cursor: "pointer" }} onClick={() => setStep(i)}>{i + 1}. {s}</li>
            ))}
          </ol>
          <div style={{ display: "flex", gap: 10 }}>
            <button className="btn" onClick={() => setStep(Math.max(0, step - 1))}>Önceki adım</button>
            <button className="btn primary" onClick={() => setStep(Math.min(STEPS.length - 1, step + 1))}>Sonraki adım</button>
            <Toggle label="Saç örtüyor" value={hair} onChange={setHair} />
          </div>
          {step >= 1 && <div className="panel readout" style={{ fontSize: 17 }}>
            {Object.entries(coverage).map(([k, v]) => <div key={k}><span style={{ color: REGION_COLORS[k] }}>{k}</span>: kalan alan <b>%{(v * 100).toFixed(0)}</b>{v < C.SKIN_MIN_VALID_FRACTION && <span className="amber"> · analize alınmaz</span>}</div>)}
          </div>}
          <p className="note">Python'da saç ve aksesuarlar Selfie Multiclass segmentasyon modeliyle ayrılır; model yoksa yüz ortancasından çok koyu pikseller atılır.</p>
        </div>
        <div className="visual" style={{ flex: "none", height: H + 2 }}>
          <span className="tag">Örnek gösterim · standart yüz modeli (aynalanmamış)</span>
          <canvas ref={ref} style={{ width: W, height: H }} />
        </div>
      </div>
    </>
  );
}

function countAlpha(g: CanvasRenderingContext2D, w: number, h: number) {
  const d = g.getImageData(0, 0, w, h).data;
  let n = 0;
  for (let i = 3; i < d.length; i += 4) if (d[i] > 127) n++;
  return n;
}

/* ------------------------------------------------------------------ 17 */
function patchStats(temp: number, intensity: number, side: number) {
  // Sabit "cilt": temel renk ve biraz daha kırmızı bir bölge. Yalnızca ışık değişir.
  const W = 120, H = 80;
  const base = [205, 152, 128], red = [212, 140, 122];
  const L: number[] = [], A: number[] = [], Bs: number[] = [];
  const pix: number[][] = [];
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const isRed = Math.hypot(x - 84, y - 44) < 16;
    const c = isRed ? red : base;
    const shade = intensity * (1 - side * (x / W));
    const r = Math.min(255, c[0] * shade * (1 + 0.22 * temp)), g = Math.min(255, c[1] * shade * (1 + 0.04 * temp)), b = Math.min(255, c[2] * shade * (1 - 0.25 * temp));
    const rgb = [Math.round(r), Math.round(g), Math.round(b)];
    pix.push(rgb);
    const [l, a, bb] = rgbToLab(rgb[0], rgb[1], rgb[2]);
    L.push(l); A.push(a); Bs.push(bb);
  }
  const med = (v: number[]) => [...v].sort((p, q) => p - q)[v.length >> 1];
  const redIdx: number[] = [], left: number[] = [], right: number[] = [];
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const i = y * W + x;
    if (Math.hypot(x - 84, y - 44) < 16) redIdx.push(i);
    else (x < W / 2 ? left : right).push(i);
  }
  const mean = (ids: number[], arr: number[]) => ids.reduce((s, i) => s + arr[i], 0) / ids.length;
  const medA = med(A);
  const dE = Math.hypot(med(left.map((i) => L[i])) - med(right.map((i) => L[i])), med(left.map((i) => A[i])) - med(right.map((i) => A[i])),
    med(left.map((i) => Bs[i])) - med(right.map((i) => Bs[i])));
  return { W, H, pix, absA: mean(left, A), deltaRed: mean(redIdx, A) - medA, dE };
}

export function Isik({ meta, index }: SceneProps) {
  const ref = useRef<HTMLCanvasElement>(null);
  const [temp, setTemp] = useState(0);
  const [intensity, setIntensity] = useState(1);
  const [side, setSide] = useState(0);
  const s = useMemo(() => patchStats(temp, intensity, side), [temp, intensity, side]);
  const base = useMemo(() => patchStats(0, 1, 0), []);
  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    c.width = s.W; c.height = s.H;
    const g = c.getContext("2d")!;
    const d = g.createImageData(s.W, s.H);
    s.pix.forEach((p, i) => { d.data[i * 4] = p[0]; d.data[i * 4 + 1] = p[1]; d.data[i * 4 + 2] = p[2]; d.data[i * 4 + 3] = 255; });
    g.putImageData(d, 0, 0);
  }, [s]);
  const diff = (v: number, b: number) => <span className={Math.abs(v - b) > 1 ? "amber" : "muted"}> ({v - b >= 0 ? "+" : ""}{(v - b).toFixed(1)})</span>;
  return (
    <>
      <Header meta={meta} index={index}>Yamadaki <strong>cilt aynıdır</strong>; yalnızca ışığın rengi, şiddeti ve yönü değişir.</Header>
      <div className="split" style={{ marginTop: 22 }}>
        <div className="col">
          <Slider label="Işık rengi (soğuk ↔ sıcak)" value={temp} min={-1} max={1} step={0.05} onChange={setTemp} format={(v) => (v > 0.1 ? "sıcak" : v < -0.1 ? "soğuk" : "nötr")} />
          <Slider label="Işık şiddeti" value={intensity} min={0.5} max={1.2} step={0.05} onChange={setIntensity} format={(v) => `%${Math.round(v * 100)}`} />
          <Slider label="Yan ışık (sağ taraf kararır)" value={side} min={0} max={0.6} step={0.05} onChange={setSide} format={(v) => `%${Math.round(v * 100)}`} />
          <div className="panel readout" style={{ fontSize: 18 }}>
            <div>mutlak a* (sol yarı) <b>{s.absA.toFixed(1)}</b>{diff(s.absA, base.absA)}</div>
            <div>kırmızı bölgenin Δa* değeri <b>{s.deltaRed.toFixed(1)}</b>{diff(s.deltaRed, base.deltaRed)}</div>
            <div>iki yarı arası ΔE <b>{s.dE.toFixed(1)}</b>{diff(s.dE, base.dE)}</div>
          </div>
          <p className="note">Parantez içi: nötr ışığa göre fark. Farklı günlerde standart ışık ve kamera ayarları olmadan alınan ölçümler gerçek değişim gibi karşılaştırılmaz.</p>
        </div>
        <div className="visual" style={{ flex: "none", height: 540 }}>
          <span className="tag">Sentetik cilt yaması</span>
          <canvas ref={ref} style={{ width: 780, height: 520, imageRendering: "auto", borderRadius: 8 }} />
        </div>
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ 18 */
function syntheticFaceImage(w: number, h: number) {
  // Örnek gösterim için sentetik yüz görüntüsü: standart yüz modeli, düz ten rengi,
  // hafif doku ve yanaklarda biraz daha kırmızı ton. Gerçek kişi değildir.
  const pts = projectFace({ scale: 34, cx: w / 2, cy: h / 2 + 20 });
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  const g = c.getContext("2d")!;
  g.fillStyle = "#3a4250"; g.fillRect(0, 0, w, h);
  const oval = idx(FaceLandmarker.FACE_LANDMARKS_FACE_OVAL).map((i) => pts[i]);
  g.fillStyle = "rgb(214,168,140)"; path(g, convexHull(oval)); g.fill();
  for (const [cx, cy] of [[pts[123].x * 0.6 + pts[205].x * 0.4, pts[123].y * 0.5 + pts[205].y * 0.5], [pts[352].x * 0.6 + pts[425].x * 0.4, pts[352].y * 0.5 + pts[425].y * 0.5]]) {
    const gr = g.createRadialGradient(cx, cy, 2, cx, cy, 55);
    gr.addColorStop(0, "rgba(220,120,110,0.35)"); gr.addColorStop(1, "rgba(220,120,110,0)");
    g.fillStyle = gr; g.beginPath(); g.arc(cx, cy, 55, 0, Math.PI * 2); g.fill();
  }
  g.fillStyle = "#2b2420";
  for (const grp of [FaceLandmarker.FACE_LANDMARKS_LEFT_EYEBROW, FaceLandmarker.FACE_LANDMARKS_RIGHT_EYEBROW]) { path(g, convexHull(idx(grp).map((i) => pts[i]))); g.fill(); }
  g.fillStyle = "#f4f1ee";
  for (const grp of [FaceLandmarker.FACE_LANDMARKS_LEFT_EYE, FaceLandmarker.FACE_LANDMARKS_RIGHT_EYE]) { path(g, convexHull(idx(grp).map((i) => pts[i]))); g.fill(); }
  g.fillStyle = "#b5615a"; path(g, convexHull(idx(FaceLandmarker.FACE_LANDMARKS_LIPS).map((i) => pts[i]))); g.fill();
  const d = g.getImageData(0, 0, w, h);
  let s = 7;
  for (let i = 0; i < w * h; i++) { s = (s * 1103515245 + 12345) & 0x7fffffff; const n = ((s / 0x7fffffff) - 0.5) * 10; for (let k = 0; k < 3; k++) d.data[i * 4 + k] = Math.max(0, Math.min(255, d.data[i * 4 + k] + n)); }
  g.putImageData(d, 0, 0);
  return { canvas: c, pts };
}

export function DemoCilt({ meta, index }: SceneProps) {
  const last = useRef<{ video: HTMLVideoElement | null; faces: Pt[][]; pose: Pose | null; w: number; h: number }>({ video: null, faces: [], pose: null, w: 0, h: 0 });
  const synth = useMemo(() => syntheticFaceImage(1280, 720), []);
  const sampleMode = useRef(false);
  const [result, setResult] = useState<SkinResult | null>(null);
  const heatRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const host = heatRef.current;
    if (!host) return;
    host.innerHTML = "";
    const cv = result?.heatmap ?? result?.regionPreview;
    if (cv) { cv.style.maxWidth = "100%"; cv.style.maxHeight = "100%"; host.appendChild(cv); }
  }, [result]);
  const onLive = (f: LiveFrame) => {
    sampleMode.current = false;
    const faces = (f.face?.faceLandmarks ?? []).map((l) => toPixels(l, f.w, f.h, false));
    const m = f.face?.facialTransformationMatrixes?.[0];
    last.current = { video: f.video, faces, pose: m ? poseFromMatrix(m.data) : null, w: f.w, h: f.h };
    const s = f.w / 1280;
    f.g.strokeStyle = "rgba(45,212,191,0.8)"; f.g.lineWidth = 1.5 * s;
    for (const p of faces) {
      const q = p.map((pt) => ({ x: f.w - pt.x, y: pt.y }));
      f.g.beginPath();
      for (const e of FACE_CONTOURS) { f.g.moveTo(q[e.start].x, q[e.start].y); f.g.lineTo(q[e.end].x, q[e.end].y); }
      f.g.stroke();
    }
    f.g.font = `500 ${22 * s}px Inter`; f.g.fillStyle = "#fcd34d"; f.g.fillText(C.SKIN_DISCLAIMER, 18 * s, 34 * s);
  };
  const onSample = (g: CanvasRenderingContext2D, w: number) => {
    sampleMode.current = true;
    g.save(); g.translate(w, 0); g.scale(-1, 1); g.drawImage(synth.canvas, 0, 0); g.restore();
    g.font = "500 22px Inter"; g.fillStyle = "#fcd34d"; g.fillText(C.SKIN_DISCLAIMER, 18, 34);
  };
  const capture = () => {
    if (sampleMode.current) { setResult(analyzeSkin(synth.canvas, 1280, 720, [synth.pts], { yaw: 0, pitch: 0, roll: 0 })); return; }
    const l = last.current;
    if (!l.video) return;
    setResult(analyzeSkin(l.video, l.w, l.h, l.faces, l.pose));
  };
  return (
    <>
      <Header meta={meta} index={index} />
      <div className="split wide-left" style={{ gridTemplateColumns: "1fr 470px", marginTop: 4 }}>
        <div className="visual"><CameraStage models={["face"]} onLive={onLive} onSample={onSample} onReset={() => setResult(null)}
                                             sampleLabel="sentetik yüz görüntüsü; analiz kodu gerçek"
                                             extra={<button className="btn primary small" onClick={capture}>Kare al ve analiz et</button>} /></div>
        <div className="col" style={{ gap: 10, overflow: "auto", maxHeight: 650 }}>
          <div className="disclaimer">{C.SKIN_DISCLAIMER} Görüntü kaydedilmez.</div>
          {!result && <p className="note">Kalite kontrolünden geçen tek bir kare analiz edilir. "Kare al ve analiz et" düğmesi kamera veya örnek gösterim açıkken görünür.</p>}
          {result && (
            <>
              <div className="panel" style={{ padding: "12px 16px" }}>
                {result.checks.map((c) => (
                  <div key={c.name} style={{ display: "flex", gap: 10, alignItems: "baseline", fontSize: 14, lineHeight: 1.45 }}>
                    <span style={{ width: 10, height: 10, borderRadius: 5, background: c.ok ? "var(--teal)" : "var(--red)", display: "inline-block", flex: "none" }} />
                    <span style={{ color: c.ok ? "var(--text)" : "var(--amber)" }}>{c.name}: <span className="mono" style={{ fontSize: 13 }}>{c.value}</span></span>
                  </div>
                ))}
                {!result.ok && <div className="amber" style={{ marginTop: 6, fontSize: 16 }}>Uygun görüntü bekleniyor. {result.checks.find((c) => !c.ok)?.hint}</div>}
              </div>
              <div ref={heatRef} style={{ height: 130, flex: "none", display: "flex", justifyContent: "center", alignItems: "center", background: "#070c16", borderRadius: 10 }} />
              {result.ok && (
                <>
                  <div className="readout" style={{ fontSize: 14 }}>Δa* haritası · sabit aralık {C.REDNESS_RANGE[0]} … +{C.REDNESS_RANGE[1]} · {result.ms.toFixed(0)} ms</div>
                  <table className="grid" style={{ fontSize: 14 }}>
                    <thead><tr><th>bölge</th><th>Δa*</th><th>parlak %</th><th>doku</th><th>ΔE</th></tr></thead>
                    <tbody>{Object.entries(result.regions).map(([k, r]) => (
                      <tr key={k}><td style={{ color: REGION_COLORS[k] }}>{k}</td><td className="mono">{r.deltaA >= 0 ? "+" : ""}{r.deltaA.toFixed(1)}</td>
                        <td className="mono">{r.shine.toFixed(1)}</td><td className="mono">{r.texture.toFixed(1)}</td><td className="mono">{r.colorDiff.toFixed(1)}</td></tr>
                    ))}</tbody>
                  </table>
                  {result.cheekDeltaE !== null && <div className="note">İki yanak arası ΔE: {result.cheekDeltaE.toFixed(1)} (çoğunlukla ışığın yönünden kaynaklanır)</div>}
                </>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ 19 */
export function Model({ meta, index }: SceneProps) {
  const refs = [useRef<HTMLCanvasElement>(null), useRef<HTMLCanvasElement>(null), useRef<HTMLCanvasElement>(null)];
  useEffect(() => {
    const spots = [[150, 120, 9], [190, 150, 7], [260, 110, 8], [120, 180, 6], [300, 170, 10]];
    refs.forEach((r, k) => {
      const c = r.current;
      if (!c) return;
      const g = prepCanvas(c, 420, 260);
      g.fillStyle = "#c9967c"; g.fillRect(0, 0, 420, 260);
      for (const [x, y, rad] of spots) { g.fillStyle = "#b5615a"; g.beginPath(); g.arc(x, y, rad, 0, Math.PI * 2); g.fill(); }
      if (k === 0) {
        g.fillStyle = "rgba(11,18,32,0.85)"; g.fillRect(0, 200, 420, 60);
        g.fillStyle = "#eef0ea"; g.font = "600 22px Space Grotesk"; g.fillText("tek etiket: \"B sınıfı\"", 16, 238);
      }
      if (k === 1) for (const [x, y, rad] of spots) { g.strokeStyle = "#3b82f6"; g.lineWidth = 2.5; g.strokeRect(x - rad - 6, y - rad - 6, 2 * rad + 12, 2 * rad + 12); }
      if (k === 2) {
        g.fillStyle = "rgba(11,18,32,0.55)"; g.fillRect(0, 0, 420, 260);
        for (const [x, y, rad] of spots) { g.fillStyle = "#2dd4bf"; g.beginPath(); g.arc(x, y, rad + 1, 0, Math.PI * 2); g.fill(); }
      }
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  const cards = [["Sınıflandırma", "Bütün görüntüye tek etiket verir. Yer bilgisi yoktur."], ["Tespit", "Nesnelerin yerini kutularla gösterir."], ["Segmentasyon", "Her piksele sınıf verir."]];
  return (
    <>
      <Header meta={meta} index={index} />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 22, marginTop: 2 }}>
        {cards.map(([t, d], k) => (
          <div key={t} className="col" style={{ gap: 8 }}>
            <div className="visual" style={{ flex: "none", height: 262 }}><span className="tag">Örnek gösterim · model çıktısı değil</span><canvas ref={refs[k]} style={{ width: 420, height: 260 }} /></div>
            <h3 style={{ margin: 0, fontFamily: "var(--font-display)", fontSize: 26 }}>{t}</h3>
            <p className="note" style={{ margin: 0, fontSize: 18 }}>{d}</p>
          </div>
        ))}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 22, marginTop: 22 }}>
        <div className="panel"><h3 className="teal">Entegre edildi: Selfie Multiclass</h3>
          <p>Segmentasyon modeli; saç, yüz cildi ve aksesuarları ayırır. Apache-2.0, 16 MB, CPU'da çalışır. Cildin durumu hakkında bir şey söylemez.</p></div>
        <div className="panel"><h3 className="amber">Değerlendirildi: acne-lds</h3>
          <p>Sınıflandırıcı (ResNet-50, 4 derece). Ağırlık lisansı belirsiz, veri yalnızca akademik, klinik fotoğraflardan web kamerasına alan farkı var. Entegre edilmedi.</p></div>
        <div className="panel"><h3>Grad-CAM bir maske değildir</h3>
          <p>Açıklama haritası modelin kararında etkili bölgeleri kabaca gösterir; lezyon segmentasyonu değildir. Sınıflandırıcıya kutu çizmek, üretmediği bilgiyi uydurmaktır.</p></div>
      </div>
    </>
  );
}
