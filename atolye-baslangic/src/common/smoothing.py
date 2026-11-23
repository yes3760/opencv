"""Titreşimi azaltan zamansal filtreler.

Model her karede noktaları biraz farklı bulur; bu küçük farklar ekranda titreme
olarak görünür. Filtreler titremeyi azaltır ama bir miktar gecikme ekler.
"""

from __future__ import annotations

import math

import numpy as np


class EMA:
    """Üstel hareketli ortalama: yeni = alpha * ölçüm + (1 - alpha) * eski."""

    def __init__(self, alpha: float = 0.35) -> None:
        if not 0.0 < alpha <= 1.0:
            raise ValueError("alpha 0 ile 1 arasında olmalı")
        self.alpha = alpha
        self.value: np.ndarray | None = None

    def update(self, measurement) -> np.ndarray:
        m = np.asarray(measurement, dtype=np.float64)
        if self.value is None:
            self.value = m.copy()
        else:
            self.value = self.alpha * m + (1.0 - self.alpha) * self.value
        return self.value

    def reset(self) -> None:
        self.value = None


class OneEuroFilter:
    """Hıza göre kendini ayarlayan filtre (Casiez, Roussel ve Vogel, CHI 2012).

    Yavaş harekette güçlü yumuşatır (titreme azalır), hızlı harekette az yumuşatır
    (gecikme azalır). İleri düzey bir seçenek olarak verilmiştir.
    """

    def __init__(self, min_cutoff: float = 1.0, beta: float = 0.02, d_cutoff: float = 1.0) -> None:
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self._x: np.ndarray | None = None
        self._dx: np.ndarray | None = None
        self._t: float | None = None

    @staticmethod
    def _alpha(cutoff: float, dt: float) -> float:
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def update(self, measurement, t_seconds: float) -> np.ndarray:
        x = np.asarray(measurement, dtype=np.float64)
        if self._x is None or self._t is None:
            self._x, self._dx, self._t = x.copy(), np.zeros_like(x), t_seconds
            return self._x
        dt = max(t_seconds - self._t, 1e-3)
        dx = (x - self._x) / dt
        a_d = self._alpha(self.d_cutoff, dt)
        self._dx = a_d * dx + (1 - a_d) * self._dx
        cutoff = self.min_cutoff + self.beta * float(np.linalg.norm(self._dx))
        a = self._alpha(cutoff, dt)
        self._x = a * x + (1 - a) * self._x
        self._t = t_seconds
        return self._x

    def reset(self) -> None:
        self._x = self._dx = self._t = None
