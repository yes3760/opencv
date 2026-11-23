"""El hareketiyle kontrol edilen uygulama içi arayüz öğeleri.

Bütün öğeler ekran koordinatlarıyla (aynalanmış görüntü üzerinde) çalışır;
kullanıcı elini sağa götürdüğünde imleç de ekranda sağa gider.
İşletim sisteminin faresi kontrol edilmez.
"""

from __future__ import annotations

import cv2
import numpy as np

from common.draw import BLUE, GRAY, INK, TEAL, VIOLET, WHITE, panel, put_text, text_size


def _inside(point, rect) -> bool:
    if point is None:
        return False
    x, y = point
    x1, y1, x2, y2 = rect
    return x1 <= x <= x2 and y1 <= y <= y2


class Slider:
    """Pinch ile tutulup sürüklenen yatay sürgü. Değer 0-1 aralığındadır."""

    def __init__(self, x: int, y: int, width: int, label: str, value: float = 0.5) -> None:
        self.x, self.y, self.width = x, y, width
        self.label = label
        self.value = value
        self.dragging = False

    @property
    def grab_rect(self):
        return (self.x - 20, self.y - 28, self.x + self.width + 20, self.y + 28)

    def update(self, cursor, pinch_started: bool, pinching: bool) -> None:
        if pinch_started and _inside(cursor, self.grab_rect):
            self.dragging = True
        if not pinching or cursor is None:
            self.dragging = False
        if self.dragging:
            self.value = float(np.clip((cursor[0] - self.x) / self.width, 0.0, 1.0))

    def draw(self, img) -> None:
        cv2.line(img, (self.x, self.y), (self.x + self.width, self.y), GRAY, 3, cv2.LINE_AA)
        knob_x = int(self.x + self.value * self.width)
        cv2.line(img, (self.x, self.y), (knob_x, self.y), TEAL, 5, cv2.LINE_AA)
        cv2.circle(img, (knob_x, self.y), 13 if self.dragging else 10,
                   TEAL if self.dragging else WHITE, -1, cv2.LINE_AA)
        put_text(img, f"{self.label}: {self.value * 100:.0f}", (self.x, self.y - 34), 17, WHITE)


class ButtonBar:
    """Üstte yan yana düğmeler. İmleç düğmenin üstündeyken pinch başlarsa tıklanır."""

    def __init__(self, labels: list[str], x: int = 12, y: int = 12, height: int = 40) -> None:
        self.labels = labels
        self.rects = []
        cx = x
        for label in labels:
            w = text_size(label, 18)[0] + 28
            self.rects.append((cx, y, cx + w, y + height))
            cx += w + 8
        self.active = 0
        self.hover: int | None = None

    def update(self, cursor, pinch_started: bool) -> int | None:
        """Tıklanan düğmenin sırasını döndürür; tıklama yoksa None."""
        self.hover = next((i for i, r in enumerate(self.rects) if _inside(cursor, r)), None)
        if pinch_started and self.hover is not None:
            self.active = self.hover
            return self.hover
        return None

    def click(self, point) -> int | None:
        """Fareyle tıklama için."""
        for i, r in enumerate(self.rects):
            if _inside(point, r):
                self.active = i
                return i
        return None

    def draw(self, img) -> None:
        for i, (label, (x1, y1, x2, y2)) in enumerate(zip(self.labels, self.rects)):
            if i == self.active:
                cv2.rectangle(img, (x1, y1), (x2, y2), TEAL, -1)
                color = INK
            else:
                panel(img, x1, y1, x2, y2, 0.7)
                cv2.rectangle(img, (x1, y1), (x2, y2), BLUE if i == self.hover else GRAY, 1, cv2.LINE_AA)
                color = WHITE
            put_text(img, label, (x1 + 14, y1 + 9), 18, color)


class DrawingCanvas:
    """İşaret parmağı jestinde çizim yapan katman."""

    def __init__(self, width: int, height: int) -> None:
        self.layer = np.zeros((height, width, 3), np.uint8)
        self._last = None

    def update(self, cursor, drawing: bool) -> None:
        if not drawing or cursor is None:
            self._last = None
            return
        point = (int(cursor[0]), int(cursor[1]))
        if self._last is not None:
            cv2.line(self.layer, self._last, point, VIOLET, 5, cv2.LINE_AA)
        self._last = point

    def clear(self) -> None:
        self.layer[:] = 0
        self._last = None

    def draw(self, img) -> None:
        mask = self.layer.any(axis=2)
        img[mask] = self.layer[mask]


class DraggableBox:
    """Pinch ile tutulup sürüklenen kutu."""

    def __init__(self, x: int, y: int, size: int = 90) -> None:
        self.x, self.y, self.size = x, y, size
        self.dragging = False
        self._offset = (0, 0)

    @property
    def rect(self):
        return (self.x, self.y, self.x + self.size, self.y + self.size)

    def update(self, cursor, pinch_started: bool, pinching: bool) -> None:
        if pinch_started and _inside(cursor, self.rect):
            self.dragging = True
            self._offset = (cursor[0] - self.x, cursor[1] - self.y)
        if not pinching or cursor is None:
            self.dragging = False
        if self.dragging:
            self.x = int(cursor[0] - self._offset[0])
            self.y = int(cursor[1] - self._offset[1])

    def draw(self, img) -> None:
        x1, y1, x2, y2 = self.rect
        cv2.rectangle(img, (x1, y1), (x2, y2), TEAL if self.dragging else BLUE, 2, cv2.LINE_AA)
        put_text(img, "sürükle", (x1 + 10, y1 + self.size // 2 - 10), 16, WHITE)
