"""08 - Kararlı jestler, Neon Hava Çizimi (isim yazma), 1-5 parmakla renk değişimi & yumrukla silme

Öğrenme hedefi:
  • İşaret parmağıyla havada parlayan NEON karalama ve isim yazma
  • 100% temassız renk seçimi: 👍 Başparmak -> 1:Turkuaz | 2-5 Parmak -> Sarı, Pembe, Yeşil, Mavi
  • Yumruk (0 parmak, 0.7 sn tut) hareketiyle tüm ekranı silme
  • Pinch (başparmak + işaret) ile fırça kalınlığı sürgüsünü ve kutuyu taşıma
  • 'n' Neon Parıltı aç/kapat | 'z' Geri Al (Undo) | 's' PNG kaydet | 'f' Özellikler rehberi

Çalıştırma : python examples/08_el_jestleri.py
Tuşlar     : f: Özellikler | n: Neon Glow | z: Geri Al | 1-5: Hızlı renk | s: PNG | c: Temizle | q: Çıkış
"""

import _yol  # noqa: F401

import time
from collections import deque

import cv2
import numpy as np

import config
from camera import Camera, CameraError
from common.app import Canvas, DisplayLoop, build_parser
from common.draw import AMBER, GRAY, INK, TEAL, WHITE, panel, put_text, status_line
from common.frame import FramePreparer
from common.models import ModelMissingError
from hands.gestures import GESTURE_NAMES, GestureController, finger_states
from hands.overlay import draw_hand, draw_pinch_gauge
from hands.tracker import HandTracker
from hands.widgets import DraggableBox, DrawingCanvas, Slider

# 5 renkli palet: (BGR renk, Türkçe ad)
PALET = [
    ((191, 212, 45), "1: Turkuaz"),
    ((60, 215, 255), "2: Altın Sarı"),
    ((180, 95, 255), "3: Neon Pembe"),
    ((140, 235, 110), "4: Mint Yeşil"),
    ((255, 150, 65), "5: Elektrik Mavi"),
]

HELP_LINES = [
    "Amaç: İşaret parmağınla havada parlayan NEON yazı yazmak ve renk seçmek.",
    "• ÇİZİM: Sadece İŞARET parmağını kaldırıp havada hareket ettir -> ekrana yazar!",
    "• EN KOLAY RENK SEÇİMİ: Parmağını üstteki 5 renk kutusundan birinin üzerine götür!",
    "• PARMAKLA RENK: Kameraya 2 (Sarı), 3 (Pembe), 4 (Yeşil) veya 5 parmak (Mavi) göster.",
    "• SİLME: Elini YUMRUK yapıp 0.7 saniye tut -> tüm çizim silinir.",
    "• KISAYOLLAR: [1-5] Renk · [n] Neon aç/kapat · [z] Geri Al · [s] PNG kaydet · [F] Kapat",
]


def acik_parmak_sayisi(points) -> tuple[int, dict]:
    """Açık (True) olan parmak sayısını (0-5) ve sözlüğünü döndürür."""
    states = finger_states(points)
    return sum(1 for v in states.values() if v is True), states


