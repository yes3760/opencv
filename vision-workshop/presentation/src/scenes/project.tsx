import { useRef, useState } from "react";
import { CameraStage, type LiveFrame } from "../components/CameraStage";
import { Header } from "../components/Header";
import { Seg } from "../components/Control";
import { toPixels, type Pt } from "../lib/geometry";
import { GestureController } from "../lib/gestures";
import { FACE_CONTOURS } from "../lib/mediapipe";
import { syntheticHand } from "../lib/syntheticHand";
import { field } from "../lib/workshop";
import { drawHand } from "./hands";
import { sampleFace } from "./face";
import type { SceneProps } from "./types";

/* ------------------------------------------------------------------ 20 */
type Repo = { name: string; url: string; code: string; model: string; status: string; role: string; cat: "used" | "idea" | "no"; verified: string; limits: string };
const REPOS: Repo[] = [
  { name: "OpenCV", url: "https://github.com/opencv/opencv", code: "Apache-2.0", model: "Haar XML: Intel License", status: "Ç", role: "Temel görüntü işleme", cat: "used",
    verified: "Proje testleri 4.14.0.94, 4.11.0.86 ve 5.0.0.93 ile geçti.", limits: "opencv-python ile opencv-contrib-python aynı ortamda çakışır; putText Türkçe karakter çizemez." },
  { name: "MediaPipe Tasks", url: "https://github.com/google-ai-edge/mediapipe", code: "Apache-2.0", model: "Model kartları: Apache-2.0", status: "Ç", role: "Yüz ve el modelleri", cat: "used",
    verified: "Aynı kod 1.1.1 ve 0.10.21 ile çalıştı; M4'te yüz 5,9 ms, el 5,4 ms.", limits: "mp.solutions 1.1.1'de yok; Intel Mac için son paket 0.10.21." },
  { name: "Selfie Multiclass", url: "https://developers.google.com/edge/mediapipe/solutions/vision/image_segmenter", code: "Apache-2.0", model: "Apache-2.0; veri yayımlanmamış", status: "Ç", role: "Seviye 2 segmentasyon", cat: "used",
    verified: "Örnek portrelerde saç ve yüz cildi ayrıldı; analiz 37 ms.", limits: "Piksel düzeyinde kusursuz değil; cilt durumu hakkında bilgi vermez." },
  { name: "mediapipe-samples", url: "https://github.com/google-ai-edge/mediapipe-samples", code: "Apache-2.0", model: "Görsel lisansı belirtilmemiş", status: "K", role: "API başvurusu", cat: "idea",
    verified: "Python not defterleri Tasks API kullanıyor.", limits: "Raspberry Pi el örneği mp.solutions kullanıyor; 1.1.1'de çalışmaz." },
  { name: "OpenCV Zoo YuNet", url: "https://github.com/opencv/opencv_zoo", code: "Apache-2.0", model: "Model: MIT", status: "B", role: "Alternatif dedektör", cat: "idea",
    verified: "README: WIDER Face AP 0,88 / 0,87 / 0,75.", limits: "Kutu ve 5 nokta verir; 478 nokta yok." },
  { name: "cvzone", url: "https://github.com/cvzone/cvzone", code: "MIT", model: "MediaPipe modelleri", status: "K", role: "Kullanılmadı", cat: "no",
    verified: "HandTrackingModule mp.solutions.hands kullanıyor.", limits: "Son güncelleme 10.05.2024; güncel MediaPipe ile uyumsuz." },
  { name: "skin-scan", url: "https://github.com/DurtyDhiana/skin-scan", code: "MIT", model: "Ağırlık yok", status: "K", role: "Yöntem fikri", cat: "idea",
    verified: "LAB a*, HSV parlama, Laplace haritaları kodda var.", limits: "Eski API; 'hydration', 'pores' gibi adlar biyolojik ölçüm çağrıştırıyor; maske göz ve ağzı içeriyor." },
  { name: "VitalGaze", url: "https://github.com/Corerishi/VitalGaze", code: "Lisans yok", model: "Kaynağı belirsiz pickle", status: "K", role: "Kullanılmadı", cat: "no",
    verified: "'Kızarıklık' HSV doygunluk ortalaması; sarhoşluk kararı iki eşikten.", limits: "Bilimsel ve etik açıdan uygun değil; pickle güvenlik riski." },
  { name: "acne-lds", url: "https://github.com/openface-io/acne-lds", code: "MIT", model: "Ağırlık: belirsiz; ACNE04: akademik", status: "K · D", role: "İleri aşama tartışma", cat: "no",
    verified: "Çıktı: 4 dereceli sınıf ve lezyon sayısı dağılımı; kutu yok.", limits: "torch 1.10.1 sabit; klinik fotoğraf - web kamerası alan farkı; ağırlıklar indirilmedi." },
];
const STATUS: Record<string, string> = { "Ç": "yerel olarak çalıştırıldı", "K": "kaynak kodu incelendi", "B": "yalnızca dokümantasyon", "D": "doğrulanamadı" };

