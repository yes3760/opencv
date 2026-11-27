"""BONUS PROJE 4 — SEIS Akıllı Cilt Aynası & A/B Işık Karşılaştırma Stüdyosu

Mevcut vision-workshop ortamındaki FaceTracker + SkinAnalyzer ile çalışır;
ek kütüphane veya yeni model indirmenize gerek yoktur.

Özellikler:
  - Canlı yüz bölgeleri (alın, sağ yanak, sol yanak) önizlemesi ve kalite kontrol kapısı
  - A / B Işık Karşılaştırma Modu: Aynı kişinin iki farklı ışık açısında (ör. pencereye düz vs yan)
    Δa*, parlama %, doku ve iki yanak arası ΔE76 değişimini yan yana karşılaştırır!
  - 4 farklı sabit aralıklı ısı haritası (1: Kızarıklık Δa*, 2: Doku, 3: Renk Farkı ΔE76, 4: Parlama)
  - Tek tuşla PNG rapor kartı kaydetme (s)

Uyarı: Eğitim amaçlı görüntü analizidir; tıbbi tanı değildir. Görüntüler otomatik kaydedilmez.

Çalıştırma : python Gemini/bonus_projeler/bonus4_cilt_ayna_studyo.py
Tuşlar     : Boşluk: Kare A / Kare B al  |  1-4: Isı haritası  |  r: Bölge maskesi aç/kapa
             c: A/B temizle  |  s: Rapor PNG kaydet  |  q: Çıkış
"""

import sys
import time
from pathlib import Path

import cv2
import numpy as np

# src klasörünü otomatik bul (hem atolye-baslangic/bonus_projeler hem Gemini/bonus_projeler için)
for _p in Path(__file__).resolve().parents:
    if (_p / "src").is_dir():
        if str(_p / "src") not in sys.path:
            sys.path.insert(0, str(_p / "src"))
        break

import config
from camera import Camera, CameraError
from common.app import Canvas, DisplayLoop, build_parser
from common.draw import put_text, status_line
from common.fps import FPSMeter
from common.frame import FramePreparer
from common.models import ModelMissingError
from face.tracker import FaceTracker
from skin.analyzer import SkinAnalyzer, SkinReport
from skin.metrics import render_heatmap
from skin.overlay import MAP_KEYS, disclaimer, draw_quality, draw_regions

# Afiş renk paleti (BGR)
PLUM_DARK = (18, 5, 28)
PLUM_CARD = (32, 10, 48)
MINT = (170, 232, 108)
CREAM = (218, 236, 247)
PEACH = (130, 161, 235)
GOLD = (85, 215, 255)
MUTED = (140, 130, 145)


def harita_kucuk(report: SkinReport, map_name: str, max_w: int, max_h: int) -> np.ndarray:
    """Raporun ısı haritasını aynalayarak panel kutusuna orantılı sığdırır."""
    m = report.metrics
    heat = render_heatmap(report.crop, m.maps[map_name], m.union, map_name)
    if config.MIRROR_DISPLAY:
        heat = cv2.flip(heat, 1)
    h, w = heat.shape[:2]
    scale = min(max_w / max(w, 1), max_h / max(h, 1))
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    return cv2.resize(heat, (nw, nh), interpolation=cv2.INTER_AREA)


def ozet_degerler(report: SkinReport) -> dict[str, float]:
    """Alın ve yanak ortalamalarından karşılaştırma özeti çıkarır."""
    regs = report.metrics.regions
    if not regs:
        return {"delta_a": 0.0, "shine": 0.0, "texture": 0.0, "cheek_de": 0.0}
    n = len(regs)
    return {
        "delta_a": sum(r.delta_a for r in regs.values()) / n,
        "shine": sum(r.shine_percent for r in regs.values()) / n,
        "texture": sum(r.texture for r in regs.values()) / n,
        "cheek_de": report.metrics.cheek_delta_e or 0.0,
    }


