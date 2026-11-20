"""Öğrenilmiş model: MediaPipe Selfie Multiclass Segmenter (isteğe bağlı).

Girdi : BGR görüntü
Çıktı : Her piksel için sınıf numarası (0 arka plan, 1 saç, 2 vücut cildi,
        3 yüz cildi, 4 giysi, 5 diğer/aksesuar)
Görev : Saç ve aksesuarların cilt bölgesinden çıkarılmasına yardım etmek.

Bu bir segmentasyon modelidir: her piksele sınıf verir. Cildin durumu hakkında
hiçbir şey söylemez; yalnızca "bu piksel yüz cildi mi?" sorusunu yanıtlar.
Model kartı: Apache 2.0, giriş 256x256. Model dosyası yoksa cilt modülü
renk tutarlılığı yöntemiyle çalışmaya devam eder.
"""

from __future__ import annotations

import cv2
import mediapipe as mp
import numpy as np

import config
from common.models import base_options, vision


class SkinSegmenter:
    def __init__(self, model_path=config.SEGMENTER_MODEL) -> None:
        options = vision.ImageSegmenterOptions(
            base_options=base_options(model_path),
            running_mode=vision.RunningMode.IMAGE,   # tek kare analizi
            output_category_mask=True,
            output_confidence_masks=False,
        )
        self._segmenter = vision.ImageSegmenter.create_from_options(options)

    def segment(self, image_bgr: np.ndarray) -> np.ndarray:
        rgb = np.ascontiguousarray(cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB))
        result = self._segmenter.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
        mask = result.category_mask.numpy_view()
        return np.squeeze(mask).astype(np.uint8).copy()

    def close(self) -> None:
        self._segmenter.close()
