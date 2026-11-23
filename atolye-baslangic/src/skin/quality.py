"""Cilt analizi öncesi görüntü kalite kontrolü.

Kalite yetersizse ölçüm üretilmez; bunun yerine "Uygun görüntü bekleniyor" ve
nedeni gösterilir. Kötü bir görüntüden sayı üretmek, sayı üretmemekten daha
yanıltıcıdır.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

import config
from face.metrics import HeadPose


@dataclass
class Check:
    name: str
    ok: bool
    value: str
    hint: str = ""


@dataclass
class QualityReport:
    checks: list[Check] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.checks) and all(c.ok for c in self.checks)

    @property
    def first_problem(self) -> str:
        for c in self.checks:
            if not c.ok:
                return f"{c.name}: {c.hint}"
        return ""


def sharpness(image_bgr: np.ndarray, box: tuple[int, int, int, int], width: int = 256) -> float:
    """Göreli netlik: Laplace varyansı / gri ton varyansı x 1000.

    Laplace işlemi kenarları vurgular; bulanık görüntüde varyansı düşer
    (Pech-Pacheco vd., ICPR 2000). Gri ton varyansına bölmek, değeri genel
    parlaklık ve kontrasttan bağımsız yapar. Yüz kesiti sabit genişliğe
    ölçeklenir. Sınırlama: görüntü gürültüsü de kenar gibi görünür ve
    değeri yükseltir.
    """
    x1, y1, x2, y2 = box
    h, w = image_bgr.shape[:2]
    crop = image_bgr[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
    if crop.size == 0:
        return 0.0
    crop = cv2.resize(crop, (width, max(1, round(crop.shape[0] * width / crop.shape[1]))),
                      interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY).astype(np.float64)
    gray_var = gray.var()
    if gray_var < 1e-6:
        return 0.0
    return float(1000.0 * cv2.Laplacian(gray, cv2.CV_64F).var() / gray_var)


def exposure_stats(image_bgr: np.ndarray, mask: np.ndarray) -> tuple[float, float, float]:
    """Maskelenmiş alanda (ortanca parlaklık, doymuş oran, çok karanlık oran). L: 0-255."""
    l_channel = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)[..., 0]
    values = l_channel[mask > 0]
    if values.size == 0:
        return 0.0, 0.0, 1.0
    return (float(np.median(values)), float(np.mean(values >= 250)), float(np.mean(values <= 25)))


def check_quality(image_bgr: np.ndarray, face_count: int, face_width_px: float,
                  pose: HeadPose | None, face_box, skin_mask: np.ndarray,
                  coverage: dict[str, float]) -> QualityReport:
    report = QualityReport()
    report.checks.append(Check(
        "Tek yüz", face_count == 1, f"{face_count} yüz",
        "Analiz için kadrajda yalnızca bir kişi bulunmalı."))
    if face_count != 1:
        return report

    report.checks.append(Check(
        "Yüz boyutu", face_width_px >= config.SKIN_MIN_FACE_WIDTH_PX,
        f"{face_width_px:.0f} px (en az {config.SKIN_MIN_FACE_WIDTH_PX})",
        "Kameraya biraz yaklaşın."))

    if pose is None:
        report.checks.append(Check("Baş pozu", False, "ölçülemedi", "Yüzünüzü kameraya çevirin."))
    else:
        pose_ok = (abs(pose.yaw) <= config.SKIN_MAX_YAW_DEG and abs(pose.pitch) <= config.SKIN_MAX_PITCH_DEG
                   and abs(pose.roll) <= config.SKIN_MAX_ROLL_DEG)
        report.checks.append(Check(
            "Baş pozu", pose_ok,
            f"dönüş {pose.yaw:+.0f}°, eğim {pose.pitch:+.0f}°, yatma {pose.roll:+.0f}°",
            "Başınızı düz tutup doğrudan kameraya bakın."))

    sharp = sharpness(image_bgr, face_box)
    report.checks.append(Check(
        "Netlik", sharp >= config.SKIN_MIN_SHARPNESS,
        f"göreli netlik {sharp:.0f} (en az {config.SKIN_MIN_SHARPNESS:.0f})",
        "Hareketsiz durun; kamera merceğini silin."))

    median_l, clipped, dark = exposure_stats(image_bgr, skin_mask)
    if median_l < config.SKIN_MIN_MEDIAN_L or dark > config.SKIN_MAX_DARK_FRACTION:
        report.checks.append(Check("Pozlama", False, f"ortanca L {median_l:.0f}, karanlık %{dark * 100:.0f}",
                                   "Ortam çok karanlık: yüzünüzü önden aydınlatın."))
    elif median_l > config.SKIN_MAX_MEDIAN_L or clipped > config.SKIN_MAX_CLIPPED_FRACTION:
        report.checks.append(Check("Pozlama", False, f"ortanca L {median_l:.0f}, doymuş %{clipped * 100:.0f}",
                                   "Aşırı ışık: doğrudan gelen ışıktan uzaklaşın."))
    else:
        report.checks.append(Check("Pozlama", True, f"ortanca L {median_l:.0f}, doymuş %{clipped * 100:.0f}"))

    valid = [name for name, frac in coverage.items() if frac >= config.SKIN_MIN_VALID_FRACTION]
    report.checks.append(Check(
        "Bölge kapsaması", len(valid) >= 2,
        ", ".join(f"{k} %{v * 100:.0f}" for k, v in coverage.items()),
        "Saç, gözlük veya el bölgeleri örtüyor olabilir."))
    return report