def studiyo_paneli_ciz(
    kare_a: SkinReport | None,
    kare_b: SkinReport | None,
    map_name: str,
    height: int,
    width: int = 470,
) -> np.ndarray:
    """Sağ tarafta SEIS temalı A/B karşılaştırma ve ısı haritası panelini çizer."""
    out = np.full((height, width, 3), PLUM_DARK, np.uint8)

    # Üst başlık şeridi
    cv2.rectangle(out, (0, 0), (width, 54), PLUM_CARD, -1)
    cv2.line(out, (0, 54), (width, 54), MINT, 1)
    put_text(out, "SEIS AKILLI CİLT AYNASI · A/B STÜDYO", (14, 10), 15, MINT)
    put_text(out, f"Harita [1-4]: {map_name}", (14, 32), 13, CREAM)

    if kare_a is None:
        put_text(out, "Nasıl Kullanılır?", (16, 86), 17, MINT)
        put_text(out, "1. Kalite listesindeki tüm noktalar yeşil olsun.", (16, 118), 14, CREAM)
        put_text(out, "2. BOŞLUK tuşuna bas → Kare A (1. ışık) alınır.", (16, 144), 14, CREAM)
        put_text(out, "3. Işığa yan dönüp tekrar BOŞLUK → Kare B alınır.", (16, 170), 14, CREAM)
        put_text(out, "4. Cilt aynıyken ışığın Δa* ve ΔE etkisini gör!", (16, 196), 14, PEACH)
        put_text(out, "1-4: Harita seç  |  r: Bölge maskesi  |  s: Kaydet", (16, 240), 13, MUTED)
        return out

    # Harita kutuları (A tek başınaysa büyük; A ve B varsa yan yana!)
    y_top = 66
    if kare_b is None:
        if kare_a.metrics is not None:
            hm = harita_kucuk(kare_a, map_name, width - 32, 220)
            x0 = (width - hm.shape[1]) // 2
            out[y_top:y_top + hm.shape[0], x0:x0 + hm.shape[1]] = hm
            cv2.rectangle(out, (x0, y_top), (x0 + hm.shape[1], y_top + hm.shape[0]), MINT, 1)
            put_text(out, "KARE A (Boşluk: Kare B ile karşılaştır)", (14, y_top + hm.shape[0] + 8), 13, MINT)
            y_tbl = y_top + hm.shape[0] + 34
        else:
            put_text(out, "Kare A reddedildi: " + kare_a.quality.first_problem, (14, 80), 13, PEACH)
            return out
    else:
        slot_w = (width - 36) // 2
        slot_h = 195
        for idx, (lbl, rep, col) in enumerate([("KARE A", kare_a, MINT), ("KARE B", kare_b, PEACH)]):
            sx = 12 + idx * (slot_w + 12)
            cv2.rectangle(out, (sx, y_top), (sx + slot_w, y_top + slot_h), PLUM_CARD, -1)
            if rep.metrics is not None:
                hm = harita_kucuk(rep, map_name, slot_w - 8, slot_h - 28)
                ox = sx + (slot_w - hm.shape[1]) // 2
                oy = y_top + 24
                out[oy:oy + hm.shape[0], ox:ox + hm.shape[1]] = hm
            put_text(out, lbl, (sx + 8, y_top + 4), 13, col)
            cv2.rectangle(out, (sx, y_top), (sx + slot_w, y_top + slot_h), col, 1)
        y_tbl = y_top + slot_h + 14

    # Gösterge Tablosu
    cv2.rectangle(out, (12, y_tbl), (width - 12, height - 38), PLUM_CARD, -1)
    cv2.rectangle(out, (12, y_tbl), (width - 12, height - 38), (70, 35, 90), 1)

    if kare_b is None and kare_a.metrics is not None:
        put_text(out, "Bölge Özeti (Kare A)", (22, y_tbl + 8), 14, MINT)
        yy = y_tbl + 34
        for name, st in kare_a.metrics.regions.items():
            put_text(
                out,
                f"{name:<10} Δa*:{st.delta_a:+5.1f}  Parlama:%{st.shine_percent:4.1f}  Doku:{st.texture:4.1f}",
                (22, yy), 13, CREAM,
            )
            yy += 24
        if kare_a.metrics.cheek_delta_e is not None:
            put_text(out, f"İki yanak arası renk farkı (ΔE): {kare_a.metrics.cheek_delta_e:.1f}", (22, yy + 6), 13, GOLD)
    elif kare_a.metrics is not None and kare_b.metrics is not None:
        sa, sb = ozet_degerler(kare_a), ozet_degerler(kare_b)
        put_text(out, "A / B IŞIK KARŞILAŞTIRMASI", (22, y_tbl + 8), 14, GOLD)
        satirlar = [
            ("Ort. Δa* (kızarıklık)", f"{sa['delta_a']:+.1f}", f"{sb['delta_a']:+.1f}", f"{sb['delta_a'] - sa['delta_a']:+.1f}"),
            ("Parlak piksel (%)", f"%{sa['shine']:.1f}", f"%{sb['shine']:.1f}", f"{sb['shine'] - sa['shine']:+.1f}"),
            ("Doku değişimi", f"{sa['texture']:.1f}", f"{sb['texture']:.1f}", f"{sb['texture'] - sa['texture']:+.1f}"),
            ("İki yanak ΔE", f"{sa['cheek_de']:.1f}", f"{sb['cheek_de']:.1f}", f"{sb['cheek_de'] - sa['cheek_de']:+.1f}"),
        ]
        yy = y_tbl + 34
        put_text(out, f"{'Gösterge':<21} {'A':>6} {'B':>6} {'Fark':>7}", (22, yy), 12, MUTED)
        yy += 22
        for ad, va, vb, vf in satirlar:
            put_text(out, f"{ad:<21} {va:>6} {vb:>6} {vf:>7}", (22, yy), 13, CREAM)
            yy += 23
        put_text(out, "Cilt aynıyken ışık açısı ölçümleri değiştirir!", (22, yy + 6), 12, PEACH)

    put_text(out, "c: Sıfırla  |  s: Raporu PNG kaydet", (14, height - 26), 12, MUTED)
    return out


