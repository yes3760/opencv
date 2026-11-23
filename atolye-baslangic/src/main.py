"""VISION LAB - birleşik uygulama

Kamera görüntüsü tek bir döngüde okunur ve etkin modüllere dağıtılır:

    Kamera -> Frame (bir kez küçültülür, bir kez RGB'ye çevrilir)
           -> Yüz modülü   (her karede, Yüz/Cilt/Birleşik modunda)
           -> El modülü    (her karede, El/Birleşik modunda)
           -> Cilt modülü  (düşük sıklıkta veya boşluk tuşuyla, tek kare)
           -> Arayüz       (düğmeler, sürgü, panel)

Çalıştırma : python src/main.py
Kamerasız  : python src/main.py --source video.mp4
Tuşlar     : 1-4 mod seçimi, boşluk: cilt analizi, c: izi temizle, q/Esc: çıkış
El ile     : İşaret parmağını üstteki bir düğmeye getirip pinch yapın.

Bir model dosyası eksikse ilgili modül kapatılır, diğerleri çalışmaya devam eder.
"""

from __future__ import annotations

import time

import cv2
import numpy as np

import config
from camera import Camera, CameraError
from common.app import Canvas, DisplayLoop, build_parser
from common.draw import AMBER, GRAY, INK, RED, TEAL, WHITE, put_text, status_line
from common.fps import FPSMeter, StageTimer
from common.frame import FramePreparer
from common.models import ModelMissingError
from face.metrics import LEFT_EYE_EAR, RIGHT_EYE_EAR, eye_aspect_ratio, mouth_aspect_ratio
from face.overlay import draw_face, draw_trails
from hands.gestures import GESTURE_NAMES, GestureController
from hands.overlay import draw_hand
from hands.widgets import ButtonBar, Slider
from skin.overlay import MAP_KEYS, disclaimer, draw_quality, result_panel

MODES = ["Yüz", "El", "Cilt", "Birleşik"]
PANEL_W = 320


def load_modules():
    """Modelleri bir kez yükler. Eksik model, yalnızca kendi modülünü kapatır."""
    modules, notes = {}, []
    try:
        from face.tracker import FaceTracker
        modules["face"] = FaceTracker(blendshapes=False)
    except ModelMissingError as exc:
        notes.append(f"Yüz modülü kapalı: {exc}")
    try:
        from hands.tracker import HandTracker
        modules["hands"] = HandTracker(max_hands=1)
    except ModelMissingError as exc:
        notes.append(f"El modülü kapalı: {exc}")
    if "face" in modules:
        from skin.analyzer import SkinAnalyzer
        modules["skin"] = SkinAnalyzer(use_segmenter=True)
        notes.append(modules["skin"].segmenter_note)
    else:
        notes.append("Cilt modülü kapalı: yüz modülüne ihtiyaç duyar.")
    return modules, notes


def side_panel(height: int, mode: str, info: dict) -> np.ndarray:
    out = np.full((height, PANEL_W, 3), INK, np.uint8)
    put_text(out, "VISION LAB", (16, 12), 24, TEAL)
    put_text(out, "Kameradan Etkileşime", (16, 44), 15, GRAY)
    y = 80
    put_text(out, f"Mod: {mode}", (16, y), 18, WHITE)
    y += 32
    put_text(out, f"FPS {info['fps']:.0f}", (16, y), 15, WHITE)
    y += 26
    for name, ms in info["timings"].items():
        put_text(out, f"{name}: {ms:.1f} ms", (16, y), 14, GRAY)
        y += 20
    y += 10
    for line, color in info["lines"]:
        put_text(out, line, (16, y), 15, color)
        y += 22
    y = height - 150
    for line in ("1-4  mod seçimi", "boşluk  cilt analizi", "c  izi temizle", "q / Esc  çıkış",
                 "El: düğme üstünde pinch"):
        put_text(out, line, (16, y), 13, GRAY)
        y += 20
    return out


