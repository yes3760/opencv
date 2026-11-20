import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useCamera } from "./lib/camera";
import { useReducedMotion } from "./lib/motion";
import { SCENES, SECTIONS } from "./scenes/meta";
import { COMPONENTS } from "./scenes";
import { CodeBlock } from "./components/CodeBlock";

const CHANNEL = "vision-lab-sunum";

function readHash(): number {
  const n = parseInt(window.location.hash.replace(/^#\/?/, ""), 10);
  return Number.isFinite(n) && n >= 1 && n <= SCENES.length ? n - 1 : 0;
}

/** Kısayollar yazı alanlarında ve form öğelerinde devre dışı kalır. */
function isTyping(target: EventTarget | null): boolean {
  const el = target as HTMLElement | null;
  if (!el) return false;
  const tag = el.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || el.isContentEditable;
}

export default function App() {
  const [index, setIndex] = useState(readHash);
  const [menu, setMenu] = useState(false);
  const [notes, setNotes] = useState(false);
  const [code, setCode] = useState(false);
  const [focus, setFocus] = useState(false);
  const [scale, setScale] = useState(1);
  const reduced = useReducedMotion();
  const camera = useCamera();
  const channel = useMemo(() => ("BroadcastChannel" in window ? new BroadcastChannel(CHANNEL) : null), []);
  const meta = SCENES[index];
  const Scene = COMPONENTS[meta.id];

  const go = useCallback((i: number) => {
    const next = Math.max(0, Math.min(SCENES.length - 1, i));
    setIndex(next);
    setCode(false);
  }, []);

  // Ekran boyutuna göre ölçek
  useEffect(() => {
    const fit = () => setScale(Math.min(window.innerWidth / 1600, window.innerHeight / 900));
    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, []);

  // Sahne değişince: adres, sunucu penceresi ve kamera
  const prevIndex = useRef(index);
  useEffect(() => {
    window.history.replaceState(null, "", `#/${index + 1}`);
    channel?.postMessage({ index });
    if (prevIndex.current !== index) camera.stop();   // kaynak yönetimi: sahneden çıkınca kamera kapanır
    prevIndex.current = index;
    document.title = `${String(index + 1).padStart(2, "0")} · ${meta.title} — VISION LAB`;
  }, [index]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!channel) return;
    channel.onmessage = (e) => { if (e.data?.request === "state") channel.postMessage({ index }); };
  }, [channel, index]);

  useEffect(() => {
    const onHash = () => setIndex(readHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  // Klavye
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (isTyping(e.target) || e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === "ArrowRight" || e.key === "PageDown") { e.preventDefault(); go(index + 1); }
      else if (e.key === "ArrowLeft" || e.key === "PageUp") { e.preventDefault(); go(index - 1); }
      else if (e.key === "Home") { e.preventDefault(); go(0); }
      else if (e.key === "End") { e.preventDefault(); go(SCENES.length - 1); }
      else if (e.key === "f" || e.key === "F") {
        const next = !focus;
        setFocus(next);
        if (next && !document.fullscreenElement) document.documentElement.requestFullscreen?.().catch(() => undefined);
        if (!next && document.fullscreenElement) document.exitFullscreen?.().catch(() => undefined);
      } else if (e.key === "Escape") {
        if (menu || notes || code) { setMenu(false); setNotes(false); setCode(false); }
        else if (focus) setFocus(false);
      } else if (e.key === "n" || e.key === "N") setNotes((v) => !v);
      else if (e.key === "m" || e.key === "M") setMenu((v) => !v);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [index, focus, menu, notes, code, go]);

  useEffect(() => {
    const onFs = () => { if (!document.fullscreenElement) setFocus(false); };
    document.addEventListener("fullscreenchange", onFs);
    return () => document.removeEventListener("fullscreenchange", onFs);
  }, []);

  // Dokunmatik kaydırma (etkileşimli tuvaller hariç)
  const touch = useRef<{ x: number; y: number; ok: boolean } | null>(null);
  const onPointerDown = (e: React.PointerEvent) => {
    const blocked = (e.target as HTMLElement).closest("[data-no-swipe], input, button, a, select");
    touch.current = e.pointerType === "touch" && !blocked ? { x: e.clientX, y: e.clientY, ok: true } : null;
  };
  const onPointerUp = (e: React.PointerEvent) => {
    const s = touch.current;
    touch.current = null;
    if (!s) return;
    const dx = e.clientX - s.x, dy = e.clientY - s.y;
    if (Math.abs(dx) > 60 && Math.abs(dy) < 60) go(index + (dx < 0 ? 1 : -1));
  };

  const openPresenter = () => {
    const url = `${window.location.pathname}?sunucu#/${index + 1}`;
    window.open(url, "vision-lab-sunucu", "width=1100,height=760");
  };

  return (
    <div className={`viewport ${reduced ? "reduced" : ""}`}>
      <div className={`stage ${focus ? "focus" : ""}`} style={{ ["--scale" as string]: scale }}
           onPointerDown={onPointerDown} onPointerUp={onPointerUp}>
        <div className="progress" aria-hidden><i style={{ width: `${((index + 1) / SCENES.length) * 100}%` }} /></div>
        <div className="topbar">
          <span className="brand">VISION <b>LAB</b></span>
          <span className="crumb">{meta.section}<span className="sep">/</span>{meta.title.split(":")[0]}</span>
          <span className="spacer" />
          <button className="btn small" onClick={() => setMenu(true)} aria-haspopup="dialog">Bölümler</button>
          <button className="btn small" aria-pressed={notes} onClick={() => setNotes(!notes)}>Notlar</button>
          <button className="btn small" onClick={openPresenter} title="Notları ayrı pencerede aç">Sunucu penceresi</button>
          <button className="btn small" aria-pressed={focus} onClick={() => { setFocus(!focus); }} title="Uygulama içi tam ekran (F)">Tam ekran</button>
          <span className="counter" aria-live="polite"><b>{String(index + 1).padStart(2, "0")}</b> / {SCENES.length}</span>
        </div>

        <main className={`scene ${reduced ? "" : "scene-anim"}`} key={meta.id} aria-label={meta.title}>
          <Scene meta={meta} index={index} />
        </main>

        <div className="bottombar">
          <button className="btn icon" onClick={() => go(index - 1)} disabled={index === 0} aria-label="Önceki sahne">←</button>
          <button className="btn icon" onClick={() => go(index + 1)} disabled={index === SCENES.length - 1} aria-label="Sonraki sahne">→</button>
          {meta.code && <button className="btn small" aria-pressed={code} onClick={() => setCode(!code)}>Kodu göster</button>}
          <span className="spacer" />
          <span className="keys"><kbd>←</kbd><kbd>→</kbd> sahne · <kbd>Home</kbd> başa · <kbd>F</kbd> tam ekran · <kbd>N</kbd> notlar · <kbd>Esc</kbd> kapat</span>
        </div>

        {meta.code && (
          <section className={`drawer ${code ? "open" : ""}`} aria-hidden={!code} aria-label="Kod">
            <div className="meta"><span>Dosya: <b>{meta.code.file}</b></span><span>Çalıştırma: <b>{meta.code.run}</b></span>
              <span className="spacer" /><button className="btn small" onClick={() => setCode(false)}>Kapat</button></div>
            <CodeBlock code={meta.code.snippet} />
          </section>
        )}

        <aside className={`notes ${notes ? "open" : ""}`} aria-hidden={!notes} aria-label="Sunucu notları">
          <div className="sub">Sunucu notu · oturum {meta.session} · ~{meta.minutes} dk</div>
          <h2>{meta.title}</h2>
          <ul>{meta.notes.map((n, i) => <li key={i}>{n}</li>)}</ul>
        </aside>

        {menu && (
          <nav className="menu" role="dialog" aria-label="Bölümler" onClick={(e) => e.target === e.currentTarget && setMenu(false)}>
            {SECTIONS.map((sec) => (
              <section key={sec}>
                <h4>{sec}</h4>
                {SCENES.map((s, i) => s.section === sec && (
                  <button key={s.id} aria-current={i === index} onClick={() => { go(i); setMenu(false); }}>
                    <span className="n">{String(i + 1).padStart(2, "0")}</span>{s.title}
                  </button>
                ))}
              </section>
            ))}
          </nav>
        )}
      </div>
    </div>
  );
}

/** Ayrı pencerede açılan sunucu görünümü: geçerli sahnenin notları, sonraki sahne ve süre. */
export function Presenter() {
  const [index, setIndex] = useState(readHash);
  const [start] = useState(() => Date.now());
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const ch = "BroadcastChannel" in window ? new BroadcastChannel(CHANNEL) : null;
    if (ch) { ch.onmessage = (e) => typeof e.data?.index === "number" && setIndex(e.data.index); ch.postMessage({ request: "state" }); }
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => { ch?.close(); clearInterval(id); };
  }, []);
  const meta = SCENES[index];
  const next = SCENES[index + 1];
  const elapsed = Math.floor((now - start) / 1000);
  return (
    <div className="presenter">
      <section>
        <div className="kicker"><span className="num">{String(index + 1).padStart(2, "0")} / {SCENES.length}</span>{meta.section} · oturum {meta.session} · ~{meta.minutes} dk</div>
        <h1>{meta.title}</h1>
        <ul>{meta.notes.map((n, i) => <li key={i}>{n}</li>)}</ul>
      </section>
      <section>
        <div className="clock">{String(Math.floor(elapsed / 60)).padStart(2, "0")}:{String(elapsed % 60).padStart(2, "0")}</div>
        <p className="note">Geçen süre (bu pencere açıldığından beri)</p>
        {next && <div className="panel" style={{ marginTop: 24 }}><h3>Sıradaki: {next.title}</h3><p>{next.notes[0]}</p></div>}
        <p className="note" style={{ marginTop: 24 }}>Bu pencere ana sunumu izler; sahneler ana pencereden değiştirilir.</p>
      </section>
    </div>
  );
}
