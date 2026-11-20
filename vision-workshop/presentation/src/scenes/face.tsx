import { useEffect, useRef, useState } from "react";
import { CameraStage, type LiveFrame } from "../components/CameraStage";
import { Header } from "../components/Header";
import { Seg, Slider, Toggle } from "../components/Control";
import { prepCanvas } from "../components/useCanvas";
import { projectFace } from "../lib/canonicalFace";
import * as C from "../lib/config";
import { CHEEK_LEFT_EDGE, CHEEK_RIGHT_EDGE, CHIN, FOREHEAD_TOP, JAW_LEFT, JAW_RIGHT, LEFT_EYE_EAR, MOUTH_CORNERS, MOUTH_INNER, RIGHT_EYE_EAR } from "../lib/faceRegions";
import { bbox, dist, earOf, poseFromMatrix, toPixels, type Pose, type Pt } from "../lib/geometry";
import { FACE_CONTOURS, FACE_IRISES, FACE_TESSELATION } from "../lib/mediapipe";
import { useAnimationFrame, useReducedMotion } from "../lib/motion";
import { EMA, OneEuro } from "../lib/smoothing";
import type { SceneProps } from "./types";

function drawMesh(g: CanvasRenderingContext2D, p: Pt[], opts: { mesh?: boolean; lw?: number } = {}) {
  if (opts.mesh) {
    g.strokeStyle = "rgba(148,163,184,0.18)"; g.lineWidth = 0.8;
    g.beginPath();
    for (const c of FACE_TESSELATION) { g.moveTo(p[c.start].x, p[c.start].y); g.lineTo(p[c.end].x, p[c.end].y); }
    g.stroke();
  }
  g.strokeStyle = "#2dd4bf"; g.lineWidth = opts.lw ?? 2;
  g.beginPath();
  for (const c of FACE_CONTOURS) { g.moveTo(p[c.start].x, p[c.start].y); g.lineTo(p[c.end].x, p[c.end].y); }
  g.stroke();
  g.strokeStyle = "#a78bfa";
  g.beginPath();
  for (const c of FACE_IRISES) { g.moveTo(p[c.start].x, p[c.start].y); g.lineTo(p[c.end].x, p[c.end].y); }
  g.stroke();
}

function drawTrail(g: CanvasRenderingContext2D, pts: Pt[], color: string, width: number) {
  if (pts.length < 2) return;
  g.strokeStyle = color; g.lineWidth = width; g.lineJoin = "round"; g.lineCap = "round";
  g.beginPath(); pts.forEach((p, i) => (i ? g.lineTo(p.x, p.y) : g.moveTo(p.x, p.y))); g.stroke();
}

function label(g: CanvasRenderingContext2D, text: string, x: number, y: number, color = "#eef0ea", size = 22) {
  g.font = `500 ${size}px Inter, sans-serif`;
  const w = g.measureText(text).width;
  g.fillStyle = "rgba(11,18,32,0.82)"; g.fillRect(x - 6, y - size, w + 12, size + 10);
  g.fillStyle = color; g.fillText(text, x, y);
}

/* ------------------------------------------------------------------ 08 */
type Obj = { x: number; y: number; id?: number };

