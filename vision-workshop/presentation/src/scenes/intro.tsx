import { useRef, useState } from "react";
import { Header } from "../components/Header";
import { prepCanvas } from "../components/useCanvas";
import { projectFace } from "../lib/canonicalFace";
import { FACE_CONTOURS, FACE_TESSELATION } from "../lib/mediapipe";
import { useAnimationFrame, useReducedMotion } from "../lib/motion";
import { field, SUBTITLE } from "../lib/workshop";
import type { SceneProps } from "./types";

function Field({ k, label }: { k: string; label: string }) {
  const f = field(k);
  return <div><span className="muted">{label}: </span><span style={{ color: f.placeholder ? "var(--dim)" : "var(--text)" }}>{f.text}</span></div>;
}

export function Acilis({ meta, index }: SceneProps) {
  const ref = useRef<HTMLCanvasElement>(null);
  const reduced = useReducedMotion();
  const W = 700, H = 640;
  useAnimationFrame((t) => {
    const c = ref.current;
    if (!c) return;
    const g = prepCanvas(c, W, H);
    const reveal = reduced ? 1 : Math.min(1, t / 1400);
    const yaw = reduced ? -12 : Math.sin(t / 2600) * 20;
    const pts = projectFace({ yaw, pitch: reduced ? 0 : Math.sin(t / 3700) * 6, scale: 30, cx: W / 2, cy: H / 2 + 10 });
    const n = Math.floor(pts.length * reveal);
    g.strokeStyle = "rgba(148,163,184,0.16)"; g.lineWidth = 0.7;
    if (reveal >= 1) {
      g.beginPath();
      for (const c2 of FACE_TESSELATION) { g.moveTo(pts[c2.start].x, pts[c2.start].y); g.lineTo(pts[c2.end].x, pts[c2.end].y); }
      g.stroke();
      g.strokeStyle = "rgba(45,212,191,0.9)"; g.lineWidth = 1.6;
      g.beginPath();
      for (const c2 of FACE_CONTOURS) { g.moveTo(pts[c2.start].x, pts[c2.start].y); g.lineTo(pts[c2.end].x, pts[c2.end].y); }
      g.stroke();
    }
    g.fillStyle = "#93c5fd";
    for (let i = 0; i < n; i++) { g.beginPath(); g.arc(pts[i].x, pts[i].y, 1.5, 0, Math.PI * 2); g.fill(); }
    g.fillStyle = "#64748b"; g.font = "15px JetBrains Mono";
    g.fillText(`${n} / 478 nokta`, 16, H - 18);
  }, true);
  return (
    <>
      <div className="split wide-left" style={{ marginTop: 0 }}>
        <div className="col" style={{ justifyContent: "center" }}>
          <div className="kicker"><span className="num">{String(index + 1).padStart(2, "0")}</span>{meta.section}</div>
          <h1 className="title" style={{ fontSize: 86, letterSpacing: "-0.03em" }}>VISION <em>LAB</em></h1>
          <p className="lead" style={{ fontSize: 34, color: "var(--text)", marginTop: -4 }}>Kameradan Etkileşime</p>
          <p className="lead" style={{ fontSize: 24 }}>{SUBTITLE}</p>
          <div className="chips" style={{ marginTop: 18 }}>
            <span className="chip ok">yüz noktaları ve hareket izi</span>
            <span className="chip ok">el ile uygulama içi kontrol</span>
            <span className="chip ok">açıklanabilir cilt görünümü haritası</span>
          </div>
          <div className="readout" style={{ marginTop: 26, fontSize: 18 }}>
            <Field k="topluluk" label="Topluluk" /><Field k="universite" label="Üniversite" />
            <Field k="egitmen" label="Eğitmen" /><Field k="tarih" label="Tarih" /><Field k="yer" label="Yer" />
          </div>
          <p className="note" style={{ marginTop: 6 }}>Kamera gönüllüdür · görüntüler kaydedilmez · hiçbir sunucuya gönderilmez</p>
        </div>
        <div className="visual" style={{ flex: "none", height: 680 }}>
          <span className="tag">Örnek gösterim · standart yüz modeli</span>
          <canvas ref={ref} style={{ width: W, height: H }} />
        </div>
      </div>
    </>
  );
}

