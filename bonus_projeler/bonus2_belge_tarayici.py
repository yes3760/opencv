"""BONUS PROJE 2 — Akıllı Belge Tarayıcı (CamScanner Mantığı)

Yalnızca OpenCV ve NumPy kullanır.
Kameraya tutulan dikdörtgen bir kağıdın veya kimlik/not kartının 4 köşesini
Canny kenar tespiti + kontur yaklaşımı ile bulur ve 's' tuşuna basıldığında
perspektif dönüşümü (warpPerspective) ile düz taranmış belgeye çevirir.

Çalıştırma : python bonus_projeler/bonus2_belge_tarayici.py
Tuşlar     : s: Belgeyi tara | f: Özellikler | q: Çıkış
"""

import time
import cv2
import numpy as np


def koseleri_sirala(pts: np.ndarray) -> np.ndarray:
    """4 köşeyi sol-üst, sağ-üst, sağ-alt, sol-alt sırasına dizer."""
    pts = pts.reshape(4, 2).astype("float32")
    sira = np.zeros((4, 2), dtype="float32")
    toplam = pts.sum(axis=1)
    fark = np.diff(pts, axis=1)
    sira[0] = pts[np.argmin(toplam)]  # sol-üst
    sira[2] = pts[np.argmax(toplam)]  # sağ-alt
    sira[1] = pts[np.argmin(fark)]    # sağ-üst
    sira[3] = pts[np.argmax(fark)]    # sol-alt
    return sira


def perspektif_duzelt(img: np.ndarray, kose: np.ndarray) -> np.ndarray:
    rect = koseleri_sirala(kose)
    tl, tr, br, bl = rect
    w = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    h = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
    w, h = max(w, 200), max(h, 200)
    hedef = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, hedef)
    return cv2.warpPerspective(img, M, (w, h))


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
        print("Kamera açılamadı veya görüntü gelmedi.")
        return

    WIN = "BONUS 2 - Akilli Belge Tarayici (f: ozellikler | q: cikis)"
    flags = cv2.WINDOW_NORMAL | (cv2.WINDOW_KEEPRATIO if hasattr(cv2, "WINDOW_KEEPRATIO") else 0)
    cv2.namedWindow(WIN, flags)

    show_help = False
    sized = False

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            h, w = frame.shape[:2]
            if not sized:
                scale = min(1.0, 1120 / max(w, 1), 680 / max(h, 1))
                cv2.resizeWindow(WIN, int(w * scale), int(h * scale))
                sized = True

            gri = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gri, (5, 5), 0)
            kenar = cv2.Canny(blur, 55, 150)
            kenar = cv2.dilate(kenar, np.ones((3, 3), np.uint8), iterations=1)

            konturlar, _ = cv2.findContours(kenar, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            konturlar = sorted(konturlar, key=cv2.contourArea, reverse=True)[:5]

            belge = None
            for c in konturlar:
                if cv2.contourArea(c) < 12000:
                    continue
                cevre = cv2.arcLength(c, True)
                yaklasik = cv2.approxPolyDP(c, 0.02 * cevre, True)
                if len(yaklasik) == 4:
                    belge = yaklasik
                    break

            goster = frame.copy()
            if belge is not None:
                cv2.drawContours(goster, [belge], -1, (170, 232, 108), 3)
                durum = "Belge bulundu! Taramak icin [s] tusuna bas  |  [F] Ozellikler"
            else:
                durum = "Koyu zemin uzerinde beyaz kagit gosterin  |  [F] Ozellikler"

            cv2.rectangle(goster, (0, 0), (w, 40), (24, 18, 28), -1)
            cv2.putText(goster, durum, (14, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (170, 232, 108), 2, cv2.LINE_AA)

            if show_help:
                ov = goster.copy()
                cv2.rectangle(ov, (w // 2 - 270, h // 2 - 90), (w // 2 + 270, h // 2 + 90), (24, 18, 28), -1)
                cv2.addWeighted(ov, 0.88, goster, 0.12, 0, goster)
                cv2.rectangle(goster, (w // 2 - 270, h // 2 - 90), (w // 2 + 270, h // 2 + 90), (170, 232, 108), 2)
                satirlar = [
                    "BONUS 2 - Akilli Belge Tarayici (CamScanner)",
                    "Amac: Kagidin 4 kosesini bulup perspektif duzeltmesi yapmak.",
                    "- Koyu masa uzerinde beyaz bir kagidi kameraya tutun.",
                    "- Yesil cerceve cikinca [s] ile tarayin  |  [F] Kapat  |  [q] Cikis",
                ]
                for i, s in enumerate(satirlar):
                    cv2.putText(goster, s, (w // 2 - 252, h // 2 - 48 + i * 34),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.50, (233, 239, 242) if i else (170, 232, 108), 1, cv2.LINE_AA)

            cv2.imshow(WIN, goster)

            tus = cv2.waitKey(1) & 0xFF
            if tus in (ord("q"), 27):
                break
            elif tus in (ord("f"), ord("F")):
                show_help = not show_help
            elif tus == ord("s") and belge is not None:
                duz = perspektif_duzelt(frame, belge)
                duz_gri = cv2.cvtColor(duz, cv2.COLOR_BGR2GRAY)
                taranmis = cv2.adaptiveThreshold(
                    duz_gri, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 8
                )
                cv2.namedWindow("Taranmis Belge (PDF Gorunumu)", flags)
                cv2.imshow("Taranmis Belge (PDF Gorunumu)", taranmis)
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
