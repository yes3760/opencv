/* SEIS OpenCV Atölyesi — Linear 21-Slide Keynote Engine + Interactive Lab & Built-in Quiz */

const slides = [...document.querySelectorAll('.slide')];
const progressBar = document.getElementById('progressBar');
const dockCounter = document.getElementById('dockCounter');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const toastEl = document.getElementById('toast');

let currentSlide = 0;

function showToast(msg) {
  toastEl.textContent = msg;
  toastEl.classList.add('show');
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => toastEl.classList.remove('show'), 1800);
}

/* Keynote Auto-Fit Engine: Guarantees ZERO vertical scrolling on every viewport */
function fitActiveSlide() {
  const active = slides[currentSlide];
  if (!active) return;
  const inner = active.querySelector('.slide-inner');
  if (!inner) return;
  inner.style.transform = 'scale(1)';
  const availH = window.innerHeight - 122;
  const availW = window.innerWidth - 44;
  const scale = Math.min(1, availH / Math.max(inner.scrollHeight, 1), availW / Math.max(inner.scrollWidth, 1));
  if (scale < 0.995) {
    inner.style.transform = `scale(${Math.max(0.58, scale).toFixed(4)})`;
  }
}

window.addEventListener('resize', () => requestAnimationFrame(fitActiveSlide));

function goToSlide(idx) {
  const target = Math.max(0, Math.min(slides.length - 1, idx));
  slides.forEach((s, i) => {
    s.classList.remove('active', 'prev-out');
    if (i < target) s.classList.add('prev-out');
    if (i === target) s.classList.add('active');
  });

  currentSlide = target;
  progressBar.style.width = `${((target + 1) / slides.length) * 100}%`;
  dockCounter.textContent = `${String(target + 1).padStart(2, '0')} / ${slides.length}`;
  prevBtn.disabled = target === 0;
  nextBtn.disabled = target === slides.length - 1;
  history.replaceState(null, '', `#${target + 1}`);
  requestAnimationFrame(fitActiveSlide);
}

prevBtn.addEventListener('click', () => goToSlide(currentSlide - 1));
nextBtn.addEventListener('click', () => goToSlide(currentSlide + 1));
document.getElementById('brandHome').addEventListener('click', () => goToSlide(0));

document.getElementById('fsBtn').addEventListener('click', () => {
  if (!document.fullscreenElement) document.documentElement.requestFullscreen().catch(() => {});
  else document.exitFullscreen().catch(() => {});
});

/* Mini Terimler Sözlüğü (Her slayttan tek tıkla açılır) */
const GLOSSARY = [
  ['BGR / RGB', 'Görüntüdeki 3 renk kanalı. OpenCV Mavi-Yeşil-Kırmızı (BGR) okur; yapay zekâ modelleri genelde RGB bekler.'],
  ['HSV', 'Renk tonunu (H) parlaklıktan (V) ayıran renk uzayı. Işık değişse de renkli nesne takibinde şaşmaz.'],
  ['LAB & ΔE', 'İnsan gözüne yakın renk uzayı. a* yeşil–kırmızı dengesini, ΔE ise iki renk arasındaki sayısal farkı ölçer.'],
  ['ROI (İlgi Bölgesi)', 'Tüm ekranı değil, sadece seçtiğimiz küçük kareyi kesip işlemek (hız kazandırır).'],
  ['Gaussian Blur', 'Görüntüyü hafifçe yumuşatarak kamera sensör gürültüsünü (karıncalanmayı) temizler.'],
  ['Otsu Eşikleme', 'Siyah-beyaz ayırma sınırını elle tahmin etmek yerine ışığa göre bilgisayara otomatik seçtirmek.'],
  ['Morfoloji', 'Siyah-beyaz görüntü temizliği: Açma küçük beyaz noktaları siler, Kapama küçük delikleri doldurur.'],
  ['Kontur', 'Siyah-beyaz görüntüdeki beyaz şekillerin dış sınır çizgisi (alan ve köşe ölçümünde kullanılır).'],
  ['FPS', 'Saniyede ekrana çizilen kare sayısı. 30 FPS için her kareye yaklaşık 33 milisaniye bütçe düşer.'],
  ['Landmark', 'Yapay zekânın yüz (478) veya elde (21) işaretlediği kilit koordinat noktaları.'],
  ['EMA (Yumuşatma)', 'Titrek kamera noktasını bir önceki konumuyla karıştırıp yağ gibi akıcı hale getiren ortalama.'],
  ['EAR', 'Göz en-boy oranı (dikey açıklık / yatay genişlik). Göz kapanınca 0’a yaklaşır; mesafeden bağımsızdır.'],
  ['Blendshape', 'Yapay zekânın “sol göz ne kadar kapalı?” gibi mimiklere 0–1 arasında verdiği hazır skor.'],
  ['Yaw / Pitch / Roll', 'Başın 3 dönüş açısı: Yaw sağa-sola, Pitch yukarı-aşağı, Roll omza yatırma.'],
  ['Histerezis', 'Kombi termostatı gibi çift eşik (0.25 tut / 0.40 bırak): parmak titreyince sahte komut üretilmesini önler.'],
  ['Debounce / Cooldown', 'Debounce (120 ms) anlık dokunmayı eler; Cooldown (700 ms) üst üste yanlışlıkla çift komutu engeller.']
];

