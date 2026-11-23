"""Cilt görünümü analizinin adımlarını sırayla çalıştırır.

Girdi : Tam çözünürlüklü kare ve yüz modülünün o karedeki sonucu
Çıktı : SkinReport (kalite raporu; kalite uygunsa göstergeler ve haritalar)
Görev : Tek kare analizi. Yüz ve el takibi kadar sık çalışması gerekmez;
        kullanıcı hazır olduğunda (boşluk tuşu) veya birkaç saniyede bir çalışır.

Adımlar:
  1. Yüz kesilir ve yüz genişliği sabit piksele ölçeklenir (mesafe etkisini azaltır).
  2. İsteğe bağlı segmentasyon modeli saç/aksesuar piksellerini belirler.
  3. Alın ve yanak maskeleri çıkarılır.
  4. Kalite kontrolü yapılır; uygun değilse burada durulur.
  5. Göstergeler ve ısı haritaları hesaplanır.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import cv2
import numpy as np

import config
from common.geometry import bounding_box
from common.models import ModelMissingError
from face.tracker import FaceObservation
from skin.metrics import SkinMetrics, compute_metrics
from skin.quality import Check, QualityReport, check_quality
from skin.regions import RegionMasks, build_region_masks


@dataclass
class SkinReport:
    quality: QualityReport
    metrics: SkinMetrics | None = None
    crop: np.ndarray | None = None
    regions: RegionMasks | None = None
    elapsed_ms: float = 0.0

    @property
    def message(self) -> str:
        if self.metrics is None:
            return "Uygun görüntü bekleniyor. " + self.quality.first_problem
        return "Analiz tamamlandı. " + config.SKIN_DISCLAIMER


class SkinAnalyzer:
    def __init__(self, use_segmenter: bool = True) -> None:
        self.segmenter = None
        self.segmenter_note = "Segmentasyon kapalı: renk tutarlılığı yöntemi kullanılıyor."
        if use_segmenter:
            try:
                from skin.segmenter import SkinSegmenter
                self.segmenter = SkinSegmenter()
                self.segmenter_note = "Segmentasyon modeli etkin (saç ve aksesuar ayrılıyor)."
            except ModelMissingError as exc:
                self.segmenter_note = f"Segmentasyon modeli yok, temel yöntemle devam ediliyor. {exc}"
            except Exception as exc:  # isteğe bağlı model çalışmazsa temel modül devam eder
                self.segmenter_note = f"Segmentasyon modeli yüklenemedi ({exc}); temel yöntemle devam ediliyor."

    def analyze(self, full_bgr: np.ndarray, faces: list[FaceObservation], scale_to_full: float) -> SkinReport:
        start = time.perf_counter()
        if len(faces) != 1:
            report = QualityReport([Check("Tek yüz", False, f"{len(faces)} yüz",
                                          "Analiz için kadrajda yalnızca bir kişi bulunmalı.")])
            return SkinReport(report, elapsed_ms=(time.perf_counter() - start) * 1000)

        face = faces[0]
        points_full = face.points * scale_to_full
        width_full = face.width_px * scale_to_full

        # 1. Yüz kesiti ve ölçekleme
        h, w = full_bgr.shape[:2]
        x1, y1, x2, y2 = bounding_box(points_full, margin=0.15)
        x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
        scale = config.SKIN_ANALYSIS_FACE_WIDTH / max(width_full, 1.0)
        crop = full_bgr[y1:y2, x1:x2]
        crop = cv2.resize(crop, (max(1, round(crop.shape[1] * scale)), max(1, round(crop.shape[0] * scale))),
                          interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
        points = (points_full - np.array([x1, y1], np.float32)) * scale

        # 2-3. Segmentasyon (varsa) ve bölge maskeleri
        seg = self.segmenter.segment(crop) if self.segmenter is not None else None
        regions = build_region_masks(crop, points, config.SKIN_ANALYSIS_FACE_WIDTH,
                                     config.SKIN_ROI_EROSION_RATIO, seg)
        union = np.zeros(crop.shape[:2], np.uint8)
        for m in regions.masks.values():
            union |= m

        # 4. Kalite kontrolü
        face_box = bounding_box(points, margin=0.0)
        quality = check_quality(crop, len(faces), width_full, face.pose, face_box, union, regions.coverage)
        if not quality.ok:
            return SkinReport(quality, None, crop, regions, (time.perf_counter() - start) * 1000)

        # 5. Göstergeler (yalnızca yeterince görünen bölgeler)
        valid = {k: m for k, m in regions.masks.items()
                 if regions.coverage[k] >= config.SKIN_MIN_VALID_FRACTION}
        metrics = compute_metrics(crop, valid)
        return SkinReport(quality, metrics, crop, regions, (time.perf_counter() - start) * 1000)

    def close(self) -> None:
        if self.segmenter is not None:
            self.segmenter.close()
