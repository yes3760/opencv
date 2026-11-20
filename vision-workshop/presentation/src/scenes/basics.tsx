import { useEffect, useMemo, useRef, useState } from "react";
import { Header } from "../components/Header";
import { Seg, Slider, Toggle } from "../components/Control";
import { prepCanvas } from "../components/useCanvas";
import { rgbToHsvOpenCV, rgbToLab } from "../lib/color";
import { closing, components, gaussianBlur, opening, otsu, threshold, toGray } from "../lib/imageops";
import { useAnimationFrame, useReducedMotion } from "../lib/motion";
import type { SceneProps } from "./types";

/** Sentetik sahne: gerçek bir fotoğraf değildir; gösterim için çizilir. */
function makeScene(w: number, h: number): ImageData {
  const c = document.createElement("canvas");
  c.width = w; c.height = h;
  const g = c.getContext("2d")!;
  const sky = g.createLinearGradient(0, 0, 0, h);
  sky.addColorStop(0, "#1e3a8a"); sky.addColorStop(0.55, "#38bdf8"); sky.addColorStop(1, "#fde68a");
  g.fillStyle = sky; g.fillRect(0, 0, w, h);
  g.fillStyle = "#f97316"; g.beginPath(); g.arc(w * 0.78, h * 0.32, h * 0.16, 0, Math.PI * 2); g.fill();
  g.fillStyle = "#14532d"; g.beginPath(); g.moveTo(0, h); g.lineTo(w * 0.28, h * 0.48); g.lineTo(w * 0.55, h); g.fill();
  g.fillStyle = "#166534"; g.beginPath(); g.moveTo(w * 0.35, h); g.lineTo(w * 0.62, h * 0.58); g.lineTo(w * 0.92, h); g.fill();
  g.fillStyle = "#e11d48"; g.fillRect(w * 0.08, h * 0.12, w * 0.12, h * 0.16);
  g.fillStyle = "#fafaf9"; g.font = `700 ${Math.round(h * 0.13)}px Space Grotesk, sans-serif`;
  g.fillText("VISION", w * 0.06, h * 0.86);
  return g.getImageData(0, 0, w, h);
}

function useSceneImage(w = 320, h = 180) {
  return useMemo(() => makeScene(w, h), [w, h]);
}

function toCanvas(img: ImageData) {
  const c = document.createElement("canvas");
  c.width = img.width; c.height = img.height;
  c.getContext("2d")!.putImageData(img, 0, 0);
  return c;
}

