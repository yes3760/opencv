import { useEffect, useRef, useState } from "react";
import { CameraStage, type LiveFrame } from "../components/CameraStage";
import { Header } from "../components/Header";
import { Slider } from "../components/Control";
import { prepCanvas } from "../components/useCanvas";
import * as C from "../lib/config";
import { angleDeg, toPixels, type Pt } from "../lib/geometry";
import { classifyStatic, Debouncer, FINGERS, fingerStates, GESTURE_NAMES, GestureController, Hysteresis } from "../lib/gestures";
import { useAnimationFrame, useReducedMotion } from "../lib/motion";
import { HAND_PAIRS, syntheticHand, type Curl } from "../lib/syntheticHand";
import type { SceneProps } from "./types";

const TIPS = new Set([4, 8, 12, 16, 20]);

export function drawHand(g: CanvasRenderingContext2D, p: Pt[], s = 1, numbers = false, pinching = false) {
  g.strokeStyle = "rgba(203,213,225,0.75)"; g.lineWidth = 3 * s; g.lineCap = "round";
  g.beginPath();
  for (const [a, b] of HAND_PAIRS) { g.moveTo(p[a].x, p[a].y); g.lineTo(p[b].x, p[b].y); }
  g.stroke();
  p.forEach((q, i) => {
    g.fillStyle = TIPS.has(i) ? "#2dd4bf" : "#eef0ea";
    g.beginPath(); g.arc(q.x, q.y, (TIPS.has(i) ? 7 : 5) * s, 0, Math.PI * 2); g.fill();
    if (numbers) { g.fillStyle = "#fcd34d"; g.font = `${13 * s}px JetBrains Mono`; g.fillText(String(i), q.x + 9 * s, q.y - 7 * s); }
  });
  if (pinching) { g.strokeStyle = "#f59e0b"; g.lineWidth = 5 * s; g.beginPath(); g.moveTo(p[4].x, p[4].y); g.lineTo(p[8].x, p[8].y); g.stroke(); }
}