export function Takip({ meta, index }: SceneProps) {
  const refs = [useRef<HTMLCanvasElement>(null), useRef<HTMLCanvasElement>(null), useRef<HTMLCanvasElement>(null)];
  const reduced = useReducedMotion();
  const [playing, setPlaying] = useState(!reduced);
  const time = useRef(0);
  const tracker = useRef<{ tracks: { id: number; x: number; y: number; miss: number }[]; next: number }>({ tracks: [], next: 1 });
  const W = 440, H = 300;
  const objects = (t: number): Obj[] => {
    const a = ((t / 5200) % 1.3) * (W + 160) - 80;                // kadrajdan çıkıp yeniden giren nokta
    const out: Obj[] = [{ x: 150 + Math.sin(t / 900) * 60, y: 150 + Math.cos(t / 1300) * 50 }];
    if (a > 0 && a < W) out.push({ x: a, y: 90 + Math.sin(t / 600) * 18 });
    return out;
  };
  const step = (dt: number) => {
    time.current += dt;
    const t = time.current;
    const dets = objects(t).map((o) => ({ x: o.x + (Math.random() - 0.5) * 5, y: o.y + (Math.random() - 0.5) * 5 }));
    // Takip: en yakın merkez eşleştirmesi (Python: face/tracker.py)
    const tr = tracker.current;
    const used = new Set<number>();
    const assigned = dets.map((d) => {
      let best: (typeof tr.tracks)[number] | null = null, bd = 60;
      for (const k of tr.tracks) if (!used.has(k.id) && Math.hypot(k.x - d.x, k.y - d.y) < bd) { best = k; bd = Math.hypot(k.x - d.x, k.y - d.y); }
      if (!best) { best = { id: tr.next++, x: d.x, y: d.y, miss: 0 }; tr.tracks.push(best); }
      used.add(best.id); best.x = d.x; best.y = d.y; best.miss = 0;
      return { ...d, id: best.id };
    });
    tr.tracks.forEach((k) => { if (!used.has(k.id)) k.miss++; });
    tr.tracks = tr.tracks.filter((k) => k.miss < 10);
    refs.forEach((r, panel) => {
      const c = r.current;
      if (!c) return;
      const g = prepCanvas(c, W, H);
      g.fillStyle = "#0a1120"; g.fillRect(0, 0, W, H);
      for (const d of assigned) {
        g.fillStyle = "#93c5fd"; g.beginPath(); g.arc(d.x, d.y, 18, 0, Math.PI * 2); g.globalAlpha = 0.35; g.fill(); g.globalAlpha = 1;
        if (panel === 0) { g.strokeStyle = "#3b82f6"; g.lineWidth = 2; g.strokeRect(d.x - 30, d.y - 34, 60, 68); }
        if (panel === 1) {
          g.strokeStyle = "#2dd4bf"; g.lineWidth = 2; g.strokeRect(d.x - 30, d.y - 34, 60, 68);
          g.fillStyle = "#2dd4bf"; g.font = "600 16px JetBrains Mono"; g.fillText(`iz ${d.id}`, d.x - 28, d.y - 42);
        }
      }
      if (panel === 2) {
        g.fillStyle = "rgba(248,113,113,0.85)"; g.font = "600 22px Space Grotesk"; g.textAlign = "center";
        g.fillText("Bu eğitimde yok", W / 2, H / 2 - 6);
        g.fillStyle = "#9aa7b8"; g.font = "16px Inter"; g.fillText("kimlik tanıma kapsam dışıdır", W / 2, H / 2 + 22);
        g.textAlign = "left";
        g.strokeStyle = "rgba(248,113,113,0.6)"; g.lineWidth = 2; g.beginPath(); g.moveTo(30, 30); g.lineTo(W - 30, H - 30); g.stroke();
      }
    });
  };
  useAnimationFrame((_, dt) => step(dt), playing);
  useEffect(() => { step(16); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  const titles = [["Tespit", "Bu karede yüz var mı, nerede?"], ["Takip", "Önceki karedeki yüz hangisi?"], ["Tanıma", "Bu kişi kim?"]];
  return (
    <>
      <Header meta={meta} index={index}>Takip numarası bir <strong>iz</strong> numarasıdır: üstteki nokta kadrajdan çıkıp girince yeni numara alır. Kişinin kimliği değildir.</Header>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 22, marginTop: 30 }}>
        {titles.map(([t, s], k) => (
          <div key={t} className="col" style={{ gap: 10 }}>
            <div><h3 style={{ margin: 0, fontFamily: "var(--font-display)", fontSize: 30 }} className={k === 2 ? "red" : k === 1 ? "teal" : "blue"}>{t}</h3><p className="note" style={{ margin: 0, fontSize: 19 }}>{s}</p></div>
            <div className="visual" style={{ flex: "none", height: H + 2 }}>
              <span className="tag">Sentetik</span>
              <canvas ref={refs[k]} style={{ width: W, height: H }} />
            </div>
          </div>
        ))}
      </div>
      <div style={{ display: "flex", gap: 12, marginTop: 22, alignItems: "center" }}>
        <button className="btn" onClick={() => setPlaying(!playing)}>{playing ? "Duraklat" : "Oynat"}</button>
        {!playing && <button className="btn" onClick={() => step(250)}>Bir adım</button>}
        <span className="note">MediaPipe model kartları gözetim ve kimlik tanımayı kapsam dışı sayar.</span>
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ 09 */
type FaceStats = { faces: number; ear: number; mar: number; pose: Pose | null; ms: number; status: string; ok: boolean };

export function useFaceOverlay() {
  const raw = useRef<Pt[]>([]);
  const smooth = useRef<Pt[]>([]);
  const ema = useRef(new EMA(C.EMA_ALPHA));
  const lost = useRef(0);
  const [stats, setStats] = useState<FaceStats>({ faces: 0, ear: 0, mar: 0, pose: null, ms: 0, status: "", ok: false });
  const lastUi = useRef(0);
  const reset = () => { raw.current = []; smooth.current = []; ema.current.reset(); };

  /** Noktaları ve izi çizer; ekrana 5 kez/sn özet gönderir. pts: ekran (aynalanmış) koordinatları. */
  const draw = (g: CanvasRenderingContext2D, faces: Pt[][], poses: (Pose | null)[], t: number, ms: number, scale = 1) => {
    if (faces.length) {
      lost.current = 0;
      const p = faces[0];
      const b = bbox(p);
      const center = { x: (b.x1 + b.x2) / 2, y: (b.y1 + b.y2) / 2 };
      raw.current.push(center);
      smooth.current.push({ ...ema.current.update(center) });
      if (raw.current.length > C.TRAIL_LENGTH) { raw.current.shift(); smooth.current.shift(); }
    } else if (++lost.current > 15) reset();
    drawTrail(g, raw.current, "rgba(148,163,184,0.75)", 2 * scale);
    drawTrail(g, smooth.current, "#2dd4bf", 5 * scale);
    faces.forEach((p, k) => {
      drawMesh(g, p, { lw: 2 * scale });
      const b = bbox(p);
      g.strokeStyle = "#3b82f6"; g.lineWidth = 3 * scale;
      g.strokeRect(b.x1, b.y1, b.x2 - b.x1, b.y2 - b.y1);
      label(g, `iz ${k + 1}`, b.x1, b.y1 - 10 * scale, "#eef0ea", 22 * scale);
    });
    const status = faces.length === 0 ? "Yüz bulunamadı: kameraya önden bakın ve ışığı kontrol edin."
      : faces.length === 1 ? "1 yüz izleniyor" : `${faces.length} yüz izleniyor (numaralar kimlik değildir)`;
    label(g, status, 18 * scale, g.canvas.height - 22 * scale, faces.length ? "#2dd4bf" : "#f59e0b", 24 * scale);
    if (t - lastUi.current > 200) {
      lastUi.current = t;
      const p = faces[0];
      setStats({
        faces: faces.length, ms, status, ok: faces.length > 0, pose: poses[0] ?? null,
        ear: p ? (earOf(p, RIGHT_EYE_EAR) + earOf(p, LEFT_EYE_EAR)) / 2 : 0,
        mar: p ? dist(p[MOUTH_INNER[0]], p[MOUTH_INNER[1]]) / Math.max(1, dist(p[MOUTH_CORNERS[0]], p[MOUTH_CORNERS[1]])) : 0,
      });
    }
  };
  return { draw, stats, reset };
}

export function sampleFace(t: number, w: number, h: number) {
  // Örnek gösterim: standart yüz modeli + sentetik hareket ve ölçüm gürültüsü
  const yaw = Math.sin(t / 1700) * 18, pitch = Math.sin(t / 2300) * 8, roll = Math.sin(t / 2900) * 6;
  const cx = w / 2 + Math.sin(t / 1100) * 220, cy = h / 2 + Math.sin(t / 1500) * 60;
  const pts = projectFace({ yaw, pitch, roll, scale: 30, cx, cy })
    .map((p) => ({ x: w - p.x, y: p.y }));                       // ekran aynalı
  const jitter = { x: (Math.random() - 0.5) * 8, y: (Math.random() - 0.5) * 8 };
  return { pts: pts.map((p) => ({ x: p.x + jitter.x, y: p.y + jitter.y })), pose: { yaw, pitch, roll } as Pose };
}

export function DemoYuz({ meta, index }: SceneProps) {
  const { draw, stats, reset } = useFaceOverlay();
  const onLive = (f: LiveFrame) => {
    const faces = (f.face?.faceLandmarks ?? []).map((l) => toPixels(l, f.w, f.h, true));
    // Model aynalanmamış kareyi gördüğü için açılar Python uygulamasıyla aynı anlamdadır.
    const poses = (f.face?.facialTransformationMatrixes ?? []).map((m) => poseFromMatrix(m.data));
    draw(f.g, faces, poses, f.t, f.faceMs, f.w / 1280);
  };
  const onSample = (g: CanvasRenderingContext2D, w: number, h: number, t: number) => {
    const s = sampleFace(t, w, h);
    draw(g, [s.pts], [s.pose], performance.now(), 0);
  };
  return (
    <>
      <Header meta={meta} index={index} />
      <div className="split wide-left" style={{ gridTemplateColumns: "1fr 400px", marginTop: 4 }}>
        <div className="visual"><CameraStage models={["face"]} onLive={onLive} onSample={onSample} onReset={reset}
                                             sampleLabel="standart yüz modeli, sentetik hareket" /></div>
        <div className="col">
          <div className="panel readout" style={{ fontSize: 18 }}>
            <div>yüz sayısı <b>{stats.faces}</b></div>
            <div>göz açıklığı (EAR) <b>{stats.ear.toFixed(2)}</b></div>
            <div>ağız açıklığı <b>{stats.mar.toFixed(2)}</b></div>
            <div>dönüş / eğim / yatma <b>{stats.pose ? `${stats.pose.yaw.toFixed(0)}° / ${stats.pose.pitch.toFixed(0)}° / ${stats.pose.roll.toFixed(0)}°` : "—"}</b></div>
            <div>model süresi <b>{stats.ms ? `${stats.ms.toFixed(1)} ms` : "—"}</b></div>
          </div>
          <ul className="points" style={{ fontSize: 19 }}>
            <li><span className="muted">gri:</span> ham yüz merkezi</li>
            <li><span className="teal">turkuaz:</span> EMA ile yumuşatılmış (α = {C.EMA_ALPHA})</li>
            <li><span className="blue">mavi kutu:</span> noktalardan hesaplanan yüz kutusu</li>
          </ul>
          <p className="note">Model aynalanmamış kareyi görür; görüntü yalnızca ekranda aynalanır. Açılar yaklaşık değerlerdir.</p>
        </div>
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ 10 */
export function Normalize({ meta, index }: SceneProps) {
  const ref = useRef<HTMLCanvasElement>(null);
  const [scale, setScale] = useState(22);
  const [mirror, setMirror] = useState(false);
  const W = 760, H = 560;
  const pts = projectFace({ scale, cx: W / 2, cy: H / 2 }).map((p) => (mirror ? { x: W - p.x, y: p.y } : p));
  const len = dist(pts[FOREHEAD_TOP], pts[CHIN]), wid = dist(pts[CHEEK_RIGHT_EDGE], pts[CHEEK_LEFT_EDGE]);
  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const g = prepCanvas(c, W, H);
    drawMesh(g, pts, { mesh: true, lw: 1.4 });
    const line = (a: Pt, b: Pt, color: string) => { g.strokeStyle = color; g.lineWidth = 3; g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(b.x, b.y); g.stroke(); };
    line(pts[FOREHEAD_TOP], pts[CHIN], "#f59e0b");
    line(pts[CHEEK_RIGHT_EDGE], pts[CHEEK_LEFT_EDGE], "#3b82f6");
    const eye = pts[263];
    g.fillStyle = "#eef0ea"; g.beginPath(); g.arc(eye.x, eye.y, 6, 0, Math.PI * 2); g.fill();
    label(g, "kişinin sol gözü (nokta 263)", eye.x + (mirror ? -260 : 16), eye.y - 16, "#eef0ea", 17);
    g.fillStyle = "#64748b"; g.font = "15px JetBrains Mono";
    g.fillText(mirror ? "ekran: aynalanmış" : "ekran: aynalanmamış (kameranın gördüğü)", 14, H - 16);
  }, [scale, mirror]); // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <>
      <Header meta={meta} index={index} />
      <div className="split" style={{ marginTop: 4 }}>
        <div className="col">
          <Slider label="Kameraya uzaklık (ölçek)" value={scale} min={10} max={34} onChange={setScale} format={(v) => (v > 26 ? "yakın" : v < 16 ? "uzak" : "orta")} />
          <div className="stats">
            <div className="stat"><span className="v amber">{len.toFixed(0)}</span><span className="k">uzunluk (piksel)</span></div>
            <div className="stat"><span className="v blue">{wid.toFixed(0)}</span><span className="k">genişlik (piksel)</span></div>
            <div className="stat"><span className="v teal">{(len / wid).toFixed(3)}</span><span className="k">oran (sabit kalır)</span></div>
          </div>
          <Toggle label="Ekranı aynala" value={mirror} onChange={setMirror} />
          <p className="note">Model aynalanmamış kareyi görür; ayna yalnızca ekrana uygulanır. Böylece "sol göz" her zaman kişinin gerçek sol gözüdür.</p>
          <p className="note">z değeri santimetre değildir: yüzün kütle merkezine göreli ve yüz genişliğiyle ölçeklidir (Face Mesh V2 model kartı).</p>
        </div>
        <div className="visual" style={{ flex: "none", height: H + 2 }}>
          <span className="tag">Örnek gösterim · standart yüz modeli</span>
          <canvas ref={ref} style={{ width: W, height: H }} />
        </div>
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ 11 */
export function Iz({ meta, index }: SceneProps) {
  const ref = useRef<HTMLCanvasElement>(null);
  const reduced = useReducedMotion();
  const [playing, setPlaying] = useState(!reduced);
  const [alpha, setAlpha] = useState(C.EMA_ALPHA);
  const [noise, setNoise] = useState(10);
  const [kind, setKind] = useState<"ema" | "euro">("ema");
  const state = useRef({ t: 0, raw: [] as Pt[], filt: [] as Pt[], truth: [] as Pt[], ema: new EMA(C.EMA_ALPHA), euro: new OneEuro(0.8, 0.02) });
  const [m, setM] = useState({ jitter: 0, lag: 0 });
  const W = 900, H = 560;
  useEffect(() => { state.current.ema.alpha = alpha; }, [alpha]);
  const step = (dt: number) => {
    const s = state.current;
    s.t += dt;
    const t = s.t / 1000;
    const truth = { x: W / 2 + Math.sin(t * 1.1) * 320, y: H / 2 + Math.sin(t * 2.2) * 170 };
    const meas = { x: truth.x + (Math.random() - 0.5) * 2 * noise, y: truth.y + (Math.random() - 0.5) * 2 * noise };
    const f = kind === "ema" ? s.ema.update(meas) : s.euro.update(meas, t);
    s.raw.push(meas); s.filt.push({ ...f }); s.truth.push(truth);
    if (s.raw.length > 90) { s.raw.shift(); s.filt.shift(); s.truth.shift(); }
    const c = ref.current;
    if (!c) return;
    const g = prepCanvas(c, W, H);
    drawTrail(g, s.truth, "rgba(59,130,246,0.35)", 1.5);
    drawTrail(g, s.raw, "rgba(148,163,184,0.85)", 1.6);
    drawTrail(g, s.filt, "#2dd4bf", 4);
    g.fillStyle = "#2dd4bf"; g.beginPath(); g.arc(f.x, f.y, 7, 0, Math.PI * 2); g.fill();
    if (s.raw.length > 30 && Math.round(s.t / 16) % 12 === 0) {
      // titreme: ardışık filtre adımlarının ikinci farkı; gecikme: gerçek konuma ortalama uzaklık
      let jit = 0, lag = 0;
      for (let i = 2; i < s.filt.length; i++) jit += Math.hypot(s.filt[i].x - 2 * s.filt[i - 1].x + s.filt[i - 2].x, s.filt[i].y - 2 * s.filt[i - 1].y + s.filt[i - 2].y);
      for (let i = 0; i < s.filt.length; i++) lag += dist(s.filt[i], s.truth[i]);
      setM({ jitter: jit / (s.filt.length - 2), lag: lag / s.filt.length });
    }
  };
  useAnimationFrame((_, dt) => step(dt), playing);
  return (
    <>
      <Header meta={meta} index={index} />
      <div className="split" style={{ marginTop: 4 }}>
        <div className="col">
          <Seg options={[["ema", "EMA"], ["euro", "One Euro"]]} value={kind} onChange={(v) => { setKind(v); state.current.ema.reset(); state.current.euro.reset(); }} />
          {kind === "ema" && <Slider label="α (yumuşatma katsayısı)" value={alpha} min={0.05} max={1} step={0.05} onChange={setAlpha} format={(v) => v.toFixed(2)} />}
          <Slider label="Ölçüm gürültüsü (piksel)" value={noise} min={0} max={30} onChange={setNoise} />
          <div className="stats" style={{ gridTemplateColumns: "1fr 1fr" }}>
            <div className="stat"><span className="v">{m.jitter.toFixed(1)}</span><span className="k">titreme (px/kare²)</span></div>
            <div className="stat"><span className="v">{m.lag.toFixed(1)}</span><span className="k">gerçek konuma uzaklık (px)</span></div>
          </div>
          <p className="note">α küçüldükçe titreme azalır ama iz gecikir. One Euro filtresi yavaş harekette güçlü, hızlı harekette az yumuşatır. Değerler sentetik sinyalden hesaplanır.</p>
          <button className="btn" onClick={() => setPlaying(!playing)}>{playing ? "Duraklat" : "Oynat"}</button>
        </div>
        <div className="visual" style={{ flex: "none", height: H + 2 }}>
          <span className="tag">Sentetik sinyal</span>
          <canvas ref={ref} style={{ width: W, height: H }} />
          <div className="readout" style={{ position: "absolute", right: 16, bottom: 12, fontSize: 15 }}>
            <span className="blue">gerçek yol</span> · <span className="muted">ham ölçüm</span> · <span className="teal">filtre</span>
          </div>
        </div>
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ 12 */
export function Geometri({ meta, index }: SceneProps) {
  const ref = useRef<HTMLCanvasElement>(null);
  const [yaw, setYaw] = useState(0);
  const [pitch, setPitch] = useState(0);
  const W = 560, H = 520;
  const pts = projectFace({ yaw, pitch, scale: 24, cx: W / 2, cy: H / 2 });
  const width = dist(pts[CHEEK_RIGHT_EDGE], pts[CHEEK_LEFT_EDGE]);
  const lw = dist(pts[FOREHEAD_TOP], pts[CHIN]) / width;
  const jaw = dist(pts[JAW_RIGHT], pts[JAW_LEFT]) / width;
  const frontal = Math.abs(yaw) <= C.FRONTAL_MAX_YAW_DEG && Math.abs(pitch) <= C.FRONTAL_MAX_PITCH_DEG;
  const tendency = jaw >= 0.86 && lw < 1.32 ? "kareye yakın eğilim" : lw < 1.2 ? "yuvarlağa yakın eğilim" : lw >= 1.38 ? "uzun ovale yakın eğilim" : "ovale yakın eğilim";
  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const g = prepCanvas(c, W, H);
    drawMesh(g, pts, { mesh: true, lw: 1.4 });
    g.strokeStyle = "#f59e0b"; g.lineWidth = 3;
    g.beginPath(); g.moveTo(pts[FOREHEAD_TOP].x, pts[FOREHEAD_TOP].y); g.lineTo(pts[CHIN].x, pts[CHIN].y); g.stroke();
    g.strokeStyle = "#3b82f6";
    g.beginPath(); g.moveTo(pts[CHEEK_RIGHT_EDGE].x, pts[CHEEK_RIGHT_EDGE].y); g.lineTo(pts[CHEEK_LEFT_EDGE].x, pts[CHEEK_LEFT_EDGE].y); g.stroke();
    label(g, "nokta 10: alnın ortası, saç çizgisi değil", 16, 34, "#9aa7b8", 15);
  }, [yaw, pitch]); // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <>
      <Header meta={meta} index={index} />
      <div style={{ display: "grid", gridTemplateColumns: "560px 1fr 1fr", gap: 30, marginTop: 4, flex: 1, minHeight: 0 }}>
        <div className="col" style={{ gap: 12 }}>
          <div className="visual" style={{ flex: "none", height: H + 2 }}>
            <span className="tag">Örnek gösterim · standart yüz modeli</span>
            <canvas ref={ref} style={{ width: W, height: H }} />
          </div>
        </div>
        <div className="col">
          <Slider label="Baş dönüşü (yaw)" value={yaw} min={-45} max={45} onChange={setYaw} format={(v) => `${v}°`} />
          <Slider label="Eğim (pitch)" value={pitch} min={-30} max={30} onChange={setPitch} format={(v) => `${v}°`} />
          <div className="stats" style={{ gridTemplateColumns: "1fr 1fr" }}>
            <div className="stat"><span className="v amber">{lw.toFixed(2)}</span><span className="k">uzunluk / genişlik</span></div>
            <div className="stat"><span className="v">{jaw.toFixed(2)}</span><span className="k">çene / elmacık</span></div>
          </div>
          <div className="panel">
            <h3 className={frontal ? "teal" : "amber"}>{frontal ? `Yaklaşık: ${tendency}` : "Uygun görüntü bekleniyor"}</h3>
            <p>{frontal ? "Standart bir sınıf değildir; ortalama yüz modeline göre bir eğilimdir." : "Baş dönükken oran yanıltıcıdır; etiket üretilmez."}</p>
          </div>
          <p className="note">Ortalama yüz modeli önden 1,29 verir; 30° dönüşte oran yaklaşık %12 artar.</p>
        </div>
        <div className="col">
          <h3 style={{ margin: 0, fontFamily: "var(--font-display)", fontSize: 26 }}>Bir kamera neyi ölçebilir?</h3>
          <div className="panel"><h3 className="teal">Gözlenebilir</h3>
            <p>Nokta konumları, oranlar, göz kırpma, ağız açıklığı, baş yönelimi, hareket hızı.</p></div>
          <div className="panel"><h3 className="red">Çıkarım yapılmaz</h3>
            <p>Kişilik, zekâ, güvenilirlik, karakter. Gülümseme sinyali ağız köşelerinin hareketidir; içsel mutluluğun kanıtı değildir.</p></div>
        </div>
      </div>
    </>
  );
}
