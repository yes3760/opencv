"""Kare hızı (FPS) ve işlem süresi ölçümü.

FPS  : Saniyede gösterilen kare sayısı. Döngünün tamamını ölçer.
Süre : Tek bir adımın (ör. yüz modeli) milisaniye cinsinden süresi.
Gecikme, kameranın kareyi yakalamasından ekranda görünmesine kadar geçen süredir;
kamera ve ekran tamponları da eklendiği için yalnızca işlem süresinden büyüktür.
"""

from __future__ import annotations

import time
from contextlib import contextmanager


class FPSMeter:
    """Kare aralıklarının üstel ortalamasıyla kararlı bir FPS değeri verir."""

    def __init__(self, smoothing: float = 0.1) -> None:
        self.smoothing = smoothing
        self._last: float | None = None
        self._avg_dt: float | None = None

    def tick(self) -> float:
        now = time.perf_counter()
        if self._last is not None:
            dt = now - self._last
            self._avg_dt = dt if self._avg_dt is None else (
                self.smoothing * dt + (1 - self.smoothing) * self._avg_dt)
        self._last = now
        return self.fps

    @property
    def fps(self) -> float:
        return 0.0 if not self._avg_dt else 1.0 / self._avg_dt


class StageTimer:
    """Adım adım işlem sürelerini (ms) ölçer ve ortalamasını tutar."""

    def __init__(self, smoothing: float = 0.1) -> None:
        self.smoothing = smoothing
        self.ms: dict[str, float] = {}

    @contextmanager
    def measure(self, name: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            old = self.ms.get(name)
            self.ms[name] = elapsed if old is None else (
                self.smoothing * elapsed + (1 - self.smoothing) * old)