/* ------------------------------------------------------------------ 03 */
export function Veri({ meta, index }: SceneProps) {
  const img = useSceneImage();
  const src = useMemo(() => toCanvas(img), [img]);
  const ref = useRef<HTMLCanvasElement>(null);
  const strip = useRef<HTMLCanvasElement>(null);
  const [zoom, setZoom] = useState(1);
  const [hover, setHover] = useState<{ x: number; y: number } | null>(null);
  const reduced = useReducedMotion();
  const fps = useRef({ v: 0, last: performance.now(), frames: 0 });
  const [fpsShown, setFps] = useState(0);
  const W = 880, H = 495;
  const view = useMemo(() => {
    const vw = img.width / zoom, vh = img.height / zoom;
    return { x: (img.width - vw) / 2, y: (img.height - vh) / 2, w: vw, h: vh };
  }, [zoom, img]);

  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const g = prepCanvas(c, W, H);
    g.imageSmoothingEnabled = false;
    g.drawImage(src, view.x, view.y, view.w, view.h, 0, 0, W, H);
    const cell = W / view.w;
    if (cell >= 22) {
      g.strokeStyle = "rgba(11,18,32,0.55)"; g.lineWidth = 1;
      const x0 = Math.floor(view.x), y0 = Math.floor(view.y);
      for (let px = x0; px <= view.x + view.w; px++) { const sx = (px - view.x) * cell; g.beginPath(); g.moveTo(sx, 0); g.lineTo(sx, H); g.stroke(); }
      for (let py = y0; py <= view.y + view.h; py++) { const sy = (py - view.y) * cell; g.beginPath(); g.moveTo(0, sy); g.lineTo(W, sy); g.stroke(); }
      if (cell >= 52) {
        g.font = `${Math.min(14, cell / 4.2)}px JetBrains Mono`; g.textAlign = "center";
        for (let py = y0; py < view.y + view.h; py++) for (let px = x0; px < view.x + view.w; px++) {
          if (px < 0 || py < 0 || px >= img.width || py >= img.height) continue;
          const i = (py * img.width + px) * 4;
          const [r, gg, b] = [img.data[i], img.data[i + 1], img.data[i + 2]];
          const sx = (px - view.x + 0.5) * cell, sy = (py - view.y + 0.5) * cell;
          g.fillStyle = 0.299 * r + 0.587 * gg + 0.114 * b > 140 ? "#0b1220" : "#f8fafc";
          g.fillText(String(b), sx, sy - cell * 0.18); g.fillText(String(gg), sx, sy + 4); g.fillText(String(r), sx, sy + cell * 0.22);
        }
      }
    }
    if (hover) {
      const sx = (hover.x - view.x) * cell, sy = (hover.y - view.y) * cell;
      g.strokeStyle = "#2dd4bf"; g.lineWidth = 2; g.strokeRect(sx, sy, Math.max(cell, 3), Math.max(cell, 3));
    }
  }, [view, hover, src, img]);

  useAnimationFrame((t) => {
    const f = fps.current;
    f.frames++;
    if (t - f.last > 500) { f.v = (f.frames * 1000) / (t - f.last); f.frames = 0; f.last = t; setFps(Math.round(f.v)); }
    const c = strip.current;
    if (!c) return;
    const g = prepCanvas(c, 1400, 70);
    const offset = reduced ? 0 : ((t / 33.3) % 1) * 120;
    for (let k = -1; k < 12; k++) {
      const x = 1400 - (k * 120 + offset) - 100;
      g.drawImage(src, x, 8, 96, 54);
      g.strokeStyle = "rgba(226,232,240,0.25)"; g.strokeRect(x, 8, 96, 54);
    }
  }, true);

  const onMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const fx = (e.clientX - r.left) / r.width, fy = (e.clientY - r.top) / r.height;
    const x = Math.floor(view.x + fx * view.w), y = Math.floor(view.y + fy * view.h);
    setHover(x >= 0 && y >= 0 && x < img.width && y < img.height ? { x, y } : null);
  };
  const px = hover ? (hover.y * img.width + hover.x) * 4 : -1;
  return (
    <>
      <Header meta={meta} index={index} />
      <div className="split" style={{ marginTop: 6 }}>
        <div className="col">
          <p className="lead" style={{ fontSize: 23 }}>Bir kare, <strong>(yükseklik, genişlik, 3)</strong> boyutunda ve <strong>uint8</strong> tipinde bir sayı dizisidir. Her değer 0-255 arasındadır.</p>
          <div className="panel readout">
            <div>frame.shape = <b>({img.height}, {img.width}, 3)</b></div>
            <div>frame.dtype = <b>uint8</b></div>
            <div>frame[y, x] = {hover ? <b>[{img.data[px + 2]}, {img.data[px + 1]}, {img.data[px]}]</b> : <span className="muted">fareyi görüntüye getirin</span>} <span className="muted">(B, G, R)</span></div>
            <div>konum = {hover ? <b>x={hover.x}, y={hover.y}</b> : "—"}</div>
          </div>
          <Slider label="Yakınlaştırma" value={zoom} min={1} max={40} onChange={setZoom} format={(v) => `${v}x`} />
          <p className="note">Yeterince yakında her hücre bir pikseldir; üç sayı B, G ve R değerleridir.</p>
        </div>
        <div className="col">
          <div className="visual" style={{ flex: "none", height: H + 2 }}>
            <span className="tag">Sentetik görüntü (320×180)</span>
            <canvas ref={ref} style={{ width: W, height: H, cursor: "crosshair" }} onMouseMove={onMove} onMouseLeave={() => setHover(null)} data-no-swipe />
          </div>
        </div>
      </div>
      <div style={{ marginTop: 14 }}>
        <div className="readout" style={{ display: "flex", gap: 24, fontSize: 15 }}>
          <span>Kamera = kareler akışı · 30 FPS'te kare başına <b>33 ms</b> bütçe</span>
          <span>Bu tarayıcının çizim hızı: <b>{fpsShown} FPS</b> <span className="muted">(kamera ölçümü değildir)</span></span>
        </div>
        <canvas ref={strip} style={{ width: 1400, height: 70 }} aria-hidden />
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ 04 */
export function Renk({ meta, index }: SceneProps) {
  const img = useSceneImage();
  const ref = useRef<HTMLCanvasElement>(null);
  const [split, setSplit] = useState(false);
  const [swap, setSwap] = useState(false);
  const [color, setColor] = useState("#d9a07e");
  const [bright, setBright] = useState(100);
  const reduced = useReducedMotion();
  const anim = useRef(0);
  const layers = useMemo(() => [0, 1, 2].map((ch) => {
    const out = new ImageData(img.width, img.height);
    for (let i = 0; i < img.data.length; i += 4) { out.data[i + ch] = img.data[i + ch]; out.data[i + 3] = 255; }
    return toCanvas(out);
  }), [img]);
  const swapped = useMemo(() => {
    const out = new ImageData(img.width, img.height);
    for (let i = 0; i < img.data.length; i += 4) { out.data[i] = img.data[i + 2]; out.data[i + 1] = img.data[i + 1]; out.data[i + 2] = img.data[i]; out.data[i + 3] = 255; }
    return toCanvas(out);
  }, [img]);
  const full = useMemo(() => toCanvas(img), [img]);
  const W = 880, H = 520;
  useAnimationFrame(() => {
    const target = split ? 1 : 0;
    anim.current = reduced ? target : anim.current + (target - anim.current) * 0.15;
    const c = ref.current;
    if (!c) return;
    const g = prepCanvas(c, W, H);
    const a = anim.current;
    const iw = 560, ih = 315;
    if (a < 0.02) {
      g.drawImage(swap ? swapped : full, (W - iw) / 2, (H - ih) / 2 - 20, iw, ih);
    } else {
      g.globalCompositeOperation = "lighter";
      const labels = ["R (kırmızı)", "G (yeşil)", "B (mavi)"];
      layers.forEach((L, k) => {
        const dx = (k - 1) * 290 * a, dy = (k - 1) * 30 * a;
        const w2 = iw * (1 - 0.48 * a), h2 = ih * (1 - 0.48 * a);
        g.drawImage(L, W / 2 - w2 / 2 + dx, H / 2 - h2 / 2 - 20 + dy, w2, h2);
      });
      g.globalCompositeOperation = "source-over";
      g.fillStyle = "#9aa7b8"; g.font = "16px JetBrains Mono"; g.textAlign = "center";
      labels.forEach((l, k) => a > 0.9 && g.fillText(l, W / 2 + (k - 1) * 290, H / 2 + 130 + (k - 1) * 30));
    }
    g.textAlign = "left"; g.fillStyle = "#64748b"; g.font = "15px JetBrains Mono";
    g.fillText(swap ? "Kanallar ters: BGR dizi RGB sanılarak gösterildi" : "Doğru sıra", 16, H - 16);
  }, true);

  const rgb = useMemo(() => {
    const n = parseInt(color.slice(1), 16);
    const k = bright / 100;
    return [((n >> 16) & 255) * k, ((n >> 8) & 255) * k, (n & 255) * k].map((v) => Math.min(255, Math.round(v)));
  }, [color, bright]);
  const hsv = rgbToHsvOpenCV(rgb[0], rgb[1], rgb[2]);
  const lab = rgbToLab(rgb[0], rgb[1], rgb[2]);
  return (
    <>
      <Header meta={meta} index={index} />
      <div className="split" style={{ marginTop: 6 }}>
        <div className="col">
          <div className="chips"><Toggle label="Kanalları ayır" value={split} onChange={setSplit} /><Toggle label="BGR'yi RGB sanmak" value={swap} onChange={setSwap} /></div>
          <p className="note">OpenCV kareyi B, G, R sırasıyla tutar; MediaPipe RGB bekler. Dönüşüm unutulursa ten renkleri mavimsi görünür.</p>
          <div className="panel" style={{ display: "grid", gridTemplateColumns: "84px 1fr", gap: 16, alignItems: "center" }}>
            <input type="color" value={color} onChange={(e) => setColor(e.target.value)} aria-label="Renk seç"
                   style={{ width: 84, height: 84, border: 0, background: "none", padding: 0 }} />
            <div className="readout" style={{ fontSize: 16 }}>
              <div>RGB <b>({rgb.join(", ")})</b> · BGR <b>({[...rgb].reverse().join(", ")})</b></div>
              <div>HSV (OpenCV) <b>({hsv.join(", ")})</b></div>
              <div>LAB <b>L* {lab[0].toFixed(1)}  a* {lab[1].toFixed(1)}  b* {lab[2].toFixed(1)}</b></div>
              <div className="muted">8 bit LAB: ({Math.round(lab[0] * 2.55)}, {Math.round(lab[1] + 128)}, {Math.round(lab[2] + 128)})</div>
            </div>
          </div>
          <Slider label="Parlaklık" value={bright} min={20} max={140} onChange={setBright} format={(v) => `%${v}`} />
          <p className="note">Parlaklık değişince RGB'nin üç kanalı birlikte değişir; HSV'de renk tonu (H) sabit kalır. LAB'da a* yeşil-kırmızı eksenidir ve cilt bölümünde yeniden kullanılır.</p>
        </div>
        <div className="visual" style={{ flex: "none", height: H + 2 }}>
          <span className="tag">Sentetik görüntü</span>
          <canvas ref={ref} style={{ width: W, height: H }} />
        </div>
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ 05 */
export function Roi({ meta, index }: SceneProps) {
  const img = useSceneImage();
  const ref = useRef<HTMLCanvasElement>(null);
  const [rect, setRect] = useState({ x1: 60, y1: 30, x2: 230, y2: 140 });
  const [scale, setScale] = useState(100);
  const [sigma, setSigma] = useState(0);
  const drag = useRef<{ x: number; y: number } | null>(null);
  const W = 880, H = 495;
  const processed = useMemo(() => {
    const k = scale / 100;
    const sw = Math.max(8, Math.round(img.width * k)), sh = Math.max(4, Math.round(img.height * k));
    const small = document.createElement("canvas");
    small.width = sw; small.height = sh;
    const sg = small.getContext("2d", { willReadFrequently: true })!;
    sg.imageSmoothingQuality = "high";
    sg.drawImage(toCanvas(img), 0, 0, sw, sh);
    if (sigma > 0) {
      const d = sg.getImageData(0, 0, sw, sh);
      for (let ch = 0; ch < 3; ch++) {
        const plane = new Float32Array(sw * sh);
        for (let i = 0; i < sw * sh; i++) plane[i] = d.data[i * 4 + ch];
        const b = gaussianBlur(plane, sw, sh, sigma * k);
        for (let i = 0; i < sw * sh; i++) d.data[i * 4 + ch] = b[i];
      }
      sg.putImageData(d, 0, 0);
    }
    return small;
  }, [img, scale, sigma]);
  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const g = prepCanvas(c, W, H);
    g.imageSmoothingEnabled = false;
    g.drawImage(processed, 0, 0, W, H);
    const s = W / img.width;
    g.fillStyle = "rgba(11,18,32,0.55)";
    g.fillRect(0, 0, W, rect.y1 * s); g.fillRect(0, rect.y2 * s, W, H - rect.y2 * s);
    g.fillRect(0, rect.y1 * s, rect.x1 * s, (rect.y2 - rect.y1) * s); g.fillRect(rect.x2 * s, rect.y1 * s, W - rect.x2 * s, (rect.y2 - rect.y1) * s);
    g.strokeStyle = "#2dd4bf"; g.lineWidth = 2; g.strokeRect(rect.x1 * s, rect.y1 * s, (rect.x2 - rect.x1) * s, (rect.y2 - rect.y1) * s);
  }, [processed, rect, img]);
  const toImg = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    return { x: Math.round(((e.clientX - r.left) / r.width) * img.width), y: Math.round(((e.clientY - r.top) / r.height) * img.height) };
  };
  const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));
  return (
    <>
      <Header meta={meta} index={index} />
      <div className="split" style={{ marginTop: 6 }}>
        <div className="col">
          <div className="panel"><pre className="code" style={{ fontSize: 19 }}>
            <span className="k">roi</span> = frame[<span className="n">{rect.y1}</span>:<span className="n">{rect.y2}</span>, <span className="n">{rect.x1}</span>:<span className="n">{rect.x2}</span>]{"\n"}
            <span className="c"># roi.shape = ({rect.y2 - rect.y1}, {rect.x2 - rect.x1}, 3)</span>
          </pre></div>
          <p className="note">Görüntü üzerinde sürükleyerek yeni bir ROI seçilir. ROI bir kopya değil, ana dizinin görünümüdür.</p>
          <Slider label="Ölçek (cv2.resize)" value={scale} min={5} max={100} onChange={setScale} format={(v) => `%${v} → ${Math.round(img.width * v / 100)}×${Math.round(img.height * v / 100)}`} />
          <Slider label="Gaussian bulanıklık (σ)" value={sigma} min={0} max={6} step={0.5} onChange={setSigma} format={(v) => v.toFixed(1)} />
          <p className="note">Tarayıcıda JavaScript ile benzetilmiştir; eğitimde aynı adımlar OpenCV ile yapılır.</p>
        </div>
        <div className="visual" style={{ flex: "none", height: H + 2 }}>
          <span className="tag">Sentetik görüntü (320×180)</span>
          <canvas ref={ref} style={{ width: W, height: H, cursor: "crosshair", touchAction: "none" }} data-no-swipe
                  onPointerDown={(e) => { drag.current = toImg(e); e.currentTarget.setPointerCapture(e.pointerId); }}
                  onPointerMove={(e) => {
                    if (!drag.current) return;
                    const p = toImg(e), a = drag.current;
                    if (Math.abs(p.x - a.x) > 6 && Math.abs(p.y - a.y) > 6)
                      setRect({ x1: clamp(Math.min(a.x, p.x), 0, img.width), y1: clamp(Math.min(a.y, p.y), 0, img.height),
                                x2: clamp(Math.max(a.x, p.x), 0, img.width), y2: clamp(Math.max(a.y, p.y), 0, img.height) });
                  }}
                  onPointerUp={() => { drag.current = null; }} />
        </div>
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ 06 */
function noisyShapes(w: number, h: number, noise: number): ImageData {
  const c = document.createElement("canvas");
  c.width = w; c.height = h;
  const g = c.getContext("2d")!;
  const grad = g.createLinearGradient(0, 0, w, 0);
  grad.addColorStop(0, "#202a3a"); grad.addColorStop(1, "#4a5568");
  g.fillStyle = grad; g.fillRect(0, 0, w, h);
  g.fillStyle = "#e2e8f0";
  [[40, 40, 16], [100, 70, 24], [170, 45, 12], [230, 90, 20], [70, 120, 10], [280, 40, 14]].forEach(([x, y, r]) => { g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2); g.fill(); });
  g.fillRect(150, 110, 60, 28);
  const d = g.getImageData(0, 0, w, h);
  let s = 12345;
  const rnd = () => { s = (s * 1103515245 + 12345) & 0x7fffffff; return s / 0x7fffffff; };
  for (let i = 0; i < w * h; i++) {
    const n = (rnd() - 0.5) * 2 * noise + (rnd() < noise / 400 ? 120 : 0);
    for (let ch = 0; ch < 3; ch++) d.data[i * 4 + ch] = Math.max(0, Math.min(255, d.data[i * 4 + ch] + n));
  }
  return d;
}