export function Karsilastirma({ meta, index }: SceneProps) {
  const [filter, setFilter] = useState<"all" | "used" | "idea" | "no">("all");
  const [sel, setSel] = useState(1);
  const rows = REPOS.map((r, i) => ({ r, i })).filter(({ r }) => filter === "all" || r.cat === filter);
  const s = REPOS[sel];
  return (
    <>
      <Header meta={meta} index={index} />
      <div style={{ display: "flex", gap: 16, alignItems: "center", marginTop: 2 }}>
        <Seg options={[["all", "Tümü"], ["used", "Kullanılan"], ["idea", "Fikir / başvuru"], ["no", "Kullanılmayan"]]} value={filter} onChange={setFilter} />
        <span className="note">Kontrol tarihi: 19.10.2026</span>
      </div>
      <div className="split wide-left" style={{ gridTemplateColumns: "1fr 460px", marginTop: 16 }}>
        <table className="grid" style={{ fontSize: 17 }}>
          <thead><tr><th>Proje</th><th>Kod lisansı</th><th>Model / veri</th><th>Durum</th><th>Rol</th></tr></thead>
          <tbody>{rows.map(({ r, i }) => (
            <tr key={r.name} className={`clickable ${i === sel ? "sel" : ""}`} onClick={() => setSel(i)} tabIndex={0} onKeyDown={(e) => e.key === "Enter" && setSel(i)}>
              <td style={{ fontWeight: 600 }}>{r.name}</td><td className="mono" style={{ fontSize: 14 }}>{r.code}</td><td style={{ fontSize: 15, color: "var(--muted)" }}>{r.model}</td>
              <td><span className={`chip ${r.status.startsWith("Ç") ? "ok" : r.status.includes("D") ? "warn" : ""}`}>{r.status}</span></td>
              <td className={r.cat === "used" ? "teal" : r.cat === "no" ? "muted" : ""}>{r.role}</td>
            </tr>
          ))}</tbody>
        </table>
        <div className="col">
          <div className="panel">
            <h3>{s.name}</h3>
            <p className="mono" style={{ fontSize: 14, wordBreak: "break-all" }}>{s.url}</p>
            <p style={{ marginTop: 12 }}><span className="teal">Doğrulanan:</span> {s.verified}</p>
            <p style={{ marginTop: 10 }}><span className="amber">Sınırlamalar:</span> {s.limits}</p>
            <p style={{ marginTop: 10 }} className="note">Durum: {s.status.split(" · ").map((k) => STATUS[k]).join(", ")}</p>
          </div>
          <p className="note">Kod, model ağırlığı ve veri kümesi lisansları ayrı değerlendirilmiştir. Herkese açık bir depo serbest kullanım izni anlamına gelmez. Yıldız sayısı kalite ölçütü olarak kullanılmamıştır.</p>
        </div>
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ 21 */
const MODULES = {
  camera: { title: "camera.py", io: "Girdi: kamera numarası veya dosya · Çıktı: BGR kare", job: "Kaynağı açar, okur, with bloğundan çıkınca serbest bırakır." },
  frame: { title: "common/frame.py", io: "Girdi: BGR kare · Çıktı: Frame (640 px, RGB, mp.Image, zaman damgası)", job: "Kareyi bir kez hazırlar; bütün modüller aynı nesneyi kullanır." },
  face: { title: "face/", io: "Girdi: Frame · Çıktı: 478 nokta, kutu, iz, poz", job: "FaceLandmarker'ı bir kez yükler, VIDEO modunda çalıştırır." },
  hands: { title: "hands/", io: "Girdi: Frame · Çıktı: 21 nokta, jest, olaylar", job: "Histerezis, bekleme, soğuma; el kaybında sıfırlama." },
  skin: { title: "skin/", io: "Girdi: tam kare + yüz sonucu · Çıktı: kalite raporu, göstergeler", job: "Düşük sıklıkta, tek kare analizi; kalite yetersizse sonuç üretmez." },
  ui: { title: "main.py", io: "Girdi: modül sonuçları · Çıktı: ekran", job: "Mod seçimi, düğmeler, sürgü; önce şekil, sonra ayna, sonra yazı." },
} as const;
type ModKey = keyof typeof MODULES;

export function Mimari({ meta, index }: SceneProps) {
  const [mode, setMode] = useState<"Yüz" | "El" | "Cilt" | "Birleşik">("Birleşik");
  const [sel, setSel] = useState<ModKey>("frame");
  const active: Record<ModKey, boolean> = {
    camera: true, frame: true, ui: true,
    face: mode !== "El", hands: mode === "El" || mode === "Birleşik", skin: mode === "Cilt",
  };
  const box = (k: ModKey, x: number, y: number, w = 230, h = 110, accent = "#2dd4bf") => (
    <g onClick={() => setSel(k)} style={{ cursor: "pointer" }} role="button" tabIndex={0} onKeyDown={(e) => e.key === "Enter" && setSel(k)} aria-label={MODULES[k].title}>
      <rect x={x} y={y} width={w} height={h} rx={12} fill={sel === k ? "rgba(45,212,191,0.12)" : "rgba(15,24,40,0.95)"}
            stroke={active[k] ? accent : "rgba(148,163,184,0.25)"} strokeWidth={active[k] ? 2.5 : 1.5} style={{ transition: "all 250ms" }} />
      <text x={x + 18} y={y + 48} fill={active[k] ? "#eef0ea" : "#64748b"} fontFamily="Space Grotesk" fontSize={24} fontWeight={600}>{MODULES[k].title}</text>
      <text x={x + 18} y={y + 80} fill="#64748b" fontFamily="JetBrains Mono" fontSize={14}>{active[k] ? (k === "skin" ? "etkin · 2 kez/sn" : "etkin") : "kapalı"}</text>
    </g>
  );
  const arrow = (x1: number, y1: number, x2: number, y2: number, on: boolean) => (
    <path d={`M${x1} ${y1} L${x2} ${y2}`} stroke={on ? "#2dd4bf" : "rgba(148,163,184,0.25)"} strokeWidth={2} markerEnd="url(#ah)" fill="none" />
  );
  return (
    <>
      <Header meta={meta} index={index} />
      <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
        <Seg options={[["Yüz", "Yüz"], ["El", "El"], ["Cilt", "Cilt"], ["Birleşik", "Birleşik"]]} value={mode} onChange={setMode} />
        <span className="note">main.py'deki modlarla aynı: yalnızca gereken modüller çalışır.</span>
      </div>
      <div className="split wide-left" style={{ gridTemplateColumns: "1fr 440px", marginTop: 14 }}>
        <svg viewBox="0 0 960 470" width={960} height={470} role="img" aria-label="Birleşik mimari">
          <defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#64748b" /></marker></defs>
          {box("camera", 10, 180, 190)}
          {box("frame", 250, 180, 220)}
          {box("face", 530, 30)}{box("hands", 530, 180)}{box("skin", 530, 330, 230, 110, "#a78bfa")}
          {box("ui", 800, 180, 150)}
          {arrow(200, 235, 248, 235, true)}
          {arrow(470, 220, 528, 90, active.face)}{arrow(470, 235, 528, 235, active.hands)}{arrow(470, 250, 528, 380, active.skin)}
          {arrow(760, 85, 798, 210, active.face)}{arrow(760, 235, 798, 235, active.hands)}{arrow(760, 385, 798, 260, active.skin)}
          <text x={530} y={462} fill="#a78bfa" fontFamily="JetBrains Mono" fontSize={13}>cilt: düşük sıklık, tek kare</text>
        </svg>
        <div className="panel">
          <h3>{MODULES[sel].title}</h3>
          <p className="mono" style={{ fontSize: 15 }}>{MODULES[sel].io}</p>
          <p style={{ marginTop: 12 }}>{MODULES[sel].job}</p>
          <p className="note" style={{ marginTop: 14 }}>Eksik model yalnızca kendi modülünü kapatır; eşikler tek yerde, src/config.py içindedir.</p>
        </div>
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ 22 */
const TASKS: [string, string[]][] = [
  ["Oturum 1", ["check_setup.py --kamera 'Ortam hazır' yazdı", "Tıklanan pikselin BGR, HSV ve LAB değerleri karşılaştırıldı", "Sabit eşik ile Otsu farklı ışıkta denendi", "Adım süreleri (ms) not edildi"]],
  ["Oturum 2", ["Yüz kadrajdan çıkınca durum mesajı görüldü", "α = 0,10 ve 0,80 ile iz karşılaştırıldı", "40 ve 80 cm'de oran ölçüldü; baş 20° döndürüldü", "EAR ile eyeBlink değerleri karşılaştırıldı"]],
  ["Oturum 3", ["Sağ el deneyi yapıldı (HANDEDNESS_SWAP)", "Bir pinch = bir komut doğrulandı", "Bekleme süresi 0 yapılıp komut sayısı not edildi", "El kaybında sürgünün bırakıldığı görüldü"]],
  ["Oturum 4", ["Döndürülmüş ve karanlık karede sonuç üretilmediği görüldü", "Pencereye dönük ve yan dönük iki analiz karşılaştırıldı", "benchmark.py sonucu tabloya eklendi", "main.py ile modlar el hareketiyle değiştirildi"]],
];

function loadDone(): Record<string, boolean> {
  try { return JSON.parse(localStorage.getItem("vision-lab-gorevler") ?? "{}"); } catch { return {}; }
}

export function Gorevler({ meta, index }: SceneProps) {
  const [done, setDone] = useState<Record<string, boolean>>(loadDone);
  const toggle = (k: string) => {
    const next = { ...done, [k]: !done[k] };
    setDone(next);
    try { localStorage.setItem("vision-lab-gorevler", JSON.stringify(next)); } catch { /* saklama kapalıysa yalnızca bu oturumda */ }
  };
  return (
    <>
      <Header meta={meta} index={index}>Her deneyin amacı bir ölçümün <strong>sınırını</strong> görmektir. İşaretler yalnızca bu tarayıcıda saklanır.</Header>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 20, marginTop: 30 }}>
        {TASKS.map(([title, items]) => (
          <div key={title} className="panel">
            <h3 className="teal">{title}</h3>
            <div style={{ display: "grid", gap: 12, marginTop: 8 }}>
              {items.map((it) => {
                const k = `${title}:${it}`;
                return (
                  <label key={k} style={{ display: "flex", gap: 10, fontSize: 17, lineHeight: 1.4, color: done[k] ? "var(--dim)" : "var(--text)", cursor: "pointer" }}>
                    <input type="checkbox" checked={!!done[k]} onChange={() => toggle(k)} style={{ width: 20, height: 20, accentColor: "#2dd4bf", flex: "none", marginTop: 2 }} />
                    <span style={{ textDecoration: done[k] ? "line-through" : "none" }}>{it}</span>
                  </label>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ 23 */
const FINAL_MODES = ["Yüz", "El", "Birleşik"] as const;

export function Final({ meta, index }: SceneProps) {
  const ctrl = useRef(new GestureController());
  const mode = useRef<(typeof FINAL_MODES)[number]>("Birleşik");
  const [shown, setShown] = useState({ mode: "Birleşik", faceMs: 0, handMs: 0, clicks: 0 });
  const clicks = useRef(0);
  const lastUi = useRef(0);

  const render = (g: CanvasRenderingContext2D, w: number, _h: number, face: Pt[] | null, hand: Pt[] | null, t: number, faceMs: number, handMs: number) => {
    const s = w / 1280;
    const useHand = mode.current !== "Yüz";
    const st = ctrl.current.update(useHand ? hand : null, t);
    const cursor = useHand && hand ? hand[8] : null;
    const btns = FINAL_MODES.map((m, i) => ({ m, x: (20 + i * 190) * s, y: 20 * s, w: 170 * s, h: 64 * s }));
    const hover = cursor ? btns.find((b) => cursor.x > b.x && cursor.x < b.x + b.w && cursor.y > b.y && cursor.y < b.y + b.h) : undefined;
    if (hover && st.events.includes("pinch_basladi")) { mode.current = hover.m; clicks.current++; }
    if (face && mode.current !== "El") {
      g.strokeStyle = "#2dd4bf"; g.lineWidth = 2 * s; g.beginPath();
      for (const e of FACE_CONTOURS) { g.moveTo(face[e.start].x, face[e.start].y); g.lineTo(face[e.end].x, face[e.end].y); }
      g.stroke();
    }
    if (hand && useHand) drawHand(g, hand, s, false, st.pinching);
    for (const b of btns) {
      const on = b.m === mode.current;
      g.fillStyle = on ? "#2dd4bf" : "rgba(11,18,32,0.82)"; g.fillRect(b.x, b.y, b.w, b.h);
      g.strokeStyle = hover === b ? "#3b82f6" : "rgba(148,163,184,0.5)"; g.lineWidth = 2 * s; g.strokeRect(b.x, b.y, b.w, b.h);
      g.fillStyle = on ? "#05231f" : "#eef0ea"; g.font = `600 ${26 * s}px Space Grotesk`; g.fillText(b.m, b.x + 22 * s, b.y + 42 * s);
    }
    if (cursor) { g.strokeStyle = st.pinching ? "#f59e0b" : "#eef0ea"; g.lineWidth = 3 * s; g.beginPath(); g.arc(cursor.x, cursor.y, 16 * s, 0, Math.PI * 2); g.stroke(); }
    if (t - lastUi.current > 250) { lastUi.current = t; setShown({ mode: mode.current, faceMs, handMs, clicks: clicks.current }); }
  };
  const onLive = (f: LiveFrame) => {
    const face = f.face?.faceLandmarks?.[0] ? toPixels(f.face.faceLandmarks[0], f.w, f.h, true) : null;
    const hand = f.hand?.landmarks?.[0] ? toPixels(f.hand.landmarks[0], f.w, f.h, true) : null;
    render(f.g, f.w, f.h, face, hand, f.t, f.faceMs, f.handMs);
  };
  const onSample = (g: CanvasRenderingContext2D, w: number, h: number, t: number) => {
    const face = sampleFace(t * 0.6, w, h).pts.map((p) => ({ x: p.x * 0.8 + w * 0.12, y: p.y * 0.8 + h * 0.15 }));
    const ph = (t % 9000) / 1000;
    const target = ph < 3 ? { x: 115, y: 52 } : ph < 6 ? { x: 305, y: 52 } : { x: 495, y: 52 };   // Yüz, El, Birleşik düğmeleri
    const local = ph % 3;
    const pinch = local > 1.4 && local < 2.0;
    const x = local < 1.2 ? 700 + (target.x - 700) * (local / 1.2) : target.x;
    const y = local < 1.2 ? 520 + (target.y - 520) * (local / 1.2) : target.y;
    const raw = syntheticHand({ thumb: pinch ? 0.55 : 0.2, index: pinch ? 0.42 : 0.05, middle: 0.85, ring: 0.9, pinky: 0.9 }, 0, 0, 150, -0.2);
    const hand = raw.map((p) => ({ x: p.x + x - raw[8].x, y: p.y + y - raw[8].y }));   // işaret ucu hedefte
    if (pinch) hand[4] = { x: hand[8].x + 8, y: hand[8].y + 10 };
    render(g, w, h, face, hand, performance.now(), 0, 0);
  };
  return (
    <>
      <Header meta={meta} index={index} />
      <div className="split wide-left" style={{ gridTemplateColumns: "1fr 380px", marginTop: 4 }}>
        <div className="visual"><CameraStage models={["face", "hand"]} onLive={onLive} onSample={onSample}
                                             onReset={() => { ctrl.current.reset(); mode.current = "Birleşik"; }}
                                             sampleLabel="sentetik yüz ve el, gerçek jest mantığı" /></div>
        <div className="col">
          <div className="panel readout" style={{ fontSize: 18 }}>
            <div>mod <b>{shown.mode}</b></div>
            <div>el ile mod değişimi <b>{shown.clicks}</b></div>
            <div>yüz modeli <b>{shown.faceMs ? `${shown.faceMs.toFixed(1)} ms` : "—"}</b></div>
            <div>el modeli <b>{shown.handMs ? `${shown.handMs.toFixed(1)} ms` : "—"}</b></div>
          </div>
          <p className="lead" style={{ fontSize: 21 }}>İşaret parmağını bir düğmenin üzerine getirip <strong>pinch</strong> yapın.</p>
          <div className="panel"><h3>Python uygulaması</h3><p className="mono" style={{ fontSize: 17 }}>python src/main.py</p>
            <p style={{ marginTop: 8 }}>Cilt analizi Python uygulamasında boşluk tuşuyla, tarayıcıda 18. sahnede yapılır.</p></div>
          <p className="note">Süreler bu tarayıcıda o an ölçülür; donanıma göre değişir.</p>
        </div>
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ 24 */
export function Sonraki({ meta, index }: SceneProps) {
  const repo = field("depo_baglantisi"), contact = field("iletisim");
  return (
    <>
      <Header meta={meta} index={index} />
      <div style={{ display: "grid", gridTemplateColumns: "1.1fr 1fr 0.9fr", gap: 36, marginTop: 18 }}>
        <div className="col">
          <h3 style={{ margin: 0, fontFamily: "var(--font-display)", fontSize: 26 }}>Temel kaynaklar</h3>
          <ul className="points" style={{ fontSize: 18 }}>
            <li>OpenCV · github.com/opencv/opencv</li>
            <li>MediaPipe · github.com/google-ai-edge/mediapipe</li>
            <li>Face / Hand Landmarker belgeleri · developers.google.com/edge/mediapipe</li>
            <li>Soukupová ve Čech (2016) · göz en-boy oranı</li>
            <li>Casiez vd. (2012) · One Euro filtresi</li>
            <li>Barrett vd. (2019) · yüz hareketleri ve duygu çıkarımı</li>
          </ul>
          <p className="note">Tam kaynakça ve lisans notları öğrenci raporunun N bölümündedir.</p>
        </div>
        <div className="col">
          <h3 style={{ margin: 0, fontFamily: "var(--font-display)", fontSize: 26 }}>Sonraki adımlar</h3>
          <ul className="points" style={{ fontSize: 18 }}>
            <li>Standart ışık düzeneğiyle tekrarlanabilirlik deneyi</li>
            <li>One Euro parametrelerini gecikme ve titreme ölçerek ayarlamak</li>
            <li>El ile çizilen şekli konturlarla tanımak</li>
            <li>Tarayıcı ve Python sonuçlarını aynı videoda karşılaştırmak</li>
          </ul>
        </div>
        <div className="col">
          <div className="panel">
            <h3>İletişim</h3>
            <p style={{ color: contact.placeholder ? "var(--dim)" : "var(--text)" }}>{contact.text}</p>
            <h3 style={{ marginTop: 16 }}>Proje deposu</h3>
            <p className="mono" style={{ fontSize: 15, color: repo.placeholder ? "var(--dim)" : "var(--text)", wordBreak: "break-all" }}>{repo.text}</p>
          </div>
          <div className="disclaimer">Cilt bölümü eğitim amaçlı görüntü analizidir; tıbbi tanı değildir.</div>
        </div>
      </div>
    </>
  );
}
