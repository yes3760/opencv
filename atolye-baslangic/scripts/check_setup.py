"""Kurulumun doğru yapıldığını kontrol eder.

Çalıştırma : python scripts/check_setup.py
Kamerayla  : python scripts/check_setup.py --kamera

Kontroller: Python sürümü, paketler, cv2 çakışması, model dosyaları, modellerin
yüklenmesi ve (istenirse) kameranın açılıp kapanması. Görüntü kaydedilmez.
"""

import argparse
import os

os.environ.setdefault("OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS", "0")
import platform
import sys
import time
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

OK, FAIL, WARN = "[tamam]", "[hata] ", "[uyarı]"
problems = 0


def report(ok: bool, text: str, warn_only: bool = False) -> None:
    global problems
    if ok:
        print(f"{OK} {text}")
    elif warn_only:
        print(f"{WARN} {text}")
    else:
        problems += 1
        print(f"{FAIL} {text}")


def version_of(name: str):
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="VISION LAB kurulum kontrolü")
    parser.add_argument("--kamera", action="store_true", help="Kamerayı da kısa süre açıp kapat.")
    parser.add_argument("--source", default="auto", help="auto veya kamera numarası")
    args = parser.parse_args()

    print(f"İşletim sistemi: {platform.system()} {platform.release()} ({platform.machine()})")
    v = sys.version_info
    report((3, 9) <= (v.major, v.minor) <= (3, 14), f"Python {v.major}.{v.minor}.{v.micro} "
           "(önerilen 3.12)")
    report(sys.prefix != sys.base_prefix, "Sanal ortam etkin", warn_only=True)

    for package in ("mediapipe", "opencv-contrib-python", "numpy", "pillow"):
        ver = version_of(package)
        report(ver is not None, f"{package} {ver or 'kurulu değil'}")
    other_cv = [p for p in ("opencv-python", "opencv-python-headless") if version_of(p)]
    report(not other_cv, "cv2 çakışması yok" if not other_cv else
           f"Aynı ortamda {', '.join(other_cv)} de kurulu. Kaldırın: pip uninstall {' '.join(other_cv)}")

    try:
        import cv2
        import mediapipe as mp
        import numpy as np
        report(True, f"İçe aktarma: cv2 {cv2.__version__}, mediapipe {mp.__version__}, numpy {np.__version__}")
    except Exception as exc:  # kurulum sorunlarını kullanıcıya göstermek için
        report(False, f"İçe aktarma başarısız: {exc}")
        return 1

    import config
    for path, required in ((config.FACE_MODEL, True), (config.HAND_MODEL, True), (config.SEGMENTER_MODEL, False)):
        exists = path.is_file() and path.stat().st_size > 0
        report(exists, f"Model {path.name}" + ("" if exists else " yok: python scripts/download_models.py"),
               warn_only=not required)

    try:
        from face.tracker import FaceTracker
        from hands.tracker import HandTracker
        from common.frame import FramePreparer
        blank = np.zeros((480, 640, 3), np.uint8)
        frame = FramePreparer(640)(blank)
        with FaceTracker() as faces, HandTracker() as hands:
            faces.process(frame)
            hands.process(frame)
        report(True, "Yüz ve el modelleri yüklendi ve boş karede çalıştı")
    except Exception as exc:
        report(False, f"Modeller çalıştırılamadı: {exc}")

    from common.draw import _get_renderer
    report(_get_renderer().unicode_ok, "Türkçe karakterli yazı tipi bulundu", warn_only=True)

    if args.kamera:
        from camera import Camera, CameraError
        try:
            start = time.perf_counter()
            with Camera(args.source, config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT) as cam:
                frames = [cam.read() for _ in range(30)]
                got = [f for f in frames if f is not None]
                size, index = cam.actual_size, cam.index
            elapsed = time.perf_counter() - start
            brightness = max((float(f.mean()) for f in got), default=0.0)
            report(len(got) == 30, f"Kamera {index} açıldı: {size[0]}x{size[1]}, {len(got)}/30 kare, "
                                   f"{elapsed:.1f} s; kamera serbest bırakıldı")
            report(brightness >= 5, f"Görüntü parlaklığı {brightness:.0f} / 255" + (
                "" if brightness >= 5 else ": görüntü siyah. Mercek kapalı olabilir veya bu numara "
                                          "başka bir kameraya ait; --source 1 deneyin."))
        except CameraError as exc:
            report(False, str(exc))

    print()
    if problems:
        print(f"{problems} sorun bulundu. Rapordaki 'Sık karşılaşılan sorunlar' bölümüne bakın.")
        return 1
    print("Ortam hazır. İlk örnek: python examples/01_kamera.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
