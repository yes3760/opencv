"""01 - İlk kamera görüntüsü

Öğrenme hedefi: Kamerayı açmak, kare okumak, ekranda göstermek ve kamerayı
düzgün kapatmak. Bu örnek yalnızca OpenCV kullanır; yardımcı modül yoktur.

Çalıştırma : python examples/01_kamera.py
Kamerasız  : python examples/01_kamera.py --source video.mp4
Çıkış      : q veya Esc
"""

import argparse
import time

import cv2

parser = argparse.ArgumentParser(description="İlk kamera görüntüsü")
parser.add_argument("--source", default="0", help="Kamera numarası (0, 1, ...) veya video dosyası")
parser.add_argument("--max-frames", type=int, default=0, help="Otomatik test için kare sınırı")
args = parser.parse_args()
source = int(args.source) if args.source.isdigit() else args.source

cap = cv2.VideoCapture(source)
if not cap.isOpened():
    print("Kamera açılamadı. Başka bir uygulama kamerayı kullanıyor olabilir "
          "veya kamera izni verilmemiş olabilir.")
    raise SystemExit(1)

frames = 0
fps = 0.0
last = time.perf_counter()
try:
    while True:
        ok, frame = cap.read()             # ok: okuma başarılı mı, frame: NumPy dizisi
        if not ok:
            print("Kare okunamadı; kaynak bitti veya kamera bağlantısı kesildi.")
            break

        if frames == 30 and frame.mean() < 5:
            # Bazı bilgisayarlarda 0 numara başka bir kameradır (ör. Mac'te iPhone).
            print("Görüntü siyah görünüyor. Mercek kapalı olabilir; başka kamera için: --source 1")
        frame = cv2.flip(frame, 1)         # 1: yatay çevirme, ayna görüntüsü
        now = time.perf_counter()
        fps = 0.9 * fps + 0.1 * (1.0 / max(now - last, 1e-6))   # yumuşatılmış FPS
        last = now

        height, width, channels = frame.shape
        info = f"{width}x{height}x{channels} {frame.dtype}  FPS: {fps:.1f}"
        # cv2.putText Türkçe karakterleri çizemez; bu yüzden burada ASCII kullanılır.
        cv2.putText(frame, info, (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (191, 212, 45), 2, cv2.LINE_AA)
        cv2.imshow("VISION LAB - 01 Kamera (q: cikis)", frame)

        frames += 1
        key = cv2.waitKey(1) & 0xFF        # 1 ms bekle; pencerenin çizilmesi için gerekli
        if key in (ord("q"), 27) or (args.max_frames and frames >= args.max_frames):
            break
finally:
    cap.release()                          # kamerayı bırak: kamera ışığı sönmeli
    cv2.destroyAllWindows()
    print(f"{frames} kare gösterildi. Kamera serbest bırakıldı.")
