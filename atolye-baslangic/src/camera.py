"""Kamera, video veya fotoğraftan kare okuma (Windows DSHOW/MSMF + macOS AVFoundation tam uyumlu)."""

from __future__ import annotations

import os
import platform
import threading
import time
from pathlib import Path

os.environ.setdefault("OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS", "0")

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
        # Windows DirectShow/MSMF COM nesneleri açıldığı ana thread'de okunmalıdır;
        # arka plan grabber thread yalnızca macOS AVFoundation için kullanılır.
        self._use_grabber = platform.system() == "Darwin"
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
            if self._use_grabber:
                self._start_grabber()
        else:
            self._open_camera(int(self.source))
            if self._use_grabber:
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
    def _brightness(cap: cv2.VideoCapture, frames: int = 16, timeout: float = 2.2) -> tuple[float | None, np.ndarray | None]:
        best, last_good, got = None, None, 0
        deadline = time.monotonic() + timeout
        while got < frames and time.monotonic() < deadline:
            ok, frame = cap.read()
            if ok and frame is not None and frame.size > 0:
                got += 1
                last_good = frame
                mean = float(frame.mean())
                best = mean if best is None else max(best, mean)
                if mean >= BLACK_MEAN and got >= 2:
                    break
            else:
                time.sleep(0.035)
        return best, last_good

    def _try_open_single(self, index: int, backend: int | None) -> tuple[cv2.VideoCapture | None, float | None, np.ndarray | None]:
        """Tek bir (index, backend) çiftini dener; Windows'ta doğal sürücü modunu bozmadan açar."""
        cap = cv2.VideoCapture(index) if backend is None else cv2.VideoCapture(index, backend)
        if not cap.isOpened():
            cap.release()
            return None, None, None

        if platform.system() == "Windows":
            # Windows'ta önce kameranın kendi doğal çözünürlüğünde (en hızlı & sıfır sürücü çökmesi) dene
            br, frm = self._brightness(cap, frames=14, timeout=1.8)
            if br is not None:
                return cap, br, frm
            # Doğal modda kare gelmediyse MJPG + 640x480 ile tekrar dene
            cap.release()
            cap2 = cv2.VideoCapture(index) if backend is None else cv2.VideoCapture(index, backend)
            if not cap2.isOpened():
                cap2.release()
                return None, None, None
            cap2.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            cap2.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap2.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            br2, frm2 = self._brightness(cap2, frames=14, timeout=1.8)
            if br2 is not None:
                return cap2, br2, frm2
            cap2.release()
            return None, None, None

        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        br, frm = self._brightness(cap, frames=16, timeout=2.2)
        if br is not None:
            return cap, br, frm
        cap.release()
        return None, None, None

    def _open_camera(self, index: int) -> None:
        fallback: tuple[cv2.VideoCapture, np.ndarray | None] | None = None
        for backend in _candidate_backends():
            cap, br, frm = self._try_open_single(index, backend)
            if cap is not None and br is not None:
                if br >= BLACK_MEAN:
                    if fallback is not None:
                        fallback[0].release()
                    self._cap, self.index, self._latest = cap, index, frm
                    return
                if fallback is None:
                    fallback = (cap, frm)
                else:
                    cap.release()
        if fallback is not None:
            self._cap, self.index, self._latest = fallback[0], index, fallback[1]
            return
        raise CameraError(
            f"Kamera {index} açılamadı! Windows'ta kontrol edin:\n"
            "  1) Ayarlar > Gizlilik ve Güvenlik > Kamera > 'Masaüstü uygulamalarının kameraya erişmesine izin ver' AÇIK olmalı.\n"
            "  2) Laptop klavyesindeki kamera tuşu (F8/F10/Fn) veya fiziksel kapak açık olmalı.\n"
            "  3) Tarayıcıdaki (Slayt 04 vb.) veya Zoom'daki açık kamerayı kapatın.\n"
            "  4) Farklı kamera için: --source 1 deneyin."
        )

    def _open_auto(self) -> None:
        fallback: tuple[cv2.VideoCapture, int, np.ndarray | None] | None = None
        for index in range(MAX_AUTO_INDEX):
            for backend in _candidate_backends():
                cap, br, frm = self._try_open_single(index, backend)
                if cap is None or br is None:
                    continue
                if br >= BLACK_MEAN:
                    if fallback is not None:
                        fallback[0].release()
                    self._cap, self.index, self._latest = cap, index, frm
                    return
                if fallback is None:
                    fallback = (cap, index, frm)
                else:
                    cap.release()
        if fallback is not None:
            self._cap, self.index, self._latest = fallback[0], fallback[1], fallback[2]
            return
        raise CameraError(
            "Hiçbir kamera açılamadı! Windows'ta kontrol edin:\n"
            "  1) Ayarlar > Gizlilik ve Güvenlik > Kamera > 'Masaüstü uygulamalarının kameraya erişmesine izin ver' AÇIK olmalı.\n"
            "  2) Laptop klavyesindeki kamera tuşu (F8/F10/Fn) veya fiziksel kapak açık olmalı.\n"
            "  3) Tarayıcıdaki (Slayt 04 vb.) veya Zoom'daki açık kamerayı kapatın."
        )

    def read(self) -> np.ndarray | None:
        if self._still is not None:
            return self._still.copy()
        if self._cap is None:
            raise CameraError("Önce open() çağrılmalı.")
        if self._grab_thread is not None and self._grab_thread.is_alive():
            with self._lock:
                if self._latest is not None:
                    return self._latest.copy()
        for _ in range(4):
            ok, frame = self._cap.read()
            if ok and frame is not None and frame.size > 0:
                self._latest = frame
                return frame
            time.sleep(0.015)
        return None

    @property
    def actual_size(self) -> tuple[int, int]:
        if self._still is not None:
            h, w = self._still.shape[:2]
            return w, h
        if self._latest is not None:
            h, w = self._latest.shape[:2]
            return w, h
        if self._cap is None:
            return 0, 0
        return int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def release(self) -> None:
        self._grab_stop.set()
        if self._grab_thread is not None and self._grab_thread.is_alive():
            self._grab_thread.join(timeout=0.5)
        self._grab_thread = None
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __enter__(self) -> "Camera":
        return self.open()

    def __exit__(self, *_) -> None:
        self.release()
