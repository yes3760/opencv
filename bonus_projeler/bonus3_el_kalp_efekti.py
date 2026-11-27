"""BONUS PROJE 3 — SEIS NEON AR VFX STÜDYOSU (Gerçek Bloom Parıltılı Bilgisayarlı Görü Efekt Motoru)

Mevcut vision-workshop ortamındaki OpenCV + NumPy + MediaPipe HandTracker (max_hands=2)
ile çalışır; ek paket veya model indirmenize gerek yoktur.

Gerçek Zamanlı VFX Motoru (Ayrı Glow Katmanı + Gaussian Bloom + Additive Blending):
  1. 🫶 İKİ ELLE KALP     : Gerçek neon bloom parıltılı kalp + şarj barı + %100'de ŞOK DALGASI & 60 parçacık patlaması!
  2. ⚡ İKİ AÇIK EL       : İki avuç arasında canlı plazma şimşek arkı + mesafeye göre büyüyen enerji küresi!
  3. 🖐️ TEK AÇIK EL       : Avuç içinde dönen Doctor Strange / siber bilgisayarlı görü mandala halkası!
  4. ☝️ İŞARET PARMAĞI    : Havada sönerek kaybolan neon ışık kurdelesi (lazer izi) ve kıvılcımlar!
  5. ✌️ V İŞARETİ         : "SEIS IT WORKSHOP!" neon rozeti + konfeti yağmuru!
  6. 👍 BAŞPARMAK YUKARI  : Altın yıldız yağmuru + "HARİKA! +100" efekti!
  7. ✊ YUMRUK            : Etraftaki enerji parçacıklarını avuca çeken çekim alanı!

Tuşlar:
  m : Arka plan modu (Sinema Neon / Doğal Kamera / TRON Kenar Modu)
  s : Hatıra fotoğrafı kaydet (PNG)
  c : Tüm efektleri ve izi temizle
  q : Çıkış
"""

import math
import random
import sys
import time
from collections import deque
from pathlib import Path

import cv2
import numpy as np

# src klasörünü otomatik bul (hem atolye-baslangic/bonus_projeler hem Gemini/bonus_projeler için)
for _p in Path(__file__).resolve().parents:
    if (_p / "src").is_dir():
        if str(_p / "src") not in sys.path:
            sys.path.insert(0, str(_p / "src"))
        break

import config
from camera import Camera, CameraError
from common.app import Canvas, DisplayLoop, build_parser
from common.draw import panel, put_text, status_line
from common.fps import FPSMeter
from common.frame import FramePreparer
from common.models import ModelMissingError
from hands.gestures import classify_static, finger_states
from hands.tracker import HandTracker

# Renk Paleti (BGR)
MINT = (170, 232, 108)
CYAN = (255, 225, 80)
CREAM = (218, 236, 247)
PEACH = (130, 161, 235)
PINK = (165, 70, 255)
MAGENTA = (220, 60, 255)
GOLD = (80, 215, 255)
PLUM_BG = (22, 8, 36)

MODLAR = ["Sinema Neon", "Dogal Kamera", "TRON Kenar"]


def kalp_pts(cx: float, cy: float, boyut: float, n: int = 64) -> np.ndarray:
    t = np.linspace(0, 2 * math.pi, n)
    x = 16 * np.sin(t) ** 3
    y = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
    return np.column_stack((cx + x * (boyut / 16.0), cy + y * (boyut / 16.0))).astype(np.int32)


def yildiz_pts(cx: float, cy: float, dis_r: float, aci: float = 0.0) -> np.ndarray:
    ic_r = dis_r * 0.42
    pts = []
    for i in range(10):
        r = dis_r if i % 2 == 0 else ic_r
        a = aci + i * math.pi / 5.0 - math.pi / 2.0
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return np.array(pts, dtype=np.int32)


