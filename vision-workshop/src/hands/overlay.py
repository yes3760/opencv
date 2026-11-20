"""El modülünün ekrana çizimleri (aynalamadan önce çağrılır)."""

from __future__ import annotations

import cv2
import numpy as np

import config
from common.draw import AMBER, GRAY, TEAL, WHITE, connections_to_pairs, draw_connections, panel, put_text
from common.models import vision

HAND_PAIRS = connections_to_pairs(vision.HandLandmarksConnections.HAND_CONNECTIONS)
TIPS = (4, 8, 12, 16, 20)


def draw_hand(img: np.ndarray, points: np.ndarray, highlight_pinch: bool = False) -> None:
    draw_connections(img, points, HAND_PAIRS, GRAY, 2)
    for i, (x, y) in enumerate(points.astype(int)):
        color = TEAL if i in TIPS else WHITE
        cv2.circle(img, (int(x), int(y)), 5 if i in TIPS else 3, color, -1, cv2.LINE_AA)
    if highlight_pinch:
        a, b = points[4].astype(int), points[8].astype(int)
        cv2.line(img, tuple(a), tuple(b), AMBER, 3, cv2.LINE_AA)


def draw_pinch_gauge(img: np.ndarray, value: float, pinching: bool, x: int, y: int, width: int = 220) -> None:
    """Pinch mesafesini, giriş ve çıkış eşikleriyle birlikte gösteren çubuk (aynalamadan sonra)."""
    panel(img, x - 10, y - 30, x + width + 10, y + 30)
    max_v = 1.0
    cv2.rectangle(img, (x, y), (x + width, y + 10), GRAY, 1)
    fill = int(min(value, max_v) / max_v * width)
    cv2.rectangle(img, (x, y), (x + fill, y + 10), AMBER if pinching else TEAL, -1)
    for thr, label in ((config.PINCH_ENTER_RATIO, "giriş"), (config.PINCH_EXIT_RATIO, "çıkış")):
        tx = x + int(thr / max_v * width)
        cv2.line(img, (tx, y - 4), (tx, y + 14), WHITE, 1)
        put_text(img, label, (tx - 14, y + 14), 12, GRAY)
    put_text(img, f"pinch mesafesi {value:.2f}  {'BASILI' if pinching else ''}", (x, y - 26), 15, WHITE)