/* ------------------------------------------------------------------ 13 */
export function El({ meta, index }: SceneProps) {
  const ref = useRef<HTMLCanvasElement>(null);
  const [curl, setCurl] = useState<Curl>({ thumb: 0.9, index: 0, middle: 0.95, ring: 0.95, pinky: 0.95 });
  const [tilt, setTilt] = useState(0);
  const W = 620, H = 560;
  const pts = syntheticHand(curl, W / 2 + 20, H * 0.84, 190, (tilt * Math.PI) / 180);
  const states = fingerStates(pts);
  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const g = prepCanvas(c, W, H);
    drawHand(g, pts, 1.2, true);
  }); // her çizimde
  const set = (k: keyof Curl) => (v: number) => setCurl({ ...curl, [k]: v / 100 });
  const names: [keyof Curl, string][] = [["thumb", "başparmak"], ["index", "işaret"], ["middle", "orta"], ["ring", "yüzük"], ["pinky", "serçe"]];
  return (
    <>
      <Header meta={meta} index={index} />
      <div style={{ display: "grid", gridTemplateColumns: "420px 620px 1fr", gap: 34, marginTop: 4, flex: 1, minHeight: 0 }}>
        <div className="col" style={{ gap: 8 }}>
          {names.map(([k, n]) => <Slider key={k} label={`${n} bükülmesi`} value={Math.round(curl[k] * 100)} min={0} max={100} onChange={set(k)} format={(v) => `%${v}`} />)}
          <Slider label="Elin eğimi" value={tilt} min={-60} max={60} onChange={setTilt} format={(v) => `${v}°`} />
          <p className="note">El döndürüldüğünde eklem açıları değişmez; "uç eklemin üstünde mi?" kuralı ise bozulur.</p>
        </div>
        <div className="visual" style={{ flex: "none", height: H + 2 }}>
          <span className="tag">Örnek gösterim · sentetik el</span>
          <canvas ref={ref} style={{ width: W, height: H }} />
        </div>
        <div className="col">
          <div className="panel"><h3 className="teal" style={{ fontSize: 28 }}>{GESTURE_NAMES[classifyStatic(states)]}</h3><p>parmak durumlarından üretilen jest</p></div>
          <table className="grid">
            <thead><tr><th>parmak</th><th>orta eklem açısı</th><th>durum</th></tr></thead>
            <tbody>
              {Object.entries(FINGERS).map(([n, [a, b, c, d]]) => {
                const ang = n === "başparmak" ? Math.min(angleDeg(pts[a], pts[b], pts[c]), angleDeg(pts[b], pts[c], pts[d])) : angleDeg(pts[a], pts[b], pts[c]);
                const st = states[n];
                return <tr key={n}><td>{n}</td><td className="mono">{ang.toFixed(0)}°</td>
                  <td className={st === true ? "teal" : st === false ? "muted" : "amber"}>{st === true ? "açık" : st === false ? "kapalı" : "belirsiz"}</td></tr>;
              })}
            </tbody>
          </table>
          <p className="note">Açık ≥ {C.FINGER_EXTENDED_DEG}° · kapalı ≤ {C.FINGER_FOLDED_DEG}° · arası belirsiz. Nokta 0 bilek, 4 başparmak ucu, 8 işaret ucu.</p>
        </div>
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ 14 */
export function Kararlilik({ meta, index }: SceneProps) {
  const ref = useRef<HTMLCanvasElement>(null);
  const reduced = useReducedMotion();
  const [playing, setPlaying] = useState(!reduced);
  const [noise, setNoise] = useState(0.03);
  const [hesitation, setHesitation] = useState(0.5);
  const sim = useRef({ t: 0, vals: [] as number[], single: [] as number[], hyst: [] as number[], cs: 0, ch: 0,
    prevS: false, prevH: false, hy: new Hysteresis(C.PINCH_ENTER_RATIO, C.PINCH_EXIT_RATIO), db: new Debouncer<boolean>(C.GESTURE_STABLE_MS, false) });
  const [counts, setCounts] = useState({ single: 0, hyst: 0 });
  const W = 1400, H = 520, N = 360;
  const reset = () => { const s = sim.current; s.vals = []; s.single = []; s.hyst = []; s.cs = 0; s.ch = 0; s.hy.reset(); s.db.reset(false); setCounts({ single: 0, hyst: 0 }); };
  useEffect(reset, [noise, hesitation]); // eslint-disable-line react-hooks/exhaustive-deps
  const step = (dt: number) => {
    const s = sim.current;
    s.t += dt;
    const ph = (s.t / 6000) % 1;                                    // 6 saniyelik bir pinch döngüsü
    const keys = [[0, 0.6], [0.15, 0.6], [0.25, 0.3 + 0.01], [0.25 + 0.15 * hesitation, 0.29], [0.42, 0.15], [0.6, 0.15],
      [0.68, 0.31], [0.68 + 0.12 * hesitation, 0.33], [0.9, 0.6], [1, 0.6]];
    let base = 0.6;
    for (let i = 1; i < keys.length; i++) if (ph <= keys[i][0]) { const [x0, y0] = keys[i - 1], [x1, y1] = keys[i]; base = y0 + ((ph - x0) / Math.max(1e-6, x1 - x0)) * (y1 - y0); break; }
    const v = base + (Math.random() - 0.5) * 2 * noise * 1.7;
    const single = v < 0.3;
    const hyst = s.db.update(s.hy.update(v), s.t);
    if (single && !s.prevS) s.cs++;
    if (hyst && !s.prevH) s.ch++;
    s.prevS = single; s.prevH = hyst;
    s.vals.push(v); s.single.push(single ? 1 : 0); s.hyst.push(hyst ? 1 : 0);
    if (s.vals.length > N) { s.vals.shift(); s.single.shift(); s.hyst.shift(); }
    const c = ref.current;
    if (!c) return;
    const g = prepCanvas(c, W, H);
    const top = 30, ph1 = 250, x = (i: number) => 120 + (i / N) * (W - 260), y = (val: number) => top + ph1 - (val / 0.75) * ph1;
    g.font = "15px JetBrains Mono"; g.fillStyle = "#64748b"; g.fillText("pinch mesafesi", 0, top + 12);
    [[C.PINCH_ENTER_RATIO, "giriş 0,25", "#9aa7b8"], [C.PINCH_EXIT_RATIO, "çıkış 0,40", "#9aa7b8"], [0.3, "tek eşik 0,30", "#fb923c"]].forEach(([tv, lb, col]) => {
      g.strokeStyle = col as string; g.setLineDash([6, 6]); g.lineWidth = 1.2;
      g.beginPath(); g.moveTo(120, y(tv as number)); g.lineTo(W - 140, y(tv as number)); g.stroke(); g.setLineDash([]);
      g.fillStyle = col as string;
      // "tek eşik" çizgisi giriş eşiğine çok yakın; etiketi sola yazılır ki üst üste binmesin
      if (tv === 0.3) g.fillText(lb as string, 124, y(tv as number) - 6);
      else g.fillText(lb as string, W - 130, y(tv as number) + 5);
    });
    g.strokeStyle = "#3b82f6"; g.lineWidth = 2.5; g.beginPath();
    s.vals.forEach((val, i) => (i ? g.lineTo(x(i), y(val)) : g.moveTo(x(i), y(val)))); g.stroke();
    const lane = (arr: number[], y0: number, col: string, title: string, n: number) => {
      g.fillStyle = "#9aa7b8"; g.fillText(title, 0, y0 + 12); g.fillStyle = "#eef0ea"; g.fillText(`${n} komut`, 0, y0 + 34);
      g.strokeStyle = col; g.lineWidth = 2.5; g.beginPath();
      arr.forEach((v2, i) => { const yy = y0 + 46 - v2 * 40; if (i) { g.lineTo(x(i), arr[i - 1] !== v2 ? y0 + 46 - arr[i - 1] * 40 : yy); g.lineTo(x(i), yy); } else g.moveTo(x(i), yy); });
      g.stroke();
    };
    lane(s.single, 320, "#fb923c", "tek eşik", s.cs);
    lane(s.hyst, 420, "#2dd4bf", "histerezis + 120 ms", s.ch);
    if (Math.round(s.t / 16) % 10 === 0) setCounts({ single: s.cs, hyst: s.ch });
  };
  useAnimationFrame((_, dt) => step(dt), playing);
  return (
    <>
      <Header meta={meta} index={index} />
      <div className="visual" style={{ flex: "none", height: H + 2, marginTop: 4 }}>
        <span className="tag">Sentetik sinyal</span>
        <canvas ref={ref} style={{ width: W, height: H }} />
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr auto auto", gap: 30, alignItems: "end", marginTop: 18 }}>
        <Slider label="Gürültü" value={noise} min={0} max={0.08} step={0.005} onChange={setNoise} format={(v) => v.toFixed(3)} />
        <Slider label="Eşik çevresinde kararsızlık" value={hesitation} min={0} max={1} step={0.05} onChange={setHesitation} format={(v) => `%${Math.round(v * 100)}`} />
        <div className="readout">tek eşik <b>{counts.single}</b> · histerezis <b>{counts.hyst}</b></div>
        <button className="btn" onClick={() => setPlaying(!playing)}>{playing ? "Duraklat" : "Oynat"}</button>
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ 15 */
type Widget = { slider: number; dragS: boolean; box: { x: number; y: number }; dragB: boolean; off: { x: number; y: number } };

export function DemoEl({ meta, index }: SceneProps) {
  const ctrl = useRef(new GestureController());
  const ui = useRef<Widget>({ slider: 0.5, dragS: false, box: { x: 900, y: 200 }, dragB: false, off: { x: 0, y: 0 } });
  const log = useRef<string[]>([]);
  const commands = useRef(0);
  const lastUi = useRef(0);
  const [view, setView] = useState({ gesture: "belirsiz", pinch: 1, pinching: false, present: false, commands: 0, log: [] as string[], ms: 0 });
  const reset = () => { ctrl.current.reset(); ui.current.dragS = ui.current.dragB = false; };

  const render = (g: CanvasRenderingContext2D, w: number, h: number, pts: Pt[] | null, t: number, ms: number) => {
    const s = w / 1280;
    const st = ctrl.current.update(pts, t);
    const started = st.events.includes("pinch_basladi");
    for (const e of st.events) {
      if (e === "pinch_basladi") commands.current++;
      log.current = [`${(t / 1000).toFixed(1)} s  ${e}`, ...log.current].slice(0, 6);
    }
    const u = ui.current;
    const cursor = pts ? pts[8] : null;
    const sx = 140 * s, sy = h - 120 * s, sw = 560 * s;
    if (started && cursor && Math.abs(cursor.y - sy) < 60 * s && cursor.x > sx - 40 * s && cursor.x < sx + sw + 40 * s) u.dragS = true;
    if (started && cursor && !u.dragS && cursor.x > u.box.x * s && cursor.x < (u.box.x + 150) * s && cursor.y > u.box.y * s && cursor.y < (u.box.y + 150) * s) {
      u.dragB = true; u.off = { x: cursor.x / s - u.box.x, y: cursor.y / s - u.box.y };
    }
    if (!st.pinching || !cursor) { u.dragS = false; u.dragB = false; }
    if (u.dragS && cursor) u.slider = Math.max(0, Math.min(1, (cursor.x - sx) / sw));
    if (u.dragB && cursor) u.box = { x: cursor.x / s - u.off.x, y: cursor.y / s - u.off.y };
    // sürgü
    g.strokeStyle = "rgba(148,163,184,0.6)"; g.lineWidth = 6 * s; g.lineCap = "round";
    g.beginPath(); g.moveTo(sx, sy); g.lineTo(sx + sw, sy); g.stroke();
    g.strokeStyle = "#2dd4bf"; g.beginPath(); g.moveTo(sx, sy); g.lineTo(sx + sw * u.slider, sy); g.stroke();
    g.fillStyle = u.dragS ? "#2dd4bf" : "#eef0ea"; g.beginPath(); g.arc(sx + sw * u.slider, sy, (u.dragS ? 22 : 17) * s, 0, Math.PI * 2); g.fill();
    g.fillStyle = "#eef0ea"; g.font = `500 ${24 * s}px Inter`; g.fillText(`sürgü (örnek): ${Math.round(u.slider * 100)}`, sx, sy - 40 * s);
    // kutu
    g.strokeStyle = u.dragB ? "#2dd4bf" : "#3b82f6"; g.lineWidth = 4 * s;
    g.strokeRect(u.box.x * s, u.box.y * s, 150 * s, 150 * s);
    g.fillStyle = "#eef0ea"; g.fillText("sürükle", (u.box.x + 32) * s, (u.box.y + 84) * s);
    if (pts) drawHand(g, pts, s, false, st.pinching);
    if (cursor) { g.strokeStyle = st.pinching ? "#f59e0b" : "#eef0ea"; g.lineWidth = 3 * s; g.beginPath(); g.arc(cursor.x, cursor.y, 16 * s, 0, Math.PI * 2); g.stroke(); }
    const status = st.events.includes("el_kayboldu") ? "El kayboldu: durum sıfırlandı." : pts ? "1 el izleniyor" : "El bulunamadı: elinizi avuç içi kameraya dönük gösterin.";
    g.font = `500 ${24 * s}px Inter`; g.fillStyle = pts ? "#2dd4bf" : "#f59e0b"; g.fillText(status, 20 * s, h - 24 * s);
    if (t - lastUi.current > 150 || st.events.length) {
      lastUi.current = t;
      setView({ gesture: st.gesture, pinch: st.pinch, pinching: st.pinching, present: st.present, commands: commands.current, log: log.current, ms });
    }
  };

  const onLive = (f: LiveFrame) => {
    const lm = f.hand?.landmarks?.[0];
    render(f.g, f.w, f.h, lm ? toPixels(lm, f.w, f.h, true) : null, f.t, f.handMs);
  };
  // Örnek gösterim: sentetik el sürgüye gider, pinch ile sürükler, bırakır, kutuyu taşır ve kadrajdan çıkar.
  const onSample = (g: CanvasRenderingContext2D, w: number, h: number, t: number) => {
    const ph = (t % 14000) / 1000;
    const path: [number, number, number, number][] = [   // zaman (s), x, y, pinch(0/1)
      [0, 300, 450, 0], [2, 420, 600, 0], [2.6, 420, 600, 1], [4.4, 640, 600, 1], [5, 640, 600, 0],
      [6.5, 975, 275, 0], [7.1, 975, 275, 1], [9, 700, 220, 1], [9.6, 700, 220, 0], [11, 1100, 300, 0], [12, 1500, 300, 0], [14, 1500, 300, 0]];
    let k = 1;
    while (k < path.length - 1 && ph > path[k][0]) k++;
    const [t0, x0, y0, p0] = path[k - 1], [t1, x1, y1, p1] = path[k];
    const u = Math.min(1, Math.max(0, (ph - t0) / (t1 - t0)));
    const x = x0 + (x1 - x0) * u, y = y0 + (y1 - y0) * u;
    const pinch = u > 0.5 ? p1 : p0;
    const visible = x < 1330;
    const curl = { thumb: pinch ? 0.55 : 0.2, index: pinch ? 0.42 : 0.05, middle: 0.85, ring: 0.9, pinky: 0.9 };
    let pts: Pt[] | null = null;
    if (visible) {
      const raw = syntheticHand(curl, 0, 0, 170, -0.25);
      const dx = x - raw[8].x, dy = y - raw[8].y;                 // işaret ucu yol üzerinde
      pts = raw.map((p) => ({ x: p.x + dx + (Math.random() - 0.5) * 2, y: p.y + dy + (Math.random() - 0.5) * 2 }));
      if (pinch) pts[4] = { x: pts[8].x + 8, y: pts[8].y + 10 };
    }
    render(g, w, h, pts, performance.now(), 0);
  };

  return (
    <>
      <Header meta={meta} index={index} />
      <div className="split wide-left" style={{ gridTemplateColumns: "1fr 400px", marginTop: 4 }}>
        <div className="visual"><CameraStage models={["hand"]} onLive={onLive} onSample={onSample} onReset={reset}
                                             sampleLabel="sentetik el, gerçek jest mantığı" /></div>
        <div className="col">
          <div className="panel readout" style={{ fontSize: 18 }}>
            <div>jest <b>{GESTURE_NAMES[view.gesture]}</b></div>
            <div>pinch mesafesi <b>{view.pinch.toFixed(2)}</b> {view.pinching && <span className="amber">BASILI</span>}</div>
            <div>pinch komutu sayısı <b>{view.commands}</b></div>
            <div>model süresi <b>{view.ms ? `${view.ms.toFixed(1)} ms` : "—"}</b></div>
          </div>
          <svg width={400} height={70} role="img" aria-label="Pinch göstergesi">
            <rect x={0} y={22} width={380} height={12} rx={6} fill="rgba(226,232,240,0.12)" />
            <rect x={0} y={22} width={Math.min(1, view.pinch) * 380} height={12} rx={6} fill={view.pinching ? "#f59e0b" : "#2dd4bf"} />
            {[[C.PINCH_ENTER_RATIO, "giriş"], [C.PINCH_EXIT_RATIO, "çıkış"]].map(([v, l]) => (
              <g key={l as string}><line x1={(v as number) * 380} x2={(v as number) * 380} y1={14} y2={42} stroke="#eef0ea" />
                <text x={(v as number) * 380 - 16} y={60} fill="#9aa7b8" fontSize={14} fontFamily="JetBrains Mono">{l}</text></g>
            ))}
          </svg>
          <div className="panel readout" style={{ fontSize: 15, minHeight: 170 }}>
            {view.log.length ? view.log.map((l, i) => <div key={i} className={l.includes("kayboldu") ? "amber" : ""}>{l}</div>) : <span className="muted">olay günlüğü</span>}
          </div>
          <p className="note">İşletim sisteminin faresi kontrol edilmez. Sürgü ve kutu yalnızca pinch başladığı anda tutulur.</p>
        </div>
      </div>
    </>
  );
}
