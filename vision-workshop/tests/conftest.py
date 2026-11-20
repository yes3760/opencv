"""Testlerin ortak ayarları ve sentetik veri üreticileri.

Testler kamera gerektirmez. Yüz geometrisi testleri MediaPipe'ın standart yüz
modelinden (shared/canonical_face_478.json) üretilen sentetik noktaları kullanır.
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="session")
def canonical_vertices() -> np.ndarray:
    data = json.loads((ROOT / "shared" / "canonical_face_478.json").read_text())
    return np.array(data["vertices"], dtype=np.float64)


def project(vertices: np.ndarray, yaw=0.0, pitch=0.0, roll=0.0, scale=20.0, center=(320, 240)) -> np.ndarray:
    """Standart yüz modelini döndürüp perspektifle görüntü düzlemine yansıtır."""
    y, p, r = map(math.radians, (yaw, pitch, roll))
    ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    rx = np.array([[1, 0, 0], [0, math.cos(p), -math.sin(p)], [0, math.sin(p), math.cos(p)]])
    rz = np.array([[math.cos(r), -math.sin(r), 0], [math.sin(r), math.cos(r), 0], [0, 0, 1]])
    pts = vertices @ (rz @ rx @ ry).T
    f, d = 60.0, 60.0
    x = f * pts[:, 0] / (d - pts[:, 2])
    yy = -f * pts[:, 1] / (d - pts[:, 2])          # görüntüde y aşağı doğrudur
    return np.stack([x * scale + center[0], yy * scale + center[1]], axis=1).astype(np.float32)


@pytest.fixture
def projector():
    return project
