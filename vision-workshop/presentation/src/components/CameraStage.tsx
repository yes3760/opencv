// Canlı demo alanı. Kamera yalnızca "Kamerayı başlat" düğmesiyle açılır; "Durdur" bütün
// izleri kapatır. Kamera izni, cihaz veya model hatasında açıklayıcı bir ekran gösterilir.
// Kamerasız anlatım için "Örnek gösterim" (sentetik) ve "Video dosyası" seçenekleri vardır.
import { useEffect, useRef, useState, type ReactNode } from "react";
import type { FaceLandmarkerResult, HandLandmarkerResult } from "@mediapipe/tasks-vision";
import { useCamera } from "../lib/camera";
import { getFaceLandmarker, getHandLandmarker, ModelLoadError, nextTimestamp } from "../lib/mediapipe";
import { useReducedMotion } from "../lib/motion";

export type LiveFrame = {
  g: CanvasRenderingContext2D; w: number; h: number; t: number;
  face: FaceLandmarkerResult | null; hand: HandLandmarkerResult | null;
  faceMs: number; handMs: number; video: HTMLVideoElement;
};

type Props = {
  models: ("face" | "hand")[];
  onLive: (f: LiveFrame) => void;
  onSample: (g: CanvasRenderingContext2D, w: number, h: number, t: number) => void;
  sampleLabel: string;
  onReset?: () => void;
  extra?: ReactNode;
};

const W = 1280, H = 720;

