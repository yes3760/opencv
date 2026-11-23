"""Ekrana çizim yardımcıları: renkler, Türkçe metin, panel ve işaret noktaları.

OpenCV'nin yerleşik cv2.putText fonksiyonu Türkçe karakterleri (ç, ğ, ı, İ, ö, ş, ü)
çizemez; "?" olarak gösterir. Bu dosyadaki put_text, sistemde bulunan bir yazı
tipini Pillow ile kullanır. Yazı tipi bulunamazsa harfleri ASCII karşılıklarına
çevirerek cv2.putText ile çizer.
"""

from __future__ import annotations

import platform
from collections import OrderedDict
from pathlib import Path

import cv2
import numpy as np

# Renkler BGR sırasındadır (OpenCV'nin sırası). Sunumdaki renklerle aynıdır.
TEAL = (191, 212, 45)        # #2DD4BF turkuaz
BLUE = (246, 130, 59)        # #3B82F6 elektrik mavisi
VIOLET = (250, 139, 167)     # #A78BFA mor (yardımcı vurgu)
WHITE = (233, 239, 242)      # #F2EFE9 kırık beyaz
GRAY = (184, 163, 148)       # #94A3B8
AMBER = (11, 158, 245)       # #F59E0B uyarı
RED = (113, 113, 248)        # #F87171 hata
INK = (31, 22, 15)           # #0F161F koyu zemin

_ASCII = str.maketrans("çÇğĞıİöÖşŞüÜâÂ", "cCgGiIoOsSuUaA")

_FONT_CANDIDATES = {
    "Darwin": ["/System/Library/Fonts/Supplemental/Arial.ttf",
               "/Library/Fonts/Arial Unicode.ttf",
               "/System/Library/Fonts/Helvetica.ttc"],
    "Windows": ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"],
    "Linux": ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/dejavu/DejaVuSans.ttf"],
}