def neon_el_iskeleti(glow: np.ndarray, pts: np.ndarray, renk=MINT):
    """El iskeletini parlak neon çizgiler ve eklem düğümleri olarak glow katmanına çizer."""
    baglar = [
        (0, 1), (1, 2), (2, 3), (3, 4),
        (0, 5), (5, 6), (6, 7), (7, 8),
        (5, 9), (9, 10), (10, 11), (11, 12),
        (9, 13), (13, 14), (14, 15), (15, 16),
        (13, 17), (0, 17), (17, 18), (18, 19), (19, 20),
    ]
    for a, b in baglar:
        p1 = (int(pts[a][0]), int(pts[a][1]))
        p2 = (int(pts[b][0]), int(pts[b][1]))
        cv2.line(glow, p1, p2, renk, 2, cv2.LINE_AA)
    for i, p in enumerate(pts):
        r = 5 if i in (4, 8, 12, 16, 20) else 3
        c = CREAM if i in (4, 8) else renk
        cv2.circle(glow, (int(p[0]), int(p[1])), r, c, -1, cv2.LINE_AA)


def siber_mandala_ciz(glow: np.ndarray, cx: int, cy: int, r: int, faz: float, renk=MINT):
    """Dönen çok katmanlı Doctor Strange / Bilgisayarlı Görü enerji halkası."""
    cv2.circle(glow, (cx, cy), r, renk, 2, cv2.LINE_AA)
    cv2.circle(glow, (cx, cy), int(r * 0.72), CYAN, 1, cv2.LINE_AA)
    cv2.circle(glow, (cx, cy), int(r * 0.35), CREAM, 1, cv2.LINE_AA)

    # Dönen yaylar
    aci = int((faz * 6) % 360)
    for off in (0, 90, 180, 270):
        cv2.ellipse(glow, (cx, cy), (r + 10, r + 10), 0, aci + off, aci + off + 48, renk, 3, cv2.LINE_AA)
        cv2.ellipse(glow, (cx, cy), (int(r * 0.85), int(r * 0.85)), 0, -aci + off, -aci + off + 38, PEACH, 2, cv2.LINE_AA)

    # Dönen iç altıgen
    hex_pts = []
    for k in range(6):
        a = faz * 0.06 + k * (math.pi / 3.0)
        hex_pts.append((int(cx + math.cos(a) * r * 0.68), int(cy + math.sin(a) * r * 0.68)))
    cv2.polylines(glow, [np.array(hex_pts, dtype=np.int32)], True, renk, 1, cv2.LINE_AA)


