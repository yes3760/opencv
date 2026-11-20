"""Yüz modülünün ekrana çizimleri (aynalamadan önce çağrılır)."""

from __future__ import annotations

import cv2
import numpy as np

from common.draw import BLUE, GRAY, TEAL, VIOLET, connections_to_pairs, draw_connections, draw_points, draw_polyline
from common.models import vision

_C = vision.FaceLandmarksConnections
TESSELATION = connections_to_pairs(_C.FACE_LANDMARKS_TESSELATION)
CONTOURS = connections_to_pairs(_C.FACE_LANDMARKS_CONTOURS)
IRISES = connections_to_pairs(_C.FACE_LANDMARKS_LEFT_IRIS) + connections_to_pairs(_C.FACE_LANDMARKS_RIGHT_IRIS)


def draw_face(img: np.ndarray, points: np.ndarray, box=None, style: str = "kontur") -> None:
    """style: 'kontur' (göz, kaş, dudak, yüz çevresi), 'ag' (tüm üçgen ağ), 'nokta'."""
    if style == "ag":
        draw_connections(img, points, TESSELATION, GRAY, 1)
        draw_connections(img, points, CONTOURS, TEAL, 1)
    elif style == "nokta":
        draw_points(img, points, TEAL, 1)
    else:
        draw_connections(img, points, CONTOURS, TEAL, 1)
        draw_connections(img, points, IRISES, VIOLET, 1)
    if box is not None:
        x1, y1, x2, y2 = (int(v) for v in box)
        cv2.rectangle(img, (x1, y1), (x2, y2), BLUE, 2, cv2.LINE_AA)


def draw_trails(img: np.ndarray, raw: list, smooth: list, scale: float) -> None:
    """Ham iz gri ve ince, yumuşatılmış iz turkuaz ve kalın çizilir."""
    if len(raw) > 1:
        draw_polyline(img, [np.asarray(p) * scale for p in raw], GRAY, 1)
    if len(smooth) > 1:
        draw_polyline(img, [np.asarray(p) * scale for p in smooth], TEAL, 3, fade=True)
        x, y = (np.asarray(smooth[-1]) * scale).astype(int)
        cv2.circle(img, (int(x), int(y)), 5, TEAL, -1, cv2.LINE_AA)
