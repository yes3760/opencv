"""BONUS PROJE 5 — SEIS Sınıf Enerji & Gülümseme Ölçer (Gün Başı vs Eğitim Sonu)

Mevcut vision-workshop ortamındaki FaceTracker (max_faces=12, blendshapes=True)
ile çalışır; ek kütüphane veya yeni model gerektirmez.

Nasıl Çalışır?
  - Kameradaki tüm yüzleri (aynı anda 12 yüze kadar) gerçek zamanlı yakalar.
  - MediaPipe blendshape mimik katsayılarından (mouthSmileLeft/Right, cheekSquintLeft/Right)
    her yüzün canlı gülümseme / enerji skorunu (%0–%100) hesaplar.
  - 1 tuşu: GÜN BAŞI (16:00) sınıf enerjisini kaydeder.
  - 2 tuşu: EĞİTİM SONU (20:00) sınıf enerjisini kaydeder ve +Δ% artışı yan yana gösterir!
  - s tuşu: SEIS Instagram / hatıra için karşılaştırma raporunu PNG kaydeder.

Not: Yüz ifadesi (gülümseme/mimik) hareket sinyali ölçümüdür; psikolojik tanı değildir.

Çalıştırma : python bonus_projeler/bonus5_sinif_enerji_olcer.py
Tuşlar     : 1: Gün Başı Kaydet  |  2: Eğitim Sonu Kaydet  |  s: PNG Kaydet  |  c: Sıfırla  |  q: Çıkış
"""

import sys
import time
from pathlib import Path

import os
os.environ.setdefault("OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS", "0")
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

# SEIS Afiş Paleti (BGR)
PLUM_DARK = (18, 5, 28)
PLUM_CARD = (32, 10, 48)
MINT = (170, 232, 108)
CREAM = (218, 236, 247)
PEACH = (130, 161, 235)
GOLD = (85, 215, 255)
MUTED = (145, 132, 148)


def yuz_enerji_skoru(bs: dict[str, float]) -> float:
    """Blendshape mimik katsayılarından 0..100 arası canlı gülümseme/enerji skoru üretir."""
    if not bs:
        return 35.0
    gulumseme = (bs.get("mouthSmileLeft", 0.0) + bs.get("mouthSmileRight", 0.0)) / 2.0
    yanak = (bs.get("cheekSquintLeft", 0.0) + bs.get("cheekSquintRight", 0.0)) / 2.0
    kas_catik = (bs.get("browDownLeft", 0.0) + bs.get("browDownRight", 0.0)) / 2.0
    # Nötr ifade ~%35, güçlü gülümseme %95-100 bandına çıkar
    ham = 0.35 + 0.68 * gulumseme + 0.15 * yanak - 0.18 * kas_catik
    return float(max(5.0, min(100.0, ham * 100.0)))


def enerji_rengi(skor: float) -> tuple[int, int, int]:
    if skor >= 72:
        return MINT
    if skor >= 50:
        return GOLD
    return PEACH


def enerji_etiketi(skor: float) -> str:
    if skor >= 78:
        return "Çok Yüksek!"
    if skor >= 60:
        return "Pozitif"
    if skor >= 42:
        return "Odaklanmış"
    return "Düşük / Yorgun"


def bar_ciz(img: np.ndarray, x: int, y: int, w: int, h: int, yuzde: float, renk):
    cv2.rectangle(img, (x, y), (x + w, y + h), (26, 8, 38), -1)
    dolu = int(w * max(0.0, min(100.0, yuzde)) / 100.0)
    if dolu > 0:
        cv2.rectangle(img, (x, y), (x + dolu, y + h), renk, -1)
    cv2.rectangle(img, (x, y), (x + w, y + h), (90, 60, 110), 1)


