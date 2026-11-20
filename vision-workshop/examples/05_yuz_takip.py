"""05 - Yüz takibi, hareket izi ve titreme azaltma

Öğrenme hedefi: Yüz merkezinin hareketini izlemek; ham iz ile yumuşatılmış izi
karşılaştırmak; takip numarasının kimlik olmadığını görmek.

Çalıştırma : python examples/05_yuz_takip.py
İki yüz    : python examples/05_yuz_takip.py --max-faces 2
Kullanım   : + / - : yumuşatma katsayısı (alpha)   c: izi temizle   q: çıkış
"""

import _yol  # noqa: F401

import config
from camera import Camera, CameraError
from common.app import Canvas, DisplayLoop, build_parser
from common.draw import GRAY, TEAL, put_text, status_line
from common.frame import FramePreparer
from common.models import ModelMissingError
from face.overlay import draw_face, draw_trails
from face.tracker import FaceTracker


def main():
    parser = build_parser("Yüz takibi ve hareket izi")
    parser.add_argument("--max-faces", type=int, default=config.MAX_FACES)
    args = parser.parse_args()
    alpha = config.EMA_ALPHA
    prepare = FramePreparer(config.PROCESS_WIDTH)

    with Camera(args.source, config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT) as cam, \
            FaceTracker(max_faces=args.max_faces, ema_alpha=alpha) as faces, \
            DisplayLoop("VISION LAB - 05 Yuz takibi", args) as loop:
        while loop.running:
            raw = cam.read()
            if raw is None:
                break
            frame = prepare(raw)
            result = faces.process(frame)

            canvas = Canvas(frame, mirror=not args.no_mirror)
            for face in result.faces:
                draw_face(canvas.image, canvas.pts(face.points), None, "nokta")
                raw_trail, smooth_trail = faces.trails(face.track_id)
                draw_trails(canvas.image, raw_trail, smooth_trail, canvas.scale)
            canvas.flip()
            for face in result.faces:
                x, y = canvas.screen(face.center_smooth)
                put_text(canvas.image, f"iz {face.track_id}", (int(x) + 10, int(y) - 30), 16, bg=(31, 22, 15))
            put_text(canvas.image, "gri: ham merkez   turkuaz: yumuşatılmış merkez", (12, 10), 16, GRAY,
                     bg=(31, 22, 15))
            put_text(canvas.image, f"alpha = {alpha:.2f}  (+/- ile değiştir)", (12, 38), 16, TEAL, bg=(31, 22, 15))
            status_line(canvas.image, result.status, "ok" if result.faces else "warn")

            key = loop.show(canvas.image)
            if key in (ord("+"), ord("=")):
                alpha = min(1.0, alpha + 0.05)
            elif key == ord("-"):
                alpha = max(0.05, alpha - 0.05)
            elif key == ord("c"):
                faces.clear_trails()
            if key in (ord("+"), ord("="), ord("-")):
                faces.set_smoothing(alpha)


if __name__ == "__main__":
    try:
        main()
    except (CameraError, ModelMissingError) as exc:
        print(exc)
