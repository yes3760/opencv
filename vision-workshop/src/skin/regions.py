"""Yüz işaret noktalarından cilt analiz bölgelerinin (ROI) maskelenmesi.

Girdi : 478 yüz noktası (piksel), görüntü boyutu, isteğe bağlı segmentasyon maskesi
Çıktı : Bölge adı -> ikili maske (uint8, 0 veya 255) ve kapsama bilgisi
Görev : Alın ve yanakları seçmek; göz, kaş, dudak ve saçı mümkün olduğunca dışarıda bırakmak.

Bölge adları kişinin kendi sağ/soluna göredir. Nokta numaraları MediaPipe
Face Mesh dizinidir ve presentation/src/lib/faceRegions.ts ile aynıdır.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from common.models import vision

FOREHEAD = [67, 109, 10, 338, 297, 299, 296, 336, 9, 107, 66, 69]
RIGHT_CHEEK = [116, 117, 118, 119, 100, 36, 205, 187, 147, 123]     # kişinin sağ yanağı
LEFT_CHEEK = [345, 346, 347, 348, 329, 266, 425, 411, 376, 352]     # kişinin sol yanağı

REGIONS = {"alın": FOREHEAD, "sağ yanak": RIGHT_CHEEK, "sol yanak": LEFT_CHEEK}

_C = vision.FaceLandmarksConnections


def _indices(connections) -> list[int]:
    return sorted({i for c in connections for i in (c.start, c.end)})


# Dışarıda bırakılacak yapılar (kenar payı eklenerek)
EXCLUDE = {
    "gözler": [_indices(_C.FACE_LANDMARKS_LEFT_EYE), _indices(_C.FACE_LANDMARKS_RIGHT_EYE)],
    "kaşlar": [_indices(_C.FACE_LANDMARKS_LEFT_EYEBROW), _indices(_C.FACE_LANDMARKS_RIGHT_EYEBROW)],
    "dudaklar": [_indices(_C.FACE_LANDMARKS_LIPS)],
}
FACE_OVAL = _indices(_C.FACE_LANDMARKS_FACE_OVAL)

# Selfie Multiclass segmentasyon modelinin sınıfları (model kartındaki sıra)
SEG_CLASSES = {0: "arka plan", 1: "saç", 2: "vücut cildi", 3: "yüz cildi", 4: "giysi", 5: "diğer (aksesuar)"}
SEG_FACE_SKIN = 3


@dataclass
class RegionMasks:
    masks: dict[str, np.ndarray]          # son, geçerli bölge maskeleri
    polygons: dict[str, np.ndarray]       # bölge çokgenleri (piksel)
    coverage: dict[str, float]            # maskeleme sonrası kalan oran (0-1)
    exclusion: np.ndarray                 # dışarıda bırakılan alan
    method: str                           # "segmentasyon" veya "renk tutarlılığı"


def polygon_mask(points: np.ndarray, indices, shape) -> np.ndarray:
    mask = np.zeros(shape[:2], np.uint8)
    poly = np.round(points[indices]).astype(np.int32)
    cv2.fillPoly(mask, [poly], 255)
    return mask


def exclusion_mask(points: np.ndarray, shape, margin_px: int) -> np.ndarray:
    """Göz, kaş ve dudak çevresinin dışbükey zarfı, kenar payıyla genişletilmiş."""
    mask = np.zeros(shape[:2], np.uint8)
    for groups in EXCLUDE.values():
        for idx in groups:
            hull = cv2.convexHull(np.round(points[idx]).astype(np.int32))
            cv2.fillConvexPoly(mask, hull, 255)
    if margin_px > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * margin_px + 1, 2 * margin_px + 1))
        mask = cv2.dilate(mask, kernel)
    return mask


def build_region_masks(image_bgr: np.ndarray, points: np.ndarray, face_width_px: float,
                       erosion_ratio: float, seg_mask: np.ndarray | None = None) -> RegionMasks:
    """Bölge maskelerini oluşturur.

    1. Çokgen, yüz noktalarından çizilir.
    2. Kenarlardan içeri çekilir (aşındırma), çünkü noktalar birkaç piksel kayabilir.
    3. Göz, kaş ve dudak çevresi çıkarılır.
    4. Saç ve aksesuarlar çıkarılır: segmentasyon maskesi varsa yalnızca "yüz cildi"
       sınıfı tutulur; yoksa yüz ortancasından çok daha koyu pikseller atılır.
    """
    shape = image_bgr.shape
    erode_px = max(1, int(round(face_width_px * erosion_ratio)))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * erode_px + 1, 2 * erode_px + 1))
    excl = exclusion_mask(points, shape, margin_px=erode_px * 2)

    polygons, raw = {}, {}
    for name, idx in REGIONS.items():
        polygons[name] = np.round(points[idx]).astype(np.int32)
        raw[name] = cv2.erode(polygon_mask(points, idx, shape), kernel)
        raw[name][excl > 0] = 0

    if seg_mask is not None:
        allowed = (seg_mask == SEG_FACE_SKIN).astype(np.uint8) * 255
        method = "segmentasyon"
    else:
        lab_l = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)[..., 0]
        union = np.zeros(shape[:2], bool)
        for m in raw.values():
            union |= m > 0
        median_l = float(np.median(lab_l[union])) if union.any() else 128.0
        allowed = (lab_l.astype(np.float32) > median_l - 35).astype(np.uint8) * 255
        method = "renk tutarlılığı"

    masks, coverage = {}, {}
    for name, m in raw.items():
        total = int(np.count_nonzero(m))
        final = cv2.bitwise_and(m, allowed)
        kept = int(np.count_nonzero(final))
        masks[name] = final
        coverage[name] = kept / total if total else 0.0
    return RegionMasks(masks, polygons, coverage, excl, method)
