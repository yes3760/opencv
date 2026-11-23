"""El tespiti ve 21 işaret noktası.

Girdi : common.frame.Frame (aynalanmamış kare)
Çıktı : HandResult; her el için 21 nokta (piksel ve normalize), sağ/sol etiketi
Görev : MediaPipe Hand Landmarker'ı bir kez yükler ve her karede çalıştırır.

Sağ/sol etiketi modelin tahminidir. Etiketin kameraya ve aynalamaya göre doğru
olup olmadığı 07_el_noktalari.py içindeki deneyle kontrol edilir; ters ise
config.HANDEDNESS_SWAP = True yapılır.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

import config
from common.frame import Frame
from common.geometry import to_array, to_pixels
from common.models import base_options, vision

_SWAP = {"Left": "Right", "Right": "Left"}
LABEL_TR = {"Left": "sol", "Right": "sağ"}


@dataclass
class HandObservation:
    landmarks: np.ndarray     # (21, 3) normalize
    points: np.ndarray        # (21, 2) işleme karesinde piksel
    handedness: str           # "Left" veya "Right" (modelin tahmini, gerekirse çevrilmiş)
    score: float              # sağ/sol tahmininin skoru (el varlığı olasılığı değildir)

    @property
    def label_tr(self) -> str:
        return LABEL_TR.get(self.handedness, self.handedness)


@dataclass
class HandResult:
    hands: list[HandObservation]
    latency_ms: float

    @property
    def status(self) -> str:
        if not self.hands:
            return "El bulunamadı: elinizi avuç içi kameraya dönük gösterin."
        return f"{len(self.hands)} el izleniyor"


class HandTracker:
    def __init__(self, model_path=config.HAND_MODEL, max_hands: int = config.MAX_HANDS) -> None:
        options = vision.HandLandmarkerOptions(
            base_options=base_options(model_path),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=config.MIN_HAND_DETECTION_CONFIDENCE,
            min_hand_presence_confidence=config.MIN_HAND_PRESENCE_CONFIDENCE,
            min_tracking_confidence=config.HAND_TRACKING_CONFIDENCE,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)
        self.last = HandResult([], 0.0)

    def process(self, frame: Frame) -> HandResult:
        start = time.perf_counter()
        result = self._landmarker.detect_for_video(frame.mp_image, frame.timestamp_ms)
        latency = (time.perf_counter() - start) * 1000
        width, height = frame.size
        hands = []
        for landmarks, handedness in zip(result.hand_landmarks, result.handedness):
            label = handedness[0].category_name
            if config.HANDEDNESS_SWAP:
                label = _SWAP.get(label, label)
            hands.append(HandObservation(to_array(landmarks), to_pixels(landmarks, width, height),
                                         label, handedness[0].score))
        self.last = HandResult(hands, latency)
        return self.last

    def close(self) -> None:
        self._landmarker.close()

    def __enter__(self) -> "HandTracker":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