document.getElementById('glossaryBtn')?.addEventListener('click', () => {
  const lb = document.getElementById('lightbox');
  const body = document.getElementById('lightboxBody');
  if (!lb || !body) return;
  body.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
      <strong style="color:var(--mint); font-family:'Syne',sans-serif; font-size:1.15rem;">📖 OpenCV Atölyesi — Sade Türkçe Terimler Sözlüğü</strong>
      <button class="copy-btn" onclick="document.getElementById('lightbox').classList.remove('open')">✕ Kapat (ESC)</button>
    </div>
    <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:10px;">
      ${GLOSSARY.map(([k, v]) => `
        <div style="padding:11px 13px; border-radius:12px; background:rgba(46,11,28,0.65); border:1px solid var(--border);">
          <div style="color:var(--mint); font-family:'JetBrains Mono',monospace; font-size:0.82rem; font-weight:700; margin-bottom:4px;">${k}</div>
          <div style="color:var(--cream-soft); font-size:0.82rem; line-height:1.45;">${v}</div>
        </div>
      `).join('')}
    </div>
  `;
  lb.classList.add('open');
});

/* Keyboard & Touch Swipe Navigation (Global across entire deck!) */
window.addEventListener('keydown', e => {
  if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
  if (e.key === 'Escape') {
    const lb = document.getElementById('lightbox');
    if (lb) lb.classList.remove('open');
    return;
  }
  if (e.key.toLowerCase() === 'f') {
    if (!document.fullscreenElement) document.documentElement.requestFullscreen().catch(() => {});
    else document.exitFullscreen().catch(() => {});
    return;
  }
  if (document.getElementById('lightbox')?.classList.contains('open')) return;
  if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') {
    e.preventDefault(); goToSlide(currentSlide + 1);
  } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
    e.preventDefault(); goToSlide(currentSlide - 1);
  } else if (e.key === 'Home') {
    e.preventDefault(); goToSlide(0);
  } else if (e.key === 'End') {
    e.preventDefault(); goToSlide(slides.length - 1);
  }
});

let touchX = 0;
window.addEventListener('touchstart', e => { touchX = e.changedTouches[0].screenX; }, { passive: true });
window.addEventListener('touchend', e => {
  const dx = e.changedTouches[0].screenX - touchX;
  if (Math.abs(dx) > 60) goToSlide(currentSlide + (dx < 0 ? 1 : -1));
}, { passive: true });

/* Startup */
const initHash = parseInt(location.hash.replace('#', ''), 10);
if (!isNaN(initHash) && initHash >= 1 && initHash <= slides.length) goToSlide(initHash - 1);
else goToSlide(0);
window.addEventListener('load', () => { fitActiveSlide(); setTimeout(fitActiveSlide, 300); });

/* Copy, Full-Code Copy, .py Download & Lightbox */
function copyText(text, btn) {
  navigator.clipboard.writeText(text.trim()).then(() => {
    if (btn) {
      const old = btn.textContent;
      btn.textContent = '✓ Kopyalandı';
      setTimeout(() => { btn.textContent = old; }, 1400);
    }
    showToast('Panoya kopyalandı!');
  }).catch(() => showToast('Kopyalama için metni seçebilirsiniz.'));
}

document.querySelectorAll('[data-copy]').forEach(btn => {
  btn.addEventListener('click', () => {
    const sel = btn.dataset.copy;
    const raw = sel.startsWith('#') ? document.querySelector(sel).innerText.trim() + '\n' : sel;
    navigator.clipboard.writeText(raw).then(() => {
      const old = btn.textContent;
      btn.textContent = '✓ Kopyalandı';
      setTimeout(() => { btn.textContent = old; }, 1400);
      showToast('Panoya kopyalandı!');
    }).catch(() => copyText(raw, btn));
  });
});

document.querySelectorAll('[data-copy-full]').forEach(btn => {
  btn.addEventListener('click', () => {
    const code = window.WORKSHOP_CODES?.[btn.dataset.copyFull];
    if (code) copyText(code, btn);
  });
});

document.querySelectorAll('[data-download-py]').forEach(btn => {
  btn.addEventListener('click', () => {
    const file = btn.dataset.downloadPy;
    const code = window.WORKSHOP_CODES?.[file];
    if (!code) return;
    const blob = new Blob([code], { type: 'text/x-python;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = file;
    a.click();
    URL.revokeObjectURL(a.href);
    showToast(`${file} indirildi!`);
  });
});

const lightbox = document.getElementById('lightbox');
const lightboxBody = document.getElementById('lightboxBody');
if (lightbox) {
  lightbox.addEventListener('click', e => { if (e.target === lightbox) lightbox.classList.remove('open'); });

  document.querySelectorAll('.guide-fig').forEach(fig => {
    fig.addEventListener('click', () => {
      const img = fig.querySelector('img');
      if (!img) return;
      lightboxBody.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
          <strong style="color:var(--mint); font-family:'JetBrains Mono',monospace; font-size:0.86rem;">${img.alt}</strong>
          <button class="copy-btn" onclick="document.getElementById('lightbox').classList.remove('open')">✕ Kapat (ESC)</button>
        </div>
        <img src="${img.src}" alt="${img.alt}" />
      `;
      lightbox.classList.add('open');
    });
  });

  document.querySelectorAll('[data-view-full]').forEach(btn => {
    btn.addEventListener('click', () => {
      const file = btn.dataset.viewFull;
      const code = window.WORKSHOP_CODES?.[file];
      if (!code) return;
      const esc = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      lightboxBody.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:12px;">
          <strong style="color:var(--mint); font-family:'JetBrains Mono',monospace; font-size:0.9rem;">examples/${file} — Tam Çalışan Kod</strong>
          <div style="display:flex; gap:8px;">
            <button class="copy-btn" id="lbCopyBtn">📋 Tam Kodu Kopyala</button>
            <button class="copy-btn" onclick="document.getElementById('lightbox').classList.remove('open')">✕ Kapat</button>
          </div>
        </div>
        <pre class="code-pre" style="max-height:74vh; border:1px solid var(--border); border-radius:12px; background:#0b0206;">${esc}</pre>
      `;
      lightbox.classList.add('open');
      document.getElementById('lbCopyBtn').addEventListener('click', function () { copyText(code, this); });
    });
  });
}

/* Poster 3D Tilt */
const posterFrame = document.getElementById('posterFrame');
if (posterFrame) {
  posterFrame.addEventListener('mousemove', e => {
    const r = posterFrame.getBoundingClientRect();
    const rx = ((e.clientY - r.top) / r.height - 0.5) * -10;
    const ry = ((e.clientX - r.left) / r.width - 0.5) * 10;
    posterFrame.style.transform = `rotateX(${rx}deg) rotateY(${ry}deg) scale(1.02)`;
  });
  posterFrame.addEventListener('mouseleave', () => {
    posterFrame.style.transform = 'rotateX(0) rotateY(0) scale(1)';
  });
}

/* 12x12 Eye Pixel Matrix (Slide 3) */
(function initPixelMatrix() {
  const grid = document.getElementById('pxGrid');
  const info = document.getElementById('pxInfo');
  if (!grid) return;
  const pal = {
    '0': [36, 9, 22], '1': [212, 142, 110], '2': [242, 234, 226],
    '3': [134, 82, 46], '4': [20, 14, 16], '5': [108, 232, 170]
  };
  const pat = [
    '000011110000', '001111111100', '011111111150', '111222222111',
    '112233332211', '122334433221', '122334433221', '112233332211',
    '111222222111', '015111111510', '001111511100', '000011110000'
  ];
  pat.forEach((row, y) => {
    [...row].forEach((ch, x) => {
      const [r, g, b] = pal[ch];
      const cell = document.createElement('div');
      cell.className = 'px-cell';
      cell.style.background = `rgb(${r},${g},${b})`;
      cell.addEventListener('mouseenter', () => {
        const gray = Math.round(0.299 * r + 0.587 * g + 0.114 * b);
        info.innerHTML = `<span style="color:var(--mint)">frame[${y}, ${x}]</span> → BGR: <strong>[${b}, ${g}, ${r}]</strong> &nbsp;|&nbsp; RGB: [${r}, ${g}, ${b}] &nbsp;|&nbsp; Gri: <strong>${gray}</strong>`;
      });
      grid.appendChild(cell);
    });
  });
})();

/* Real Pixel-Level Canvas Vision Lab (Slide 4) */
(function initVisionLab() {
  const canvas = document.getElementById('labCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  const W = 480, H = 300;
  canvas.width = W; canvas.height = H;
  const off = document.createElement('canvas');
  off.width = W; off.height = H;
  const octx = off.getContext('2d', { willReadFrequently: true });

  const bg = octx.createRadialGradient(W * 0.5, H * 0.52, 20, W * 0.5, H * 0.52, 270);
  bg.addColorStop(0, '#5a1735'); bg.addColorStop(1, '#1c0410');
  octx.fillStyle = bg; octx.fillRect(0, 0, W, H);
  octx.beginPath();
  octx.moveTo(65, 190); octx.bezierCurveTo(95, 70, 260, 52, 415, 115);
  octx.bezierCurveTo(430, 195, 360, 268, 225, 255); octx.bezierCurveTo(135, 265, 80, 240, 65, 190);
  const skin = octx.createRadialGradient(240, 158, 25, 240, 158, 190);
  skin.addColorStop(0, '#e8a888'); skin.addColorStop(0.6, '#c77c5e'); skin.addColorStop(1, '#854534');
  octx.fillStyle = skin; octx.fill();
  octx.beginPath(); octx.moveTo(118, 116); octx.quadraticCurveTo(240, 74, 368, 108);
  octx.lineWidth = 14; octx.lineCap = 'round'; octx.strokeStyle = '#3c1e16'; octx.stroke();
  octx.beginPath(); octx.moveTo(132, 165); octx.quadraticCurveTo(240, 104, 348, 165); octx.quadraticCurveTo(240, 220, 132, 165);
  const sc = octx.createRadialGradient(240, 162, 12, 240, 162, 115);
  sc.addColorStop(0, '#f7f1ec'); sc.addColorStop(0.8, '#dfd0c8'); sc.addColorStop(1, '#b69084');
  octx.fillStyle = sc; octx.fill(); octx.lineWidth = 3.5; octx.strokeStyle = '#2d1210'; octx.stroke();
  const iris = octx.createRadialGradient(240, 163, 10, 240, 163, 44);
  iris.addColorStop(0, '#a3642e'); iris.addColorStop(0.55, '#6e4526'); iris.addColorStop(1, '#2a1a12');
  octx.beginPath(); octx.arc(240, 163, 42, 0, Math.PI * 2); octx.fillStyle = iris; octx.fill();
  octx.beginPath(); octx.arc(240, 163, 17, 0, Math.PI * 2); octx.fillStyle = '#0d090a'; octx.fill();
  octx.beginPath(); octx.arc(226, 149, 7, 0, Math.PI * 2); octx.fillStyle = 'rgba(255,255,255,0.88)'; octx.fill();
  const baseData = octx.getImageData(0, 0, W, H);

  let mode = 'original', param = 95;
  let camStream = null, camVideo = null, camRaf = null;
  const badge = document.getElementById('labBadge');
  const codeEl = document.getElementById('labCode');
  const slider = document.getElementById('labSlider');
  const sliderVal = document.getElementById('labSliderVal');
  const sliderLabel = document.getElementById('labSliderLabel');
  const camBtn = document.getElementById('labCamBtn');

  const SNIPPETS = {
    original: () => `<span class="kw">import</span> cv2\ncap = cv2.<span class="fn">VideoCapture</span>(<span class="num">0</span>)\nok, frame = cap.<span class="fn">read</span>()\nframe = cv2.<span class="fn">flip</span>(frame, <span class="num">1</span>)`,
    gray: () => `gray = cv2.<span class="fn">cvtColor</span>(frame, cv2.COLOR_BGR2GRAY)\n<span class="fn">print</span>(gray.shape)  <span class="cm"># 3 kanal -> 1 kanal</span>`,
    blur: v => { const k = Math.max(1, Math.floor(v / 18) * 2 + 1); return `blurred = cv2.<span class="fn">GaussianBlur</span>(frame, (<span class="num">${k}</span>, <span class="num">${k}</span>), <span class="num">0</span>)`; },
    canny: v => `edges = cv2.<span class="fn">Canny</span>(gray, <span class="num">${v}</span>, <span class="num">${Math.min(255, v * 2)}</span>)`,
    otsu: v => `_, binary = cv2.<span class="fn">threshold</span>(gray, <span class="num">${v}</span>, <span class="num">255</span>, cv2.THRESH_BINARY)`,
    mesh: () => `rgb = cv2.<span class="fn">cvtColor</span>(frame, cv2.COLOR_BGR2RGB)\nres = face_landmarker.<span class="fn">detect</span>(mp_image)\near = <span class="fn">eye_aspect_ratio</span>(res.face_landmarks[<span class="num">0</span>])`
  };

  function getSourcePixels() {
    if (camVideo && camVideo.readyState >= 2) {
      octx.save();
      octx.translate(W, 0);
      octx.scale(-1, 1);
      octx.drawImage(camVideo, 0, 0, W, H);
      octx.restore();
      return octx.getImageData(0, 0, W, H).data;
    }
    return baseData.data;
  }

  function render() {
    const src = getSourcePixels(), out = ctx.createImageData(W, H), dst = out.data;
    if (mode === 'original' || mode === 'mesh') { dst.set(src); ctx.putImageData(out, 0, 0); }
    else if (mode === 'gray') {
      for (let i = 0; i < src.length; i += 4) { const g = 0.299 * src[i] + 0.587 * src[i + 1] + 0.114 * src[i + 2]; dst[i] = dst[i + 1] = dst[i + 2] = g; dst[i + 3] = 255; }
      ctx.putImageData(out, 0, 0);
    } else if (mode === 'otsu') {
      for (let i = 0; i < src.length; i += 4) { const g = 0.299 * src[i] + 0.587 * src[i + 1] + 0.114 * src[i + 2]; const v = g >= param ? 255 : 0; dst[i] = dst[i + 1] = dst[i + 2] = v; dst[i + 3] = 255; }
      ctx.putImageData(out, 0, 0);
    } else if (mode === 'blur') {
      ctx.save(); ctx.filter = `blur(${(param / 26).toFixed(1)}px)`; ctx.drawImage(off, 0, 0); ctx.restore();
    } else if (mode === 'canny') {
      const gray = new Float32Array(W * H);
      for (let i = 0, p = 0; i < src.length; i += 4, p++) gray[p] = 0.299 * src[i] + 0.587 * src[i + 1] + 0.114 * src[i + 2];
      for (let y = 1; y < H - 1; y++) for (let x = 1; x < W - 1; x++) {
        const i = y * W + x;
        const gx = -gray[i - W - 1] + gray[i - W + 1] - 2 * gray[i - 1] + 2 * gray[i + 1] - gray[i + W - 1] + gray[i + W + 1];
        const gy = -gray[i - W - 1] - 2 * gray[i - W] - gray[i - W + 1] + gray[i + W - 1] + 2 * gray[i + W] + gray[i + W + 1];
        const on = Math.hypot(gx, gy) > param * 0.9, idx = i * 4;
        dst[idx] = on ? 108 : 16; dst[idx + 1] = on ? 232 : 4; dst[idx + 2] = on ? 170 : 10; dst[idx + 3] = 255;
      }
      ctx.putImageData(out, 0, 0);
    }
    if (mode === 'mesh' && !camStream) {
      ctx.save(); ctx.strokeStyle = '#6ce8aa'; ctx.lineWidth = 1.6;
      const pts = [[132, 165], [185, 134], [240, 124], [295, 134], [348, 165], [295, 194], [240, 202], [185, 194]];
      ctx.beginPath(); pts.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath(); ctx.stroke();
      pts.forEach(([x, y]) => { ctx.beginPath(); ctx.arc(x, y, 3.6, 0, Math.PI * 2); ctx.fillStyle = '#6ce8aa'; ctx.fill(); });
      ctx.strokeStyle = 'rgba(235,161,130,0.85)'; ctx.setLineDash([6, 5]); ctx.strokeRect(102, 74, 290, 182); ctx.restore();
    }
    badge.textContent = `${camStream ? 'LIVE CAM' : 'CV2'}::${mode.toUpperCase()} · param=${param}`;
    codeEl.innerHTML = SNIPPETS[mode](param);
    sliderVal.textContent = param;
    sliderLabel.textContent = mode === 'blur' ? 'Bulanıklık:' : mode === 'canny' ? 'Kenar Eşiği:' : mode === 'otsu' ? 'Eşik Değeri:' : 'Parametre:';
  }

  function stopLabCam() {
    if (camRaf) { cancelAnimationFrame(camRaf); camRaf = null; }
    if (camStream) { camStream.getTracks().forEach(t => t.stop()); camStream = null; }
    camVideo = null;
    if (camBtn) { camBtn.textContent = '📷 Canlı Kameram'; camBtn.classList.remove('active'); }
    octx.putImageData(baseData, 0, 0);
    render();
  }
  window._stopLabCam = stopLabCam;

  async function toggleLabCam() {
    if (camStream) { stopLabCam(); showToast('Örnek sahneye dönüldü'); return; }
    try {
      camStream = await navigator.mediaDevices.getUserMedia({ video: { width: 480, height: 300, facingMode: 'user' }, audio: false });
      camVideo = document.createElement('video');
      camVideo.srcObject = camStream; camVideo.playsInline = true; camVideo.muted = true;
      await camVideo.play();
      camBtn.textContent = '⏹ Kamerayı Kapat';
      camBtn.classList.add('active');
      showToast('📷 Canlı kamera aktif! Canny Kenar ve Otsu dene!');
      (function tick() {
        if (!camStream) return;
        if (currentSlide !== 3) { stopLabCam(); return; }
        render();
        camRaf = requestAnimationFrame(tick);
      })();
    } catch (_) {
      showToast('Kamera izni verilmedi veya bulunamadı');
    }
  }
  camBtn?.addEventListener('click', toggleLabCam);

  document.querySelectorAll('#labTabs .tab-btn[data-mode]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#labTabs .tab-btn[data-mode]').forEach(b => b.classList.toggle('active', b === btn));
      mode = btn.dataset.mode; render();
    });
  });
  slider.addEventListener('input', () => { param = Number(slider.value); render(); });
  render();
})();