def main() -> None:
    args = build_parser("VISION LAB birleşik uygulama").parse_args()
    modules, notes = load_modules()
    for note in notes:
        print(note)
    face_mod, hand_mod, skin_mod = modules.get("face"), modules.get("hands"), modules.get("skin")

    prepare = FramePreparer(config.PROCESS_WIDTH)
    timer, fps = StageTimer(), FPSMeter()
    gestures = GestureController()
    buttons, slider = ButtonBar(MODES), None
    mode = "Birleşik"
    buttons.active = MODES.index(mode)
    skin_preview = skin_captured = None
    last_skin = 0.0
    clicks: list = []

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            clicks.append((x, y))

    try:
        with Camera(args.source, config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT) as cam, \
                DisplayLoop(
                    "VISION LAB",
                    args,
                    help_title="VISION LAB — Birleşik Uygulama",
                    help_lines=[
                        "Amaç: Yüz, El ve Cilt analizi modüllerini tek bir canlı akışta deneyimlemek.",
                        "• [1] Yüz  ·  [2] El  ·  [3] Cilt  ·  [4] Birleşik modları arasında geçiş yap.",
                        "• [Boşluk] Cilt modunda kalite uygunken tek kare ısı haritası analizi alır.",
                        "• [El ile] İşaret parmağını üstteki düğmeye getirip Pinch (çimdik) ile tıkla.",
                        "• [c] Yüz hareket izini temizler  ·  [F] Bu rehberi açar/kapatır.",
                    ],
                ) as loop:
            loop.on_mouse(on_mouse)
            where = f" (kamera {cam.index})" if cam.index is not None else ""
            print(f"Kamera açıldı: {cam.actual_size[0]}x{cam.actual_size[1]}{where}")
            while loop.running:
                raw = cam.read()
                if raw is None:
                    print("Kare alınamadı; döngü sonlandırılıyor.")
                    break
                with timer.measure("hazırlık"):
                    frame = prepare(raw)

                use_face = face_mod is not None and mode in ("Yüz", "Cilt", "Birleşik")
                use_hands = hand_mod is not None and mode in ("El", "Birleşik")
                face_res = hand_res = None
                if use_face:
                    with timer.measure("yüz modeli"):
                        face_res = face_mod.process(frame)
                if use_hands:
                    with timer.measure("el modeli"):
                        hand_res = hand_mod.process(frame)
                for stage, active in (("yüz modeli", use_face), ("el modeli", use_hands)):
                    if not active:
                        timer.ms.pop(stage, None)

                canvas = Canvas(frame, mirror=not args.no_mirror)
                if slider is None:
                    slider = Slider(60, canvas.height - 90, canvas.width // 2, "sürgü (örnek)")

                # --- El: imleç ve kararlı olaylar
                hand = hand_res.hands[0] if hand_res and hand_res.hands else None
                cursor = canvas.screen(hand.points[8]) if hand else None
                state = gestures.update(hand.points if hand else None, frame.timestamp_ms, cursor)
                started = "pinch_basladi" in state.events
                clicked = buttons.update(cursor, started) if hand_mod else None
                for point in clicks:
                    clicked = buttons.click(point)
                clicks.clear()
                if clicked is not None:
                    mode = MODES[clicked]
                if mode in ("El", "Birleşik"):
                    slider.update(cursor, started and clicked is None, state.pinching)

                # --- Cilt: düşük sıklıkta kalite önizlemesi
                if skin_mod and mode == "Cilt" and face_res and time.monotonic() - last_skin > 0.5:
                    with timer.measure("cilt analizi"):
                        skin_preview = skin_mod.analyze(frame.full_bgr, face_res.faces, frame.scale_to_full)
                    last_skin = time.monotonic()

                # --- Çizim: önce şekiller, sonra ayna, sonra yazılar
                lines = []
                if face_res:
                    for face in face_res.faces:
                        draw_face(canvas.image, canvas.pts(face.points), None, "kontur")
                        if mode in ("Yüz", "Birleşik"):
                            raw_trail, smooth_trail = face_mod.trails(face.track_id)
                            draw_trails(canvas.image, raw_trail, smooth_trail, canvas.scale)
                    if face_res.faces:
                        f = face_res.faces[0]
                        ear = (eye_aspect_ratio(f.points, RIGHT_EYE_EAR) + eye_aspect_ratio(f.points, LEFT_EYE_EAR)) / 2
                        lines.append((f"Yüz: {len(face_res.faces)} (iz {f.track_id})", TEAL))
                        lines.append((f"göz {ear:.2f}  ağız {mouth_aspect_ratio(f.points):.2f}", WHITE))
                        if f.pose:
                            lines.append((f"dönüş {f.pose.yaw:+.0f}°  eğim {f.pose.pitch:+.0f}°", WHITE))
                    else:
                        lines.append(("Yüz bulunamadı", AMBER))
                if hand:
                    draw_hand(canvas.image, canvas.pts(hand.points), highlight_pinch=state.pinching)
                if use_hands:
                    lines.append((f"El: {GESTURE_NAMES[state.gesture] if hand else 'yok'}", TEAL if hand else AMBER))
                    lines.append((f"pinch {state.pinch_value:.2f} {'basılı' if state.pinching else ''}", WHITE))
                if mode == "Cilt" and skin_preview is not None:
                    lines.append(("Cilt: " + ("hazır, boşluk tuşu" if skin_preview.quality.ok
                                              else "uygun görüntü bekleniyor"),
                                  TEAL if skin_preview.quality.ok else AMBER))
                for note in notes:
                    if "kapalı" in note:
                        lines.append((note.split(":")[0], RED))
                canvas.flip()
                img = canvas.image
                buttons.draw(img)
                if mode in ("El", "Birleşik"):
                    slider.draw(img)
                if mode == "Cilt":
                    disclaimer(img)
                    if skin_preview is not None:
                        draw_quality(img, skin_preview.quality, 12, 64)
                if cursor is not None:
                    cv2.circle(img, (int(cursor[0]), int(cursor[1])), 9, AMBER if state.pinching else WHITE, 2)
                status = face_res.status if face_res else (hand_res.status if hand_res else "Modül seçin")
                status_line(img, status, "ok")

                info = {"fps": fps.tick(), "timings": timer.ms, "lines": lines}
                if mode == "Cilt":   # cilt modunda yan panel yerine analiz sonucu gösterilir
                    side = result_panel(skin_captured, MAP_KEYS[0], img.shape[0], 380)
                else:
                    side = side_panel(img.shape[0], mode, info)
                screen = np.hstack([img, side])
                key = loop.show(screen)

                if ord("1") <= key <= ord("4"):
                    mode = MODES[key - ord("1")]
                    buttons.active = MODES.index(mode)
                elif key == ord("c") and face_mod:
                    face_mod.clear_trails()
                elif key == ord(" ") and skin_mod and face_res:
                    skin_captured = skin_mod.analyze(frame.full_bgr, face_res.faces, frame.scale_to_full)
                    print(skin_captured.message)
    except CameraError as exc:
        print(exc)
    finally:
        for module in modules.values():
            module.close()
        print("Kamera ve modeller serbest bırakıldı.")


if __name__ == "__main__":
    main()
