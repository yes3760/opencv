"""Parmak durumları, statik jestler ve kararlı komut üretimi.

Ham model çıktısı her karede biraz değişir. Bir jesti doğrudan komuta çevirmek,
tek bir hareketin onlarca komut üretmesine yol açar. Bu dosyadaki üç araç bunu önler:

  Histerezis    : Girmek ve çıkmak için farklı eşik (ör. pinch 0,25'te başlar, 0,40'ta biter).
  Bekleme süresi: Jest belirli bir süre aynı kalmadan kabul edilmez (debounce).
  Soğuma süresi : Bir komuttan sonra kısa süre yeni komut üretilmez (cooldown).

El kaybolursa bütün durum sıfırlanır; böylece el geri geldiğinde eski bir
"basılı tutma" durumu yanlışlıkla devam etmez.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

import config
from common.geometry import angle_deg, distance

# El noktası numaraları (MediaPipe Hand Landmarker, 21 nokta)
WRIST = 0
THUMB = (1, 2, 3, 4)          # CMC, MCP, IP, uç
INDEX = (5, 6, 7, 8)          # MCP, PIP, DIP, uç
MIDDLE = (9, 10, 11, 12)
RING = (13, 14, 15, 16)
PINKY = (17, 18, 19, 20)
FINGERS = {"başparmak": THUMB, "işaret": INDEX, "orta": MIDDLE, "yüzük": RING, "serçe": PINKY}

GESTURE_NAMES = {
    "acik_el": "açık el",
    "yumruk": "yumruk",
    "isaret": "işaret parmağı",
    "zafer": "V işareti",
    "basparmak": "başparmak yukarı",
    "belirsiz": "belirsiz",
}


def palm_size(points: np.ndarray) -> float:
    """Bilek ile orta parmak kökü arası mesafe. Elin kameraya uzaklığına göre değişir;
    diğer mesafeleri buna bölmek ölçümü mesafeden bağımsız hale getirir."""
    return max(distance(points[WRIST], points[MIDDLE[0]]), 1e-6)


def pinch_ratio(points: np.ndarray) -> float:
    """Başparmak ucu ile işaret parmağı ucu arasındaki normalize mesafe."""
    return distance(points[THUMB[3]], points[INDEX[3]]) / palm_size(points)


def finger_states(points: np.ndarray) -> dict[str, bool | None]:
    """Her parmak için True (açık), False (kapalı) veya None (belirsiz).

    Açı kullanmanın nedeni: "uç, eklemden yukarıda mı?" gibi kurallar el
    döndüğünde bozulur. Eklem açısı elin yönünden bağımsızdır.
    """
    states: dict[str, bool | None] = {}
    for name, (mcp, pip, dip, tip) in FINGERS.items():
        if name == "başparmak":
            a_mcp = angle_deg(points[mcp], points[pip], points[dip])   # 1-2-3
            a_ip = angle_deg(points[pip], points[dip], points[tip])    # 2-3-4
            if a_mcp >= config.THUMB_EXTENDED_DEG and a_ip >= config.THUMB_EXTENDED_DEG:
                states[name] = True
            elif a_mcp < config.THUMB_FOLDED_DEG or a_ip < config.THUMB_FOLDED_DEG:
                states[name] = False
            else:
                states[name] = None
            continue
        a_pip = angle_deg(points[mcp], points[pip], points[dip])
        if a_pip >= config.FINGER_EXTENDED_DEG:
            states[name] = True
        elif a_pip <= config.FINGER_FOLDED_DEG:
            states[name] = False
        else:
            states[name] = None
    return states


def classify_static(states: dict[str, bool | None]) -> str:
    """Parmak durumlarından tek karelik jest adı üretir."""
    thumb = states["başparmak"]
    others = [states["işaret"], states["orta"], states["yüzük"], states["serçe"]]
    if all(s is True for s in others):      # başparmak hafif bükük olsa da açık el sayılır
        return "acik_el"
    if all(s is False for s in others):
        return "basparmak" if thumb is True else "yumruk"
    if states["işaret"] is True and all(s is False for s in others[1:]):
        return "isaret"
    if states["işaret"] is True and states["orta"] is True and \
            states["yüzük"] is False and states["serçe"] is False:
        return "zafer"
    return "belirsiz"


class Hysteresis:
    """İki eşikli anahtar: değer 'enter' altına inince açılır, 'exit' üstüne çıkınca kapanır."""

    def __init__(self, enter: float, exit: float) -> None:
        if exit <= enter:
            raise ValueError("Çıkış eşiği giriş eşiğinden büyük olmalı")
        self.enter, self.exit = enter, exit
        self.active = False

    def update(self, value: float) -> bool:
        if not self.active and value < self.enter:
            self.active = True
        elif self.active and value > self.exit:
            self.active = False
        return self.active

    def reset(self) -> None:
        self.active = False


class Debouncer:
    """Bir değeri, belirli süre değişmeden kaldıktan sonra kabul eder."""

    def __init__(self, stable_ms: int, initial=None) -> None:
        self.stable_ms = stable_ms
        self.value = initial
        self._candidate = initial
        self._since: int | None = None

    def update(self, candidate, t_ms: int):
        if candidate != self._candidate:
            self._candidate = candidate
            self._since = t_ms
        elif candidate != self.value and self._since is not None and \
                t_ms - self._since >= self.stable_ms:
            self.value = candidate
        return self.value

    def reset(self, value=None) -> None:
        self.value = self._candidate = value
        self._since = None


@dataclass
class GestureState:
    present: bool = False
    gesture: str = "belirsiz"            # kararlı jest
    raw_gesture: str = "belirsiz"        # bu karedeki ham jest
    pinching: bool = False               # kararlı pinch durumu
    pinch_value: float = 1.0             # normalize pinch mesafesi
    cursor: tuple[float, float] | None = None   # işaret parmağı ucu, ekran koordinatı (0-1)
    events: list[str] = field(default_factory=list)


class GestureController:
    """Her karede el noktalarını alır, kararlı jest ve tek seferlik olaylar üretir.

    Olaylar:
      "pinch_basladi" / "pinch_bitti" : pinch durumuna geçiş anları (tek sefer)
      "jest:<ad>"                     : kararlı jest değiştiğinde (soğuma süresiyle sınırlı)
      "el_kayboldu"                   : el HAND_LOST_RESET_MS boyunca görünmediğinde
    """

    def __init__(self) -> None:
        self.pinch = Hysteresis(config.PINCH_ENTER_RATIO, config.PINCH_EXIT_RATIO)
        self.pinch_debounce = Debouncer(config.GESTURE_STABLE_MS, initial=False)
        self.gesture_debounce = Debouncer(config.GESTURE_STABLE_MS, initial="belirsiz")
        self._last_command_ms = -10**9
        self._last_seen_ms: int | None = None
        self._lost_reported = True
        self.state = GestureState()

    def reset(self) -> None:
        self.pinch.reset()
        self.pinch_debounce.reset(False)
        self.gesture_debounce.reset("belirsiz")
        self.state = GestureState()

    def update(self, points: np.ndarray | None, t_ms: int, cursor: tuple[float, float] | None = None) -> GestureState:
        events: list[str] = []
        if points is None:
            if self._last_seen_ms is not None and not self._lost_reported and \
                    t_ms - self._last_seen_ms >= config.HAND_LOST_RESET_MS:
                if self.state.pinching:
                    events.append("pinch_bitti")
                self.reset()
                self._lost_reported = True
                events.append("el_kayboldu")
            self.state.present = False
            self.state.cursor = None
            self.state.events = events
            return self.state

        self._last_seen_ms = t_ms
        self._lost_reported = False
        value = pinch_ratio(points)
        raw_pinch = self.pinch.update(value)
        stable_pinch = self.pinch_debounce.update(raw_pinch, t_ms)
        if stable_pinch and not self.state.pinching:
            events.append("pinch_basladi")
        elif not stable_pinch and self.state.pinching:
            events.append("pinch_bitti")

        raw_gesture = classify_static(finger_states(points))
        previous = self.state.gesture
        gesture = self.gesture_debounce.update(raw_gesture, t_ms)
        if gesture != previous and gesture != "belirsiz" and \
                t_ms - self._last_command_ms >= config.COMMAND_COOLDOWN_MS:
            events.append(f"jest:{gesture}")
            self._last_command_ms = t_ms

        self.state = GestureState(True, gesture, raw_gesture, stable_pinch, value, cursor, events)
        return self.state