const STAGES = [
  { name: "Kamera", file: "01_kamera.py", out: "Kamerayı açmak, kare okumak, düzgün kapatmak", s: 1 },
  { name: "Temeller", file: "02_piksel_renk.py · 03_filtre_esik.py", out: "Görüntüyü dizi olarak okumak, kural tabanlı işleme hattı kurmak", s: 1 },
  { name: "Yüz", file: "04_yuz_tespiti.py · 05_yuz_takip.py", out: "Tespit, takip ve tanımayı ayırmak; 478 nokta ve hareket izi", s: 2 },
  { name: "Geometri", file: "06_yuz_geometrisi.py", out: "Mesafeden bağımsız ölçüm; göz, ağız, baş yönelimi ve sınırları", s: 2 },
  { name: "El", file: "07_el_noktalari.py · 08_el_jestleri.py", out: "Parmak durumları, pinch ve kararlı komut", s: 3 },
  { name: "Cilt", file: "09_cilt_bolgeleri.py · 10_cilt_analizi.py", out: "Kaliteye bağlı, açıklanabilir görünüm göstergeleri", s: 4 },
  { name: "Birleşik", file: "src/main.py", out: "Tek kamera akışında bütün modüller", s: 4 },
];

export function Rota({ meta, index }: SceneProps) {
  const [sel, setSel] = useState(0);
  const x0 = 70, x1 = 1330, y = 150;
  const xs = STAGES.map((_, i) => x0 + ((x1 - x0) * i) / (STAGES.length - 1));
  const sessions = [1, 2, 3, 4].map((s) => {
    const ids = STAGES.map((st, i) => (st.s === s ? i : -1)).filter((i) => i >= 0);
    return { s, a: xs[ids[0]] - 50, b: xs[ids[ids.length - 1]] + 50 };
  });
  return (
    <>
      <Header meta={meta} index={index}>Her aşama, <strong>examples/</strong> klasöründe tek başına çalışan bir dosyadır. Sonunda hepsi <strong>src/main.py</strong> içinde birleşir.</Header>
      <div className="visual" style={{ marginTop: 34, flex: "none", height: 330 }} data-no-swipe>
        <svg width={1400} height={330} viewBox="0 0 1400 330" role="img" aria-label="Öğrenme rotası">
          <line x1={x0} y1={y} x2={x1} y2={y} stroke="rgba(226,232,240,0.18)" strokeWidth={2} />
          <line x1={x0} y1={y} x2={xs[sel]} y2={y} stroke="url(#gr)" strokeWidth={3} style={{ transition: "all 300ms" }} />
          <defs><linearGradient id="gr" x1="0" x2="1"><stop offset="0" stopColor="#2dd4bf" /><stop offset="1" stopColor="#3b82f6" /></linearGradient></defs>
          {STAGES.map((st, i) => (
            <g key={st.name} onClick={() => setSel(i)} style={{ cursor: "pointer" }} role="button" tabIndex={0}
               onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && setSel(i)} aria-label={st.name}>
              <circle cx={xs[i]} cy={y} r={i === sel ? 17 : 11} fill={i <= sel ? "#2dd4bf" : "#0b1220"} stroke="#2dd4bf" strokeWidth={2} />
              <text x={xs[i]} y={y - 38} textAnchor="middle" fill={i === sel ? "#eef0ea" : "#9aa7b8"} fontSize={24} fontFamily="Space Grotesk" fontWeight={600}>{st.name}</text>
              <text x={xs[i]} y={y + 48} textAnchor="middle" fill="#64748b" fontSize={15} fontFamily="JetBrains Mono">{String(i + 1).padStart(2, "0")}</text>
            </g>
          ))}
          {sessions.map(({ s, a, b }) => (
            <g key={s}>
              <path d={`M${a} 252 v14 H${b} v-14`} fill="none" stroke="rgba(59,130,246,0.55)" strokeWidth={1.5} />
              <text x={(a + b) / 2} y={296} textAnchor="middle" fill="#93c5fd" fontSize={17} fontFamily="JetBrains Mono">Oturum {s} · 3 saat</text>
            </g>
          ))}
        </svg>
      </div>
      <div className="split even" style={{ marginTop: 28 }}>
        <div className="panel"><h3>{String(sel + 1).padStart(2, "0")} · {STAGES[sel].name}</h3><p>{STAGES[sel].out}</p></div>
        <div className="panel"><h3 className="mono" style={{ fontSize: 18 }}>{STAGES[sel].file}</h3>
          <p>Her oturum: 75 dk + 15 dk ara + 90 dk. Toplam 12 saatin 11 saati eğitim ve uygulamadır.</p></div>
      </div>
    </>
  );
}
