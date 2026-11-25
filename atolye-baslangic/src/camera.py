"""Kamera, video veya fotoğraftan kare okuma.

Girdi : "auto" (görüntü veren ilk kamera), kamera numarası (ör. 0) ya da bir dosya yolu
Çıktı : BGR renk sırasında, uint8 tipinde NumPy dizisi (yükseklik, genişlik, 3)
Görev : Kaynağı açmak, kareyi okumak ve iş bitince kamerayı serbest bırakmak.

Kullanım:
    with Camera("auto") as cam:
        frame = cam.read()

Bir bilgisayarda birden fazla kamera olabilir (ör. Mac'te iPhone Süreklilik Kamerası).
0 numara her zaman dahili kamera değildir; "auto" seçeneği siyah olmayan görüntü veren
ilk kamerayı seçer.
"""

from __future__ import annotations

import platform
import threading
import time
from pathlib import Path

import cv2
import numpy as np

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
BLACK_MEAN = 5.0        # ortalama parlaklığı bunun altında olan kare "siyah" sayılır (0-255)
MAX_AUTO_INDEX = 4      # "auto" seçeneğinin deneyeceği kamera numarası sayısı


class CameraError(RuntimeError):
    """Kamera açılamadığında veya görüntü alınamadığında fırlatılır."""


def _preferred_backend() -> int:
    """İşletim sistemine uygun OpenCV kamera arka ucunu seçer."""
    system = platform.system()
    if system == "Windows":
        return cv2.CAP_DSHOW          # Windows'ta genellikle daha hızlı açılır.
    if system == "Darwin":
        return cv2.CAP_AVFOUNDATION   # macOS'un kamera arayüzü
    return cv2.CAP_ANY


def parse_source(text: str | int) -> int | str:
    """'0' gibi bir metni kamera numarasına çevirir; 'auto' ve dosya yolları metin kalır."""
    if isinstance(text, int):
        return text
    text = text.strip()
    if text.lower() == "auto":
        return "auto"
    return int(text) if text.isdigit() else text


