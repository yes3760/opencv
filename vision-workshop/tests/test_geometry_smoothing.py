import numpy as np
import pytest

from common.geometry import angle_deg, bounding_box, distance, mirror_x
from common.smoothing import EMA, OneEuroFilter


def test_distance_and_angle():
    assert distance([0, 0], [3, 4]) == pytest.approx(5.0)
    assert angle_deg([1, 0], [0, 0], [0, 1]) == pytest.approx(90.0)
    assert angle_deg([-1, 0], [0, 0], [1, 0]) == pytest.approx(180.0)
    assert angle_deg([0, 0], [0, 0], [1, 0]) == 0.0        # tanımsız açı güvenli döner


def test_bounding_box_and_mirror():
    pts = np.array([[10, 20], [30, 60]], np.float32)
    assert bounding_box(pts) == (10, 20, 30, 60)
    mirrored = mirror_x(pts, width=100)
    assert mirrored[0, 0] == pytest.approx(89) and mirrored[0, 1] == 20


def test_ema_reduces_jitter_but_lags():
    rng = np.random.default_rng(0)
    truth = np.zeros(300)
    noisy = truth + rng.normal(0, 5, 300)
    ema = EMA(0.2)
    smooth = np.array([ema.update(v) for v in noisy]).ravel()
    assert smooth[50:].std() < noisy[50:].std() / 2          # titreme azalır
    step = EMA(0.2)
    out = [float(step.update(10.0 if i >= 1 else 0.0)) for i in range(5)]
    assert out[1] < 10.0                                      # ani değişime gecikmeli tepki


def test_ema_rejects_bad_alpha():
    with pytest.raises(ValueError):
        EMA(0.0)


def test_one_euro_follows_fast_motion_better_than_heavy_ema():
    t = np.arange(0, 2, 1 / 30)
    signal = np.where(t > 1, 100.0, 0.0)
    euro, ema = OneEuroFilter(min_cutoff=1.0, beta=0.05), EMA(0.1)
    e_out = [float(euro.update(v, ti)) for v, ti in zip(signal, t)]
    m_out = [float(ema.update(v)) for v in signal]
    idx = int(np.argmax(t > 1)) + 5
    assert e_out[idx] > m_out[idx]
