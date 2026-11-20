"""06 - Yüz geometrisi ve hareket analizi

Öğrenme hedefi: Noktalardan normalize ölçümler üretmek: göz ve ağız açıklığı,
yaklaşık baş yönelimi ve yüz oranları. Kural tabanlı ölçümü (EAR) modelin
öğrenilmiş çıktısıyla (blendshape) karşılaştırmak.

Çalıştırma : python examples/06_yuz_geometrisi.py
Kullanım   : q: çıkış

Not: Bu ölçümler gözlenebilir hareketlerdir. Kişilik, zekâ, güvenilirlik veya
duygu durumu hakkında bilgi vermez.
"""

import _yol  # noqa: F401

from collections import deque

import numpy as np

import config
from camera import Camera, CameraError
from common.app import Canvas, DisplayLoop, build_parser
from common.draw import AMBER, GRAY, TEAL, WHITE, panel, put_text, status_line
from common.frame import FramePreparer
from common.models import ModelMissingError
from face.metrics import (LEFT_EYE_EAR, RIGHT_EYE_EAR, BlinkDetector, approximate_shape_tendency,
                          eye_aspect_ratio, face_ratios, is_frontal, mouth_aspect_ratio)
from face.overlay import draw_face
from face.tracker import FaceTracker


def shape_status(face, frame_width, history) -> tuple[str, str]:
    """Şekil eğilimi yalnızca uygun koşullarda gösterilir; aksi halde neden yazılır."""
    if not is_frontal(face.pose):
        history.clear()
        return "Uygun görüntü bekleniyor: başınızı düz tutup kameraya bakın.", "warn"
    if face.width_px / frame_width < config.MIN_FACE_WIDTH_RATIO:
        history.clear()
        return "Uygun görüntü bekleniyor: kameraya biraz yaklaşın.", "warn"
    ratios = face_ratios(face.points)
    history.append(ratios["uzunluk/genişlik"])
    if len(history) < config.SHAPE_STABLE_FRAMES or np.std(history) > config.SHAPE_MAX_RATIO_STD:
        return "Uygun görüntü bekleniyor: birkaç saniye hareketsiz kalın.", "warn"
    return f"Yaklaşık: {approximate_shape_tendency(ratios)} (standart bir sınıf değildir)", "ok"


def main():
    args = build_parser("Yüz geometrisi ve hareket analizi").parse_args()
    prepare = FramePreparer(config.PROCESS_WIDTH)
    blink = BlinkDetector()
    history: deque = deque(maxlen=config.SHAPE_STABLE_FRAMES)

    with Camera(args.source, config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT) as cam, \
            FaceTracker(blendshapes=True) as faces, \
            DisplayLoop("VISION LAB - 06 Yuz geometrisi", args) as loop:
        while loop.running:
            raw = cam.read()
            if raw is None:
                break
            frame = prepare(raw)
            result = faces.process(frame)
            canvas = Canvas(frame, mirror=not args.no_mirror)
            if result.faces:
                draw_face(canvas.image, canvas.pts(result.faces[0].points), None, "kontur")
            canvas.flip()

            img = canvas.image
            x0 = canvas.width - 360
            panel(img, x0, 0, canvas.width, canvas.height - 34)
            put_text(img, "Yüz geometrisi", (x0 + 14, 12), 20, WHITE)
            if not result.faces:
                blink.reset()
                history.clear()
                status_line(img, result.status, "warn")
                loop.show(img)
                continue

            face = result.faces[0]
            p = face.points
            ear = (eye_aspect_ratio(p, RIGHT_EYE_EAR) + eye_aspect_ratio(p, LEFT_EYE_EAR)) / 2
            closed = blink.update(ear)
            mar = mouth_aspect_ratio(p)
            bs = face.blendshapes
            rows = [
                ("Kural tabanlı (geometri)", None, TEAL),
                (f"göz açıklığı EAR {ear:.2f}", "kapalı" if closed else "açık", WHITE),
                (f"göz kırpma sayısı {blink.blinks}", None, WHITE),
                (f"ağız açıklığı {mar:.2f}", "açık" if mar > config.MOUTH_OPEN_MAR else "kapalı", WHITE),
                ("Öğrenilmiş (blendshape, 0-1)", None, TEAL),
                (f"eyeBlinkLeft {bs.get('eyeBlinkLeft', 0):.2f}  Right {bs.get('eyeBlinkRight', 0):.2f}", None, WHITE),
                (f"jawOpen {bs.get('jawOpen', 0):.2f}", None, WHITE),
                ("Yaklaşık baş yönelimi (derece)", None, TEAL),
            ]
            if face.pose:
                rows.append((f"dönüş {face.pose.yaw:+.0f}  eğim {face.pose.pitch:+.0f}  "
                             f"yatma {face.pose.roll:+.0f}", None, WHITE))
            rows.append(("Oranlar (yüz genişliğine göre)", None, TEAL))
            for name, value in face_ratios(p).items():
                rows.append((f"{name} {value:.2f}", None, WHITE))
            y = 48
            for text, tag, color in rows:
                put_text(img, text, (x0 + 14, y), 15, color)
                if tag:
                    put_text(img, tag, (x0 + 270, y), 15, AMBER)
                y += 24
            put_text(img, "Ölçümler hareket bilgisidir; duygu", (x0 + 14, y + 10), 13, GRAY)
            put_text(img, "veya kişilik çıkarımı yapılmaz.", (x0 + 14, y + 28), 13, GRAY)

            message, kind = shape_status(face, frame.size[0], history)
            status_line(img, message, kind)
            loop.show(img)


if __name__ == "__main__":
    try:
        main()
    except (CameraError, ModelMissingError) as exc:
        print(exc)
