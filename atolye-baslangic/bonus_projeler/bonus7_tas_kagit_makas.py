"""BONUS PROJE 7 — Yapay Zekâya Karşı Taş–Kağıt–Makas (21 El Eklem Noktası)

Kameraya gösterdiğiniz el işaretini parmak açılarına göre anlık tanır:
  • ✊ TAŞ   : 0 veya 1 açık parmak (yumruk)
  • ✌️ MAKAS : İşaret + orta parmak açık, yüzük + serçe kapalı
  • 🖐️ KAĞIT : 4 veya 5 açık parmak (açık el)

Çalıştırma : python bonus_projeler/bonus7_tas_kagit_makas.py
Tuşlar     : Boşluk: Yeni Tur (3-2-1 geri sayım) | c: Skoru sıfırla | f: Özellikler | q: Çıkış
"""

from __future__ import annotations

import random
import sys
import time
from pathlib import Path

for _p in Path(__file__).resolve().parents:
    if (_p / "src").is_dir():
        sys.path.insert(0, str(_p / "src"))
        break

import cv2
import numpy as np

import config
from camera import Camera, CameraError
from common.app import Canvas, DisplayLoop, build_parser
from common.draw import AMBER, BLUE, GRAY, INK, RED, TEAL, WHITE, panel, put_text, status_line
from common.frame import FramePreparer
from common.models import ModelMissingError
from hands.gestures import finger_states
from hands.overlay import draw_hand
from hands.tracker import HandTracker

HAMLELER = ["TAŞ", "KAĞIT", "MAKAS"]
KAZANAN = {("TAŞ", "MAKAS"), ("KAĞIT", "TAŞ"), ("MAKAS", "KAĞIT")}

HELP_LINES = [
    "Amaç: 21 el eklem noktasından parmak durumlarını okuyarak bilgisayara karşı Taş–Kağıt–Makas oynamak.",
    "• ✊ TAŞ (yumruk)  ·  ✌️ MAKAS (işaret+orta açık)  ·  🖐️ KAĞIT (4-5 parmak açık).",
    "• [Boşluk / Space] 3-2-1 geri sayımını başlatır; süre bitince elindeki hamle okunur!",
    "• [c] Skor tablosunu ve galibiyet serisini sıfırlar.",
    "• [F] Bu rehberi aç/kapat  ·  [Q / Esc] Çıkış.",
]


def hamle_tani(points) -> str | None:
    """Parmak açık/kapalı durumlarından TAŞ, KAĞIT veya MAKAS döndürür."""
    st = finger_states(points)
    acik = sum(1 for v in st.values() if v is True)
    if acik <= 1:
        return "TAŞ"
    if acik >= 4:
        return "KAĞIT"
    if st.get("işaret") is True and st.get("orta") is True and st.get("yüzük") is False and st.get("serçe") is False:
        return "MAKAS"
    return None


def main() -> None:
    args = build_parser("Taş-Kağıt-Makas (AI vs Sen)").parse_args()
    prepare = FramePreparer(config.PROCESS_WIDTH)

    sen_skor = 0
    ai_skor = 0
    berabere = 0
    seri = 0

    geri_sayim_bitis: float | None = None
    son_sen: str | None = None
    son_ai: str | None = None
    son_sonuc = "Başlamak için [Boşluk] tuşuna bas!"
    son_renk = TEAL

    with Camera(args.source, config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT) as cam, \
            HandTracker(max_hands=1) as hands, \
            DisplayLoop(
                "SEIS BONUS 7 - Tas Kagit Makas (AI vs Sen)",
                args,
                help_title="Bonus 7 · Yapay Zekâya Karşı Taş–Kağıt–Makas",
                help_lines=HELP_LINES,
            ) as loop:
        while loop.running:
            raw = cam.read()
            if raw is None:
                break
            frame = prepare(raw)
            result = hands.process(frame)
            canvas = Canvas(frame, width=920, mirror=not args.no_mirror)

            hand = result.hands[0] if result.hands else None
            anlik_hamle = hamle_tani(hand.points) if hand else None
            if hand:
                draw_hand(canvas.image, canvas.pts(hand.points))

            canvas.flip()
            img = canvas.image
            h, w = img.shape[:2]

            # Geri sayım kontrolü
            now = time.monotonic()
            if geri_sayim_bitis is not None:
                kalan = geri_sayim_bitis - now
                if kalan > 0:
                    sayi = int(np.ceil(kalan))
                    cx, cy = w // 2, h // 2 - 20
                    panel(img, cx - 95, cy - 68, cx + 95, cy + 68, alpha=0.82)
                    cv2.circle(img, (cx, cy), 56, TEAL, 3, cv2.LINE_AA)
                    put_text(img, str(sayi), (cx - 18, cy - 32), 54, AMBER)
                    put_text(img, "HAMLE HAZIRLA!", (cx - 72, cy + 40), 14, WHITE)
                else:
                    geri_sayim_bitis = None
                    if anlik_hamle is None:
                        son_sen, son_ai = "ALGILANMADI", "-"
                        son_sonuc = "El görünmedi! Tekrar [Boşluk] bas."
                        son_renk = AMBER
                    else:
                        son_sen = anlik_hamle
                        son_ai = random.choice(HAMLELER)
                        if son_sen == son_ai:
                            berabere += 1
                            son_sonuc = f"BERABERE! ({son_sen} = {son_ai})"
                            son_renk = BLUE
                        elif (son_sen, son_ai) in KAZANAN:
                            sen_skor += 1
                            seri += 1
                            son_sonuc = f"KAZANDIN! ({son_sen} > {son_ai})"
                            son_renk = TEAL
                        else:
                            ai_skor += 1
                            seri = 0
                            son_sonuc = f"BİLGİSAYAR KAZANDI! ({son_ai} > {son_sen})"
                            son_renk = RED

            # Üst skor tabelası
            panel(img, 0, 0, w, 46, alpha=0.84)
            put_text(img, f"SEN {sen_skor}  :  {ai_skor} BİLGİSAYAR   (Berabere: {berabere} · Seri: {seri})",
                     (16, 12), 17, WHITE)

            # Sol alt: Anlık algılanan el hamlesi
            panel(img, 14, 58, 280, 146, alpha=0.78)
            put_text(img, "Canlı El Algılama", (26, 66), 14, GRAY)
            put_text(img, anlik_hamle or "El bekleniyor...", (26, 94), 24, TEAL if anlik_hamle else AMBER)

            # Sağ alt: Son tur sonucu
            panel(img, w - 340, 58, w - 14, 176, alpha=0.80)
            put_text(img, "Son Tur Sonucu", (w - 326, 66), 14, GRAY)
            put_text(img, f"Sen: {son_sen or '-'}   vs   AI: {son_ai or '-'}", (w - 326, 94), 17, WHITE)
            put_text(img, son_sonuc, (w - 326, 128), 15, son_renk)

            status_line(img, "[Boşluk] Yeni Tur Başlat (3-2-1)  ·  [c] Skoru Sıfırla  ·  [F] Özellikler",
                        "ok" if hand else "warn")

            key = loop.show(img)
            if key == ord(" ") and geri_sayim_bitis is None:
                geri_sayim_bitis = time.monotonic() + 2.6
            elif key in (ord("c"), ord("C")):
                sen_skor = ai_skor = berabere = seri = 0
                son_sen = son_ai = None
                son_sonuc = "Skor sıfırlandı! [Boşluk] ile başla."
                son_renk = TEAL


if __name__ == "__main__":
    try:
        main()
    except (CameraError, ModelMissingError) as exc:
        print(exc)
