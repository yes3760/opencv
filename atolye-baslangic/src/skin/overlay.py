"""Cilt modülünün ekrana çizimleri."""

from __future__ import annotations

import cv2
import numpy as np

import config
from common.draw import AMBER, BLUE, GRAY, INK, RED, TEAL, VIOLET, WHITE, panel, put_text
from skin.metrics import MAP_RANGES, render_heatmap

REGION_COLORS = {"alın": TEAL, "sağ yanak": BLUE, "sol yanak": VIOLET}
MAP_KEYS = list(MAP_RANGES.keys())


def draw_regions(img: np.ndarray, regions) -> None:
    """Bölge maskelerini yarı saydam boyar ve çokgen sınırlarını çizer (aynalamadan önce)."""
    overlay = img.copy()
    for name, mask in regions.masks.items():
        overlay[mask > 0] = REGION_COLORS[name]
        cv2.polylines(img, [regions.polygons[name]], True, REGION_COLORS[name], 1, cv2.LINE_AA)
    cv2.addWeighted(overlay, 0.45, img, 0.55, 0, dst=img)
    excl = regions.exclusion > 0
    img[excl] = (img[excl] * 0.55).astype(np.uint8)


def draw_quality(img: np.ndarray, report, x: int, y: int, width: int = 420) -> int:
    """Kalite kontrol listesini çizer; kullanılan yüksekliği döndürür."""
    rows = report.checks
    height = 34 + 24 * len(rows)
    panel(img, x, y, x + width, y + height)
    put_text(img, "Görüntü kalite kontrolü", (x + 10, y + 8), 16, WHITE)
    for i, c in enumerate(rows):
        yy = y + 34 + 24 * i
        # Simgeler her yazı tipinde bulunmadığı için durum renkli bir daireyle gösterilir.
        cv2.circle(img, (x + 16, yy + 8), 6, TEAL if c.ok else RED, -1, cv2.LINE_AA)
        put_text(img, f"{c.name}: {c.value}", (x + 30, yy), 12, WHITE if c.ok else AMBER)
    return height


def disclaimer(img: np.ndarray) -> None:
    """Uyarı metni her zaman görünür kalır."""
    h, w = img.shape[:2]
    panel(img, 0, 0, w, 28, alpha=0.8)
    put_text(img, config.SKIN_DISCLAIMER, (10, 5), 16, AMBER)


def result_panel(report, map_name: str, height: int = 540, width: int = 420) -> np.ndarray:
    """Analiz sonucunu (ısı haritası, gösterge tablosu, açıklama) ayrı bir panel olarak çizer."""
    out = np.full((height, width, 3), INK, np.uint8)
    put_text(out, "Cilt görünümü analizi (tek kare)", (14, 10), 18, WHITE)
    put_text(out, config.SKIN_DISCLAIMER, (14, 36), 13, AMBER)
    if report is None:
        put_text(out, "Boşluk tuşu: analiz için kare al", (14, 70), 15, GRAY)
        return out
    if report.metrics is None:
        put_text(out, "Uygun görüntü bekleniyor.", (14, 70), 17, AMBER)
        put_text(out, report.quality.first_problem, (14, 96), 13, WHITE)
        return out

    m = report.metrics
    heat = render_heatmap(report.crop, m.maps[map_name], m.union, map_name)
    # Isı haritası da ekrandaki gibi aynalanır ki kullanıcı kendi yüzünü tanısın.
    if config.MIRROR_DISPLAY:
        heat = cv2.flip(heat, 1)
    th = 250
    tw = int(heat.shape[1] * th / heat.shape[0])
    if tw > width - 28:
        tw = width - 28
        th = int(heat.shape[0] * tw / heat.shape[1])
    out[66:66 + th, 14:14 + tw] = cv2.resize(heat, (tw, th))
    lo, hi = MAP_RANGES[map_name]
    bar = cv2.applyColorMap(np.linspace(0, 255, 160).astype(np.uint8)[None, :].repeat(10, 0), cv2.COLORMAP_VIRIDIS)
    by = 66 + th + 8
    out[by:by + 10, 14:174] = bar
    put_text(out, f"{map_name}: {lo:g} … {hi:g} (sabit aralık)", (182, by - 3), 12, GRAY)

    y = by + 26
    header = ["bölge", "Δa*", "parlak %", "doku", "ΔE"]
    cols = [14, 120, 180, 265, 330]
    for cx, htxt in zip(cols, header):
        put_text(out, htxt, (cx, y), 13, GRAY)
    for name, s in m.regions.items():
        y += 22
        values = [name, f"{s.delta_a:+.1f}", f"{s.shine_percent:.1f}", f"{s.texture:.1f}", f"{s.color_diff:.1f}"]
        for cx, v in zip(cols, values):
            put_text(out, v, (cx, y), 14, REGION_COLORS.get(name, WHITE) if cx == 14 else WHITE)
    if m.cheek_delta_e is not None:
        y += 26
        put_text(out, f"İki yanak arası renk farkı ΔE: {m.cheek_delta_e:.1f}", (14, y), 13, WHITE)
        put_text(out, "Genellikle ışığın yönünden kaynaklanır.", (14, y + 18), 12, GRAY)
    put_text(out, "1-4: harita seç   boşluk: yeni analiz", (14, height - 26), 13, GRAY)
    return out