/* Ambient Background Landmark Mesh */
(function initBgMesh() {
  const c = document.getElementById('meshCanvas');
  const ctx = c.getContext('2d');
  let w, h, nodes = [];
  const mouse = { x: -999, y: -999 };
  function resize() {
    w = c.width = innerWidth; h = c.height = innerHeight;
    const n = Math.min(44, Math.floor((w * h) / 30000));
    nodes = Array.from({ length: n }, () => ({ x: Math.random() * w, y: Math.random() * h, vx: (Math.random() - 0.5) * 0.38, vy: (Math.random() - 0.5) * 0.38 }));
  }
  addEventListener('resize', resize);
  addEventListener('mousemove', e => { mouse.x = e.clientX; mouse.y = e.clientY; });
  resize();
  (function loop() {
    ctx.clearRect(0, 0, w, h);
    for (let i = 0; i < nodes.length; i++) {
      const a = nodes[i];
      a.x += a.vx; a.y += a.vy;
      if (a.x < 0 || a.x > w) a.vx *= -1;
      if (a.y < 0 || a.y > h) a.vy *= -1;
      const dm = Math.hypot(mouse.x - a.x, mouse.y - a.y);
      if (dm < 150) { ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(mouse.x, mouse.y); ctx.strokeStyle = `rgba(108,232,170,${(1 - dm / 150) * 0.2})`; ctx.stroke(); }
      for (let j = i + 1; j < nodes.length; j++) {
        const b = nodes[j], d = Math.hypot(a.x - b.x, a.y - b.y);
        if (d < 130) { ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.strokeStyle = `rgba(108,232,170,${(1 - d / 130) * 0.13})`; ctx.stroke(); }
      }
      ctx.beginPath(); ctx.arc(a.x, a.y, 1.8, 0, Math.PI * 2); ctx.fillStyle = 'rgba(108,232,170,0.48)'; ctx.fill();
    }
    requestAnimationFrame(loop);
  })();
})();


