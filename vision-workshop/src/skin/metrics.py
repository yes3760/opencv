"""Açıklanabilir cilt görünümü göstergeleri ve ısı haritaları.

Bu göstergeler kameranın kaydettiği piksel değerlerinin özetidir; biyolojik
ölçüm değildir:

  Göreli kızarıklık görünümü : LAB a* kanalının yüzün kendi ortancasından farkı.
                               Klinik bir teşhis değildir.
  Parlak piksel oranı         : Yüzün geri kalanından belirgin biçimde açık ve soluk
                               piksellerin yüzdesi. Işık yansımasını gösterir; yağ
                               üretiminin ölçümü değildir.
  Doku değişimi               : Aydınlatma çıkarıldıktan sonra kalan ince parlaklık
                               dalgalanması. Gözenek veya hastalık tanısı değildir;
                               kamera gürültüsü, keskinleştirme, makyaj ve sakaldan etkilenir.
  Yerel renk farkı            : Her pikselin bölge ortancasına CIELAB uzaklığı (ΔE76).

Bütün değerler aynı kamerada, aynı ışıkta ve aynı ayarlarla bile değişebilir.
Farklı günlerde alınan sonuçlar standart koşullar olmadan karşılaştırılmamalıdır.

OpenCV'de 8 bit LAB kodlaması: L = L* x 255/100, a = a* + 128, b = b* + 128.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

import config

# Isı haritalarının sabit gösterim aralıkları. Her görüntüde en düşük-en yüksek
# değere göre ölçeklemek küçük farkları abartır; bu yüzden sabit aralık kullanılır.
MAP_RANGES = {
    "kızarıklık görünümü": (-10.0, 10.0),   # Δa*
    "doku değişimi": (0.0, 12.0),           # L düzeyi
    "yerel renk farkı": (0.0, 15.0),        # ΔE76
    "parlama": (0.0, 1.0),
}


@dataclass
class RegionStats:
    pixels: int
    mean_a: float               # a* ortalaması (kameraya bağlı, kalibre değil)
    delta_a: float              # a* - yüz ortancası
    shine_percent: float        # parlak piksel yüzdesi
    texture: float              # doku değişimi ortalaması
    color_diff: float           # bölge içi ortalama ΔE76


@dataclass
class SkinMetrics:
    regions: dict[str, RegionStats] = field(default_factory=dict)
    maps: dict[str, np.ndarray] = field(default_factory=dict)   # float32 haritalar
    union: np.ndarray | None = None                               # tüm geçerli bölgeler
    cheek_delta_e: float | None = None                            # sağ ve sol yanak ortancaları arası ΔE76


def lab_float(image_bgr: np.ndarray) -> np.ndarray:
    """OpenCV 8 bit LAB'ı gerçek ölçeğe çevirir: L* 0-100, a* ve b* yaklaşık -128..127."""
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    lab[..., 0] *= 100.0 / 255.0
    lab[..., 1:] -= 128.0
    return lab


def compute_metrics(image_bgr: np.ndarray, masks: dict[str, np.ndarray]) -> SkinMetrics:
    lab = lab_float(image_bgr)
    l_star, a_star, b_star = lab[..., 0], lab[..., 1], lab[..., 2]
    l_8bit = l_star * 255.0 / 100.0

    union = np.zeros(image_bgr.shape[:2], bool)
    for m in masks.values():
        union |= m > 0
    result = SkinMetrics(union=union.astype(np.uint8) * 255)
    if not union.any():
        return result

    # 1) Göreli kızarıklık görünümü: a* - yüz ortancası
    median_a = float(np.median(a_star[union]))
    redness = a_star - median_a

    # 2) Parlama: yüzün geri kalanına göre belirgin biçimde daha açık ve daha soluk pikseller
    chroma = np.sqrt(a_star ** 2 + b_star ** 2)
    median_l = float(np.median(l_8bit[union]))
    median_chroma = float(np.median(chroma[union]))
    shine = ((l_8bit >= median_l + config.SPECULAR_DELTA_L) &
             (chroma <= config.SPECULAR_CHROMA_RATIO * median_chroma)).astype(np.float32)

    # 3) Doku değişimi: büyük ölçekli aydınlatmayı çıkar, kalan ince ayrıntının yerel enerjisi
    blurred = cv2.GaussianBlur(l_8bit, (0, 0), config.TEXTURE_BLUR_SIGMA)
    detail = l_8bit - blurred
    texture = np.sqrt(cv2.GaussianBlur(detail ** 2, (0, 0), 2.0))

    # 4) Yerel renk farkı: her pikselin kendi bölgesinin ortancasına uzaklığı
    color_diff = np.zeros_like(l_star)
    medians = {}
    for name, m in masks.items():
        sel = m > 0
        if not sel.any():
            continue
        med = np.median(lab[sel], axis=0)
        medians[name] = med
        color_diff[sel] = np.linalg.norm(lab[sel] - med, axis=1)

    for name, m in masks.items():
        sel = m > 0
        if not sel.any():
            continue
        result.regions[name] = RegionStats(
            pixels=int(sel.sum()),
            mean_a=float(a_star[sel].mean()),
            delta_a=float(redness[sel].mean()),
            shine_percent=float(shine[sel].mean() * 100),
            texture=float(texture[sel].mean()),
            color_diff=float(color_diff[sel].mean()),
        )
    if "sağ yanak" in medians and "sol yanak" in medians:
        result.cheek_delta_e = float(np.linalg.norm(medians["sağ yanak"] - medians["sol yanak"]))

    result.maps = {
        "kızarıklık görünümü": redness,
        "doku değişimi": texture,
        "yerel renk farkı": color_diff,
        "parlama": shine,
    }
    return result


def render_heatmap(image_bgr: np.ndarray, values: np.ndarray, mask: np.ndarray, name: str,
                   alpha: float = 0.6) -> np.ndarray:
    """Haritayı sabit aralıkla renklendirip yalnızca maske içinde görüntünün üstüne bindirir."""
    lo, hi = MAP_RANGES[name]
    norm = np.clip((values - lo) / (hi - lo), 0, 1)
    colored = cv2.applyColorMap((norm * 255).astype(np.uint8), cv2.COLORMAP_VIRIDIS)
    out = image_bgr.copy()
    sel = mask > 0
    out[sel] = (alpha * colored[sel] + (1 - alpha) * image_bgr[sel]).astype(np.uint8)
    dim = ~sel
    out[dim] = (out[dim] * 0.45).astype(np.uint8)   # bölge dışını karart
    return out
