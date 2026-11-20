"""02 - Pikseller ve renk uzayları

Öğrenme hedefi: Görüntünün bir NumPy dizisi olduğunu görmek; BGR-RGB farkını,
gri tonlamayı, HSV ve LAB uzaylarını karşılaştırmak.

Çalıştırma : python examples/02_piksel_renk.py
Kullanım   : Görüntüye tıklayın; o pikselin değerleri terminale yazılır.
             b tuşu: "BGR'yi RGB sanma" hatasını aç/kapat.  q: çıkış
"""

import _yol  # noqa: F401  (src klasörünü bulmak için)

import cv2
import numpy as np

import config
from camera import Camera, CameraError
from common.app import DisplayLoop, build_parser
from common.draw import put_text
from common.frame import resize_to_width

TILE_W = 320


def label(img, text):
    put_text(img, text, (8, 6), 15, (233, 239, 242), bg=(31, 22, 15))
    return img


def gray3(channel):
    """Tek kanallı görüntüyü yan yana koyabilmek için 3 kanala çevirir."""
    return cv2.cvtColor(channel, cv2.COLOR_GRAY2BGR)


def main():
    args = build_parser("Pikseller ve renk uzayları").parse_args()
    state = {"swap": False, "frame": None}

    def on_click(event, x, y, flags, param):
        if event != cv2.EVENT_LBUTTONDOWN or state["frame"] is None:
            return
        small = state["frame"]
        th = small.shape[0]
        px, py = x % TILE_W, y % th              # hangi kutucuğa tıklanırsa aynı piksel
        b, g, r = small[py, px]
        h, s, v = cv2.cvtColor(small[py:py + 1, px:px + 1], cv2.COLOR_BGR2HSV)[0, 0]
        L, a, bb = cv2.cvtColor(small[py:py + 1, px:px + 1], cv2.COLOR_BGR2LAB)[0, 0]
        print(f"piksel (x={px}, y={py})  BGR=({b},{g},{r})  RGB=({r},{g},{b})  "
              f"HSV=({h},{s},{v})  LAB(8 bit)=({L},{a},{bb})  gri={int(0.114*b + 0.587*g + 0.299*r)}")

    try:
        with Camera(args.source, config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT) as cam, \
                DisplayLoop("VISION LAB - 02 Piksel ve renk", args) as loop:
            loop.on_mouse(on_click)
            first = cam.read()
            print(f"Kare: shape={first.shape} (yükseklik, genişlik, kanal), dtype={first.dtype}, "
                  f"en küçük={first.min()}, en büyük={first.max()}")
            while loop.running:
                frame = cam.read()
                if frame is None:
                    break
                if not args.no_mirror:
                    frame = cv2.flip(frame, 1)
                small = resize_to_width(frame, TILE_W)
                state["frame"] = small

                shown = small[:, :, ::-1].copy() if state["swap"] else small.copy()   # kanalları ters çevir
                gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
                lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB)

                row1 = np.hstack([
                    label(shown, "RGB sanılan BGR (hatalı)" if state["swap"] else "Orijinal (BGR)"),
                    label(gray3(gray), "Gri ton"),
                    label(gray3(hsv[..., 0]), "HSV: H (renk tonu)"),
                ])
                row2 = np.hstack([
                    label(gray3(hsv[..., 2]), "HSV: V (parlaklık)"),
                    label(gray3(lab[..., 0]), "LAB: L (açıklık)"),
                    label(gray3(lab[..., 1]), "LAB: a (yeşil-kırmızı)"),
                ])
                key = loop.show(np.vstack([row1, row2]))
                if key == ord("b"):
                    state["swap"] = not state["swap"]
    except CameraError as exc:
        print(exc)


if __name__ == "__main__":
    main()