class Camera:
    """Tek bir görüntü kaynağını yönetir. Aynı anda yalnızca bir nesne kamerayı açmalıdır."""

    def __init__(self, source: int | str = "auto", width: int = 1280, height: int = 720):
        self.source = parse_source(source)
        self.width = width
        self.height = height
        self._cap: cv2.VideoCapture | None = None
        self._still: np.ndarray | None = None     # fotoğraf kaynağı için
        self.is_file = not isinstance(self.source, int) and self.source != "auto"
        self.index: int | None = None              # açılan kameranın numarası
        self._lock = threading.Lock()
        self._latest: np.ndarray | None = None
        self._grab_stop = threading.Event()
        self._grab_thread: threading.Thread | None = None
        self._first_ready = threading.Event()

    # -- açma -------------------------------------------------------------
    def open(self) -> "Camera":
        if self.is_file:
            self._open_file(Path(self.source))
        elif self.source == "auto":
            self._open_auto()
            self._start_grabber()
        else:
            self._open_camera(int(self.source))
            self._start_grabber()
        return self

    def _start_grabber(self) -> None:
        """Canlı kameradan arka planda hep en güncel kareyi okur (kasmayı ve gecikmeyi önler)."""
        if self._cap is None:
            return
        self._grab_stop.clear()
        self._first_ready.clear()

        def _loop() -> None:
            while not self._grab_stop.is_set() and self._cap is not None:
                ok, frm = self._cap.read()
                if ok and frm is not None:
                    with self._lock:
                        self._latest = frm
                    self._first_ready.set()
                else:
                    time.sleep(0.005)

        self._grab_thread = threading.Thread(target=_loop, daemon=True)
        self._grab_thread.start()
        self._first_ready.wait(timeout=2.0)

    def _open_file(self, path: Path) -> None:
        if not path.exists():
            raise CameraError(f"Dosya bulunamadı: {path}")
        if path.suffix.lower() in IMAGE_SUFFIXES:
            image = cv2.imread(str(path))
            if image is None:
                raise CameraError(f"Fotoğraf okunamadı: {path}")
            self._still = image
            return
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            raise CameraError(f"Video açılamadı: {path}")
        self._cap = cap

    def _connect(self, index: int, wait_for_permission: bool) -> cv2.VideoCapture:
        """Kamerayı açar. macOS ilk çalıştırmada izin sorar; OpenCV cevabı beklemeden hata
        verdiği için macOS'ta izin penceresi yanıtlanana kadar birkaç saniye denenir."""
        is_mac = platform.system() == "Darwin"
        deadline = time.monotonic() + (20.0 if is_mac and wait_for_permission else 0.0)
        announced = False
        while True:
            cap = cv2.VideoCapture(index, _preferred_backend())
            if not cap.isOpened():
                cap.release()
                cap = cv2.VideoCapture(index)      # varsayılan arka uçla bir kez daha dene
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                return cap
            cap.release()
            if time.monotonic() >= deadline:
                raise CameraError(
                    f"Kamera {index} açılamadı. Olası nedenler: kamera başka bir uygulamada "
                    "açık (Zoom, Teams, tarayıcı), kamera izni verilmemiş veya numara yanlış. "
                    + ("macOS'ta Sistem Ayarları > Gizlilik ve Güvenlik > Kamera bölümünde "
                       "programı başlattığınız uygulamaya (Terminal, VS Code, Claude) izin verip "
                       "programı yeniden başlatın. " if is_mac else "")
                    + "Farklı numara için: --source 1"
                )
            if not announced:
                print("Kamera izni bekleniyor: macOS izin penceresinde 'İzin Ver' seçilirse "
                      "kamera açılır (en fazla 20 saniye)...")
                announced = True
            time.sleep(1.0)

    @staticmethod
    def _brightness(cap: cv2.VideoCapture, frames: int = 20, timeout: float = 3.0) -> float | None:
        """Birkaç kare okuyup en yüksek ortalama parlaklığı döndürür; kare gelmezse None.
        Otomatik pozlama ilk karelerde ayarlandığı için tek kareye bakılmaz."""
        best, got = None, 0
        deadline = time.monotonic() + timeout
        while got < frames and time.monotonic() < deadline:
            ok, frame = cap.read()
            if ok and frame is not None and frame.size > 0:
                got += 1
                mean = float(frame.mean())
                best = mean if best is None else max(best, mean)
                if mean >= BLACK_MEAN and got >= 3:
                    break
            else:
                time.sleep(0.05)
        return best

    def _open_camera(self, index: int) -> None:
        cap = self._connect(index, wait_for_permission=True)
        brightness = self._brightness(cap)
        if brightness is None:
            cap.release()
            raise CameraError(
                "Kamera açıldı ancak görüntü gelmedi. macOS'ta Sistem Ayarları > Gizlilik ve "
                "Güvenlik > Kamera bölümünden programı başlattığınız uygulamaya izin verin; "
                "Windows'ta Ayarlar > Gizlilik > Kamera bölümünü kontrol edin."
            )
        if brightness < BLACK_MEAN:
            print(f"Uyarı: kamera {index} siyah görüntü veriyor. Mercek kapalı olabilir veya bu "
                  "numara başka bir kameraya (ör. iPhone) ait olabilir. Otomatik seçim için: "
                  "--source auto, elle: --source 1")
        self._cap, self.index = cap, index

    def _open_auto(self) -> None:
        """Siyah olmayan görüntü veren ilk kamerayı seçer."""
        fallback: tuple[cv2.VideoCapture, int] | None = None
        first_error: CameraError | None = None
        for index in range(MAX_AUTO_INDEX):
            try:
                cap = self._connect(index, wait_for_permission=(index == 0))
            except CameraError as exc:
                first_error = first_error or exc
                continue
            brightness = self._brightness(cap)
            if brightness is not None and brightness >= BLACK_MEAN:
                if fallback is not None:
                    fallback[0].release()
                self._cap, self.index = cap, index
                return
            if brightness is not None and fallback is None:
                fallback = (cap, index)            # görüntü siyah ama kamera çalışıyor
            else:
                cap.release()
        if fallback is not None:
            self._cap, self.index = fallback
            print(f"Uyarı: hiçbir kamera aydınlık görüntü vermedi; kamera {self.index} kullanılıyor. "
                  "Mercek kapalı olabilir veya ortam çok karanlık.")
            return
        raise first_error or CameraError("Kullanılabilir bir kamera bulunamadı.")

    # -- okuma ------------------------------------------------------------
    def read(self) -> np.ndarray | None:
        """En güncel kareyi gecikmesiz döndürür. Kaynak bittiyse None döner."""
        if self._still is not None:
            return self._still.copy()
        if self._cap is None:
            raise CameraError("Önce open() çağrılmalı.")
        if self._grab_thread is not None:
            with self._lock:
                return self._latest.copy() if self._latest is not None else None
        ok, frame = self._cap.read()
        if not ok and self.is_file:
            # Video bitti: eğitim sırasında kesintisiz göstermek için başa sar.
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self._cap.read()
        return frame if ok else None

    @property
    def actual_size(self) -> tuple[int, int]:
        """Kaynağın gerçekte verdiği (genişlik, yükseklik)."""
        if self._still is not None:
            return self._still.shape[1], self._still.shape[0]
        if self._cap is None:
            return 0, 0
        return (int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    @property
    def is_open(self) -> bool:
        return self._still is not None or (self._cap is not None and self._cap.isOpened())

    # -- kapatma ----------------------------------------------------------
    def release(self) -> None:
        """Arka plan okuyucuyu durdurur ve kamerayı serbest bırakır; kamera ışığı sönmelidir."""
        self._grab_stop.set()
        if self._grab_thread is not None:
            self._grab_thread.join(timeout=1.0)
            self._grab_thread = None
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self._latest = None
        self._still = None

    def __enter__(self) -> "Camera":
        return self.open()

    def __exit__(self, *exc) -> None:
        self.release()
