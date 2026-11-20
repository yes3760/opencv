"""Noktalar arası mesafe ve açı hesapları.

MediaPipe koordinatları 0-1 aralığında normalize edilir: x görüntü genişliğine,
y görüntü yüksekliğine bölünür. Genişlik ve yükseklik farklı olduğu için normalize
koordinatlarda doğrudan mesafe ölçmek yanlıştır; önce piksele çevrilmelidir.
"""

from __future__ import annotations

import math

import numpy as np


def to_pixels(landmarks, width: int, height: int) -> np.ndarray:
    """MediaPipe nokta listesini (N, 2) piksel dizisine çevirir."""
    return np.array([[p.x * width, p.y * height] for p in landmarks], dtype=np.float32)


def to_array(landmarks) -> np.ndarray:
    """MediaPipe nokta listesini (N, 3) normalize diziye çevirir (x, y, z)."""
    return np.array([[p.x, p.y, p.z] for p in landmarks], dtype=np.float32)


def distance(a: np.ndarray, b: np.ndarray) -> float:
    """İki nokta arasındaki Öklid mesafesi."""
    return float(np.linalg.norm(np.asarray(a, dtype=np.float64) - np.asarray(b, dtype=np.float64)))


def angle_deg(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """b noktasındaki açı (a-b-c), derece. Düz bir parmakta 180'e yaklaşır."""
    ba = np.asarray(a, dtype=np.float64) - np.asarray(b, dtype=np.float64)
    bc = np.asarray(c, dtype=np.float64) - np.asarray(b, dtype=np.float64)
    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denom < 1e-9:
        return 0.0
    cos = float(np.clip(np.dot(ba, bc) / denom, -1.0, 1.0))
    return math.degrees(math.acos(cos))


def bounding_box(points: np.ndarray, margin: float = 0.0) -> tuple[int, int, int, int]:
    """Noktaları içeren kutu: (x1, y1, x2, y2). margin, kutu boyutunun oranıdır."""
    x1, y1 = points.min(axis=0)
    x2, y2 = points.max(axis=0)
    mx, my = (x2 - x1) * margin, (y2 - y1) * margin
    return int(x1 - mx), int(y1 - my), int(x2 + mx), int(y2 + my)


def mirror_x(points: np.ndarray, width: int) -> np.ndarray:
    """Piksel noktalarını yatayda aynalar (ekrandaki ayna görüntüsü için)."""
    out = points.copy()
    out[..., 0] = (width - 1) - out[..., 0]
    return out