class _TextRenderer:
    def __init__(self) -> None:
        self._font_path: str | None = None
        self._fonts: dict[int, object] = {}
        self._cache: OrderedDict = OrderedDict()
        try:
            from PIL import ImageFont  # noqa: F401
            for candidate in _FONT_CANDIDATES.get(platform.system(), []):
                if Path(candidate).exists():
                    self._font_path = candidate
                    break
        except ImportError:
            self._font_path = None

    @property
    def unicode_ok(self) -> bool:
        return self._font_path is not None

    def _font(self, size: int):
        from PIL import ImageFont
        if size not in self._fonts:
            self._fonts[size] = ImageFont.truetype(self._font_path, size)
        return self._fonts[size]

    def _sprite(self, text: str, size: int) -> np.ndarray:
        """Metni gri tonlu bir maske (alfa) olarak döndürür; sonuç önbelleğe alınır."""
        key = (text, size)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        from PIL import Image, ImageDraw
        font = self._font(size)
        left, top, right, bottom = font.getbbox(text)
        w, h = max(1, right - left), max(1, size + size // 3)
        canvas = Image.new("L", (w, h), 0)
        ImageDraw.Draw(canvas).text((-left, 0), text, font=font, fill=255)
        mask = np.asarray(canvas, dtype=np.float32) / 255.0
        self._cache[key] = mask
        if len(self._cache) > 512:
            self._cache.popitem(last=False)
        return mask

    def size(self, text: str, size: int) -> tuple[int, int]:
        if self.unicode_ok:
            mask = self._sprite(text, size)
            return mask.shape[1], mask.shape[0]
        scale = size / 30
        (w, h), base = cv2.getTextSize(text.translate(_ASCII), cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
        return w, h + base

    def draw(self, img: np.ndarray, text: str, org: tuple[int, int], size: int, color) -> tuple[int, int]:
        x, y = int(org[0]), int(org[1])
        if not self.unicode_ok:
            scale = size / 30
            thickness = 2 if size >= 24 else 1
            (w, h), base = cv2.getTextSize(text.translate(_ASCII), cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
            cv2.putText(img, text.translate(_ASCII), (x, y + h), cv2.FONT_HERSHEY_SIMPLEX,
                        scale, color, thickness, cv2.LINE_AA)
            return w, h + base
        mask = self._sprite(text, size)
        h, w = mask.shape
        x1, y1 = max(x, 0), max(y, 0)
        x2, y2 = min(x + w, img.shape[1]), min(y + h, img.shape[0])
        if x2 <= x1 or y2 <= y1:
            return w, h
        alpha = mask[y1 - y:y2 - y, x1 - x:x2 - x, None]
        roi = img[y1:y2, x1:x2].astype(np.float32)
        roi = roi * (1 - alpha) + np.array(color, dtype=np.float32) * alpha
        img[y1:y2, x1:x2] = roi.astype(np.uint8)
        return w, h


_renderer: _TextRenderer | None = None


def _get_renderer() -> _TextRenderer:
    global _renderer
    if _renderer is None:
        _renderer = _TextRenderer()
    return _renderer


def put_text(img: np.ndarray, text: str, org: tuple[int, int], size: int = 18,
             color=WHITE, bg=None, pad: int = 4) -> tuple[int, int]:
    """Türkçe karakter destekli metin çizer. org, metnin sol üst köşesidir."""
    r = _get_renderer()
    if bg is not None:
        w, h = r.size(text, size)
        x, y = int(org[0]), int(org[1])
        cv2.rectangle(img, (x - pad, y - pad), (x + w + pad, y + h + pad), bg, -1)
    return r.draw(img, text, org, size, color)


def text_size(text: str, size: int = 18) -> tuple[int, int]:
    return _get_renderer().size(text, size)


def panel(img: np.ndarray, x1: int, y1: int, x2: int, y2: int, alpha: float = 0.72, color=INK) -> None:
    """Yarı saydam koyu panel çizer (altındaki görüntü hafifçe görünür)."""
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(img.shape[1], x2), min(img.shape[0], y2)
    if x2 <= x1 or y2 <= y1:
        return
    roi = img[y1:y2, x1:x2]
    overlay = np.full_like(roi, color)
    cv2.addWeighted(overlay, alpha, roi, 1 - alpha, 0, dst=roi)


def connections_to_pairs(connections) -> list[tuple[int, int]]:
    """MediaPipe Connection nesnelerini (başlangıç, bitiş) çiftlerine çevirir."""
    return [(c.start, c.end) for c in connections]


def draw_connections(img, points: np.ndarray, pairs, color=GRAY, thickness: int = 1) -> None:
    pts = points.astype(np.int32)
    for a, b in pairs:
        if a < len(pts) and b < len(pts):
            cv2.line(img, tuple(pts[a]), tuple(pts[b]), color, thickness, cv2.LINE_AA)


def draw_points(img, points: np.ndarray, color=TEAL, radius: int = 2) -> None:
    for x, y in points.astype(np.int32):
        cv2.circle(img, (int(x), int(y)), radius, color, -1, cv2.LINE_AA)


def draw_polyline(img, points, color, thickness: int = 2, fade: bool = False) -> None:
    """Hareket izini çizer. fade=True ise eski noktalar daha ince çizilir."""
    pts = [tuple(int(v) for v in p) for p in points]
    n = len(pts)
    for i in range(1, n):
        t = max(1, int(thickness * i / n)) if fade else thickness
        cv2.line(img, pts[i - 1], pts[i], color, t, cv2.LINE_AA)


def status_line(img: np.ndarray, text: str, kind: str = "info") -> None:
    """Görüntünün altına durum mesajı yazar. kind: info, ok, warn, error."""
    color = {"ok": TEAL, "warn": AMBER, "error": RED}.get(kind, WHITE)
    h, w = img.shape[:2]
    panel(img, 0, h - 34, w, h, alpha=0.75)
    put_text(img, text, (12, h - 28), size=18, color=color)