export function CameraStage({ models, onLive, onSample, sampleLabel, onReset, extra }: Props) {
  const { source, devices, deviceId, start, stop, openFile } = useCamera();
  const [dark, setDark] = useState(false);
  const reduced = useReducedMotion();
  const [sample, setSample] = useState(false);
  const [samplePlaying, setSamplePlaying] = useState(!reduced);
  const [modelState, setModelState] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [modelError, setModelError] = useState("");
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const cbs = useRef({ onLive, onSample });
  cbs.current = { onLive, onSample };
  const live = source.status === "camera" || source.status === "file";

  // Kaynağı video öğesine bağla
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    if (source.status === "camera") { v.srcObject = source.stream; v.src = ""; }
    else if (source.status === "file") { v.srcObject = null; v.src = source.url; v.loop = true; }
    else { v.srcObject = null; v.removeAttribute("src"); v.load(); return; }
    v.muted = true;
    v.play().catch(() => undefined);
    setSample(false);
    onReset?.();
  }, [source]); // eslint-disable-line react-hooks/exhaustive-deps

  // Modelleri yükle (bir kez; önbellekte tutulur)
  useEffect(() => {
    if (!live) return;
    let cancelled = false;
    setModelState("loading");
    Promise.all(models.map((m) => (m === "face" ? getFaceLandmarker() : getHandLandmarker())))
      .then(() => !cancelled && setModelState("ready"))
      .catch((e) => {
        if (cancelled) return;
        setModelState("error");
        setModelError(e instanceof ModelLoadError ? e.message : String(e));
      });
    return () => { cancelled = true; };
  }, [live]); // eslint-disable-line react-hooks/exhaustive-deps

  // Canlı döngü
  useEffect(() => {
    if (!live || modelState !== "ready") return;
    let id = 0;
    let lastTime = -1;
    let face: FaceLandmarkerResult | null = null, hand: HandLandmarkerResult | null = null;
    let faceMs = 0, handMs = 0, frameCount = 0;
    const probe = document.createElement("canvas");
    probe.width = 32; probe.height = 18;
    const loop = async () => {
      const v = videoRef.current, c = canvasRef.current;
      if (v && c && v.readyState >= 2 && v.videoWidth > 0) {
        if (c.width !== v.videoWidth) { c.width = v.videoWidth; c.height = v.videoHeight; }
        if (v.currentTime !== lastTime) {
          lastTime = v.currentTime;
          if (models.includes("face")) {
            const fl = await getFaceLandmarker();
            const t0 = performance.now(); face = fl.detectForVideo(v, nextTimestamp()); faceMs = performance.now() - t0;
          }
          if (models.includes("hand")) {
            const hl = await getHandLandmarker();
            const t0 = performance.now(); hand = hl.detectForVideo(v, nextTimestamp()); handMs = performance.now() - t0;
          }
        }
        const g = c.getContext("2d")!;
        g.save(); g.translate(c.width, 0); g.scale(-1, 1); g.drawImage(v, 0, 0, c.width, c.height); g.restore();
        if (++frameCount % 30 === 0) {
          // Görüntü tamamen siyahsa (yanlış kamera veya kapalı mercek) kullanıcı uyarılır.
          probe.getContext("2d")!.drawImage(v, 0, 0, 32, 18);
          const d = probe.getContext("2d")!.getImageData(0, 0, 32, 18).data;
          let sum = 0;
          for (let i = 0; i < d.length; i += 4) sum += d[i] + d[i + 1] + d[i + 2];
          setDark(sum / (32 * 18 * 3) < 5);
        }
        cbs.current.onLive({ g, w: c.width, h: c.height, t: performance.now(), face, hand, faceMs, handMs, video: v });
      }
      id = requestAnimationFrame(loop);
    };
    id = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(id);
  }, [live, modelState]); // eslint-disable-line react-hooks/exhaustive-deps

  // Örnek gösterim döngüsü
  useEffect(() => {
    if (!sample || live) return;
    let id = 0;
    const t0 = performance.now();
    let frozen = 0;
    const draw = (now: number) => {
      const c = canvasRef.current;
      if (!c) return;
      if (c.width !== W) { c.width = W; c.height = H; }
      const g = c.getContext("2d")!;
      g.fillStyle = "#0a1120"; g.fillRect(0, 0, W, H);
      cbs.current.onSample(g, W, H, samplePlaying ? now - t0 : frozen);
    };
    if (samplePlaying) {
      const loop = (now: number) => { draw(now); id = requestAnimationFrame(loop); };
      id = requestAnimationFrame(loop);
    } else { frozen = 1200; draw(performance.now()); }
    return () => cancelAnimationFrame(id);
  }, [sample, live, samplePlaying]);

  const showGate = !live && !sample;
  return (
    <div className="camstage" data-no-swipe>
      <video ref={videoRef} playsInline muted aria-hidden />
      <canvas ref={canvasRef} width={W} height={H} aria-label="Demo görüntüsü" />
      {live && modelState === "ready" && <span className="tag live">{source.status === "camera" ? "Canlı kamera · yerel işleme" : `Video dosyası · ${source.status === "file" ? source.name : ""}`}</span>}
      {sample && !live && <span className="tag">Örnek gösterim · {sampleLabel}</span>}
      {live && modelState === "ready" && dark && (
        <div className="gate" style={{ pointerEvents: "none" }}><div className="box">
          <h3 className="err">Görüntü siyah</h3>
          <p>Seçili kamera görüntü vermiyor. Mercek kapalı olabilir veya bu kamera başka bir cihaza (ör. iPhone) ait. Alttaki listeden başka bir kamera seçin.</p>
        </div></div>
      )}

      {showGate && (
        <div className="gate">
          <div className="box">
            {source.status === "error" ? (
              <>
                <h3 className="err">{source.error.title}</h3>
                <p>{source.error.hint}</p>
              </>
            ) : (
              <>
                <h3>{source.status === "starting" ? "Kamera açılıyor…" : "Kamera kapalı"}</h3>
                <p>Kamera yalnızca düğmeye basıldığında açılır. Görüntü bu bilgisayarda işlenir; kaydedilmez ve hiçbir sunucuya gönderilmez.</p>
              </>
            )}
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", justifyContent: "center" }}>
              <button className="btn primary" onClick={() => start()} disabled={source.status === "starting"}>Kamerayı başlat</button>
              <button className="btn" onClick={() => fileRef.current?.click()}>Video dosyası seç</button>
              <button className="btn" onClick={() => setSample(true)}>Örnek gösterim</button>
            </div>
          </div>
        </div>
      )}
      {live && modelState === "loading" && <div className="gate"><div className="box"><h3>Model yükleniyor…</h3><p>Model dosyası yerelden okunuyor; ilk yükleme birkaç saniye sürebilir.</p></div></div>}
      {live && modelState === "error" && (
        <div className="gate"><div className="box">
          <h3 className="err">Model yüklenemedi</h3>
          <p>{modelError} Proje kökünde <span className="mono">python scripts/download_models.py</span>, ardından sunum klasöründe <span className="mono">npm run setup</span> çalıştırılır.</p>
          <button className="btn" onClick={() => { stop(); setSample(true); }}>Örnek gösterimle devam et</button>
        </div></div>
      )}

      <input ref={fileRef} type="file" accept="video/*" hidden
             onChange={(e) => { const f = e.target.files?.[0]; if (f) openFile(f); e.target.value = ""; }} />
      {(live || sample) && (
        <div className="camctl">
          {live && <button className="btn danger small" onClick={() => stop()}>{source.status === "camera" ? "Kamerayı durdur" : "Videoyu kapat"}</button>}
          {source.status === "camera" && devices.length > 1 && (
            <select className="btn small" value={deviceId ?? ""} aria-label="Kamera seç"
                    onChange={(e) => { setDark(false); start(e.target.value); }} style={{ maxWidth: 260 }}>
              {devices.map((d) => <option key={d.id} value={d.id}>{d.label}</option>)}
            </select>
          )}
          {sample && !live && <button className="btn small" onClick={() => setSample(false)}>Örnek gösterimi kapat</button>}
          {sample && !live && <button className="btn small" aria-pressed={samplePlaying} onClick={() => setSamplePlaying(!samplePlaying)}>{samplePlaying ? "Duraklat" : "Oynat"}</button>}
          <span className="grow" />
          {extra}
        </div>
      )}
    </div>
  );
}
