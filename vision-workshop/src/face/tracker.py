"""Yüz tespiti, işaret noktaları ve takip.

Girdi : common.frame.Frame (aynalanmamış kare)
Çıktı : FaceResult; her yüz için 478 nokta, kutu, merkez, iz, baş yönelimi
Görev : MediaPipe Face Landmarker'ı bir kez yükler ve her karede çalıştırır.

Üç kavram birbirinden ayrıdır:
  Tespit : Bu karede yüz var mı, nerede?
  Takip  : Önceki karedeki yüz bu karede hangisi? (takip numarası verir)
  Tanıma : Bu kişi kim? Bu proje kimlik tanıma YAPMAZ. Takip numarası yalnızca
           "kaçıncı iz" bilgisidir; yüz kadrajdan çıkıp girdiğinde yeni numara alabilir.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field

import numpy as np

import config
from common.frame import Frame
from common.geometry import bounding_box, distance, to_array, to_pixels
from common.models import base_options, vision
from common.smoothing import EMA
from face.metrics import CHEEK_LEFT_EDGE, CHEEK_RIGHT_EDGE, HeadPose, head_pose_from_matrix


@dataclass
class FaceObservation:
    track_id: int
    landmarks: np.ndarray            # (478, 3) normalize x, y, z
    points: np.ndarray               # (478, 2) işleme karesinde piksel
    box: tuple[int, int, int, int]   # (x1, y1, x2, y2)
    center: np.ndarray               # ham merkez (piksel)
    center_smooth: np.ndarray        # yumuşatılmış merkez (piksel)
    width_px: float                  # elmacık hizasında yüz genişliği
    pose: HeadPose | None
    blendshapes: dict[str, float] = field(default_factory=dict)


@dataclass
class FaceResult:
    faces: list[FaceObservation]
    latency_ms: float

    @property
    def status(self) -> str:
        if not self.faces:
            return "Yüz bulunamadı: kameraya önden bakın ve ışığı kontrol edin."
        if len(self.faces) == 1:
            return "1 yüz izleniyor"
        return f"{len(self.faces)} yüz izleniyor (numaralar kimlik değildir)"


class _Track:
    def __init__(self, track_id: int, center: np.ndarray, alpha: float, trail_len: int) -> None:
        self.track_id = track_id
        self.ema = EMA(alpha)
        self.raw_trail: deque = deque(maxlen=trail_len)
        self.smooth_trail: deque = deque(maxlen=trail_len)
        self.last_center = center
        self.missing = 0


class FaceTracker:
    def __init__(self, model_path=config.FACE_MODEL, max_faces: int = config.MAX_FACES,
                 blendshapes: bool = False, ema_alpha: float = config.EMA_ALPHA,
                 trail_length: int = config.TRAIL_LENGTH) -> None:
        options = vision.FaceLandmarkerOptions(
            base_options=base_options(model_path),
            running_mode=vision.RunningMode.VIDEO,     # kareler sırayla verilir, takip açık
            num_faces=max_faces,
            min_face_detection_confidence=config.MIN_FACE_DETECTION_CONFIDENCE,
            min_face_presence_confidence=config.MIN_FACE_PRESENCE_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE,
            output_face_blendshapes=blendshapes,
            output_facial_transformation_matrixes=True,
        )
        self._landmarker = vision.FaceLandmarker.create_from_options(options)
        self._tracks: list[_Track] = []
        self._next_id = 1
        self._alpha = ema_alpha
        self._trail_length = trail_length
        self.last: FaceResult = FaceResult([], 0.0)

    # ------------------------------------------------------------------
    def process(self, frame: Frame) -> FaceResult:
        start = time.perf_counter()
        result = self._landmarker.detect_for_video(frame.mp_image, frame.timestamp_ms)
        latency = (time.perf_counter() - start) * 1000

        width, height = frame.size
        detections = []
        for i, landmarks in enumerate(result.face_landmarks):
            points = to_pixels(landmarks, width, height)
            pose = None
            if result.facial_transformation_matrixes:
                pose = head_pose_from_matrix(result.facial_transformation_matrixes[i])
            shapes = {}
            if result.face_blendshapes:
                shapes = {c.category_name: c.score for c in result.face_blendshapes[i]}
            detections.append((to_array(landmarks), points, pose, shapes))

        faces = self._assign_tracks(detections)
        self.last = FaceResult(faces, latency)
        return self.last

    def _assign_tracks(self, detections) -> list[FaceObservation]:
        """Her yüzü önceki karedeki en yakın ize bağlar (en yakın merkez eşleştirmesi)."""
        used: set[int] = set()
        faces = []
        for landmarks, points, pose, shapes in detections:
            center = points.mean(axis=0)
            width_px = distance(points[CHEEK_RIGHT_EDGE], points[CHEEK_LEFT_EDGE])
            best, best_dist = None, config.TRACK_MATCH_MAX_DIST * max(width_px, 1.0)
            for track in self._tracks:
                if track.track_id in used:
                    continue
                d = distance(center, track.last_center)
                if d < best_dist:
                    best, best_dist = track, d
            if best is None:
                best = _Track(self._next_id, center, self._alpha, self._trail_length)
                self._next_id += 1
                self._tracks.append(best)
            used.add(best.track_id)
            best.missing = 0
            best.last_center = center
            smooth = best.ema.update(center)
            best.raw_trail.append(center.copy())
            best.smooth_trail.append(smooth.copy())
            faces.append(FaceObservation(best.track_id, landmarks, points, bounding_box(points, 0.05),
                                         center, smooth.copy(), width_px, pose, shapes))
        # Görünmeyen izleri yaşlandır; uzun süre görünmeyenleri sil.
        for track in self._tracks:
            if track.track_id not in used:
                track.missing += 1
        self._tracks = [t for t in self._tracks if t.missing < config.FACE_LOST_RESET_FRAMES]
        return faces

    def trails(self, track_id: int) -> tuple[list, list]:
        """Bir izin (ham, yumuşatılmış) merkez noktaları."""
        for track in self._tracks:
            if track.track_id == track_id:
                return list(track.raw_trail), list(track.smooth_trail)
        return [], []

    def set_smoothing(self, alpha: float) -> None:
        """Yumuşatma katsayısını hem mevcut hem yeni izler için değiştirir."""
        self._alpha = alpha
        for track in self._tracks:
            track.ema.alpha = alpha

    def clear_trails(self) -> None:
        for track in self._tracks:
            track.raw_trail.clear()
            track.smooth_trail.clear()

    def close(self) -> None:
        self._landmarker.close()

    def __enter__(self) -> "FaceTracker":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
