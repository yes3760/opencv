"""BONUS PROJE 1 — Sanal Çizim Tahtası (HSV Renk Takibi)

Yalnızca OpenCV ve NumPy kullanır (ek model gerekmez).
Elinizdeki parlak mavi (veya 1/2/3 tuşuyla seçtiğiniz) bir kalem kapağını
kamerada takip ederek havada çizim yapmanızı sağlar.

Çalıştırma : python bonus_projeler/bonus1_sanal_kalem.py
Tuşlar     : 1: Mavi takip | 2: Yeşil takip | 3: Sarı takip
             c: Tuvali temizle | f: Özellikler | q: Çıkış
"""

import time
import cv2
import numpy as np

# HSV renk aralıkları: (alt_sınır, üst_sınır, çizim_BGR_rengi, etiket)
RENKLER = {
    "1": ((95, 110, 70), (130, 255, 255), (255, 190, 60), "MAVI"),
    "2": ((38, 80, 60), (85, 255, 255), (170, 232, 108), "YESIL"),
    "3": ((18, 110, 90), (35, 255, 255), (90, 220, 255), "SARI"),
}


def kamera_ac():
    for idx in (0, 1):
        c = cv2.VideoCapture(idx)
        if not c.isOpened():
            c.release()
            continue
        for _ in range(20):
            ok, frm = c.read()
            if ok and frm is not None and frm.size > 0:
                return c
            time.sleep(0.04)
        c.release()
    return None


def main():
    cap = kamera_ac()
    if cap is None:
        print("Kamera açılamadı veya görüntü gelmedi. Kamera iznini kontrol edin.")
        return

    WIN = "BONUS 1 - Sanal Cizim Tahtasi (f: ozellikler | q: cikis)"
    flags = cv2.WINDOW_NORMAL | (cv2.WINDOW_KEEPRATIO if hasattr(cv2, "WINDOW_KEEPRATIO") else 0)
    cv2.namedWindow(WIN, flags)

    aktif = "1"
    tuval = None
    onceki = None
    show_help = False
    sized = False

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            if not sized:
                scale = min(1.0, 1120 / max(w, 1), 680 / max(h, 1))
                cv2.resizeWindow(WIN, int(w * scale), int(h * scale))
                sized = True
            if tuval is None:
                tuval = np.zeros_like(frame)

            alt, ust, renk, ad = RENKLER[aktif]
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            maske = cv2.inRange(hsv, np.array(alt), np.array(ust))

            # Gürültüyü temizle
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
            maske = cv2.morphologyEx(maske, cv2.MORPH_OPEN, kernel)
            maske = cv2.morphologyEx(maske, cv2.MORPH_DILATE, kernel)

            konturlar, _ = cv2.findContours(maske, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if konturlar:
                en_buyuk = max(konturlar, key=cv2.contourArea)
                if cv2.contourArea(en_buyuk) > 450:
                    (x, y), r = cv2.minEnclosingCircle(en_buyuk)
                    merkez = (int(x), int(y))
                    cv2.circle(frame, merkez, int(r), renk, 2)
                    cv2.circle(frame, merkez, 6, (255, 255, 255), -1)
                    if onceki is not None:
                        cv2.line(tuval, onceki, merkez, renk, 6, cv2.LINE_AA)
                    onceki = merkez
                else:
                    onceki = None
            else:
                onceki = None

            # Çizimi kamera görüntüsüyle birleştir
            gri_tuval = cv2.cvtColor(tuval, cv2.COLOR_BGR2GRAY)
            _, ters_maske = cv2.threshold(gri_tuval, 10, 255, cv2.THRESH_BINARY_INV)
            arka = cv2.bitwise_and(frame, frame, mask=ters_maske)
            sonuc = cv2.add(arka, tuval)

            cv2.rectangle(sonuc, (0, 0), (w, 40), (24, 18, 28), -1)
            cv2.putText(
                sonuc,
                f"Takip: {ad}  (1:Mavi 2:Yesil 3:Sari | c:Temizle | [F] Ozellikler | q:Cikis)",
                (14, 27),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.56,
                (170, 232, 108),
                2,
                cv2.LINE_AA,
            )

            if show_help:
                ov = sonuc.copy()
                cv2.rectangle(ov, (w // 2 - 270, h // 2 - 90), (w // 2 + 270, h // 2 + 90), (24, 18, 28), -1)
                cv2.addWeighted(ov, 0.88, sonuc, 0.12, 0, sonuc)
                cv2.rectangle(sonuc, (w // 2 - 270, h // 2 - 90), (w // 2 + 270, h // 2 + 90), (170, 232, 108), 2)
                satirlar = [
                    "BONUS 1 - Sanal Cizim Tahtasi (HSV)",
                    "Amac: Renkli bir kalem kapagini HSV maskesiyle takip edip cizmek.",
                    "- [1] Mavi  |  [2] Yesil  |  [3] Sari nesne takibi sec",
                    "- [c] Tuvali temizle  |  [F] Kapat  |  [q / Esc] Cikis",
                ]
                for i, s in enumerate(satirlar):
                    cv2.putText(sonuc, s, (w // 2 - 252, h // 2 - 48 + i * 34),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.50, (233, 239, 242) if i else (170, 232, 108), 1, cv2.LINE_AA)

            cv2.imshow(WIN, sonuc)

            tus = cv2.waitKey(1) & 0xFF
            if tus in (ord("q"), 27):
                break
            elif tus in (ord("f"), ord("F")):
                show_help = not show_help
            elif tus == ord("c"):
                tuval[:] = 0
            elif tus in (ord("1"), ord("2"), ord("3")):
                aktif = chr(tus)
                onceki = None
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