def sag_panel_ciz(
    anlik_skor: float,
    anlik_kisi: int,
    gun_basi: dict | None,
    egitim_sonu: dict | None,
    height: int,
    width: int = 410,
) -> np.ndarray:
    """Sağ tarafta SEIS Sınıf Enerji Karşılaştırma Paneli çizer."""
    out = np.full((height, width, 3), PLUM_DARK, np.uint8)
    cv2.rectangle(out, (0, 0), (width, 56), PLUM_CARD, -1)
    cv2.line(out, (0, 56), (width, 56), MINT, 1)
    put_text(out, "SEIS SINIF ENERJİ ÖLÇER", (16, 10), 17, MINT)
    put_text(out, "Gün Başı vs Eğitim Sonu Karşılaştırma", (16, 33), 12, CREAM)

    # 1. Anlık Canlı Kart
    cv2.rectangle(out, (14, 70), (width - 14, 178), PLUM_CARD, -1)
    cv2.rectangle(out, (14, 70), (width - 14, 178), MINT, 1)
    put_text(out, f"CANLI SINIF ENERJİSİ ({anlik_kisi} yüz)", (24, 78), 13, MINT)
    renk = enerji_rengi(anlik_skor)
    put_text(out, f"%{anlik_skor:.0f}", (24, 102), 34, renk)
    put_text(out, enerji_etiketi(anlik_skor), (124, 116), 16, CREAM)
    bar_ciz(out, 24, 150, width - 48, 16, anlik_skor, renk)

    # 2. Gün Başı (16:00) Kaydı
    cv2.rectangle(out, (14, 192), (width - 14, 280), PLUM_CARD, -1)
    put_text(out, "1 · GÜN BAŞI ÖLÇÜMÜ (16:00)", (24, 200), 13, GOLD)
    if gun_basi:
        put_text(out, f"%{gun_basi['skor']:.1f}  ({gun_basi['kisi']} yüz · {gun_basi['saat']})", (24, 224), 16, CREAM)
        bar_ciz(out, 24, 254, width - 48, 14, gun_basi["skor"], GOLD)
    else:
        put_text(out, "Kaydetmek için [1] tuşuna bas", (24, 232), 14, MUTED)

    # 3. Eğitim Sonu (20:00) Kaydı
    cv2.rectangle(out, (14, 294), (width - 14, 382), PLUM_CARD, -1)
    put_text(out, "2 · EĞİTİM SONU ÖLÇÜMÜ (20:00)", (24, 302), 13, MINT)
    if egitim_sonu:
        put_text(out, f"%{egitim_sonu['skor']:.1f}  ({egitim_sonu['kisi']} yüz · {egitim_sonu['saat']})", (24, 326), 16, CREAM)
        bar_ciz(out, 24, 356, width - 48, 14, egitim_sonu["skor"], MINT)
    else:
        put_text(out, "Kaydetmek için [2] tuşuna bas", (24, 334), 14, MUTED)

    # 4. Fark / Sonuç Kartı
    y_res = 396
    if y_res + 74 < height:
        cv2.rectangle(out, (14, y_res), (width - 14, height - 34), (24, 48, 38) if (gun_basi and egitim_sonu) else PLUM_CARD, -1)
        if gun_basi and egitim_sonu:
            fark = egitim_sonu["skor"] - gun_basi["skor"]
            isaret = "+" if fark >= 0 else ""
            put_text(out, f"ENERJİ DEĞİŞİMİ: {isaret}%{fark:.1f}", (24, y_res + 12), 18, MINT if fark >= 0 else PEACH)
            put_text(out, "Harika bir SEIS OpenCV Atölyesi!", (24, y_res + 42), 13, CREAM)
        else:
            put_text(out, "1 ve 2 kaydedilince artış burada görünür.", (24, y_res + 20), 13, MUTED)

    put_text(out, "Mimik hareket sinyali ölçümüdür (eğitim demosu).", (14, height - 24), 11, MUTED)
    return out


