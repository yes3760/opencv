"""07 - El işaret noktaları ve parmak durumları

Öğrenme hedefi: 21 el noktasını görmek, eklem açılarından parmakların açık mı
kapalı mı olduğunu belirlemek ve sağ/sol etiketini bir deneyle kontrol etmek.

Çalıştırma : python examples/07_el_noktalari.py
Kullanım   : n: nokta numaralarını göster/gizle   q: çıkış

Deney: Yalnızca SAĞ elinizi kaldırın. Ekranda "sağ" yazmalı. "sol" yazıyorsa
src/config.py içinde HANDEDNESS_SWAP = True yapın ve tekrar deneyin.
"""

import _yol  # noqa: F401

import config
from camera import Camera, CameraError
from common.app import Canvas, DisplayLoop, build_parser
from common.draw import AMBER, GRAY, TEAL, WHITE, panel, put_text, status_line
from common.frame import FramePreparer
from common.geometry import angle_deg
from common.models import ModelMissingError
from hands.gestures import FINGERS, GESTURE_NAMES, classify_static, finger_states
from hands.overlay import draw_hand
from hands.tracker import HandTracker


def main():
    parser = build_parser("El işaret noktaları ve parmak durumları")
    parser.add_argument("--max-hands", type=int, default=2)
    args = parser.parse_args()
    prepare = FramePreparer(config.PROCESS_WIDTH)
    show_ids = False

    with Camera(args.source, config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT) as cam, \
            HandTracker(max_hands=args.max_hands) as hands, \
            DisplayLoop(
                "VISION LAB - 07 El noktalari",
                args,
                help_title="07 · 21 El Eklem Noktası & Parmak Açıları",
                help_lines=[
                    "Amaç: 21 el noktasından parmak eklem açılarını hesaplayıp açık/kapalı durumlarını görmek.",
                    "• [n] 0–20 arası eklem noktalarının numaralarını el üzerinde göster/gizle.",
                    "• Deney: Yalnızca SAĞ elini kaldır; etiket 'sağ' yazmalı (sol yazarsa config.py HANDEDNESS_SWAP).",
                    "• [F] Bu rehberi aç/kapat  ·  [Q / Esc] Çıkış.",
                ],
            ) as loop:
        while loop.running:
            raw = cam.read()
            if raw is None:
                break
            frame = prepare(raw)
            result = hands.process(frame)
            canvas = Canvas(frame, mirror=not args.no_mirror)
            for hand in result.hands:
                draw_hand(canvas.image, canvas.pts(hand.points))
            canvas.flip()
            img = canvas.image

            for k, hand in enumerate(result.hands):
                wx, wy = canvas.screen(hand.points[0])
                put_text(img, f"{hand.label_tr} el ({hand.score:.2f})", (int(wx) - 40, int(wy) + 12), 16,
                         bg=(31, 22, 15))
                if show_ids:
                    for i, pt in enumerate(hand.points):
                        x, y = canvas.screen(pt)
                        put_text(img, str(i), (int(x) + 4, int(y) - 14), 11, AMBER)
                states = finger_states(hand.points)
                x0, y0 = 12 + k * 300, 12
                panel(img, x0, y0, x0 + 290, y0 + 176)
                put_text(img, f"{hand.label_tr} el: {GESTURE_NAMES[classify_static(states)]}", (x0 + 10, y0 + 8), 16, TEAL)
                for j, (name, (a, b, c, d)) in enumerate(FINGERS.items()):
                    angle = angle_deg(hand.points[a], hand.points[b], hand.points[c])
                    state = {True: "açık", False: "kapalı", None: "belirsiz"}[states[name]]
                    put_text(img, f"{name:<10} {angle:5.0f}°  {state}", (x0 + 10, y0 + 36 + 26 * j), 15,
                             WHITE if states[name] is not None else GRAY)
            status_line(img, result.status + "   Deney: sağ elinizi kaldırın, etiket 'sağ' olmalı.",
                        "ok" if result.hands else "warn")
            if loop.show(img) == ord("n"):
                show_ids = not show_ids


if __name__ == "__main__":
    try:
        main()
    except (CameraError, ModelMissingError) as exc:
        print(exc)
