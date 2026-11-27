"""BONUS PROJE 6 — SEIS Neon Flappy Oyunu (Göz Kırpma / Ağız Açma / Kafa Kontrolü)

Ek kütüphane (pyautogui vb.) gerektirmez — tamamen OpenCV + MediaPipe ile çalışır!
3 farklı temassız kontrol modu arasında 'm' tuşuyla anında geçiş yapabilirsiniz:
  1) KAFA MODU (Varsayılan · En Kolay): Başını yukarı/aşağı oynat -> kuş burnunu takip eder!
  2) GÖZ KIRPMA (EAR): Gözünü her kırptığında kuş zıplar!
  3) AĞIZ AÇMA (MAR): Ağzını açınca kuş zıplar!

Çalıştırma : python bonus_projeler/bonus6_goz_flappy_oyunu.py
Tuşlar     : m: Kontrol modu değiştir | Boşluk / r: Yeniden başlat | f: Özellikler | q: Çıkış
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

import os
os.environ.setdefault("OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS", "0")
import cv2
import numpy as np

import config
from camera import Camera, CameraError
from common.app import Canvas, DisplayLoop, build_parser
from common.draw import AMBER, GRAY, INK, RED, TEAL, WHITE, panel, put_text, status_line
from common.frame import FramePreparer
from common.models import ModelMissingError
from face.metrics import LEFT_EYE_EAR, RIGHT_EYE_EAR, BlinkDetector, eye_aspect_ratio, mouth_aspect_ratio
from face.tracker import FaceTracker

MODLAR = ["KAFA (Burun Takibi)", "GÖZ KIRPMA (EAR)", "AĞIZ AÇMA (MAR)"]

HELP_LINES = [
    "Amaç: Yüz hareketlerinle (kafa, göz kırpma veya ağız açma) neon Flappy oyununu temassız oynamak!",
    "• [m] Kontrol modunu değiştirir: 1) Kafa (en kolay)  2) Göz Kırpma (EAR)  3) Ağız Açma (MAR).",
    "• [Boşluk / r] Oyun bittiğinde anında yeniden başlatır · En yüksek skor otomatik tutulur!",
    "• İpucu: Tarayıcıdaki Chrome Dino için aynı EAR/MAR tetiklemesine pyautogui.press('space') bağlanabilir.",
    "• [F] Bu rehberi aç/kapat  ·  [Q / Esc] Çıkış.",
]


def boru_uret(w: int, h: int, aralik: int = 168) -> dict:
    ust_h = random.randint(75, max(95, h - aralik - 115))
    return {"x": float(w + 40), "ust": ust_h, "aralik": aralik, "gecti": False}


def main() -> None:
    args = build_parser("SEIS Neon Flappy - Göz/Ağız/Kafa Oyunu").parse_args()
    prepare = FramePreparer(config.PROCESS_WIDTH)
    blink = BlinkDetector()

    mod_idx = 0
    skor = 0
    rekor = 0
    oyun_bitti = False
    basladi = False

    kus_y = 240.0
    kus_vy = 0.0
    borular: list[dict] = []
    son_agiz_acik = False
    son_blink = 0
    son_zaman = time.perf_counter()

    with Camera(args.source, config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT) as cam, \
            FaceTracker(max_faces=1) as faces, \
            DisplayLoop(
                "SEIS BONUS 6 - Neon Flappy (Goz / Agiz / Kafa)",
                args,
                help_title="Bonus 6 · SEIS Neon Flappy (Göz / Ağız / Kafa Kontrolü)",
                help_lines=HELP_LINES,
            ) as loop:
        while loop.running:
            raw = cam.read()
            if raw is None:
                break
            frame = prepare(raw)
            result = faces.process(frame)
            canvas = Canvas(frame, width=920, mirror=not args.no_mirror)
            canvas.flip()
            img = canvas.image
            h, w = img.shape[:2]

            # Oyun arka planını hafifçe karart ki neon borular ve kuş net parlasın
            cv2.convertScaleAbs(img, alpha=0.58, beta=0, dst=img)

            now = time.perf_counter()
            dt = min(0.05, now - son_zaman)
            son_zaman = now

            kus_x = int(w * 0.24)
            kus_r = 18
            ear = 0.0
            mar = 0.0
            zipla = False

            if result.faces:
                face = result.faces[0]
                p = face.points
                ear = (eye_aspect_ratio(p, RIGHT_EYE_EAR) + eye_aspect_ratio(p, LEFT_EYE_EAR)) / 2.0
                blink.update(ear)
                mar = mouth_aspect_ratio(p)

                # Mod 0: Kafa (Burun noktası 1) — en kolay ve akıcı mod
                if mod_idx == 0:
                    _, burun_y = canvas.screen(p[1])
                    hedef_y = float(np.clip((burun_y - h * 0.22) / max(h * 0.56, 1.0) * (h - 90) + 45, 45, h - 60))
                    kus_y += (hedef_y - kus_y) * 0.28
                    if not basladi and not oyun_bitti:
                        basladi = True
                # Mod 1: Göz kırpma (EAR)
                elif mod_idx == 1:
                    if blink.blinks > son_blink:
                        son_blink = blink.blinks
                        zipla = True
                # Mod 2: Ağız açma (MAR)
                elif mod_idx == 2:
                    agiz_acik = mar > max(0.32, config.MOUTH_OPEN_MAR * 0.85)
                    if agiz_acik and not son_agiz_acik:
                        zipla = True
                    son_agiz_acik = agiz_acik

            if zipla:
                if oyun_bitti:
                    borular.clear()
                    skor = 0
                    kus_y = h * 0.45
                    kus_vy = -310.0
                    oyun_bitti = False
                    basladi = True
                else:
                    basladi = True
                    kus_vy = -310.0

            # Fizik ve boru hareketi
            if basladi and not oyun_bitti:
                if mod_idx != 0:
                    kus_vy += 860.0 * dt
                    kus_y += kus_vy * dt
                if not borular or borular[-1]["x"] < w - 300:
                    borular.append(boru_uret(w, h, aralik=max(150, int(h * 0.34))))
                hiz = 185.0 + min(130.0, skor * 6.0)
                for b in borular:
                    b["x"] -= hiz * dt
                    if not b["gecti"] and b["x"] + 58 < kus_x:
                        b["gecti"] = True
                        skor += 1
                        rekor = max(rekor, skor)
                borular = [b for b in borular if b["x"] > -80]

                # Çarpışma kontrolü
                if kus_y - kus_r < 34 or kus_y + kus_r > h - 38:
                    oyun_bitti = True
                for b in borular:
                    bx1, bx2 = int(b["x"]), int(b["x"] + 58)
                    if bx1 - kus_r < kus_x < bx2 + kus_r:
                        if kus_y - kus_r < b["ust"] or kus_y + kus_r > b["ust"] + b["aralik"]:
                            oyun_bitti = True

            # Neon boruları çiz
            for b in borular:
                bx1, bx2 = int(b["x"]), int(b["x"] + 58)
                ust = int(b["ust"])
                alt = int(b["ust"] + b["aralik"])
                cv2.rectangle(img, (bx1, 34), (bx2, ust), (90, 210, 120), -1)
                cv2.rectangle(img, (bx1, 34), (bx2, ust), (180, 255, 200), 2)
                cv2.rectangle(img, (bx1, alt), (bx2, h - 38), (90, 210, 120), -1)
                cv2.rectangle(img, (bx1, alt), (bx2, h - 38), (180, 255, 200), 2)

            # Neon SEIS kuşunu çiz
            ky = int(np.clip(kus_y, 40, h - 46))
            cv2.circle(img, (kus_x, ky), kus_r + 6, (90, 220, 255), 2, cv2.LINE_AA)
            cv2.circle(img, (kus_x, ky), kus_r, (40, 210, 255), -1, cv2.LINE_AA)
            cv2.circle(img, (kus_x + 7, ky - 5), 5, WHITE, -1, cv2.LINE_AA)
            cv2.circle(img, (kus_x + 9, ky - 5), 2, INK, -1, cv2.LINE_AA)
            cv2.polylines(img, [np.array([[kus_x + 16, ky - 2], [kus_x + 28, ky + 2], [kus_x + 16, ky + 7]])],
                          True, AMBER, 2, cv2.LINE_AA)

            # Üst skor & mod paneli
            panel(img, 0, 0, w, 40, alpha=0.82)
            put_text(img, f"SKOR: {skor}   REKOR: {rekor}   ·   Mod: {MODLAR[mod_idx]} [m]",
                     (14, 10), 16, TEAL)
            put_text(img, f"EAR:{ear:.2f}  MAR:{mar:.2f}", (w - 300, 11), 13, GRAY)

            if not basladi and not oyun_bitti:
                panel(img, w // 2 - 220, h // 2 - 44, w // 2 + 220, h // 2 + 44, alpha=0.85)
                put_text(img, "Başlamak için göz kırp / ağzını aç / Boşluk bas!",
                         (w // 2 - 200, h // 2 - 14), 15, WHITE)
            elif oyun_bitti:
                panel(img, w // 2 - 190, h // 2 - 58, w // 2 + 190, h // 2 + 58, alpha=0.88)
                cv2.rectangle(img, (w // 2 - 190, h // 2 - 58), (w // 2 + 190, h // 2 + 58), RED, 2)
                put_text(img, f"OYUN BİTTİ!   Skor: {skor}  (Rekor: {rekor})", (w // 2 - 165, h // 2 - 36), 17, AMBER)
                put_text(img, "Tekrar oynamak için [Boşluk] veya [r] tuşuna bas", (w // 2 - 170, h // 2 + 6), 14, WHITE)

            status_line(img, "[m] Mod değiştir (Kafa / Göz / Ağız)  ·  [r] Yeniden başlat  ·  [F] Özellikler",
                        "ok" if result.faces else "warn")

            key = loop.show(img)
            if key in (ord("m"), ord("M")):
                mod_idx = (mod_idx + 1) % len(MODLAR)
                kus_vy = 0.0
                son_blink = blink.blinks
            elif key in (ord(" "), ord("r"), ord("R")):
                borular.clear()
                skor = 0
                kus_y = h * 0.45
                kus_vy = -260.0 if mod_idx != 0 else 0.0
                oyun_bitti = False
                basladi = True
                son_blink = blink.blinks


if __name__ == "__main__":
    try:
        main()
    except (CameraError, ModelMissingError) as exc:
        print(exc)
