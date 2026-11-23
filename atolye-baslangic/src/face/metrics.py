"""Yüz işaret noktalarından ölçümler: göz/ağız açıklığı, baş yönelimi, oranlar.

Bütün ölçümler normalize edilir (bir uzunluğun başka bir yüz uzunluğuna oranı).
Böylece kişi kameraya yaklaşıp uzaklaştığında değerler değişmez. Hiçbiri
santimetre değildir; MediaPipe'ın z değeri de gerçek derinlik değil, yüz
ölçeğine göre göreli bir değerdir.

Nokta numaraları MediaPipe Face Mesh dizinidir. "Sol/sağ" kişinin kendi
sol/sağıdır: aynalanmamış kamera görüntüsünde kişinin sol gözü görüntünün sağında kalır.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

import config
from common.geometry import distance

# Göz en-boy oranı (EAR) için 6 nokta: köşe, üst, üst, köşe, alt, alt
RIGHT_EYE_EAR = (33, 160, 158, 133, 153, 144)    # kişinin sağ gözü
LEFT_EYE_EAR = (362, 385, 387, 263, 373, 380)    # kişinin sol gözü
MOUTH_INNER = (13, 14)                           # iç üst dudak, iç alt dudak
MOUTH_CORNERS = (78, 308)                        # iç ağız köşeleri

FOREHEAD_TOP = 10      # yüz ağının en üst orta noktası (saç çizgisi değildir)
CHIN = 152
CHEEK_LEFT_EDGE = 454  # elmacık hizasında yüz kenarı
CHEEK_RIGHT_EDGE = 234
JAW_LEFT = 397         # çene köşesi hizası
JAW_RIGHT = 172
TEMPLE_LEFT = 284      # alnın üst-yan noktaları
TEMPLE_RIGHT = 54
NOSE_TIP = 1


def eye_aspect_ratio(points: np.ndarray, idx=RIGHT_EYE_EAR) -> float:
    """EAR = (|p2-p6| + |p3-p5|) / (2 |p1-p4|). Göz kapandıkça 0'a yaklaşır.

    Kaynak: Soukupová ve Čech, "Real-Time Eye Blink Detection using Facial
    Landmarks", CVWW 2016. Orijinal çalışma dlib'in 68 noktasını kullanır;
    burada MediaPipe'taki karşılık gelen noktalar seçilmiştir.
    """
    p1, p2, p3, p4, p5, p6 = (points[i] for i in idx)
    width = distance(p1, p4)
    if width < 1e-6:
        return 0.0
    return (distance(p2, p6) + distance(p3, p5)) / (2.0 * width)


def mouth_aspect_ratio(points: np.ndarray) -> float:
    """İç dudak açıklığının ağız genişliğine oranı."""
    width = distance(points[MOUTH_CORNERS[0]], points[MOUTH_CORNERS[1]])
    if width < 1e-6:
        return 0.0
    return distance(points[MOUTH_INNER[0]], points[MOUTH_INNER[1]]) / width


@dataclass
class HeadPose:
    pitch: float   # derece; aşağı-yukarı eğim
    yaw: float     # derece; sağa-sola dönüş
    roll: float    # derece; başın yana yatması


def head_pose_from_matrix(matrix) -> HeadPose:
    """FaceLandmarker'ın 4x4 dönüşüm matrisinden yaklaşık Euler açıları.

    Matris, MediaPipe'ın standart yüz modelinin kameraya göre dönüşünü verir.
    Değerler yaklaşık yönelim içindir; ölçüm cihazı doğruluğunda değildir.
    """
    r = np.asarray(matrix, dtype=np.float64)[:3, :3]
    pitch = math.degrees(math.atan2(r[2, 1], r[2, 2]))
    yaw = math.degrees(math.asin(float(np.clip(-r[2, 0], -1.0, 1.0))))
    roll = math.degrees(math.atan2(r[1, 0], r[0, 0]))
    return HeadPose(pitch, yaw, roll)


def is_frontal(pose: HeadPose | None, max_yaw=config.FRONTAL_MAX_YAW_DEG,
               max_pitch=config.FRONTAL_MAX_PITCH_DEG, max_roll=config.FRONTAL_MAX_ROLL_DEG) -> bool:
    if pose is None:
        return False
    return abs(pose.yaw) <= max_yaw and abs(pose.pitch) <= max_pitch and abs(pose.roll) <= max_roll


def face_ratios(points: np.ndarray) -> dict[str, float]:
    """Yüz genişliğine (elmacık hizası) göre normalize oranlar."""
    width = distance(points[CHEEK_RIGHT_EDGE], points[CHEEK_LEFT_EDGE])
    if width < 1e-6:
        return {}
    return {
        "uzunluk/genişlik": distance(points[FOREHEAD_TOP], points[CHIN]) / width,
        "çene/elmacık": distance(points[JAW_RIGHT], points[JAW_LEFT]) / width,
        "üst alın/elmacık": distance(points[TEMPLE_RIGHT], points[TEMPLE_LEFT]) / width,
    }


def face_width_px(points: np.ndarray) -> float:
    return distance(points[CHEEK_RIGHT_EDGE], points[CHEEK_LEFT_EDGE])


def approximate_shape_tendency(ratios: dict[str, float]) -> str:
    """Oranlardan yaklaşık bir şekil eğilimi üretir.

    Bu bir sınıflandırma standardı değildir. Sınırlar [Deney] değerleridir:
    MediaPipe'ın ortalama yüz modeli önden bakışta uzunluk/genişlik = 1,29 ve
    çene/elmacık = 0,80 verir; sınırlar bu ortalamanın çevresine konmuştur.
    Yüz ağının üst noktası saç çizgisi değil alnın ortasıdır; bu nedenle
    "uzunluk" gerçek yüz uzunluğundan kısadır. Baş 30 derece döndüğünde
    uzunluk/genişlik oranı yaklaşık yüzde 12 artar; bu yüzden etiket yalnızca
    önden ve kararlı pozda gösterilir.
    """
    lw = ratios["uzunluk/genişlik"]
    jaw = ratios["çene/elmacık"]
    if jaw >= 0.86 and lw < 1.32:
        return "kareye yakın eğilim"
    if lw < 1.20:
        return "yuvarlağa yakın eğilim"
    if lw >= 1.38:
        return "uzun ovale yakın eğilim"
    return "ovale yakın eğilim"


class BlinkDetector:
    """Göz kırpmayı kişinin kendi açık göz değerine göre algılar.

    Sabit bir EAR eşiği (ör. 0,20) bazı kişilerde gülümserken bile "kapalı"
    sonucunu verir. Bu nedenle son karelerdeki EAR ortancası kişisel temel
    değer kabul edilir ve göz, bu değerin belirli bir oranının altına inince
    kapalı sayılır.
    """

    def __init__(self, history: int = 60, closed_ratio: float = config.EYE_CLOSED_RATIO) -> None:
        from collections import deque
        self.values: deque[float] = deque(maxlen=history)
        self.closed_ratio = closed_ratio
        self.closed = False
        self.blinks = 0

    def update(self, ear: float) -> bool:
        self.values.append(ear)
        if len(self.values) < 10:
            return False
        baseline = float(np.median(self.values))
        closed_now = ear < baseline * self.closed_ratio
        if closed_now and not self.closed:
            self.blinks += 1             # açıktan kapalıya geçiş bir kırpmadır
        self.closed = closed_now
        return closed_now

    def reset(self) -> None:
        self.values.clear()
        self.closed = False
