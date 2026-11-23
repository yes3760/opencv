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


def draw_quality(img: np.ndarray, report, x: int, y: int, width: int = 335) -> int:
    """Kompakt kalite kontrol listesini çizer; yüzü kapatmaz."""
    rows = report.checks
    row_h = 21
    height = 30 + row_h * len(rows) + 6
    panel(img, x, y, x + width, y + height, alpha=0.76)
    cv2.rectangle(img, (x, y), (x + width, y + height), (65, 58, 52), 1)
    put_text(img, "Görüntü kalite kontrolü", (x + 10, y + 6), 14, WHITE)
    for i, c in enumerate(rows):
        yy = y + 29 + row_h * i
        cv2.circle(img, (x + 15, yy + 7), 5, TEAL if c.ok else RED, -1, cv2.LINE_AA)
        put_text(img, f"{c.name}: {c.value}", (x + 27, yy), 12, WHITE if c.ok else AMBER)
    return height


def disclaimer(img: np.ndarray) -> None:
    """Uyarı metni her zaman görünür kalır."""
    h, w = img.shape[:2]
    panel(img, 0, 0, w, 30, alpha=0.84)
    put_text(img, config.SKIN_DISCLAIMER, (10, 6), 14, AMBER)


def result_panel(report, map_name: str, height: int = 540, width: int = 430) -> np.ndarray:
    """Analiz sonucunu yüksekliğe duyarlı (taşmayan) ayrı bir panel olarak çizer."""
    out = np.full((height, width, 3), INK, np.uint8)
    cv2.line(out, (0, 0), (0, height), (65, 58, 52), 1)
    put_text(out, "Cilt görünümü analizi (tek kare)", (14, 10), 17, WHITE)
    put_text(out, config.SKIN_DISCLAIMER, (14, 34), 12, AMBER)
    if report is None:
        put_text(out, "Boşluk tuşu: analiz için kare al", (14, 70), 15, TEAL)
        put_text(out, "1-4 tuşları: harita değiştir", (14, 98), 13, GRAY)
        put_text(out, "F tuşu: tüm özellikler & kullanım", (14, 122), 13, GRAY)
        return out
    if report.metrics is None:
        put_text(out, "Uygun görüntü bekleniyor.", (14, 70), 16, AMBER)
        put_text(out, report.quality.first_problem, (14, 98), 13, WHITE)
        return out

    m = report.metrics
    heat = render_heatmap(report.crop, m.maps[map_name], m.union, map_name)
    if config.MIRROR_DISPLAY:
        heat = cv2.flip(heat, 1)

    # Panel yüksekliğine göre dinamik ısı haritası boyutu (yazılar asla üst üste binmez)
    footer_y = height - 28
    reserved_bottom = 178 if m.cheek_delta_e is not None else 136
    avail_h = max(110, footer_y - 58 - reserved_bottom)
    th = min(230, avail_h)
    tw = int(heat.shape[1] * th / max(heat.shape[0], 1))
    if tw > width - 28:
        tw = width - 28
        th = max(90, int(heat.shape[0] * tw / max(heat.shape[1], 1)))

    top_y = 56
    out[top_y:top_y + th, 14:14 + tw] = cv2.resize(heat, (tw, th))
    lo, hi = MAP_RANGES[map_name]
    bar = cv2.applyColorMap(np.linspace(0, 255, 140).astype(np.uint8)[None, :].repeat(9, 0), cv2.COLORMAP_VIRIDIS)
    by = top_y + th + 8
    out[by:by + 9, 14:154] = bar
    put_text(out, f"{map_name}: {lo:g} … {hi:g}", (162, by - 3), 12, GRAY)

    y = by + 22
    header = ["bölge", "Δa*", "parlak %", "doku", "ΔE"]
    cols = [14, 118, 178, 260, 326]
    for cx, htxt in zip(cols, header):
        put_text(out, htxt, (cx, y), 12, GRAY)
    row_step = 20 if height < 480 else 22
    for name, s in m.regions.items():
        y += row_step
        values = [name, f"{s.delta_a:+.1f}", f"{s.shine_percent:.1f}", f"{s.texture:.1f}", f"{s.color_diff:.1f}"]
        for cx, v in zip(cols, values):
            put_text(out, v, (cx, y), 13, REGION_COLORS.get(name, WHITE) if cx == 14 else WHITE)
    if m.cheek_delta_e is not None and y + 36 < footer_y:
        y += 24
        put_text(out, f"İki yanak renk farkı ΔE: {m.cheek_delta_e:.1f}", (14, y), 12, WHITE)
        if y + 18 < footer_y - 6:
            put_text(out, "Genellikle ışığın yönünden kaynaklanır.", (14, y + 16), 11, GRAY)

    cv2.line(out, (12, footer_y - 6), (width - 12, footer_y - 6), (65, 58, 52), 1)
    put_text(out, "1-4: harita  ·  Boşluk: analiz  ·  F: yardım", (14, footer_y), 12, GRAY)
    return out
