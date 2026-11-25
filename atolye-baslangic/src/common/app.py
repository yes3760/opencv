"""Örnek programların ortak komut satırı seçenekleri ve pencere döngüsü."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

import config


def build_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--source", default=str(config.CAMERA_INDEX),
                        help="auto (görüntü veren ilk kamera), kamera numarası (0, 1, ...) veya "
                             "video/fotoğraf dosyası. Kamerasız katılım için bir dosya yolu verilebilir.")
    parser.add_argument("--no-mirror", action="store_true",
                        help="Ekranı ayna gibi gösterme.")
    parser.add_argument("--max-frames", type=int, default=0,
                        help="Bu kadar kareden sonra kapan (0 = sınırsız). Otomatik test içindir.")
    parser.add_argument("--snapshot", default=None,
                        help="Kapanırken son ekranı bu dosyaya kaydet. Varsayılan: kaydetme.")
    return parser


class DisplayLoop:
    """Pencereyi gösterir, tuşları okur ve kapanma koşullarını yönetir.

    Program şu durumlarda kapanır: q veya Esc tuşu, pencerenin kapatılması,
    --max-frames sınırına ulaşılması.
    'f' tuşu: labın amacını ve tuşlarını gösteren Özellikler panelini açar/kapatır.
    """

    def __init__(self, window: str, args: argparse.Namespace,
                 help_title: str = "", help_lines: list[str] | None = None) -> None:
        self.window = window
        self.max_frames = args.max_frames
        self.snapshot = Path(args.snapshot) if args.snapshot else None
        self.frames = 0
        self.running = True
        self.last_key = -1
        self._last_image: np.ndarray | None = None
        self.help_title = help_title or window
        self.help_lines: list[str] = list(help_lines) if help_lines else []
        self.show_help = False
        self._sized = False
        flags = cv2.WINDOW_NORMAL
        if hasattr(cv2, "WINDOW_KEEPRATIO"):
            flags |= cv2.WINDOW_KEEPRATIO
        cv2.namedWindow(self.window, flags)

    def set_help(self, title: str, lines: list[str]) -> None:
        """Özellikler/Yardım menüsü metinlerini çalışma sırasında günceller."""
        self.help_title = title
        self.help_lines = list(lines)

    def on_mouse(self, callback) -> None:
        """callback(event, x, y, flags, param) imzasında bir fonksiyon bağlar."""
        cv2.setMouseCallback(self.window, callback)

    def _fit_window(self, image: np.ndarray) -> None:
        """Pencereyi ilk karede görüntünün oranına göre boyutlandırır (üstteki boş şeridi engeller)."""
        h, w = image.shape[:2]
        max_w, max_h = 1260, 740
        scale = min(1.0, max_w / max(w, 1), max_h / max(h, 1))
        cv2.resizeWindow(self.window, max(320, int(w * scale)), max(240, int(h * scale)))
        self._sized = True

    def show(self, image: np.ndarray) -> int:
        view = image
        if self.help_lines:
            from common.draw import draw_help_badge, draw_help_overlay
            if self.show_help:
                view = image.copy()
                draw_help_overlay(view, self.help_title, self.help_lines)
            draw_help_badge(view, active=self.show_help)
        if not self._sized:
            self._fit_window(view)
        cv2.imshow(self.window, view)
        self._last_image = view
        key = cv2.waitKey(1) & 0xFF
        self.frames += 1
        self.last_key = key
        if key in (ord("f"), ord("F")) and self.help_lines:
            self.show_help = not self.show_help
        # Pencere başka bir uygulamanın arkasında açılabilir; ilk saniyede öne getirilir.
        if self.frames in (1, 30):
            try:
                cv2.setWindowProperty(self.window, cv2.WND_PROP_TOPMOST, 1 if self.frames == 1 else 0)
            except cv2.error:
                pass
        if key in (ord("q"), 27):
            self.running = False
        elif self.frames > 1 and (self.frames % 12 == 0) and cv2.getWindowProperty(self.window, cv2.WND_PROP_VISIBLE) < 1:
            self.running = False          # pencere çarpı düğmesiyle kapatıldı
        elif self.max_frames and self.frames >= self.max_frames:
            self.running = False
        return key

    def close(self) -> None:
        if self.snapshot is not None and self._last_image is not None:
            self.snapshot.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(self.snapshot), self._last_image)
        cv2.destroyAllWindows()
        cv2.waitKey(1)                    # bazı sistemlerde pencerenin kapanması için gerekir

    def __enter__(self) -> "DisplayLoop":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


class Canvas:
    """Ekranda gösterilecek görüntü.

    Sıra önemlidir:
      1. Şekiller (noktalar, kutular, maskeler) aynalanmamış görüntüye çizilir.
      2. flip() ile görüntü aynalanır.
      3. Yazılar en son eklenir; aksi halde yazılar da ters görünürdü.
    Modeller her zaman aynalanmamış kareyi görür; böylece "sol göz" gibi
    etiketler kişinin gerçek sol tarafını gösterir.
    """

    def __init__(self, frame, width: int = config.DISPLAY_WIDTH, mirror: bool = True,
                 max_height: int = 720) -> None:
        from common.frame import resize_to_width
        h, w = frame.full_bgr.shape[:2]
        width = min(width, int(w * max_height / h))     # dikey fotoğraflar ekrana sığsın
        self.image = resize_to_width(frame.full_bgr, width).copy()
        self.scale = self.image.shape[1] / frame.size[0]
        self.mirror = mirror
        self.flipped = False

    @property
    def width(self) -> int:
        return self.image.shape[1]

    @property
    def height(self) -> int:
        return self.image.shape[0]

    def pts(self, points: np.ndarray) -> np.ndarray:
        """İşleme karesindeki noktaları (aynalanmamış) ekran ölçeğine taşır."""
        return np.asarray(points, dtype=np.float32) * self.scale

    def flip(self) -> None:
        if self.mirror and not self.flipped:
            self.image = cv2.flip(self.image, 1)
        self.flipped = True

    def screen(self, point) -> tuple[float, float]:
        """İşleme karesindeki bir noktanın, aynalama sonrası ekrandaki yeri."""
        x, y = float(point[0]) * self.scale, float(point[1]) * self.scale
        if self.mirror:
            x = self.width - 1 - x
        return x, y