def main():
    args = build_parser("SEIS Sınıf Enerji & Gülümseme Ölçer").parse_args()
    prepare, fps = FramePreparer(config.PROCESS_WIDTH), FPSMeter()

    gun_basi = None
    egitim_sonu = None
    smooth_skor = 50.0
    bildirim = ""
    bildirim_bitis = 0.0

    with Camera(args.source, config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT) as cam, \
            FaceTracker(max_faces=12, blendshapes=True) as faces, \
            DisplayLoop(
                "SEIS Sinif Enerji Olcer",
                args,
                help_title="Bonus 5 · SEIS Sınıf Enerji & Mutluluk Ölçer",
                help_lines=[
                    "Amaç: Sınıftaki 12 yüze kadar gülümseme/canlılık skorunu Gün Başı vs Eğitim Sonu kıyaslamak.",
                    "• [1] Gün Başı (16:00) sınıf ortalama enerjisini ve kişi sayısını kaydeder.",
                    "• [2] Eğitim Sonu (20:00) ölçümünü alır ve +Δ% değişim tablosunu gösterir.",
                    "• [s] Karşılaştırma raporunu PNG kaydet  ·  [c] Kayıtları sıfırla  ·  [F] Kapat.",
                ],
            ) as loop:
        while loop.running:
            raw = cam.read()
            if raw is None:
                break
            frame = prepare(raw)
            result = faces.process(frame)

            canvas = Canvas(frame, width=720, mirror=not args.no_mirror)
            skorlar = []
            etiketler = []

            for face in result.faces:
                skor = yuz_enerji_skoru(face.blendshapes)
                skorlar.append(skor)
                renk = enerji_rengi(skor)
                bx = canvas.pts(face.box)
                x1, y1, x2, y2 = int(bx[0]), int(bx[1]), int(bx[2]), int(bx[3])
                cv2.rectangle(canvas.image, (x1, y1), (x2, y2), renk, 2, cv2.LINE_AA)
                etiketler.append((face.box, skor, renk))

            canvas.flip()
            img = canvas.image

            for box, skor, renk in etiketler:
                px, py = canvas.screen((box[2] if canvas.mirror else box[0], box[1]))
                put_text(img, f"%{skor:.0f}", (int(px), max(10, int(py) - 24)), 15, renk, bg=PLUM_DARK)

            anlik = sum(skorlar) / len(skorlar) if skorlar else 0.0
            if skorlar:
                smooth_skor = 0.25 * anlik + 0.75 * smooth_skor
            goster_skor = smooth_skor if skorlar else 0.0

            put_text(img, f"Algılanan Yüz: {len(skorlar)}  ·  FPS {fps.tick():.0f}", (14, 12), 15, MINT, bg=PLUM_DARK)
            if time.monotonic() < bildirim_bitis and bildirim:
                put_text(img, bildirim, (14, img.shape[0] - 66), 16, GOLD, bg=PLUM_DARK)

            status_line(
                img,
                "[1] Gün Başı Kaydet  |  [2] Eğitim Sonu Kaydet  |  [s] PNG Rapor  |  [c] Sıfırla  |  [q] Çıkış",
                "ok" if skorlar else "warn",
            )

            sag = sag_panel_ciz(goster_skor, len(skorlar), gun_basi, egitim_sonu, height=img.shape[0])
            birlesik = np.hstack([img, sag])
            key = loop.show(birlesik)

            if key == ord("1") and skorlar:
                gun_basi = {"skor": goster_skor, "kisi": len(skorlar), "saat": time.strftime("%H:%M")}
                bildirim = f"✓ Gün Başı kaydedildi: %{goster_skor:.1f} ({len(skorlar)} yüz)"
                bildirim_bitis = time.monotonic() + 2.6
            elif key == ord("2") and skorlar:
                egitim_sonu = {"skor": goster_skor, "kisi": len(skorlar), "saat": time.strftime("%H:%M")}
                bildirim = f"✓ Eğitim Sonu kaydedildi: %{goster_skor:.1f} ({len(skorlar)} yüz)"
                bildirim_bitis = time.monotonic() + 2.6
            elif key == ord("c"):
                gun_basi = egitim_sonu = None
                bildirim = "Ölçümler sıfırlandı."
                bildirim_bitis = time.monotonic() + 1.8
            elif key == ord("s"):
                dosya = f"seis_sinif_enerji_{int(time.time())}.png"
                cv2.imwrite(dosya, birlesik)
                bildirim = f"📸 Kaydedildi: {dosya}"
                bildirim_bitis = time.monotonic() + 2.5


if __name__ == "__main__":
    try:
        main()
    except (CameraError, ModelMissingError) as exc:
        print(exc)