/* ===== PRO KEYNOTE PRESENTER TOOLS: SLIDE MAP (G), TIMER (T), LASER (L) ===== */
(function initPresenterStudio() {
  const lb = document.getElementById('lightbox');
  const body = document.getElementById('lightboxBody');
  const gridBtn = document.getElementById('gridBtn');
  const timerBtn = document.getElementById('timerBtn');
  const laserBtn = document.getElementById('laserBtn');
  const laserDot = document.getElementById('laserDot');
  const timerPill = document.getElementById('timerPill');
  const timerDisplay = document.getElementById('timerDisplay');
  const timerToggleBtn = document.getElementById('timerToggleBtn');
  const timerCloseBtn = document.getElementById('timerCloseBtn');

  /* 1) Slide Map Grid (G or click dock counter) */
  function openSlideMap() {
    if (!lb || !body) return;
    const cards = slides.map((s, idx) => {
      const num = String(idx + 1).padStart(2, '0');
      const titleEl = s.querySelector('.slide-title, .hero-h1');
      const title = titleEl ? titleEl.textContent.replace(/\s+/g, ' ').trim() : `Slayt ${num}`;
      const eyEl = s.querySelector('.eyebrow');
      const section = eyEl ? eyEl.textContent.split('·').slice(1, 2).join('').trim() : 'KAPAK';
      return `
        <button class="slide-map-card ${idx === currentSlide ? 'current' : ''}" data-jump="${idx}">
          <span class="slide-map-num">${num} / ${slides.length}${section ? ' · ' + section : ''}</span>
          <span class="slide-map-title">${title}</span>
        </button>
      `;
    }).join('');
    body.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
        <strong style="color:var(--mint); font-family:'Syne',sans-serif; font-size:1.15rem;">🗺 Slayt Haritası (${slides.length} Slayt) — Tek Tıkla Atla</strong>
        <button class="copy-btn" onclick="document.getElementById('lightbox').classList.remove('open')">✕ Kapat (ESC)</button>
      </div>
      <div class="slide-map-grid">${cards}</div>
    `;
    body.querySelectorAll('[data-jump]').forEach(btn => {
      btn.addEventListener('click', () => {
        goToSlide(Number(btn.dataset.jump));
        lb.classList.remove('open');
      });
    });
    lb.classList.add('open');
  }
  gridBtn?.addEventListener('click', openSlideMap);
  dockCounter?.addEventListener('click', openSlideMap);

  /* 2) Workshop Countdown Timer (T) */
  let remainSec = 0, running = false, iv = null;
  function beepDone() {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      [523.25, 659.25, 783.99].forEach((freq, i) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine'; osc.frequency.value = freq;
        gain.gain.setValueAtTime(0.12, ctx.currentTime + i * 0.14);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.14 + 0.35);
        osc.connect(gain); gain.connect(ctx.destination);
        osc.start(ctx.currentTime + i * 0.14); osc.stop(ctx.currentTime + i * 0.14 + 0.36);
      });
    } catch (_) {}
  }
  function renderTimer() {
    const m = Math.floor(remainSec / 60), s = remainSec % 60;
    timerDisplay.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    timerPill.classList.toggle('urgent', remainSec > 0 && remainSec <= 30);
    timerToggleBtn.textContent = running ? '⏸' : '▶';
  }
  function startTimer(minutes) {
    remainSec = Math.max(10, Math.round(minutes * 60));
    running = true;
    timerPill.classList.add('show');
    timerBtn?.classList.add('active-tool');
    renderTimer();
    clearInterval(iv);
    iv = setInterval(() => {
      if (!running) return;
      if (remainSec > 0) {
        remainSec--;
        renderTimer();
        if (remainSec === 0) {
          running = false;
          renderTimer();
          beepDone();
          showToast('⏱ Süre doldu!');
        }
      }
    }, 1000);
  }
  timerToggleBtn?.addEventListener('click', () => { running = !running; renderTimer(); });
  timerCloseBtn?.addEventListener('click', () => {
    running = false; clearInterval(iv);
    timerPill.classList.remove('show', 'urgent');
    timerBtn?.classList.remove('active-tool');
  });

  function openTimerModal() {
    if (!lb || !body) return;
    body.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
        <strong style="color:var(--mint); font-family:'Syne',sans-serif; font-size:1.15rem;">⏱ Atölye &amp; Mola Geri Sayım Sayacı</strong>
        <button class="copy-btn" onclick="document.getElementById('lightbox').classList.remove('open')">✕ Kapat (ESC)</button>
      </div>
      <p style="color:var(--cream-soft); font-size:0.86rem; margin-bottom:16px;">
        Kodlama alıştırması veya çay molası için hazır süre seç — sayaç sol alt köşede tüm slaytların üstünde akar:
      </p>
      <div style="display:flex; flex-wrap:wrap; gap:10px;">
        ${[3, 5, 10, 15, 20].map(m => `<button class="btn-primary" data-mins="${m}" style="padding:10px 18px;">⏱ ${m} Dakika</button>`).join('')}
      </div>
    `;
    body.querySelectorAll('[data-mins]').forEach(btn => {
      btn.addEventListener('click', () => {
        startTimer(Number(btn.dataset.mins));
        lb.classList.remove('open');
        showToast(`⏱ ${btn.dataset.mins} dakikalık sayaç başladı!`);
      });
    });
    lb.classList.add('open');
  }
  timerBtn?.addEventListener('click', openTimerModal);

  /* 3) Stage Laser Pointer (L) */
  let laserOn = false;
  function toggleLaser() {
    laserOn = !laserOn;
    document.body.classList.toggle('laser-on', laserOn);
    laserBtn?.classList.toggle('active-tool', laserOn);
    showToast(laserOn ? '🔴 Lazer işaretçi açık (L ile kapat)' : 'Lazer işaretçi kapatıldı');
  }
  laserBtn?.addEventListener('click', toggleLaser);
  window.addEventListener('mousemove', e => {
    if (!laserOn || !laserDot) return;
    laserDot.style.left = `${e.clientX}px`;
    laserDot.style.top = `${e.clientY}px`;
  });

  /* Keyboard shortcuts: G (grid), T (timer), L (laser) */
  window.addEventListener('keydown', e => {
    if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
    const k = e.key.toLowerCase();
    if (k === 'g') { e.preventDefault(); openSlideMap(); }
    else if (k === 't') { e.preventDefault(); openTimerModal(); }
    else if (k === 'l') { e.preventDefault(); toggleLaser(); }
  });
})();