export function Esik({ meta, index }: SceneProps) {
  const [noise, setNoise] = useState(30);
  const [thr, setThr] = useState(128);
  const [radius, setRadius] = useState(1);
  const [sigma, setSigma] = useState(1);
  const w = 320, h = 200;
  const refs = [useRef<HTMLCanvasElement>(null), useRef<HTMLCanvasElement>(null), useRef<HTMLCanvasElement>(null)];
  const img = useMemo(() => noisyShapes(w, h, noise), [noise]);
  const gray = useMemo(() => gaussianBlur(toGray(img), w, h, sigma), [img, sigma]);
  const result = useMemo(() => {
    const bin = threshold(gray, thr);
    const cleaned = closing(opening(bin, w, h, radius), w, h, radius);
    return { bin, cleaned, comps: components(cleaned, w, h, 15), raw: components(bin, w, h, 1) };
  }, [gray, thr, radius]);
  useEffect(() => {
    const paint = (c: HTMLCanvasElement | null, fn: (d: ImageData) => void) => {
      if (!c) return;
      c.width = w; c.height = h;
      const g = c.getContext("2d")!;
      const d = g.createImageData(w, h);
      fn(d);
      g.putImageData(d, 0, 0);
    };
    paint(refs[0].current, (d) => { for (let i = 0; i < w * h; i++) { d.data[i * 4] = d.data[i * 4 + 1] = d.data[i * 4 + 2] = gray[i]; d.data[i * 4 + 3] = 255; } });
    paint(refs[1].current, (d) => { for (let i = 0; i < w * h; i++) { const v = result.bin[i] * 255; d.data[i * 4] = d.data[i * 4 + 1] = d.data[i * 4 + 2] = v; d.data[i * 4 + 3] = 255; } });
    paint(refs[2].current, (d) => { for (let i = 0; i < w * h; i++) {
      const v = result.cleaned[i] * 200, b = result.comps.border[i];
      d.data[i * 4] = b ? 45 : v; d.data[i * 4 + 1] = b ? 212 : v; d.data[i * 4 + 2] = b ? 191 : v; d.data[i * 4 + 3] = 255; } });
  }, [gray, result]); // eslint-disable-line react-hooks/exhaustive-deps
  const panes = [["1 · gri + Gaussian", `σ = ${sigma}`], ["2 · eşik", `t = ${thr} · ${result.raw.count} parça`], ["3 · açma + kapama + kontur", `${result.comps.count} kontur`]];
  return (
    <>
      <Header meta={meta} index={index} />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20, marginTop: 10 }}>
        {panes.map(([t, v], k) => (
          <div key={t} className="visual" style={{ flex: "none", height: 320, flexDirection: "column" }}>
            <canvas ref={refs[k]} style={{ width: 448, height: 280, imageRendering: "pixelated" }} />
            <div className="readout" style={{ position: "absolute", left: 12, top: 8, fontSize: 15, background: "rgba(11,18,32,.8)", padding: "2px 8px", borderRadius: 6 }}>{t} · <b>{v}</b></div>
          </div>
        ))}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr) auto", gap: 28, alignItems: "end", marginTop: 26 }}>
        <Slider label="Gürültü" value={noise} min={0} max={80} onChange={setNoise} />
        <Slider label="Bulanıklık σ" value={sigma} min={0} max={4} step={0.5} onChange={setSigma} />
        <Slider label="Eşik" value={thr} min={0} max={255} onChange={setThr} />
        <Slider label="Morfoloji yarıçapı" value={radius} min={0} max={4} onChange={setRadius} />
        <button className="btn primary" onClick={() => setThr(otsu(gray))}>Otsu eşiği</button>
      </div>
      <p className="note" style={{ marginTop: 18 }}>Sentetik görüntü; işlemler tarayıcıda JavaScript ile benzetilmiştir. Gürültü artınca sabit kuralın ne kadar çabuk bozulduğu, morfolojinin bunu ne ölçüde telafi ettiği görülür.</p>
    </>
  );
}

