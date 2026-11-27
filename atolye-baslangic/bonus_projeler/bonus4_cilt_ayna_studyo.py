"""BONUS PROJE 4 — Işık Kamerayı Nasıl Yanıltır? (1. Çekim vs 2. Çekim Cilt Deneyi)

Amaç (Çok Basit!):
  Sosyal medyadaki veya uygulamalardaki 'yapay zekâ cilt analizi' araçlarının
  sadece ışık açısı değiştiğinde nasıl farklı sonuçlar verdiğini canlı kanıtlamak!

Nasıl Yapılır?
  1) Normal dururken [BOŞLUK] tuşuna bas -> 1. Çekim (Normal Işık) alınır.
  2) Telefon fenerini yüzüne tut (veya pencereye dön) ve tekrar [BOŞLUK] bas -> 2. Çekim alınır.
  3) Sağ ekranda aynı yüzün sadece ışık değişince nasıl bambaşka sayılar verdiğini gör!

Uyarı: Eğitim amaçlı görüntü analizidir; tıbbi tanı değildir.

Çalıştırma : python bonus_projeler/bonus4_cilt_ayna_studyo.py
Tuşlar     : Boşluk: 1. / 2. Çekimi Al | 1-4: Harita Değiştir | r: Maske | c: Sıfırla | s: PNG Kaydet | q: Çıkış
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

for _p in Path(__file__).resolve().parents:
    if (_p / "src").is_dir():
        if str(_p / "src") not in sys.path:
            sys.path.insert(0, str(_p / "src"))
        break

import cv2
import numpy as np

import config
from camera import Camera, CameraError
from common.app import Canvas, DisplayLoop, build_parser
from common.draw import put_text, status_line
from common.fps import FPSMeter
from common.frame import FramePreparer
from common.models import ModelMissingError
from face.tracker import FaceTracker
from skin.analyzer import SkinAnalyzer, SkinReport
from skin.metrics import compute_metrics, render_heatmap
from skin.overlay import MAP_KEYS, disclaimer, draw_regions
from skin.regions import build_region_masks

PLUM_DARK = (18, 5, 28)
PLUM_CARD = (34, 12, 50)
MINT = (170, 232, 108)
CREAM = (232, 240, 248)
PEACH = (130, 175, 245)
GOLD = (85, 215, 255)
MUTED = (165, 155, 170)

HARITA_ADLARI = {
    MAP_KEYS[0]: "1: Kızarıklık Haritası",
    MAP_KEYS[1]: "2: Parlama Haritası",
    MAP_KEYS[2]: "3: Doku / Pürüz Haritası",
    MAP_KEYS[3]: "4: Renk Tonu Farkı",
}

HELP_LINES = [
    "Amaç: Sadece ışık değiştiğinde kameranın cilt ölçümlerinin nasıl değiştiğini kanıtlamak.",
    "• ADIM 1: Kameraya bak ve [BOŞLUK] tuşuna bas -> 1. Çekim (Normal Işık) kaydedilir.",
    "• ADIM 2: Telefon flaşını yüzüne tut veya ışığa yan dön, tekrar [BOŞLUK] bas -> 2. Çekim alınır.",
    "• SONUÇ: Sağdaki tabloda aynı cildin iki ışıkta ne kadar farklı çıktığını karşılaştır!",
    "• [1-4] Isı haritası seç  ·  [r] Bölge maskesi  ·  [c] Baştan başla  ·  [s] PNG kaydet",
]


def esnek_cekim_al(analyzer: SkinAnalyzer, frame, faces) -> SkinReport | None:
    """Kalite kapısına takılıp kullanıcıyı bekletmeden tek yüz varsa her zaman çekim üretir."""
    if len(faces) != 1:
        return None
    rep = analyzer.analyze(frame.full_bgr, faces, frame.scale_to_full)
    if rep.metrics is not None:
        return rep
    # Yüz biraz uzak veya açı hafif eğik olsa bile eğitim deneyinde çekimi yine de hesapla
    if rep.crop is not None and rep.regions is not None:
        rep.metrics = compute_metrics(rep.crop, rep.regions)
        return rep
    face = faces[0]
    pts_full = face.points * frame.scale_to_full
    w_full = face.width_px * frame.scale_to_full
    x1, y1, x2, y2 = [int(v * frame.scale_to_full) for v in face.box]
    pad = int(w_full * 0.25)
    H, W = frame.full_bgr.shape[:2]
    cx1, cy1 = max(0, x1 - pad), max(0, y1 - pad)
    cx2, cy2 = min(W, x2 + pad), min(H, y2 + pad)
    crop = frame.full_bgr[cy1:cy2, cx1:cx2].copy()
    if crop.size == 0:
        return None
    local_pts = pts_full - np.array([cx1, cy1], dtype=np.float32)
    regs = build_region_masks(crop, local_pts, w_full, config.SKIN_ROI_EROSION_RATIO, None)
    rep.crop = crop
    rep.regions = regs
    rep.metrics = compute_metrics(crop, regs)
    return rep


def harita_kucuk(report: SkinReport, map_name: str, max_w: int, max_h: int) -> np.ndarray:
    m = report.metrics
    heat = render_heatmap(report.crop, m.maps[map_name], m.union, map_name)
    if config.MIRROR_DISPLAY:
        heat = cv2.flip(heat, 1)
    h, w = heat.shape[:2]
    scale = min(max_w / max(w, 1), max_h / max(h, 1))
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    return cv2.resize(heat, (nw, nh), interpolation=cv2.INTER_LINEAR)


def ozet_degerler(report: SkinReport) -> dict[str, float]:
    regs = report.metrics.regions
    if not regs:
        return {"kizarik": 0.0, "parlama": 0.0, "doku": 0.0, "yanak_fark": 0.0}
    n = len(regs)
    return {
        "kizarik": sum(r.delta_a for r in regs.values()) / n,
        "parlama": sum(r.shine_percent for r in regs.values()) / n,
        "doku": sum(r.texture for r in regs.values()) / n,
        "yanak_fark": report.metrics.cheek_delta_e or 0.0,
    }


def sag_panel_ciz(
    cekim_1: SkinReport | None,
    cekim_2: SkinReport | None,
    map_name: str,
    height: int,
    width: int = 470,
) -> np.ndarray:
    """Yüksekliğe tam duyarlı, hiçbir satırı taşmayan sade Türkçe karşılaştırma paneli."""
    out = np.full((height, width, 3), PLUM_DARK, np.uint8)
    cv2.line(out, (0, 0), (0, height), (80, 50, 95), 2)

    # Üst başlık (sağ üstteki [F] Özellikler rozetine çarpmaması için solda hizalı)
    cv2.rectangle(out, (2, 0), (width, 56), PLUM_CARD, -1)
    cv2.line(out, (0, 56), (width, 56), MINT, 1)
    put_text(out, "IŞIK DENEYİ: 1. ÇEKİM vs 2. ÇEKİM", (14, 9), 15, MINT)
    put_text(out, HARITA_ADLARI.get(map_name, map_name) + "  [1-4]", (14, 33), 13, CREAM)

    footer_y = height - 28

    # Henüz hiç çekim alınmadıysa büyük ve çok net 2 adımlı rehber
    if cekim_1 is None:
        kutu_y = 74
        cv2.rectangle(out, (14, kutu_y), (width - 14, kutu_y + 210), PLUM_CARD, -1)
        cv2.rectangle(out, (14, kutu_y), (width - 14, kutu_y + 210), MINT, 1)
        put_text(out, "2 Adımda Işık Hilesini Gör:", (28, kutu_y + 16), 17, GOLD)
        put_text(out, "ADIM 1:", (28, kutu_y + 54), 14, MINT)
        put_text(out, "Normal dururken [BOŞLUK] tuşuna bas.", (104, kutu_y + 54), 14, CREAM)
        put_text(out, "ADIM 2:", (28, kutu_y + 92), 14, PEACH)
        put_text(out, "Telefon ışığı tut / yan dön, tekrar [BOŞLUK] bas.", (104, kutu_y + 92), 14, CREAM)
        put_text(out, "SONUÇ:", (28, kutu_y + 132), 14, GOLD)
        put_text(out, "Cildin aynı olduğu halde kameranın nasıl", (104, kutu_y + 132), 14, CREAM)
        put_text(out, "farklı sayılar ürettiğini yan yana gör!", (104, kutu_y + 154), 14, CREAM)
        put_text(out, "[r] Bölge maskesi  ·  [s] PNG kaydet  ·  [F] Yardım", (14, footer_y), 12, MUTED)
        return out

    # Dinamik görsel kutu yüksekliği (alt tabloya her zaman en az 185 px yer bırakır)
    y_top = 66
    avail_img_h = max(105, footer_y - y_top - 190)

    if cekim_2 is None:
        hm = harita_kucuk(cekim_1, map_name, width - 40, avail_img_h)
        x0 = (width - hm.shape[1]) // 2
        out[y_top:y_top + hm.shape[0], x0:x0 + hm.shape[1]] = hm
        cv2.rectangle(out, (x0, y_top), (x0 + hm.shape[1], y_top + hm.shape[0]), MINT, 2)
        y_tbl = y_top + hm.shape[0] + 12

        cv2.rectangle(out, (14, y_tbl), (width - 14, footer_y - 10), PLUM_CARD, -1)
        cv2.rectangle(out, (14, y_tbl), (width - 14, footer_y - 10), MINT, 1)
        put_text(out, "1. ÇEKİM ALINDI! Şimdi 2. Adım:", (26, y_tbl + 12), 15, GOLD)
        put_text(out, "Yüzüne telefon feneri tut veya pencereye dönüp", (26, y_tbl + 42), 13, CREAM)
        put_text(out, "tekrar [BOŞLUK] tuşuna bas -> karşılaştırma açılır!", (26, y_tbl + 64), 13, MINT)
        s1 = ozet_degerler(cekim_1)
        put_text(
            out,
            f"1. Çekim -> Kızarıklık:{s1['kizarik']:+.1f}  Parlama:%{s1['parlama']:.1f}  Doku:{s1['doku']:.1f}",
            (26, y_tbl + 100), 12, MUTED,
        )
    else:
        slot_w = (width - 36) // 2
        slot_h = avail_img_h
        for idx, (lbl, rep, col) in enumerate([("1. ÇEKİM (Önce)", cekim_1, MINT), ("2. ÇEKİM (Yeni Işık)", cekim_2, PEACH)]):
            sx = 12 + idx * (slot_w + 12)
            cv2.rectangle(out, (sx, y_top), (sx + slot_w, y_top + slot_h), PLUM_CARD, -1)
            hm = harita_kucuk(rep, map_name, slot_w - 8, max(70, slot_h - 26))
            ox = sx + (slot_w - hm.shape[1]) // 2
            oy = y_top + 23
            out[oy:oy + hm.shape[0], ox:ox + hm.shape[1]] = hm
            put_text(out, lbl, (sx + 8, y_top + 4), 12, col)
            cv2.rectangle(out, (sx, y_top), (sx + slot_w, y_top + slot_h), col, 1)

        y_tbl = y_top + slot_h + 10
        cv2.rectangle(out, (12, y_tbl), (width - 12, footer_y - 8), PLUM_CARD, -1)
        cv2.rectangle(out, (12, y_tbl), (width - 12, footer_y - 8), (85, 50, 105), 1)

        s1, s2 = ozet_degerler(cekim_1), ozet_degerler(cekim_2)
        put_text(out, "KARŞILAŞTIRMA TABLOSU", (22, y_tbl + 7), 14, GOLD)
        cols = [22, 218, 292, 372]
        yy = y_tbl + 29
        for cx, htxt in zip(cols, ["Ölçülen Özellik", "1.Çekim", "2.Çekim", "Değişim"]):
            put_text(out, htxt, (cx, yy), 12, MUTED)

        satirlar = [
            ("Kızarıklık tonu", f"{s1['kizarik']:+.1f}", f"{s2['kizarik']:+.1f}", f"{s2['kizarik'] - s1['kizarik']:+.1f}"),
            ("Parlama oranı", f"%{s1['parlama']:.1f}", f"%{s2['parlama']:.1f}", f"{s2['parlama'] - s1['parlama']:+.1f}%"),
            ("Cilt dokusu", f"{s1['doku']:.1f}", f"{s2['doku']:.1f}", f"{s2['doku'] - s1['doku']:+.1f}"),
            ("Sağ-Sol yanak farkı", f"{s1['yanak_fark']:.1f}", f"{s2['yanak_fark']:.1f}", f"{s2['yanak_fark'] - s1['yanak_fark']:+.1f}"),
        ]
        for ad, v1, v2, vf in satirlar:
            yy += 21
            if yy + 18 > footer_y - 24:
                break
            put_text(out, ad, (cols[0], yy), 12, CREAM)
            put_text(out, v1, (cols[1], yy), 12, MINT)
            put_text(out, v2, (cols[2], yy), 12, PEACH)
            put_text(out, vf, (cols[3], yy), 12, GOLD)

        if yy + 22 < footer_y - 6:
            put_text(out, "Sonuç: Cildin değişmedi, sadece ışık sayıları değiştirdi!", (22, footer_y - 28), 12, GOLD)

    put_text(out, "[Boşluk] Yeni çekim  ·  [c] Sıfırla  ·  [s] PNG kaydet", (14, footer_y), 12, MUTED)
    return out


def main() -> None:
    args = build_parser("Işık Kamerayı Nasıl Yanıltır? - 1. ve 2. Çekim Deneyi").parse_args()
    prepare, fps = FramePreparer(config.PROCESS_WIDTH), FPSMeter()
    analyzer = SkinAnalyzer(use_segmenter=True)

    cekim_1: SkinReport | None = None
    cekim_2: SkinReport | None = None
    map_name = MAP_KEYS[0]
    show_regions = True
    bildirim = ""
    bildirim_bitis = 0.0

    with Camera(args.source, config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT) as cam, \
            FaceTracker() as faces, \
            DisplayLoop(
                "SEIS BONUS 4 - Isik Kamerayi Nasil Yaniltir?",
                args,
                help_title="Bonus 4 · Işık Kamerayı Nasıl Yanıltır? (1. vs 2. Çekim)",
                help_lines=HELP_LINES,
            ) as loop:
        while loop.running:
            raw = cam.read()
            if raw is None:
                break
            frame = prepare(raw)
            result = faces.process(frame)

            # 860px genişlik -> ~484px yükseklik: sağ panelde hiçbir satır kesilmez!
            canvas = Canvas(frame, width=860, mirror=not args.no_mirror)
            if show_regions and len(result.faces) == 1:
                face = result.faces[0]
                live_reg = build_region_masks(
                    canvas.image, canvas.pts(face.points), face.width_px * canvas.scale,
                    config.SKIN_ROI_EROSION_RATIO, None,
                )
                draw_regions(canvas.image, live_reg)
            canvas.flip()
            img = canvas.image
            disclaimer(img)

            # Sol üstte sade adım göstergesi (yüzü kapatmaz!)
            adim_metni = (
                "ADIM 1: [BOŞLUK] bas -> 1. Çekimi al"
                if cekim_1 is None else
                ("ADIM 2: Işığı değiştirip [BOŞLUK] bas -> 2. Çekimi al"
                 if cekim_2 is None else
                 "TAMAMLANDI! Sağda 1. ve 2. çekim farkını incele")
            )
            put_text(img, adim_metni, (14, 38), 15, MINT, bg=PLUM_DARK)
            put_text(img, f"FPS {fps.tick():.0f}", (img.shape[1] - 86, 38), 14, CREAM, bg=PLUM_DARK)

            if time.monotonic() < bildirim_bitis and bildirim:
                put_text(img, bildirim, (14, img.shape[0] - 68), 15, GOLD, bg=PLUM_DARK)

            alt_ipucu = (
                "[Boşluk] Fotoğraf Çek  ·  [1-4] Harita  ·  [r] Maske Aç/Kapa  ·  [c] Sıfırla  ·  [s] Kaydet"
                if len(result.faces) == 1 else "Lütfen kameraya tek kişi olarak bakın."
            )
            status_line(img, alt_ipucu, "ok" if len(result.faces) == 1 else "warn")

            sag = sag_panel_ciz(cekim_1, cekim_2, map_name, height=img.shape[0], width=470)
            birlesik = np.hstack([img, sag])
            key = loop.show(birlesik)

            if key == ord(" "):
                yeni = esnek_cekim_al(analyzer, frame, result.faces)
                if yeni is None:
                    bildirim = "Yüz algılanamadı! Kameraya bakıp tekrar Boşluk bas."
                elif cekim_1 is None:
                    cekim_1 = yeni
                    bildirim = "1. Çekim alındı! Şimdi telefon ışığı tutup tekrar Boşluk bas."
                else:
                    cekim_2 = yeni
                    bildirim = "2. Çekim alındı! Sağdaki değişim tablosuna bak!"
                bildirim_bitis = time.monotonic() + 3.0
            elif ord("1") <= key <= ord("4"):
                map_name = MAP_KEYS[key - ord("1")]
            elif key in (ord("r"), ord("R")):
                show_regions = not show_regions
            elif key in (ord("c"), ord("C")):
                cekim_1 = cekim_2 = None
                bildirim = "Sıfırlandı — 1. Çekim için tekrar Boşluk bas."
                bildirim_bitis = time.monotonic() + 2.0
            elif key in (ord("s"), ord("S")):
                dosya = f"isik_deneyi_{int(time.time())}.png"
                cv2.imwrite(dosya, birlesik)
                bildirim = f"Rapor kaydedildi: {dosya}"
                bildirim_bitis = time.monotonic() + 2.4
    analyzer.close()


if __name__ == "__main__":
    try:
        main()
    except (CameraError, ModelMissingError) as exc:
        print(exc)