def main():
    args = build_parser("SEIS Akıllı Cilt Aynası & A/B Stüdyo").parse_args()
    prepare, fps = FramePreparer(config.PROCESS_WIDTH), FPSMeter()
    analyzer = SkinAnalyzer(use_segmenter=True)
    print(analyzer.segmenter_note)

    preview: SkinReport | None = None
    kare_a: SkinReport | None = None
    kare_b: SkinReport | None = None
    map_name = MAP_KEYS[0]
    show_regions = True
    last_preview = 0.0
    bildirim = ""
    bildirim_bitis = 0.0

    with Camera(args.source, config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT) as cam, \
            FaceTracker() as faces, \
            DisplayLoop(
                "SEIS Akilli Cilt Aynasi - A/B Isik Studyosu",
                args,
                help_title="Bonus 4 · SEIS Akıllı Cilt Aynası (A/B Işık Stüdyosu)",
                help_lines=[
                    "Amaç: Farklı ışık açılarının cilt görünümü ölçümlerini nasıl değiştirdiğini A/B kıyaslamak.",
                    "• [Boşluk] İlk basışta Kare A, farklı ışık açısında ikinci basışta Kare B alır.",
                    "• [1-4] Kızarıklık, parlama, doku ve ΔE ısı haritaları arasında geçiş yap.",
                    "• [r] Canlı bölge maskesini aç/kapat  ·  [c] A/B sıfırla  ·  [s] Raporu PNG kaydet.",
                ],
            ) as loop:
        while loop.running:
            raw = cam.read()
            if raw is None:
                break
            frame = prepare(raw)
            result = faces.process(frame)
            now = time.monotonic()

            if now - last_preview >= 0.45:
                preview = analyzer.analyze(frame.full_bgr, result.faces, frame.scale_to_full)
                last_preview = now

            canvas = Canvas(frame, width=700, mirror=not args.no_mirror)
            if show_regions and preview is not None and preview.regions is not None and len(result.faces) == 1:
                # Canlı bölge önizlemesi (sade poligon çizimi)
                from skin.regions import build_region_masks
                face = result.faces[0]
                live_reg = build_region_masks(
                    canvas.image, canvas.pts(face.points), face.width_px * canvas.scale,
                    config.SKIN_ROI_EROSION_RATIO, None,
                )
                draw_regions(canvas.image, live_reg)
            canvas.flip()
            img = canvas.image
            disclaimer(img)

            if preview is not None:
                draw_quality(img, preview.quality, 12, 36, width=360)
            put_text(img, f"FPS {fps.tick():.0f}", (img.shape[1] - 88, 36), 14, MINT, bg=PLUM_DARK)

            if time.monotonic() < bildirim_bitis and bildirim:
                put_text(img, bildirim, (16, img.shape[0] - 66), 16, GOLD, bg=PLUM_DARK)

            ok_kalite = preview is not None and preview.quality.ok
            hedef = "Kare A" if kare_a is None else ("Kare B" if kare_b is None else "Kare B'yi yenile")
            hint = f"Kalite uygun! Boşluk → {hedef}" if ok_kalite else (
                "Uygun görüntü bekleniyor. " + (preview.quality.first_problem if preview else "")
            )
            status_line(img, hint, "ok" if ok_kalite else "warn")

            sag = studiyo_paneli_ciz(kare_a, kare_b, map_name, height=img.shape[0])
            birlesik = np.hstack([img, sag])
            key = loop.show(birlesik)

            if key == ord(" "):
                yeni = analyzer.analyze(frame.full_bgr, result.faces, frame.scale_to_full)
                if yeni.metrics is None:
                    bildirim = "Kalite yetersiz: " + yeni.quality.first_problem
                elif kare_a is None:
                    kare_a = yeni
                    bildirim = f"Kare A alındı ({yeni.elapsed_ms:.0f} ms) — Şimdi ışığa dönüp Kare B al!"
                else:
                    kare_b = yeni
                    bildirim = f"Kare B alındı ({yeni.elapsed_ms:.0f} ms) — A/B farkı sağda!"
                bildirim_bitis = time.monotonic() + 2.8
            elif ord("1") <= key <= ord("4"):
                map_name = MAP_KEYS[key - ord("1")]
            elif key == ord("r"):
                show_regions = not show_regions
            elif key == ord("c"):
                kare_a = kare_b = None
                bildirim = "A/B karşılaştırma temizlendi."
                bildirim_bitis = time.monotonic() + 1.8
            elif key == ord("s"):
                dosya = f"seis_cilt_raporu_{int(time.time())}.png"
                cv2.imwrite(dosya, birlesik)
                bildirim = f"Kaydedildi: {dosya}"
                bildirim_bitis = time.monotonic() + 2.4
    analyzer.close()


if __name__ == "__main__":
    try:
        main()
    except (CameraError, ModelMissingError) as exc:
        print(exc)