/* ------------------------------------------------------------------ 07 */
const PIPE = [
  { k: "cv", title: "Kamera", sub: "cv2.VideoCapture", rule: true },
  { k: "cv", title: "Küçült + BGR→RGB", sub: "cv2.resize · cv2.cvtColor", rule: true },
  { k: "mp", title: "Yüz dedektörü", sub: "BlazeFace (öğrenilmiş)", rule: false },
  { k: "mp", title: "Yüz noktaları", sub: "Face Mesh V2 · 478 nokta", rule: false },
  { k: "np", title: "Ölçüm", sub: "NumPy: oran, açı, EAR", rule: true },
  { k: "cv", title: "Çizim", sub: "cv2.line · put_text", rule: true },
];

export function Roller({ meta, index }: SceneProps) {
  const [mode, setMode] = useState<"lib" | "rule" | "learned">("lib");
  const color = (p: (typeof PIPE)[number]) => {
    if (mode === "rule") return p.rule ? "#2dd4bf" : "rgba(148,163,184,0.25)";
    if (mode === "learned") return !p.rule ? "#3b82f6" : "rgba(148,163,184,0.25)";
    return p.k === "mp" ? "#3b82f6" : p.k === "np" ? "#a78bfa" : "#2dd4bf";
  };
  return (
    <>
      <Header meta={meta} index={index}>OpenCV görüntünün <strong>nasıl</strong> işlendiğini, MediaPipe öğrenilmiş modelin <strong>ne</strong> bulduğunu gösterir.</Header>
      <div style={{ marginTop: 24 }}>
        <Seg options={[["lib", "Kütüphaneye göre"], ["rule", "Kural tabanlı adımlar"], ["learned", "Öğrenilmiş adımlar"]]} value={mode} onChange={setMode} />
      </div>
      <svg width={1408} height={230} viewBox="0 0 1408 230" style={{ marginTop: 18 }} role="img" aria-label="İşleme hattı">
        {PIPE.map((p, i) => {
          const x = i * 236;
          return (
            <g key={p.title}>
              <rect x={x} y={40} width={200} height={130} rx={12} fill="rgba(15,24,40,0.9)" stroke={color(p)} strokeWidth={2} style={{ transition: "stroke 250ms" }} />
              <rect x={x} y={40} width={200} height={6} rx={3} fill={color(p)} style={{ transition: "fill 250ms" }} />
              <text x={x + 18} y={98} fill="#eef0ea" fontFamily="Space Grotesk" fontWeight={600} fontSize={22}>{p.title}</text>
              <text x={x + 18} y={130} fill="#9aa7b8" fontFamily="JetBrains Mono" fontSize={13}>{p.sub}</text>
              {i < PIPE.length - 1 && <path d={`M${x + 204} 105 h28 m-8 -6 l8 6 l-8 6`} stroke="#64748b" strokeWidth={2} fill="none" />}
            </g>
          );
        })}
        <text x={0} y={212} fill="#64748b" fontFamily="JetBrains Mono" fontSize={14}>turkuaz: OpenCV · mavi: MediaPipe · mor: NumPy</text>
      </svg>
      <div className="split even" style={{ marginTop: 16 }}>
        <div className="panel">
          <h3>Güncel arayüz: Tasks API</h3>
          <p><span className="mono teal">mp.tasks.vision.FaceLandmarker</span> ve <span className="mono teal">HandLandmarker</span> kullanılır. Eski <span className="mono red">mp.solutions</span> arayüzü mediapipe 1.1.1'de yoktur; internetteki örneklerin çoğu bu yüzden çalışmaz.</p>
        </div>
        <div className="panel">
          <h3>Test edilen sürümler (19.10.2026)</h3>
          <p className="mono" style={{ fontSize: 16 }}>Python 3.12 · mediapipe 1.1.1 · opencv-contrib-python 4.14.0.94 · Intel Mac: mediapipe 0.10.21</p>
        </div>
      </div>
    </>
  );
}
