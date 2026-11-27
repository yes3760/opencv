"""04 - Yüz tespiti ve yüz işaret noktaları

Öğrenme hedefi: Öğrenilmiş bir modelle (MediaPipe Face Landmarker) yüzü bulmak,
478 noktayı ve yüz kutusunu çizmek, yüz yoksa uygun mesaj göstermek.
Karşılaştırma için OpenCV'nin klasik Haar yöntemi de seçilebilir.

Çalıştırma : python examples/04_yuz_tespiti.py
Haar ile   : python examples/04_yuz_tespiti.py --yontem haar
Kullanım   : m tuşu: çizim biçimi (kontur / ağ / nokta)   q: çıkış
"""

import _yol  # noqa: F401

import cv2

import config
from camera import Camera, CameraError
from common.app import Canvas, DisplayLoop, build_parser
from common.draw import BLUE, put_text, status_line
from common.fps import FPSMeter
from common.frame import FramePreparer
from common.models import ModelMissingError
from face.overlay import draw_face
from face.tracker import FaceTracker

STYLES = ["kontur", "ag", "nokta"]


def run_haar(args):
    """Klasik yöntem: Viola-Jones (Haar) sınıflandırıcısı. Yalnızca kutu verir, nokta vermez."""
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    prepare, fps = FramePreparer(config.PROCESS_WIDTH), FPSMeter()
    with Camera(args.source, config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT) as cam, \
            DisplayLoop("VISION LAB - 04 Yuz (Haar)", args) as loop:
        while loop.running:
            raw = cam.read()
            if raw is None:
                break
            frame = prepare(raw)
            gray = cv2.cvtColor(frame.bgr, cv2.COLOR_BGR2GRAY)
            boxes = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
            canvas = Canvas(frame, mirror=not args.no_mirror)
            for (x, y, w, h) in boxes:
                p1, p2 = canvas.pts([x, y]), canvas.pts([x + w, y + h])
                cv2.rectangle(canvas.image, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), BLUE, 2)
            canvas.flip()
            put_text(canvas.image, f"Haar: {len(boxes)} yüz  FPS {fps.tick():.0f}", (12, 10), 18, bg=(31, 22, 15))
            loop.show(canvas.image)


def main():
    parser = build_parser("Yüz tespiti ve işaret noktaları")
    parser.add_argument("--yontem", choices=["mediapipe", "haar"], default="mediapipe")
    parser.add_argument("--max-faces", type=int, default=config.MAX_FACES)
    args = parser.parse_args()
    if args.yontem == "haar":
        run_haar(args)
        return

    style = 0
    prepare, fps = FramePreparer(config.PROCESS_WIDTH), FPSMeter()
    with Camera(args.source, config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT) as cam, \
            FaceTracker(max_faces=args.max_faces) as faces, \
            DisplayLoop(
                "VISION LAB - 04 Yuz noktalari",
                args,
                help_title="04 · Yüz Tespiti & 478 Yüz İşaret Noktası",
                help_lines=[
                    "Amaç: MediaPipe Face Landmarker ile yüzü bulmak ve 478 noktayı gerçek zamanlı çizmek.",
                    "• [m] Çizim stilini değiştirir: kontur -> 478 nokta ağı -> yalnızca noktalar.",
                    "• Klasik Haar yöntemiyle kıyaslamak için: --yontem haar parametresiyle çalıştır.",
                    "• [F] Bu rehberi aç/kapat  ·  [Q / Esc] Çıkış.",
                ],
            ) as loop:
        while loop.running:
            raw = cam.read()
            if raw is None:
                break
            frame = prepare(raw)                     # tek kare hazırlığı: boyut, RGB, mp.Image
            result = faces.process(frame)            # model çağrısı

            canvas = Canvas(frame, mirror=not args.no_mirror)
            for face in result.faces:                # 1) şekiller
                draw_face(canvas.image, canvas.pts(face.points), canvas.pts(face.box), STYLES[style])
            canvas.flip()                            # 2) ayna
            for face in result.faces:                # 3) yazılar
                x1 = canvas.screen((face.box[2] if canvas.mirror else face.box[0], face.box[1]))
                put_text(canvas.image, f"iz {face.track_id}", (int(x1[0]), int(x1[1]) - 26), 16, bg=(31, 22, 15))
            n_points = len(result.faces[0].points) if result.faces else 0
            put_text(canvas.image, f"{n_points} nokta  model {result.latency_ms:.1f} ms  FPS {fps.tick():.0f}",
                     (12, 10), 18, bg=(31, 22, 15))
            status_line(canvas.image, result.status, "ok" if result.faces else "warn")
            if loop.show(canvas.image) == ord("m"):
                style = (style + 1) % len(STYLES)


if __name__ == "__main__":
    try:
        main()
    except (CameraError, ModelMissingError) as exc:
        print(exc)
