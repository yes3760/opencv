"""Örneklerin src klasöründeki modülleri bulabilmesi için yol ayarı.

Her örnek "import _yol" satırıyla başlar. Bu satır, proje kökündeki src
klasörünü Python'un arama yoluna ekler; böylece "from camera import Camera"
gibi içe aktarmalar çalışır.
"""

import os
import sys
from pathlib import Path

# Windows 10/11 MSMF donanım hızlandırma kilitlenmesini cv2 yüklenmeden kapat
os.environ.setdefault("OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS", "0")

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
