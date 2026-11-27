"""Kamera, video veya fotoğraftan kare okuma (Windows DSHOW/MSMF + macOS AVFoundation tam uyumlu)."""

from __future__ import annotations

import platform
import threading
import time
from pathlib import Path

import cv2
import numpy as np

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
BLACK_MEAN = 5.0
MAX_AUTO_INDEX = 4


class CameraError(RuntimeError):
    """Kamera açılamadığında veya görüntü alınamadığında fırlatılır."""


def _candidate_backends() -> list[int | None]:
    """İşletim sistemine göre denenecek tüm kamera arka uçlarını sırayla döndürür."""
    system = platform.system()
    if system == "Windows":
        out: list[int | None] = []
        for attr in ("CAP_DSHOW", "CAP_MSMF"):
            if hasattr(cv2, attr):
                out.append(getattr(cv2, attr))
        out.append(None)
        return out
    if system == "Darwin":
        return [cv2.CAP_AVFOUNDATION, None]
    return [None]


def parse_source(text: str | int) -> int | str:
    if isinstance(text, int):
        return text
    text = text.strip()
    if text.lower() == "auto":
        return "auto"
    return int(text) if text.isdigit() else text


class Camera:
    """Tek bir görüntü kaynağını yönetir."""

    def __init__(self, source: int | str = "auto", width: int = 1280, height: int = 720):
        self.source = parse_source(source)
        self.width = width
        self.height = height
        self._cap: cv2.VideoCapture | None = None
        self._still: np.ndarray | None = None
        self.is_file = not isinstance(self.source, int) and self.source != "auto"
        self.index: int | None = None
        self._lock = threading.Lock()
        self._latest: np.ndarray | None = None
        self._grab_stop = threading.Event()
        self._grab_thread: threading.Thread | None = None
        self._first_ready = threading.Event()

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
        if self._cap is None:
            return
        self._grab_stop.clear()
        self._first_ready.clear()

        def _loop() -> None:
            while not self._grab_stop.is_set() and self._cap is not None:
                ok, frm = self._cap.read()
                if ok and frm is not None and frm.size > 0:
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

    @staticmethod
    def _brightness(cap: cv2.VideoCapture, frames: int = 20, timeout: float = 2.8) -> float | None:
        best, got = None, 0
        deadline = time.monotonic() + timeout
        while got < frames and time.monotonic() < deadline:
            ok, frame = cap.read()
            if ok and frame is not None and frame.size > 0:
                got += 1
                mean = float(frame.mean())
                best = mean if best is None else max(best, mean)
                if mean >= BLACK_MEAN and got >= 2:
                    break
            else:
                time.sleep(0.04)
        return best

    def _try_open_single(self, index: int, backend: int | None) -> tuple[cv2.VideoCapture | None, float | None]:
        """Tek bir (index, backend) çiftini dener; çözünürlük ayarı bozarsa doğal çözünürlüğe döner."""
        cap = cv2.VideoCapture(index) if backend is None else cv2.VideoCapture(index, backend)
        if not cap.isOpened():
            cap.release()
            return None, None

        # Windows'ta MJPG + çözünürlük dene; kare gelmezse doğal (varsayılan) çözünürlükle yeniden aç!
        if platform.system() == "Windows":
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        else:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        br = self._brightness(cap, frames=12, timeout=1.8)
        if br is not None:
            return cap, br

        # Çözünürlük zorlaması bu Windows sürücüsünü kilitlediyse dokunmadan doğal çözünürlükte aç!
        cap.release()
        cap2 = cv2.VideoCapture(index) if backend is None else cv2.VideoCapture(index, backend)
        if not cap2.isOpened():
            cap2.release()
            return None, None
        br2 = self._brightness(cap2, frames=15, timeout=2.2)
        if br2 is not None:
            return cap2, br2
        cap2.release()
        return None, None

    def _open_camera(self, index: int) -> None:
        fallback_cap = None
        for backend in _candidate_backends():
            cap, br = self._try_open_single(index, backend)
            if cap is not None and br is not None:
                if br >= BLACK_MEAN:
                    if fallback_cap is not None:
                        fallback_cap.release()
                    self._cap, self.index = cap, index
                    return
                if fallback_cap is None:
                    fallback_cap = cap
                else:
                    cap.release()
        if fallback_cap is not None:
            self._cap, self.index = fallback_cap, index
            return
        raise CameraError(
            f"Kamera {index} açılamadı! Windows'ta kontrol edin:\n"
            "  1) Ayarlar > Gizlilik ve Güvenlik > Kamera > 'Masaüstü uygulamalarının erişmesine izin ver' AÇIK olmalı.\n"
            "  2) Klavyedeki kamera kapatma tuşu (F8/F10) veya fiziksel kapak kapalı olmamalı.\n"
            "  3) Zoom / Teams / Tarayıcı kamerayı kullanıyor olabilir.\n"
            "  4) Farklı kamera için: --source 1 veya --source auto deneyin."
        )

    def _open_auto(self) -> None:
        fallback: tuple[cv2.VideoCapture, int] | None = None
        for index in range(MAX_AUTO_INDEX):
            for backend in _candidate_backends():
                cap, br = self._try_open_single(index, backend)
                if cap is None or br is None:
                    continue
                if br >= BLACK_MEAN:
                    if fallback is not None:
                        fallback[0].release()
                    self._cap, self.index = cap, index
                    return
                if fallback is None:
                    fallback = (cap, index)
                else:
                    cap.release()
        if fallback is not None:
            self._cap, self.index = fallback
            return
        raise CameraError(
            "Hiçbir kamera açılamadı! Windows'ta kontrol edin:\n"
            "  1) Ayarlar > Gizlilik ve Güvenlik > Kamera > 'Masaüstü uygulamalarının kameraya erişmesine izin ver' AÇIK olmalı.\n"
            "  2) Laptop klavyesindeki kamera kapatma tuşu (F8/F10/Fn) veya fiziksel mercek kapağı açık olmalı.\n"
            "  3) Tarayıcıdaki (Slayt 04 vb.) veya Zoom'daki açık kamerayı kapatın."
        )

    def read(self) -> np.ndarray | None:
        if self._still is not None:
            return self._still.copy()
        if self._cap is None:
            raise CameraError("Önce open() çağrılmalı.")
        if self._grab_thread is not None:
            with self._lock:
                return self._latest.copy() if self._latest is not None else None
        ok, frame = self._cap.read()
        if not ok and self.is_file:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self._cap.read()
        return frame if ok else None

    @property
    def actual_size(self) -> tuple[int, int]:
        if self._still is not None:
            return self._still.shape[1], self._still.shape[0]
        if self._cap is None:
            return 0, 0
        return (int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    @property
    def is_open(self) -> bool:
        return self._still is not None or (self._cap is not None and self._cap.isOpened())

    def release(self) -> None:
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
