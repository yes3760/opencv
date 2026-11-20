"""03 - ROI, bulanıklaştırma, eşikleme, morfoloji ve konturlar

Öğrenme hedefi: Kural tabanlı bir görüntü işleme hattını adım adım kurmak ve
her adımın süresini ölçmek.

Çalıştırma : python examples/03_filtre_esik.py
Kullanım   : Pencerenin üstündeki sürgülerle parametreleri değiştirin.
             Fareyle sürükleyerek ilgi bölgesini (ROI) seçin.  q: çıkış
"""

import _yol  # noqa: F401

import cv2
import numpy as np

import config
from camera import Camera, CameraError
from common.app import DisplayLoop, build_parser
from common.draw import AMBER, TEAL, put_text
from common.fps import FPSMeter, StageTimer
from common.frame import resize_to_width

WINDOW = "VISION LAB - 03 Filtre ve esik"
TILE_W = 400


def odd(n: int) -> int:
    """Gaussian çekirdeği tek sayı olmalıdır: 0->1, 4->9 gibi."""
    return 2 * n + 1


def main():
    args = build_parser("ROI, filtre, eşikleme ve konturlar").parse_args()
    roi = {"rect": None, "start": None}

    def on_mouse(event, x, y, flags, param):
        x = min(x, TILE_W - 1)                      # yalnızca ilk kutucukta seçim
        if event == cv2.EVENT_LBUTTONDOWN:
            roi["start"] = (x, y)
        elif event == cv2.EVENT_LBUTTONUP and roi["start"]:
            (x0, y0), (x1, y1) = roi["start"], (x, y)
            if abs(x1 - x0) > 10 and abs(y1 - y0) > 10:
                roi["rect"] = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
            else:
                roi["rect"] = None                  # küçük tıklama seçimi sıfırlar
            roi["start"] = None

    try:
        with Camera(args.source, config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT) as cam, \
                DisplayLoop(WINDOW, args) as loop:
            loop.on_mouse(on_mouse)
            cv2.createTrackbar("blur", WINDOW, 2, 10, lambda v: None)
            cv2.createTrackbar("esik (0=Otsu)", WINDOW, 0, 255, lambda v: None)
            cv2.createTrackbar("morfoloji", WINDOW, 2, 10, lambda v: None)
            timer, fps = StageTimer(), FPSMeter()

            while loop.running:
                frame = cam.read()
                if frame is None:
                    break
                if not args.no_mirror:
                    frame = cv2.flip(frame, 1)
                with timer.measure("boyut"):
                    small = resize_to_width(frame, TILE_W)              # yeniden boyutlandırma
                view = small.copy()
                x1, y1, x2, y2 = roi["rect"] or (0, 0, small.shape[1], small.shape[0])
                region = small[y1:y2, x1:x2]                            # ROI: dizinin bir dilimi

                k = odd(cv2.getTrackbarPos("blur", WINDOW))
                t = cv2.getTrackbarPos("esik (0=Otsu)", WINDOW)
                m = odd(cv2.getTrackbarPos("morfoloji", WINDOW))
                with timer.measure("gri+blur"):
                    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
                    blurred = cv2.GaussianBlur(gray, (k, k), 0)
                with timer.measure("eşik"):
                    if t == 0:   # Otsu, eşiği histogramdan otomatik seçer
                        used, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    else:
                        used, binary = cv2.threshold(blurred, t, 255, cv2.THRESH_BINARY)
                with timer.measure("morfoloji"):
                    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (m, m))
                    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)    # küçük lekeleri sil
                    cleaned = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)  # küçük delikleri kapat
                with timer.measure("kontur"):
                    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    big = [c for c in contours if cv2.contourArea(c) > 80]
                    cv2.drawContours(view[y1:y2, x1:x2], big, -1, TEAL, 2)
                cv2.rectangle(view, (x1, y1), (x2 - 1, y2 - 1), AMBER, 1)

                def tile(img):
                    out = np.zeros_like(small)
                    out[y1:y2, x1:x2] = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                    return out

                t_blur, t_bin, t_clean = tile(blurred), tile(binary), tile(cleaned)
                put_text(view, f"ROI {x2 - x1}x{y2 - y1}  kontur: {len(big)}", (8, 6), 15, bg=(31, 22, 15))
                put_text(t_blur, f"Gaussian {k}x{k}", (8, 6), 15, bg=(31, 22, 15))
                put_text(t_bin, f"eşik = {used:.0f}" + (" (Otsu)" if t == 0 else ""), (8, 6), 15, bg=(31, 22, 15))
                put_text(t_clean, f"açma + kapama {m}x{m}", (8, 6), 15, bg=(31, 22, 15))
                times = "  ".join(f"{name} {ms:.1f} ms" for name, ms in timer.ms.items())
                put_text(t_clean, f"FPS {fps.tick():.0f}", (8, t_clean.shape[0] - 26), 15, bg=(31, 22, 15))
                grid = np.vstack([np.hstack([view, t_blur]), np.hstack([t_bin, t_clean])])
                put_text(grid, times, (8, grid.shape[0] // 2 - 24), 14, bg=(31, 22, 15))
                loop.show(grid)
    except CameraError as exc:
        print(exc)


if __name__ == "__main__":
    main()
