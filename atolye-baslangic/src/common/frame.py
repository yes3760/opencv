"""Bir kareyi tüm modüllerin ortak kullanacağı biçime hazırlar.

Kamera karesi bir kez okunur, bir kez küçültülür ve bir kez RGB'ye çevrilir.
Yüz, el ve cilt modülleri aynı Frame nesnesini paylaşır; böylece aynı iş
her modülde tekrar yapılmaz.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import cv2
import mediapipe as mp
import numpy as np


@dataclass
class Frame:
    full_bgr: np.ndarray     # kameranın verdiği çözünürlükte, aynalanmamış (cilt analizi için)
    bgr: np.ndarray          # işleme çözünürlüğünde, aynalanmamış
    rgb: np.ndarray          # bgr'nin RGB kopyası (MediaPipe RGB bekler)
    mp_image: mp.Image       # MediaPipe'ın görüntü nesnesi
    timestamp_ms: int        # VIDEO modu için artan zaman damgası
    index: int               # kaç numaralı kare olduğu

    @property
    def size(self) -> tuple[int, int]:
        """İşleme karesinin (genişlik, yükseklik) değeri."""
        return self.bgr.shape[1], self.bgr.shape[0]

    @property
    def scale_to_full(self) -> float:
        """İşleme karesindeki bir pikselin tam çözünürlükte kaç piksel olduğu."""
        return self.full_bgr.shape[1] / self.bgr.shape[1]


def resize_to_width(image: np.ndarray, width: int) -> np.ndarray:
    """En-boy oranını koruyarak görüntüyü verilen genişliğe hızlıca getirir."""
    h, w = image.shape[:2]
    if w == width:
        return image
    height = round(h * width / w)
    # INTER_LINEAR gerçek zamanlı videoda INTER_AREA'ya göre ~10x daha hızlıdır.
    return cv2.resize(image, (width, height), interpolation=cv2.INTER_LINEAR)


class FrameClock:
    """MediaPipe VIDEO modu için her zaman artan milisaniye zaman damgası üretir."""

    def __init__(self) -> None:
        self._start = time.monotonic()
        self._last = -1

    def now_ms(self) -> int:
        ms = int((time.monotonic() - self._start) * 1000)
        if ms <= self._last:          # aynı milisaniyede iki kare gelirse
            ms = self._last + 1
        self._last = ms
        return ms


class FramePreparer:
    """Ham kamera karesinden Frame nesnesi üretir."""

    def __init__(self, process_width: int = 640) -> None:
        self.process_width = process_width
        self.clock = FrameClock()
        self.count = 0

    def __call__(self, full_bgr: np.ndarray) -> Frame:
        bgr = resize_to_width(full_bgr, self.process_width)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
        self.count += 1
        return Frame(full_bgr, bgr, rgb, mp_image, self.clock.now_ms(), self.count)
