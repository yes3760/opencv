import numpy as np

import config
from hands.gestures import (Debouncer, GestureController, Hysteresis, classify_static, finger_states,
                            pinch_ratio)


def synthetic_hand(index_bent=False, others_bent=True, thumb_open=False, pinch=False):
    """Avuç içi kameraya dönük, parmakları yukarı bakan basit bir el (piksel)."""
    pts = np.zeros((21, 2), np.float32)
    pts[0] = (200, 400)                                   # bilek
    bases = {1: (150, 360), 5: (170, 300), 9: (200, 295), 13: (230, 300), 17: (255, 310)}
    for base, (x, y) in bases.items():
        pts[base] = (x, y)
    def straight(base, dx, dy):
        for k in range(1, 4):
            pts[base + k] = pts[base] + np.array([dx, dy]) * k
    def bent(base):
        pts[base + 1] = pts[base] + (0, -30)
        pts[base + 2] = pts[base + 1] + (0, 25)           # geri dönen parmak: keskin açı
        pts[base + 3] = pts[base + 2] + (5, 15)
    straight(5, 0, -30) if not index_bent else bent(5)
    for b in (9, 13, 17):
        bent(b) if others_bent else straight(b, 0, -30)
    if thumb_open:
        straight(1, -25, -20)
    else:
        pts[2] = (165, 340); pts[3] = (185, 330); pts[4] = (200, 345)
    if pinch:
        pts[4] = pts[8] + (3, 3)
    return pts


def test_finger_states_and_static_gestures():
    pointing = synthetic_hand(index_bent=False, others_bent=True)
    states = finger_states(pointing)
    assert states["işaret"] is True and states["orta"] is False
    assert classify_static(states) == "isaret"
    fist = synthetic_hand(index_bent=True, others_bent=True)
    assert classify_static(finger_states(fist)) == "yumruk"
    palm = synthetic_hand(index_bent=False, others_bent=False, thumb_open=True)
    assert classify_static(finger_states(palm)) == "acik_el"


def test_pinch_ratio_is_scale_invariant():
    hand = synthetic_hand(pinch=True)
    assert pinch_ratio(hand) < config.PINCH_ENTER_RATIO
    assert abs(pinch_ratio(hand) - pinch_ratio(hand * 2.5)) < 1e-6


def test_hysteresis_prevents_flicker():
    rng = np.random.default_rng(1)
    values = 0.30 + rng.normal(0, 0.03, 200)          # eşik çevresinde gürültülü değer
    single = [v < 0.30 for v in values]
    toggles_single = int(np.sum(np.diff(single) != 0))
    hyst = Hysteresis(0.25, 0.40)
    states = [hyst.update(v) for v in values]
    toggles_hyst = int(np.sum(np.diff(states) != 0))
    assert toggles_single > 20 and toggles_hyst <= 2


def test_debouncer_waits_for_stability():
    d = Debouncer(stable_ms=100, initial="a")
    assert d.update("b", 0) == "a"
    assert d.update("b", 50) == "a"
    assert d.update("b", 120) == "b"
    assert d.update("a", 130) == "b"                  # kısa değişim yok sayılır
    assert d.update("b", 140) == "b"


def test_one_pinch_gives_one_command_and_loss_resets():
    ctrl = GestureController()
    open_hand = synthetic_hand(index_bent=False, others_bent=True)
    pinched = synthetic_hand(index_bent=False, others_bent=True, pinch=True)
    rng = np.random.default_rng(2)
    events, t = [], 0
    sequence = [open_hand] * 10 + [pinched] * 30 + [open_hand] * 10
    for pts in sequence:
        t += 33
        state = ctrl.update(pts + rng.normal(0, 1.0, pts.shape).astype(np.float32), t)
        events += state.events
    assert events.count("pinch_basladi") == 1
    assert events.count("pinch_bitti") == 1

    # Pinch sırasında el kaybolursa durum sıfırlanır ve tek bir "el_kayboldu" olayı üretilir.
    for _ in range(10):
        t += 33
        ctrl.update(pinched, t)
    lost_events = []
    for _ in range(20):
        t += 33
        lost_events += ctrl.update(None, t).events
    assert lost_events.count("el_kayboldu") == 1
    assert "pinch_bitti" in lost_events
    assert ctrl.state.pinching is False


def test_command_cooldown_limits_rapid_gestures():
    ctrl = GestureController()
    fist = synthetic_hand(index_bent=True)
    point = synthetic_hand(index_bent=False)
    t, commands = 0, 0
    for i in range(60):                                # her 150 ms'de jest değişiyor
        t += 30
        pts = fist if (i // 5) % 2 == 0 else point
        commands += sum(e.startswith("jest:") for e in ctrl.update(pts, t).events)
    max_allowed = (60 * 30) // config.COMMAND_COOLDOWN_MS + 1
    assert 1 <= commands <= max_allowed
