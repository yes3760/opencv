"""İşlem sürelerini ölçer (pencere açmadan, görüntü kaydetmeden).

Çalıştırma : python scripts/benchmark.py                 (kamera 0)
Dosyayla   : python scripts/benchmark.py --source video.mp4 --frames 200

Ölçülen süre yalnızca işlem süresidir; kamera ve ekran gecikmesi dahil değildir.
Sonuç, raporun "Deneyler ve değerlendirme" bölümündeki tabloya donanım bilgisiyle
birlikte yazılabilir.
"""

import argparse
import platform
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import cv2  # noqa: E402
import mediapipe as mp  # noqa: E402
import numpy as np  # noqa: E402

import config  # noqa: E402
from camera import Camera  # noqa: E402
from common.frame import FramePreparer  # noqa: E402
from face.tracker import FaceTracker  # noqa: E402
from hands.tracker import HandTracker  # noqa: E402
from skin.analyzer import SkinAnalyzer  # noqa: E402


def summary(values):
    values = sorted(values)
    p95 = values[min(len(values) - 1, int(len(values) * 0.95))]
    return f"ortanca {statistics.median(values):6.1f} ms   %95 {p95:6.1f} ms"


def main():
    parser = argparse.ArgumentParser(description="VISION LAB süre ölçümü")
    parser.add_argument("--source", default="auto")
    parser.add_argument("--frames", type=int, default=150)
    args = parser.parse_args()

    stages = {"kare hazırlığı": [], "yüz modeli": [], "el modeli": [], "toplam (yüz+el)": []}
    skin_times = []
    prepare = FramePreparer(config.PROCESS_WIDTH)
    analyzer = SkinAnalyzer()
    with Camera(args.source, config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT) as cam, \
            FaceTracker() as faces, HandTracker() as hands:
        size = cam.actual_size
        for i in range(args.frames):
            raw = cam.read()
            if raw is None:
                break
            t0 = time.perf_counter()
            frame = prepare(raw)
            t1 = time.perf_counter()
            face_res = faces.process(frame)
            t2 = time.perf_counter()
            hands.process(frame)
            t3 = time.perf_counter()
            if i >= 10:                      # ilk kareler model ısınması içindir
                stages["kare hazırlığı"].append((t1 - t0) * 1000)
                stages["yüz modeli"].append((t2 - t1) * 1000)
                stages["el modeli"].append((t3 - t2) * 1000)
                stages["toplam (yüz+el)"].append((t3 - t0) * 1000)
            if i >= 10 and i % 15 == 0:
                skin_times.append(analyzer.analyze(frame.full_bgr, face_res.faces, frame.scale_to_full).elapsed_ms)
    analyzer.close()

    print(f"Donanım : {platform.platform()} | {platform.machine()} | {platform.processor() or '-'}")
    print(f"Sürümler: Python {platform.python_version()}, OpenCV {cv2.__version__}, "
          f"MediaPipe {mp.__version__}, NumPy {np.__version__}")
    print(f"Kaynak  : {args.source} | giriş {size[0]}x{size[1]} | işleme genişliği {config.PROCESS_WIDTH}")
    for name, values in stages.items():
        if values:
            print(f"{name:<18} {summary(values)}   (n={len(values)})")
    if stages["toplam (yüz+el)"]:
        med = statistics.median(stages["toplam (yüz+el)"])
        print(f"Yalnızca işlem süresine göre üst sınır: yaklaşık {1000 / med:.0f} kare/sn "
              "(kamera genellikle 30 kare/sn ile sınırlar)")
    if skin_times:
        print(f"{'cilt analizi':<18} {summary(skin_times)}   (n={len(skin_times)}, tek kare)")


if __name__ == "__main__":
    main()
