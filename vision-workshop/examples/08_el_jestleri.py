"""08 - Kararlı jestler ve el ile etkileşim

Öğrenme hedefi: Pinch hareketini histerezis, bekleme ve soğuma süresiyle
kararlı hale getirmek; tek hareketin tek komut üretmesini sağlamak; el
kaybolunca durumu sıfırlamak. Uygulama içinde sürgü, sürüklenen kutu ve
çizim alanı kontrol edilir.

Çalıştırma : python examples/08_el_jestleri.py
Kullanım   : Sürgüyü pinch ile tutup sürükleyin. Kutuyu pinch ile taşıyın.
             İşaret parmağı jestiyle çizin; açık eli 1 saniye tutunca çizim silinir.
             q: çıkış
"""

import _yol  # noqa: F401

from collections import deque

import config
from camera import Camera, CameraError
from common.app import Canvas, DisplayLoop, build_parser
from common.draw import AMBER, GRAY, TEAL, WHITE, panel, put_text, status_line
from common.frame import FramePreparer
from common.models import ModelMissingError
from hands.gestures import GESTURE_NAMES, GestureController
from hands.overlay import draw_hand, draw_pinch_gauge
from hands.tracker import HandTracker
from hands.widgets import DraggableBox, DrawingCanvas, Slider


def main():
    args = build_parser("Kararlı jestler ve etkileşim").parse_args()
    prepare = FramePreparer(config.PROCESS_WIDTH)
    controller = GestureController()
    log: deque = deque(maxlen=6)
    counts = {"pinch_basladi": 0}
    widgets = None
    open_palm_since = None

    with Camera(args.source, config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT) as cam, \
            HandTracker(max_hands=1) as hands, \
            DisplayLoop("VISION LAB - 08 El jestleri", args) as loop:
        while loop.running:
            raw = cam.read()
            if raw is None:
                break
            frame = prepare(raw)
            result = hands.process(frame)
            canvas = Canvas(frame, mirror=not args.no_mirror)
            if widgets is None:   # öğeler ilk karede ekran boyutuna göre yerleştirilir
                w, h = canvas.width, canvas.height
                widgets = (Slider(60, h - 80, w // 2, "ses düzeyi (örnek)"),
                           DraggableBox(w - 200, 120), DrawingCanvas(w, h))
            slider, box, drawing = widgets

            hand = result.hands[0] if result.hands else None
            cursor = canvas.screen(hand.points[8]) if hand else None    # işaret parmağı ucu
            state = controller.update(hand.points if hand else None, frame.timestamp_ms, cursor)
            started = "pinch_basladi" in state.events
            for event in state.events:
                counts[event] = counts.get(event, 0) + 1
                log.appendleft(f"{frame.timestamp_ms / 1000:6.1f} s  {event}")

            slider.update(cursor, started, state.pinching)
            box.update(cursor, started, state.pinching and not slider.dragging)
            drawing.update(cursor, state.gesture == "isaret" and not state.pinching)
            if state.gesture == "acik_el":
                open_palm_since = open_palm_since or frame.timestamp_ms
                if frame.timestamp_ms - open_palm_since >= config.OPEN_PALM_HOLD_MS:
                    drawing.clear()
                    log.appendleft(f"{frame.timestamp_ms / 1000:6.1f} s  çizim temizlendi")
                    open_palm_since = None
            else:
                open_palm_since = None

            if hand:
                draw_hand(canvas.image, canvas.pts(hand.points), highlight_pinch=state.pinching)
            canvas.flip()
            img = canvas.image
            drawing.draw(img)
            slider.draw(img)
            box.draw(img)

            panel(img, 12, 12, 330, 196)
            put_text(img, f"jest: {GESTURE_NAMES[state.gesture]}", (24, 20), 18, TEAL)
            put_text(img, f"ham: {GESTURE_NAMES[state.raw_gesture]}", (24, 46), 14, GRAY)
            put_text(img, f"pinch komutu sayısı: {counts['pinch_basladi']}", (24, 68), 14, WHITE)
            for i, line in enumerate(log):
                put_text(img, line, (24, 92 + 16 * i), 12, AMBER if "kayboldu" in line else WHITE)
            if hand:
                draw_pinch_gauge(img, state.pinch_value, state.pinching, canvas.width - 250, 40)
            status_line(img, "El kayboldu: durum sıfırlandı." if "el_kayboldu" in state.events
                        else result.status, "ok" if hand else "warn")
            loop.show(img)


if __name__ == "__main__":
    try:
        main()
    except (CameraError, ModelMissingError) as exc:
        print(exc)