def neon_cizim_birlestir(img: np.ndarray, layer: np.ndarray, neon_on: bool) -> None:
    """Çizim katmanını hızlı 1/4 ölçekli Gaussian Neon Bloom parıltısıyla görüntüye ekler."""
    if neon_on:
        h, w = layer.shape[:2]
        kucuk = cv2.resize(layer, (max(1, w // 4), max(1, h // 4)), interpolation=cv2.INTER_LINEAR)
        glow = cv2.resize(cv2.GaussianBlur(kucuk, (11, 11), 0), (w, h), interpolation=cv2.INTER_LINEAR)
        cv2.add(img, glow, dst=img)
    cv2.add(img, layer, dst=img)


def palet_kutulari(w: int) -> list[tuple[int, int, int, int]]:
    """Üstteki 5 renk kutusunun ekran koordinatlarını (x1, y1, x2, y2) döndürür."""
    kutu_w, kutu_h, gap = 116, 38, 8
    toplam_w = len(PALET) * kutu_w + (len(PALET) - 1) * gap
    x0 = max(12, (w - toplam_w) // 2)
    y0 = 10
    return [(x0 + i * (kutu_w + gap), y0, x0 + i * (kutu_w + gap) + kutu_w, y0 + kutu_h)
            for i in range(len(PALET))]


def palet_ciz(img, aktif_idx: int, parmak_sayisi: int | None, neon_on: bool) -> list[tuple[int, int, int, int]]:
    """Üst ortaya dokunmatik 5 renkli canlı palet çubuğunu çizer."""
    kutular = palet_kutulari(img.shape[1])
    x0, y0 = kutular[0][0], kutular[0][1]
    x_son, y_son = kutular[-1][2], kutular[-1][3]
    panel(img, x0 - 8, y0 - 5, x_son + 8, y_son + 6, alpha=0.82)
    for i, ((rx1, ry1, rx2, ry2), (bgr, ad)) in enumerate(zip(kutular, PALET)):
        cv2.rectangle(img, (rx1, ry1), (rx2, ry2), bgr, -1)
        if i == aktif_idx:
            cv2.rectangle(img, (rx1 - 2, ry1 - 2), (rx2 + 2, ry2 + 2), WHITE, 3, cv2.LINE_AA)
        put_text(img, ad, (rx1 + 7, ry1 + 10), 13, INK)
    info = f"Renk seçmek için parmağını kutuya değdir!  ·  Neon: {'AÇIK' if neon_on else 'KAPALI'} [n]"
    put_text(img, info, (x0, y_son + 10), 13, TEAL, bg=INK)
    return kutular


def main():
    args = build_parser("Kararlı jestler, Neon hava çizimi ve renk paleti").parse_args()
    prepare = FramePreparer(config.PROCESS_WIDTH)
    controller = GestureController()
    log: deque = deque(maxlen=4)
    undo_stack: deque = deque(maxlen=15)
    widgets = None

    aktif_renk_idx = 0
    neon_on = True
    onceki_ciziyor = False
    fist_since = None
    color_hold_target = None
    color_hold_since = None
    son_bildirim = ""
    bildirim_bitis = 0.0

    with Camera(args.source, config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT) as cam, \
            HandTracker(max_hands=1) as hands, \
            DisplayLoop(
                "VISION LAB - 08 Neon Hava Cizimi & El Jestleri",
                args,
                help_title="08 · Neon Hava Çizimi, 1–5 Parmak Renk & Yumrukla Sil",
                help_lines=HELP_LINES,
            ) as loop:
        while loop.running:
            raw = cam.read()
            if raw is None:
                break
            frame = prepare(raw)
            result = hands.process(frame)
            canvas = Canvas(frame, mirror=not args.no_mirror)
            if widgets is None:
                w, h = canvas.width, canvas.height
                widgets = (
                    Slider(56, h - 72, min(320, w // 3), "fırça kalınlığı", value=0.35),
                    DraggableBox(w - 140, 120, size=86),
                    DrawingCanvas(w, h),
                )
            slider, box, drawing = widgets

            hand = result.hands[0] if result.hands else None
            cursor = canvas.screen(hand.points[8]) if hand else None
            state = controller.update(hand.points if hand else None, frame.timestamp_ms, cursor)
            started = "pinch_basladi" in state.events
            for event in state.events:
                log.appendleft(f"{frame.timestamp_ms / 1000:5.1f}s {event}")

            slider.update(cursor, started, state.pinching)
            box.update(cursor, started, state.pinching and not slider.dragging)
            firca_kalinlik = int(3 + slider.value * 13)

            parmak_n, fstates = acik_parmak_sayisi(hand.points) if hand else (None, {})
            now_ms = frame.timestamp_ms
            kutular = palet_kutulari(canvas.width)

            # Üstteki renk kutularına parmak değdi mi? (En kolay & anında renk seçimi!)
            palet_uzerinde = False
            if cursor is not None:
                cx_p, cy_p = cursor
                if cy_p <= 64:
                    palet_uzerinde = True
                for idx_k, (rx1, ry1, rx2, ry2) in enumerate(kutular):
                    if rx1 <= cx_p <= rx2 and ry1 - 6 <= cy_p <= ry2 + 10:
                        if aktif_renk_idx != idx_k:
                            aktif_renk_idx = idx_k
                            son_bildirim = f"Renk seçildi -> {PALET[aktif_renk_idx][1]}"
                            bildirim_bitis = time.monotonic() + 1.5
                        break

            # 1) İşaret parmağıyla havada çizim / isim yazma (üst palet bölgesinde çizmez)
            ciziyor = (hand is not None and state.gesture == "isaret"
                       and not state.pinching and not palet_uzerinde)
            if ciziyor and not onceki_ciziyor:
                undo_stack.append(drawing.layer.copy())
            onceki_ciziyor = ciziyor

            renk_bgr, renk_ad = PALET[aktif_renk_idx]
            drawing.update(cursor, ciziyor, color=renk_bgr, thickness=firca_kalinlik)

            # 2) %100 temassız renk seçimi: 👍 sadece başparmak -> 1:Turkuaz | 2-5 parmak -> 2..5
            hedef_renk = None
            if hand is not None and not state.pinching:
                sadece_basparmak = (parmak_n == 1 and fstates.get("başparmak") is True)
                if sadece_basparmak:
                    hedef_renk = 0
                elif parmak_n in (2, 3, 4, 5):
                    hedef_renk = parmak_n - 1

            if hedef_renk is not None:
                if color_hold_target != hedef_renk:
                    color_hold_target = hedef_renk
                    color_hold_since = now_ms
                elif now_ms - color_hold_since >= 350 and aktif_renk_idx != hedef_renk:
                    aktif_renk_idx = hedef_renk
                    son_bildirim = f"Renk değişti -> {PALET[aktif_renk_idx][1]}"
                    bildirim_bitis = time.monotonic() + 1.8
                    log.appendleft(f"{now_ms / 1000:5.1f}s renk: {PALET[aktif_renk_idx][1]}")
            else:
                color_hold_target = None
                color_hold_since = None

            # 3) Yumruk (0 parmak) ile 0.7 sn tutunca ekranı silme
            silme_orani = 0.0
            if hand is not None and (state.gesture == "yumruk" or parmak_n == 0) and not state.pinching:
                fist_since = fist_since or now_ms
                silme_orani = min(1.0, (now_ms - fist_since) / 700.0)
                if silme_orani >= 1.0:
                    undo_stack.append(drawing.layer.copy())
                    drawing.clear()
                    son_bildirim = "Yumruk algılandı -> Tüm çizim silindi! (z: geri al)"
                    bildirim_bitis = time.monotonic() + 2.0
                    log.appendleft(f"{now_ms / 1000:5.1f}s yumruk: çizim silindi")
                    fist_since = None
                    silme_orani = 0.0
            else:
                fist_since = None

            if hand:
                draw_hand(canvas.image, canvas.pts(hand.points), highlight_pinch=state.pinching)
            canvas.flip()
            img = canvas.image
            neon_cizim_birlestir(img, drawing.layer, neon_on)
            slider.draw(img)
            box.draw(img)

            # İşaret parmağı ucunda her zaman görünür imleç halkası
            if cursor is not None:
                cv2.circle(img, (int(cursor[0]), int(cursor[1])),
                           max(7, firca_kalinlik) if ciziyor else 6, renk_bgr, 2, cv2.LINE_AA)

            # Üst renk paleti
            palet_ciz(img, aktif_renk_idx, parmak_n, neon_on)

            # Sol kompakt durum kartı
            panel(img, 12, 62, 268, 212, alpha=0.76)
            put_text(img, f"Jest: {GESTURE_NAMES[state.gesture]}", (22, 70), 16, TEAL)
            put_text(img, f"Renk: {PALET[aktif_renk_idx][1]}", (22, 95), 14, WHITE)
            put_text(img, f"Fırça: {firca_kalinlik} px  ·  Geri al: [z]", (22, 117), 12, GRAY)
            for i, line in enumerate(log):
                put_text(img, line, (22, 140 + 16 * i), 11, AMBER if "silindi" in line else WHITE)

            # Yumrukla silme ilerleme çubuğu
            if silme_orani > 0.05:
                cx = canvas.width // 2
                cy = canvas.height - 96
                panel(img, cx - 130, cy - 22, cx + 130, cy + 20, alpha=0.85)
                put_text(img, f"Yumruk tut -> Siliniyor %{int(silme_orani * 100)}", (cx - 116, cy - 16), 14, AMBER)
                cv2.rectangle(img, (cx - 116, cy + 6), (cx + 116, cy + 14), GRAY, 1)
                cv2.rectangle(img, (cx - 116, cy + 6), (cx - 116 + int(232 * silme_orani), cy + 14), AMBER, -1)

            if son_bildirim and time.monotonic() < bildirim_bitis:
                put_text(img, son_bildirim, (canvas.width // 2 - 160, 74), 15, TEAL, bg=INK)

            if hand:
                draw_pinch_gauge(img, state.pinch_value, state.pinching, canvas.width - 245, 52)

            alt_mesaj = (
                "İşaret: Yaz · Üst kutuya dokun veya 2-5 parmak: Renk · Yumruk: Sil · [z] Geri Al · [F] Özellikler"
                if hand else result.status + "  ·  [F] Özellikler"
            )
            status_line(img, alt_mesaj, "ok" if hand else "warn")

            key = loop.show(img)
            if ord("1") <= key <= ord("5"):
                aktif_renk_idx = key - ord("1")
                son_bildirim = f"Renk -> {PALET[aktif_renk_idx][1]}"
                bildirim_bitis = time.monotonic() + 1.5
            elif key in (ord("n"), ord("N")):
                neon_on = not neon_on
                son_bildirim = f"Neon parıltı: {'AÇIK' if neon_on else 'KAPALI'}"
                bildirim_bitis = time.monotonic() + 1.5
            elif key in (ord("z"), ord("Z")) and undo_stack:
                drawing.layer[:] = undo_stack.pop()
                son_bildirim = "Son çizim geri alındı!"
                bildirim_bitis = time.monotonic() + 1.5
            elif key == ord("c"):
                undo_stack.append(drawing.layer.copy())
                drawing.clear()
                son_bildirim = "Tuval temizlendi! (z: geri al)"
                bildirim_bitis = time.monotonic() + 1.5
            elif key == ord("s"):
                dosya = f"cizim_{int(time.time())}.png"
                cv2.imwrite(dosya, img)
                son_bildirim = f"Kaydedildi: {dosya}"
                bildirim_bitis = time.monotonic() + 2.2
                print(f"Çizim kaydedildi: {dosya}")


if __name__ == "__main__":
    try:
        main()
    except (CameraError, ModelMissingError) as exc:
        print(exc)
