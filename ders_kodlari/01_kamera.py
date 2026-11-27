"""01 - İlk kamera görüntüsü

Öğrenme hedefi: Kamerayı açmak, kare okumak, ekranda göstermek ve kamerayı
düzgün kapatmak. Bu örnek yalnızca OpenCV kullanır; yardımcı modül yoktur.

Çalıştırma : python examples/01_kamera.py
Kamerasız  : python examples/01_kamera.py --source video.mp4
Tuşlar     : f: Özellikler rehberi  |  q veya Esc: Çıkış
"""

import argparse
import time

import cv2

parser = argparse.ArgumentParser(description="İlk kamera görüntüsü")
parser.add_argument("--source", default="0", help="Kamera numarası (0, 1, ...) veya video dosyası")
parser.add_argument("--max-frames", type=int, default=0, help="Otomatik test için kare sınırı")
args = parser.parse_args()
source = int(args.source) if args.source.isdigit() else args.source

def kamera_ac(kaynak):
    """Kamerayı açar; Mac'te 0 numara (iPhone vb.) siyah/boş dönerse otomatik 1 numarayı dener."""
    import platform
    backend = cv2.CAP_AVFOUNDATION if platform.system() == "Darwin" and isinstance(kaynak, int) else cv2.CAP_ANY
    adaylar = [0, 1, 2] if kaynak == 0 else [kaynak]
    yedek = None
    for ad in adaylar:
        c = cv2.VideoCapture(ad, backend) if isinstance(ad, int) else cv2.VideoCapture(ad)
        if not c.isOpened():
            c.release()
            continue
        for _ in range(25):
            ok, test = c.read()
            if ok and test is not None and test.size > 0:
                if test.mean() >= 5.0 or not isinstance(ad, int):
                    if yedek is not None:
                        yedek.release()
                    return c
                if yedek is None:
                    yedek = c
                    c = None
                    break
            time.sleep(0.04)
        if c is not None:
            c.release()
    return yedek


cap = kamera_ac(source)
if cap is None:
    print("Kamera açılamadı veya görüntü gelmedi. Kamera iznini kontrol edin veya --source 1 deneyin.")
    raise SystemExit(1)

WIN = "VISION LAB - 01 Kamera (f: ozellikler | q: cikis)"
flags = cv2.WINDOW_NORMAL | (cv2.WINDOW_KEEPRATIO if hasattr(cv2, "WINDOW_KEEPRATIO") else 0)
cv2.namedWindow(WIN, flags)

frames = 0
fps = 0.0
show_help = False
sized = False
last = time.perf_counter()
try:
    while True:
        ok, frame = cap.read()             # ok: okuma başarılı mı, frame: NumPy dizisi
        if not ok:
            print("Kare okunamadı; kaynak bitti veya kamera bağlantısı kesildi.")
            break

        if frames == 30 and frame.mean() < 5:
            print("Görüntü siyah görünüyor. Mercek kapalı olabilir; başka kamera için: --source 1")
        frame = cv2.flip(frame, 1)         # 1: yatay çevirme, ayna görüntüsü
        now = time.perf_counter()
        fps = 0.9 * fps + 0.1 * (1.0 / max(now - last, 1e-6))   # yumuşatılmış FPS
        last = now

        height, width, channels = frame.shape
        if not sized:
            scale = min(1.0, 1120 / max(width, 1), 680 / max(height, 1))
            cv2.resizeWindow(WIN, int(width * scale), int(height * scale))
            sized = True

        info = f"{width}x{height}x{channels} {frame.dtype}  FPS: {fps:.1f}  |  [F] Ozellikler"
        cv2.rectangle(frame, (0, 0), (width, 40), (24, 18, 28), -1)
        cv2.putText(frame, info, (12, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.68, (191, 212, 45), 2, cv2.LINE_AA)

        if show_help:
            overlay = frame.copy()
            cv2.rectangle(overlay, (width // 2 - 270, height // 2 - 90),
                          (width // 2 + 270, height // 2 + 90), (24, 18, 28), -1)
            cv2.addWeighted(overlay, 0.88, frame, 0.12, 0, frame)
            cv2.rectangle(frame, (width // 2 - 270, height // 2 - 90),
                          (width // 2 + 270, height // 2 + 90), (191, 212, 45), 2)
            satirlar = [
                "01 - Ilk Kamera Goruntusu",
                "Amac: Kamerayi acmak, NumPy kare boyutunu ve FPS'i gormek.",
                "- Her kare (Yukseklik x Genislik x 3) uint8 dizisidir.",
                "- [F] Bu pencereyi ac/kapat   |   [Q / Esc] Cikis",
            ]
            for i, s in enumerate(satirlar):
                cv2.putText(frame, s, (width // 2 - 250, height // 2 - 48 + i * 34),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.52, (233, 239, 242) if i else (191, 212, 45), 1, cv2.LINE_AA)

        cv2.imshow(WIN, frame)

        frames += 1
        key = cv2.waitKey(1) & 0xFF        # 1 ms bekle; pencerenin çizilmesi için gerekli
        if key in (ord("f"), ord("F")):
            show_help = not show_help
        elif key in (ord("q"), 27) or (args.max_frames and frames >= args.max_frames):
            break
finally:
    cap.release()                          # kamerayı bırak: kamera ışığı sönmeli
    cv2.destroyAllWindows()
    print(f"{frames} kare gösterildi. Kamera serbest bırakıldı.")