def plazma_simsek_ciz(glow: np.ndarray, p1: tuple[int, int], p2: tuple[int, int], faz: float):
    """İki avuç arasında canlı kırılan plazma şimşek arkı ve orta enerji küresi çizer."""
    x1, y1 = p1
    x2, y2 = p2
    mesafe = max(1.0, math.hypot(x2 - x1, y2 - y1))
    nx, ny = -(y2 - y1) / mesafe, (x2 - x1) / mesafe  # dik vektör

    # 2 katmanlı kırık şimşek kolu
    for katman, (renk, kalinlik, genlik) in enumerate([(CYAN, 4, 22), (CREAM, 2, 12)]):
        adim = 14
        noktalar = []
        for i in range(adim + 1):
            t = i / adim
            bx = x1 + (x2 - x1) * t
            by = y1 + (y2 - y1) * t
            sapma = 0.0 if i in (0, adim) else random.uniform(-genlik, genlik) * math.sin(t * math.pi)
            noktalar.append((int(bx + nx * sapma), int(by + ny * sapma)))
        cv2.polylines(glow, [np.array(noktalar, dtype=np.int32)], False, renk, kalinlik, cv2.LINE_AA)

    # Ortada mesafeye göre büyüyen enerji küresi
    mx, my = (x1 + x2) // 2, (y1 + y2) // 2
    kure_r = int(min(54, max(16, mesafe * 0.14)) + 4 * math.sin(faz * 0.4))
    cv2.circle(glow, (mx, my), kure_r, CYAN, 3, cv2.LINE_AA)
    cv2.circle(glow, (mx, my), max(6, kure_r // 2), CREAM, -1, cv2.LINE_AA)


def kalp_algila(hands) -> tuple[bool, tuple[float, float] | None]:
    if len(hands) < 2:
        return False, None
    h1, h2 = hands[0].points, hands[1].points
    avuc = max(float(np.linalg.norm(h1[0] - h1[9])), float(np.linalg.norm(h2[0] - h2[9])), 1.0)
    bas_d = float(np.linalg.norm(h1[4] - h2[4])) / avuc
    isr_d = float(np.linalg.norm(h1[8] - h2[8])) / avuc
    ust_y = (h1[8][1] + h2[8][1]) / 2.0
    alt_y = (h1[4][1] + h2[4][1]) / 2.0
    if bas_d < 0.78 and isr_d < 0.88 and ust_y < alt_y + 0.25 * avuc:
        return True, ((h1[4][0] + h2[4][0] + h1[8][0] + h2[8][0]) / 4.0, (ust_y + alt_y) / 2.0)
    return False, None


class Parcacik:
    def __init__(self, x, y, vx, vy, boyut, tur, renk, omur=36):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = float(vx), float(vy)
        self.boyut = float(boyut)
        self.tur = tur  # "kalp" | "yildiz" | "konfeti" | "kivilcim"
        self.renk = renk
        self.omur = omur
        self.max_omur = omur
        self.faz = random.uniform(0, 6.28)

    def guncelle_ve_ciz(self, glow: np.ndarray) -> bool:
        self.x += self.vx + (math.sin(self.faz) * 0.8 if self.tur == "kalp" else 0.0)
        self.y += self.vy
        self.vx *= 0.97
        self.vy += 0.07 if self.tur == "konfeti" else -0.02
        self.faz += 0.22
        self.omur -= 1
        if self.omur <= 0:
            return False

        oran = self.omur / self.max_omur
        b = max(3.0, self.boyut * (0.45 + 0.55 * oran))
        renk = tuple(int(c * (0.35 + 0.65 * oran)) for c in self.renk)
        ix, iy = int(self.x), int(self.y)
        if self.tur == "kalp":
            cv2.fillPoly(glow, [kalp_pts(ix, iy, b, n=28)], renk, cv2.LINE_AA)
        elif self.tur == "yildiz":
            cv2.fillPoly(glow, [yildiz_pts(ix, iy, b, self.faz)], renk, cv2.LINE_AA)
        else:
            cv2.circle(glow, (ix, iy), max(2, int(b * 0.42)), renk, -1, cv2.LINE_AA)
        return True


def bloom_birlestir(arka: np.ndarray, glow: np.ndarray) -> np.ndarray:
    """Glow katmanına gerçek Gaussian bloom uygulayıp sahneye ekler (additive neon)."""
    # Hızlı bloom için yarı çözünürlükte bulanıklaştırıp geri büyüt (yüksek FPS!)
    h, w = glow.shape[:2]
    kucuk = cv2.resize(glow, (w // 2, h // 2), interpolation=cv2.INTER_LINEAR)
    bul = cv2.GaussianBlur(kucuk, (21, 21), 0)
    bloom = cv2.resize(bul, (w, h), interpolation=cv2.INTER_LINEAR)
    sonuc = cv2.add(arka, bloom)
    return cv2.add(sonuc, glow)


def main():
    args = build_parser("SEIS Neon AR VFX Stüdyosu").parse_args()
    prepare, fps = FramePreparer(config.PROCESS_WIDTH), FPSMeter()

    parcaciklar: list[Parcacik] = []
    sok_dalgalari: list[list[float]] = []  # [cx, cy, r, max_r]
    lazer_izi: deque = deque(maxlen=28)

    faz = 0.0
    kalp_sarj = 0.0
    smooth_heart = None
    mod_idx = 0
    bildirim = ""
    bildirim_bitis = 0.0

    with Camera(args.source, config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT) as cam, \
            HandTracker(max_hands=2) as hands, \
            DisplayLoop(
                "SEIS NEON AR VFX STUDYOSU",
                args,
                help_title="Bonus 3 · SEIS Neon AR El Jestleri VFX Stüdyosu",
                help_lines=[
                    "Amaç: 21 el noktasından 7 farklı canlı neon AR efekti ve parçacık fiziği üretmek.",
                    "• 🫶 İki Elle Kalp: Neon kalp + %100 dolunca şok dalgası patlaması!",
                    "• ⚡ İki Açık El: Avuçlar arası canlı plazma şimşek arkı.",
                    "• ☝️ İşaret / 🖐️ Açık El / ✌️ V / 👍 Başparmak / ✊ Yumruk: Lazer, mandala, konfeti, yıldız!",
                    "• [m] Sahne modu (Sinema / Doğal / TRON)  ·  [s] Hatıra PNG kaydet  ·  [F] Kapat",
                ],
            ) as loop:
        while loop.running:
            raw = cam.read()
            if raw is None:
                break
            faz += 1.0
            frame = prepare(raw)
            result = hands.process(frame)

            canvas = Canvas(frame, mirror=not args.no_mirror)
            canvas.flip()
            arka = canvas.image
            h, w = arka.shape[:2]

            # Arka plan atmosfer modu
            if mod_idx == 0:  # Sinema Neon (neonların patlaması için hafif koyu bordo tonu)
                arka = (arka.astype(np.float32) * 0.68).astype(np.uint8)
            elif mod_idx == 2:  # TRON Kenar Modu
                gri = cv2.cvtColor(arka, cv2.COLOR_BGR2GRAY)
                kenar = cv2.Canny(cv2.GaussianBlur(gri, (5, 5), 0), 55, 145)
                arka = np.zeros_like(arka)
                arka[kenar > 0] = (95, 130, 62)

            # Siyah neon glow katmanı (tüm parlayan efektler buraya çizilir)
            glow = np.zeros_like(arka)

            # Ekran koordinatlarına çevrilmiş eller
            ekran_elleri = []
            for hand in result.hands:
                e_pts = np.array([canvas.screen(pt) for pt in hand.points], dtype=np.float32)
                jest = classify_static(finger_states(hand.points))
                ekran_elleri.append((e_pts, jest))
                neon_el_iskeleti(glow, e_pts, renk=MINT if jest != "yumruk" else PEACH)

            aktif_efekt = "Hazır — Jestini Göster!"
            kalp_var, ham_merkez = kalp_algila(result.hands)

            if kalp_var and ham_merkez is not None:
                lazer_izi.clear()
                sx, sy = canvas.screen(ham_merkez)
                smooth_heart = (sx, sy) if smooth_heart is None else (
                    0.35 * sx + 0.65 * smooth_heart[0], 0.35 * sy + 0.65 * smooth_heart[1]
                )
                cx, cy = int(smooth_heart[0]), int(smooth_heart[1])
                kalp_sarj = min(100.0, kalp_sarj + 3.0)
                nabiz = 48 + 10 * math.sin(faz * 0.35) + kalp_sarj * 0.16

                # Neon kalp + iç parlak katman + yörünge ışıkları
                cv2.fillPoly(glow, [kalp_pts(cx, cy, nabiz)], PINK, cv2.LINE_AA)
                cv2.fillPoly(glow, [kalp_pts(cx, cy - nabiz * 0.05, nabiz * 0.65)], CREAM, cv2.LINE_AA)
                for k in range(8):
                    a = faz * 0.1 + k * (math.pi / 4.0)
                    cv2.circle(glow, (int(cx + math.cos(a) * nabiz * 1.4), int(cy + math.sin(a) * nabiz * 1.15)),
                               4, MINT if k % 2 == 0 else GOLD, -1, cv2.LINE_AA)

                aktif_efekt = f"KALP ALGILANDI! (Şarj: %{int(kalp_sarj)})"
                if int(faz) % 2 == 0:
                    parcaciklar.append(Parcacik(
                        cx + random.randint(-42, 42), cy + random.randint(-12, 12),
                        random.uniform(-1.5, 1.5), random.uniform(-5.0, -2.2),
                        random.uniform(11, 20), "kalp", random.choice([PINK, MAGENTA, PEACH]), omur=34,
                    ))

                # %100 dolunca ŞOK DALGASI + 60 parçacık patlaması!
                if kalp_sarj >= 100.0:
                    sok_dalgalari.append([cx, cy, 24.0, max(w, h) * 0.65])
                    for _ in range(56):
                        a = random.uniform(0, 2 * math.pi)
                        spd = random.uniform(4.0, 12.0)
                        parcaciklar.append(Parcacik(
                            cx, cy, math.cos(a) * spd, math.sin(a) * spd - 1.5,
                            random.uniform(12, 22), random.choice(["kalp", "yildiz", "konfeti"]),
                            random.choice([PINK, MINT, GOLD, CYAN, CREAM]), omur=46,
                        ))
                    kalp_sarj = 15.0
                    bildirim = "SEIS KALP PATLAMASI!"
                    bildirim_bitis = time.monotonic() + 2.2
            else:
                smooth_heart = None
                kalp_sarj = max(0.0, kalp_sarj - 3.5)

                # İKİ AÇIK EL → PLAZMA ŞİMŞEK ARKI!
                acik_eller = [e_pts for e_pts, j in ekran_elleri if j == "acik_el"]
                if len(acik_eller) == 2:
                    lazer_izi.clear()
                    p1 = (int(acik_eller[0][9][0]), int(acik_eller[0][9][1]))
                    p2 = (int(acik_eller[1][9][0]), int(acik_eller[1][9][1]))
                    siber_mandala_ciz(glow, p1[0], p1[1], 38, faz, CYAN)
                    siber_mandala_ciz(glow, p2[0], p2[1], 38, -faz, CYAN)
                    plazma_simsek_ciz(glow, p1, p2, faz)
                    aktif_efekt = "PLAZMA ENERJİ ARKI! (İki Açık El)"
                else:
                    isaret_aktif = False
                    for e_pts, jest in ekran_elleri:
                        hx, hy = int(e_pts[9][0]), int(e_pts[9][1])
                        if jest == "acik_el":
                            siber_mandala_ciz(glow, hx, hy, 46, faz, MINT)
                            aktif_efekt = "SİBER MANDALA HUD (Açık El)"
                        elif jest == "isaret":
                            isaret_aktif = True
                            ix, iy = int(e_pts[8][0]), int(e_pts[8][1])
                            lazer_izi.append((ix, iy))
                            cv2.circle(glow, (ix, iy), 8, CYAN, -1, cv2.LINE_AA)
                            if int(faz) % 2 == 0:
                                parcaciklar.append(Parcacik(
                                    ix, iy, random.uniform(-2, 2), random.uniform(-2, 2),
                                    random.uniform(5, 10), "kivilcim", random.choice([CYAN, MINT, CREAM]), omur=20,
                                ))
                            aktif_efekt = "NEON LAZER ÇİZİMİ (İşaret Parmağı)"
                        elif jest == "v_isareti":
                            aktif_efekt = "SEIS IT WORKSHOP! (V İşareti)"
                            for _ in range(2):
                                parcaciklar.append(Parcacik(
                                    hx + random.randint(-30, 30), hy - 55,
                                    random.uniform(-3.0, 3.0), random.uniform(-6.0, -2.5),
                                    random.uniform(9, 15), "konfeti", random.choice([MINT, CREAM, PEACH]), omur=38,
                                ))
                        elif jest == "basparmak_yukari":
                            aktif_efekt = "HARİKA! +100 (Başparmak Yukarı)"
                            tx, ty = int(e_pts[4][0]), int(e_pts[4][1])
                            if int(faz) % 2 == 0:
                                parcaciklar.append(Parcacik(
                                    tx + random.randint(-18, 18), ty - 10,
                                    random.uniform(-1.8, 1.8), random.uniform(-5.2, -2.5),
                                    random.uniform(11, 18), "yildiz", GOLD, omur=34,
                                ))
                        elif jest == "yumruk":
                            aktif_efekt = "ENERJİ TOPLANIYOR (Yumruk)"
                            a = random.uniform(0, 2 * math.pi)
                            parcaciklar.append(Parcacik(
                                hx + math.cos(a) * 95, hy + math.sin(a) * 95,
                                -math.cos(a) * 5.2, -math.sin(a) * 5.2,
                                9, "kivilcim", PEACH, omur=18,
                            ))
                    if not isaret_aktif and lazer_izi:
                        lazer_izi.popleft()

            # Lazer kurdelesini çiz (kuyruktan uca kalınlaşan neon şerit)
            if len(lazer_izi) > 1:
                pts_l = list(lazer_izi)
                for i in range(1, len(pts_l)):
                    kal = max(1, int(9 * (i / len(pts_l))))
                    cv2.line(glow, pts_l[i - 1], pts_l[i], CYAN if i < len(pts_l) - 4 else CREAM, kal, cv2.LINE_AA)

            # Şok dalgalarını çiz
            yeni_dalga = []
            for d in sok_dalgalari:
                d[2] += 18.0
                if d[2] < d[3]:
                    oran = 1.0 - (d[2] / d[3])
                    renk = tuple(int(c * oran) for c in MINT)
                    cv2.circle(glow, (int(d[0]), int(d[1])), int(d[2]), renk, max(1, int(8 * oran)), cv2.LINE_AA)
                    yeni_dalga.append(d)
            sok_dalgalari = yeni_dalga

            # Parçacıkları güncelle ve glow katmanına çiz
            parcaciklar = [p for p in parcaciklar[-160:] if p.guncelle_ve_ciz(glow)]

            # Gerçek Neon Bloom birleştirme!
            img = bloom_birlestir(arka, glow)

            # Üst HUD Paneli
            panel(img, 12, 10, min(w - 12, 510), 74)
            put_text(img, f"SEIS NEON AR VFX  ·  Mod: {MODLAR[mod_idx]}  ·  FPS {fps.tick():.0f}", (24, 16), 15, MINT)
            put_text(img, aktif_efekt, (24, 42), 15, CREAM)

            # Kalp şarj çubuğu
            if kalp_sarj > 1:
                bx1, by1, bx2, by2 = w - 210, 16, w - 16, 36
                cv2.rectangle(img, (bx1, by1), (bx2, by2), PLUM_BG, -1)
                cv2.rectangle(img, (bx1, by1), (bx1 + int((bx2 - bx1) * kalp_sarj / 100.0), by2), PINK, -1)
                cv2.rectangle(img, (bx1, by1), (bx2, by2), MINT, 2)

            if time.monotonic() < bildirim_bitis and bildirim:
                put_text(img, bildirim, (w // 2 - 140, 88), 24, GOLD, bg=PLUM_BG)

            status_line(
                img,
                "Kalp | İki Açık El (Şimşek) | Tek Açık El | İşaret (Lazer) | V (SEIS) | Yumruk   (m: mod, s: foto, q: çıkış)",
                "ok" if result.hands else "warn",
            )

            key = loop.show(img)
            if key == ord("m"):
                mod_idx = (mod_idx + 1) % len(MODLAR)
            elif key == ord("c"):
                parcaciklar.clear()
                lazer_izi.clear()
                sok_dalgalari.clear()
                kalp_sarj = 0.0
            elif key == ord("s"):
                dosya = f"seis_neon_vfx_{int(time.time())}.png"
                cv2.imwrite(dosya, img)
                bildirim = f"Kaydedildi: {dosya}"
                bildirim_bitis = time.monotonic() + 2.2


if __name__ == "__main__":
    try:
        main()
    except (CameraError, ModelMissingError) as exc:
        print(exc)