/* ===== STAGE BLACKOUT (B), SPEAKER NOTES (N) & SHORTCUTS (?) ===== */
(function initStageExtras() {
  const blackout = document.getElementById('blackoutCurtain');
  const snBar = document.getElementById('speakerNote');
  const snText = document.getElementById('speakerNoteText');
  const lb = document.getElementById('lightbox');
  const body = document.getElementById('lightboxBody');
  let notesOn = false;

  const NOTES = {
    0: 'Hoş geldiniz! Enerjiyi yüksek başlat: "4 saat sonra kameranız el hareketlerinizle neon yazı yazacak!"',
    3: 'Sahnede "📷 Canlı Kameram" butonuna basıp Canny Kenar filtresini sınıfın canlı yüzünde göster!',
    7: 'Herkesin git clone ... seis-opencv yapıp atolye-baslangic içine girdiğini kontrol et (T ile 5 dk sayaç aç).',
    11: '01_kamera.py: İlk kez canlı kamera açılıyor! F tuşuyla Özellikler rehberini göster.',
    12: '02_piksel_renk.py: b tuşuna basıp mavi yüz (BGR-RGB tuzağı) şakasını mutlaka göster!',
    17: '06_yuz_geometrisi.py: Göz kırpınca EAR değerinin düşüşünü ve baş dönüş (yaw) açısını canlı göster.',
    22: '08_el_jestleri.py: Havada kendi adını NEON harflerle yaz, 2-5 parmakla renk değiştir, yumrukla sil!',
    25: '10_cilt_analizi.py: Kalite kutuları yeşil olunca Boşluk ile ısı haritası al; tıbbi tanı olmadığını vurgula.',
    30: 'bonus3_el_kalp_efekti.py: İki elle kalp yapıp %100 şok dalgası patlamasını sahnede göster!',
    32: 'bonus5_sinif_enerji_olcer.py: Gün Başı (1) ve Eğitim Sonu (2) sınıf enerjisi karşılaştırmasını yap!',
    34: 'Ödüllü Kahoot zamanı! Eğitmen ekranından kahoot.html açıp QR kodu yansıt (Şifre: SEIS2026).'
  };

  function syncNote() {
    if (!snBar || !snText) return;
    if (!notesOn) { snBar.classList.remove('show'); return; }
    const s = slides[currentSlide];
    const title = s?.querySelector('.slide-title, .hero-h1')?.textContent.replace(/\s+/g, ' ').trim() || '';
    snText.textContent = NOTES[currentSlide] || `Slayt ${currentSlide + 1}: "${title}" — Kısa özetle ve katılımcılara [F] Özellikler tuşunu hatırlat.`;
    snBar.classList.add('show');
  }

  /* Hook goToSlide to also refresh speaker notes & section badge */
  const origGoTo = window.goToSlide;
  window.goToSlide = function(idx) {
    origGoTo(idx);
    syncNote();
    const ey = slides[currentSlide]?.querySelector('.eyebrow')?.textContent || '';
    const sec = ey.split('·')[1]?.trim();
    if (dockCounter) {
      const base = `${String(currentSlide + 1).padStart(2, '0')} / ${slides.length}`;
      dockCounter.textContent = sec ? `${base} · ${sec.slice(0, 18)}` : base;
    }
  };
  syncNote();

  function openShortcuts() {
    if (!lb || !body) return;
    const keys = [
      ['← / → / Boşluk', 'Önceki / Sonraki slayt'],
      ['G', '🗺 Slayt Haritası (35 slayt arasında tek tıkla atla)'],
      ['T', '⏱ Atölye & Mola Geri Sayım Sayacı'],
      ['L', '🔴 Sahne Lazer İşaretçi aç/kapat'],
      ['B', '⬛ Sahne Karartma (Blackout) perdesi'],
      ['N', '🎙 Eğitmen Sahne Notları çubuğu aç/kapat'],
      ['F', '⛶ Tam ekran aç/kapat'],
      ['ESC', 'Açık pencereyi / perdeyi kapat']
    ];
    body.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
        <strong style="color:var(--mint); font-family:'Syne',sans-serif; font-size:1.15rem;">⌨️ Eğitmen Klavye Kısayolları</strong>
        <button class="copy-btn" onclick="document.getElementById('lightbox').classList.remove('open')">✕ Kapat (ESC)</button>
      </div>
      <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:9px;">
        ${keys.map(([k, d]) => `
          <div style="padding:10px 12px; border-radius:12px; background:rgba(46,11,28,0.65); border:1px solid var(--border); display:flex; align-items:center; gap:10px;">
            <code style="color:var(--mint); font-weight:700; min-width:92px;">${k}</code>
            <span style="color:var(--cream-soft); font-size:0.82rem;">${d}</span>
          </div>
        `).join('')}
      </div>
    `;
    lb.classList.add('open');
  }

  /* Clicking blackout triggers energy burst instead of closing (use B or ESC to close) */

  window.addEventListener('keydown', e => {
    if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
    const k = e.key.toLowerCase();
    if (k === 'b') {
      blackout?.classList.toggle('open');
    } else if (k === 'n') {
      notesOn = !notesOn;
      syncNote();
      showToast(notesOn ? '🎙 Eğitmen sahne notları açıldı' : 'Sahne notları kapatıldı');
    } else if (e.key === '?' || (e.shiftKey && e.key === '/')) {
      openShortcuts();
    } else if (e.key === 'Escape') {
      blackout?.classList.remove('open');
    }
  });
})();


/* ===== LIVE 60FPS STAGE VISUALIZER FOR BLACKOUT (B KEY) ===== */
(function initBlackoutVisualizer() {
  const curtain = document.getElementById('blackoutCurtain');
  const canvas = document.getElementById('blackoutCanvas');
  const clockEl = document.getElementById('boClock');
  const logoWrap = curtain?.querySelector('.blackout-logo-wrap');
  if (!curtain || !canvas) return;
  const ctx = canvas.getContext('2d');
  let w = 0, h = 0, raf = null, t = 0;
  const mx = { x: 0, y: 0, tx: 0, ty: 0 };

  const COLORS = ['108,232,170', '124,196,250', '235,161,130', '247,236,218'];
  let stars = [], sparks = [], bursts = [], shockwaves = [];

  const comets = [
    { rx: 195, ry: 72, rot: -0.32, speed: 0.032, a: 0, col: '108,232,170', trail: [] },
    { rx: 215, ry: 82, rot: 0.42,  speed: -0.026, a: 2.1, col: '124,196,250', trail: [] },
    { rx: 178, ry: 68, rot: 1.05,  speed: 0.036, a: 4.2, col: '235,161,130', trail: [] }
  ];

  function spawnBurst(x, y) {
    shockwaves.push({ x, y, r: 16, maxR: 260, a: 0.9, col: COLORS[Math.floor(Math.random() * 3)] });
    for (let i = 0; i < 42; i++) {
      const ang = (Math.PI * 2 * i) / 42 + (Math.random() - 0.5) * 0.2;
      const spd = 2.2 + Math.random() * 6.4;
      bursts.push({
        x, y,
        vx: Math.cos(ang) * spd,
        vy: Math.sin(ang) * spd,
        r: 1.8 + Math.random() * 3.0,
        life: 1,
        decay: 0.016 + Math.random() * 0.016,
        col: COLORS[i % COLORS.length]
      });
    }
  }

  curtain.addEventListener('click', e => {
    if (!curtain.classList.contains('open')) return;
    spawnBurst(e.clientX, e.clientY);
  });

  function resize() {
    w = canvas.width = innerWidth;
    h = canvas.height = innerHeight;
    stars = Array.from({ length: 90 }, (_, i) => ({
      angle: Math.random() * Math.PI * 2,
      radius: 165 + Math.random() * Math.min(w, h) * 0.48,
      speed: (0.0018 + Math.random() * 0.0042) * (i % 2 ? 1 : -1),
      tilt: 0.44 + Math.random() * 0.54,
      size: 1.4 + Math.random() * 2.6,
      col: COLORS[i % COLORS.length],
      phase: Math.random() * Math.PI * 2
    }));
    sparks = Array.from({ length: 48 }, (_, i) => ({
      x: Math.random() * w,
      y: Math.random() * h,
      vy: 0.4 + Math.random() * 1.0,
      vx: (Math.random() - 0.5) * 0.35,
      r: 1.2 + Math.random() * 2.5,
      col: COLORS[i % COLORS.length],
      a: 0.25 + Math.random() * 0.65
    }));
  }
  addEventListener('resize', resize);
  addEventListener('mousemove', e => {
    mx.tx = (e.clientX / Math.max(w, 1) - 0.5) * 32;
    mx.ty = (e.clientY / Math.max(h, 1) - 0.5) * 24;
  });
  resize();

  function updateClock() {
    if (!clockEl) return;
    const d = new Date();
    clockEl.textContent = d.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
  setInterval(updateClock, 1000);
  updateClock();

  function draw() {
    if (!curtain.classList.contains('open')) { raf = null; return; }
    t += 0.016;
    mx.x += (mx.tx - mx.x) * 0.08;
    mx.y += (mx.ty - mx.y) * 0.08;
    if (logoWrap) {
      logoWrap.style.transform = `perspective(700px) rotateY(${(mx.x * 0.42).toFixed(2)}deg) rotateX(${(-mx.y * 0.42).toFixed(2)}deg)`;
    }

    ctx.clearRect(0, 0, w, h);

    const cx = w * 0.5 + mx.x * 0.7;
    const cy = h * 0.41 + mx.y * 0.7;

    /* 1) Subtle expanding energy rings behind logo */
    for (let k = 0; k < 3; k++) {
      const p = ((t * 0.26 + k / 3) % 1);
      const r = 130 + p * Math.min(w, h) * 0.44;
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(108,232,170,${(1 - p) * 0.26})`;
      ctx.lineWidth = 1.6;
      ctx.stroke();
    }

    /* 2) 3D Orbital neural constellation */
    const pts = stars.map(s => {
      s.angle += s.speed;
      const x = cx + Math.cos(s.angle) * s.radius;
      const y = cy + Math.sin(s.angle) * s.radius * s.tilt;
      return { x, y, s };
    });

    for (let i = 0; i < pts.length; i++) {
      const a = pts[i];
      for (let j = i + 1; j < pts.length; j++) {
        const b = pts[j];
        const d = Math.hypot(a.x - b.x, a.y - b.y);
        if (d < 118) {
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.strokeStyle = `rgba(${a.s.col},${(1 - d / 118) * 0.24})`;
          ctx.lineWidth = 0.9;
          ctx.stroke();
        }
      }
      const tw = 0.55 + 0.45 * Math.sin(t * 2.6 + a.s.phase);
      ctx.beginPath();
      ctx.arc(a.x, a.y, a.s.size * (0.85 + tw * 0.35), 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${a.s.col},${0.35 + tw * 0.65})`;
      ctx.shadowColor = `rgba(${a.s.col},0.9)`;
      ctx.shadowBlur = 10;
      ctx.fill();
    }

    /* 3) 3 Glowing 3D Orbiting Comets around SEIS Medallion */
    for (const c of comets) {
      c.a += c.speed;
      const lx = Math.cos(c.a) * c.rx;
      const ly = Math.sin(c.a) * c.ry;
      const cr = Math.cos(c.rot), sr = Math.sin(c.rot);
      const px = cx + lx * cr - ly * sr;
      const py = cy + lx * sr + ly * cr;
      c.trail.push({ x: px, y: py });
      if (c.trail.length > 26) c.trail.shift();

      for (let i = 1; i < c.trail.length; i++) {
        const frac = i / c.trail.length;
        ctx.beginPath();
        ctx.moveTo(c.trail[i - 1].x, c.trail[i - 1].y);
        ctx.lineTo(c.trail[i].x, c.trail[i].y);
        ctx.strokeStyle = `rgba(${c.col},${frac * 0.85})`;
        ctx.lineWidth = frac * 4.2;
        ctx.lineCap = 'round';
        ctx.stroke();
      }
      ctx.beginPath();
      ctx.arc(px, py, 4.8, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.shadowColor = `rgba(${c.col},1)`;
      ctx.shadowBlur = 18;
      ctx.fill();
    }
    ctx.shadowBlur = 0;

    /* 4) Rising stage bokeh sparks */
    for (const sp of sparks) {
      sp.y -= sp.vy;
      sp.x += sp.vx + Math.sin(t + sp.y * 0.01) * 0.24;
      if (sp.y < -10) { sp.y = h + 10; sp.x = Math.random() * w; }
      ctx.beginPath();
      ctx.arc(sp.x, sp.y, sp.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${sp.col},${sp.a})`;
      ctx.fill();
    }

    /* 5) Harmonic neon spectrum ribbons along bottom edge */
    const ribbons = [
      { col: '108,232,170', amp: 18, freq: 0.0085, spd: 2.1, off: 0, alpha: 0.34 },
      { col: '124,196,250', amp: 14, freq: 0.0115, spd: -1.7, off: 2.0, alpha: 0.28 },
      { col: '235,161,130', amp: 11, freq: 0.0065, spd: 1.4, off: 4.1, alpha: 0.24 }
    ];
    for (const rb of ribbons) {
      ctx.beginPath();
      for (let x = 0; x <= w; x += 10) {
        const env = Math.sin((x / w) * Math.PI);
        const y = h - 38 + Math.sin(x * rb.freq + t * rb.spd + rb.off) * rb.amp * env
                         + Math.cos(x * rb.freq * 1.9 - t * 1.2) * (rb.amp * 0.45) * env;
        if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.strokeStyle = `rgba(${rb.col},${rb.alpha})`;
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    /* 6) Click Shockwaves & Starburst Explosions */
    for (let i = shockwaves.length - 1; i >= 0; i--) {
      const sw = shockwaves[i];
      sw.r += 7.5;
      sw.a *= 0.93;
      if (sw.r >= sw.maxR || sw.a < 0.02) { shockwaves.splice(i, 1); continue; }
      ctx.beginPath();
      ctx.arc(sw.x, sw.y, sw.r, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(${sw.col},${sw.a})`;
      ctx.lineWidth = 2.6;
      ctx.stroke();
    }
    for (let i = bursts.length - 1; i >= 0; i--) {
      const b = bursts[i];
      b.x += b.vx; b.y += b.vy;
      b.vx *= 0.96; b.vy *= 0.96;
      b.life -= b.decay;
      if (b.life <= 0) { bursts.splice(i, 1); continue; }
      ctx.beginPath();
      ctx.arc(b.x, b.y, b.r * b.life, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${b.col},${b.life})`;
      ctx.shadowColor = `rgba(${b.col},0.95)`;
      ctx.shadowBlur = 12;
      ctx.fill();
    }
    ctx.shadowBlur = 0;

    raf = requestAnimationFrame(draw);
  }

  /* Watch class changes on curtain so animation runs ONLY when open */
  new MutationObserver(() => {
    if (curtain.classList.contains('open') && !raf) {
      updateClock();
      spawnBurst(innerWidth * 0.5, innerHeight * 0.41);
      raf = requestAnimationFrame(draw);
    }
  }).observe(curtain, { attributes: true, attributeFilter: ['class'] });
})();
