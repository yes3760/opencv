"""Rapordaki şekilleri üretir. Gerçek kişi görüntüsü kullanılmaz:
yüz şekilleri MediaPipe'ın standart yüz modelinden (Apache 2.0) üretilir,
grafikler sentetik sinyallerden ve proje kodunun kendisinden hesaplanır.

Çalıştırma: python docs/tools/make_figures.py
"""

import json
import math
import sys
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

import config  # noqa: E402
from conftest import project  # noqa: E402
from face.metrics import face_ratios  # noqa: E402
from hands.gestures import Hysteresis  # noqa: E402
from skin.regions import build_region_masks  # noqa: E402
from face.overlay import CONTOURS, TESSELATION  # noqa: E402

OUT = ROOT / "docs" / "assets"
SERIES_1, SERIES_2 = "#2a78d6", "#eb6834"     # doğrulanmış iki renk (dataviz denetiminden geçti)
INK, MUTED, GRID = "#1f2328", "#52514e", "#e6e4df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False})

vertices = np.array(json.loads((ROOT / "shared" / "canonical_face_478.json").read_text())["vertices"])


def fig_regions():
    pts = project(vertices, scale=21, center=(340, 335))
    img = np.full((640, 680, 3), (250, 250, 249), np.uint8)
    for a, b in TESSELATION:
        cv2.line(img, tuple(pts[a].astype(int)), tuple(pts[b].astype(int)), (215, 212, 208), 1, cv2.LINE_AA)
    width = float(np.linalg.norm(pts[234] - pts[454]))
    rm = build_region_masks(img, pts, width, config.SKIN_ROI_EROSION_RATIO)
    colors = {"alın": (164, 148, 13), "sağ yanak": (214, 120, 42), "sol yanak": (52, 104, 235)}
    overlay = img.copy()
    for name, mask in rm.masks.items():
        overlay[mask > 0] = colors[name]
    img = cv2.addWeighted(overlay, 0.55, img, 0.45, 0)
    excl = rm.exclusion > 0
    img[excl] = (img[excl] * 0.55).astype(np.uint8)
    for a, b in CONTOURS:
        cv2.line(img, tuple(pts[a].astype(int)), tuple(pts[b].astype(int)), (60, 60, 60), 1, cv2.LINE_AA)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    fig, ax = plt.subplots(figsize=(4.6, 4.3), dpi=200)
    ax.imshow(rgb)
    ax.axis("off")
    # Kişinin sağ yanağı aynalanmamış görüntüde solda görünür.
    labels = {"alın": (340, 62, "center"), "sağ yanak\n(kişinin sağı)": (8, 360, "left"),
              "sol yanak\n(kişinin solu)": (672, 360, "right"),
              "koyu: dışarıda bırakılan (göz, kaş, dudak)": (340, 622, "center")}
    for name, (x, y, ha) in labels.items():
        ax.text(x, y, name, ha=ha, va="center", fontsize=7.5, color=INK)
    fig.tight_layout(pad=0.2)
    fig.savefig(OUT / "sekil_bolgeler.png")
    plt.close(fig)


def fig_pose_ratio():
    yaws = np.arange(0, 46, 5)
    ratios = [face_ratios(project(vertices, yaw=float(y)))["uzunluk/genişlik"] for y in yaws]
    fig, ax = plt.subplots(figsize=(4.6, 2.5), dpi=200)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.plot(yaws, ratios, color=SERIES_1, linewidth=2)
    ax.plot(yaws, ratios, "o", color=SERIES_1, markersize=4)
    ax.axvspan(0, config.FRONTAL_MAX_YAW_DEG, color=SERIES_1, alpha=0.08, linewidth=0)
    ax.text(1, max(ratios) * 0.995, "önden poz kabul aralığı", fontsize=7.5, color=MUTED, va="top")
    ax.annotate(f"{ratios[-1]:.2f}", (yaws[-1], ratios[-1]), textcoords="offset points", xytext=(-4, 6),
                ha="right", fontsize=8, color=INK)
    ax.annotate(f"{ratios[0]:.2f}", (0, ratios[0]), textcoords="offset points", xytext=(4, 6), fontsize=8, color=INK)
    ax.set_xlabel("baş dönüşü (yaw, derece)")
    ax.set_ylabel("uzunluk / genişlik")
    fig.tight_layout()
    fig.savefig(OUT / "sekil_poz_oran.png")
    plt.close(fig)
    return list(zip(yaws.tolist(), [round(r, 3) for r in ratios]))


def fig_hysteresis():
    rng = np.random.default_rng(7)
    t = np.arange(0, 4, 1 / 30)
    # Parmaklar yavaşça yaklaşır, eşik çevresinde bir süre kararsız kalır, sonra kapanır;
    # bırakırken de aynı kararsızlık yaşanır. Gerçek kullanımda sık görülen durumdur.
    keys_t = [0.0, 0.8, 1.2, 1.7, 2.0, 2.6, 2.9, 3.4, 4.0]
    keys_v = [0.60, 0.60, 0.31, 0.29, 0.15, 0.15, 0.30, 0.32, 0.60]
    signal = np.interp(t, keys_t, keys_v) + rng.normal(0, 0.03, t.size)
    single = (signal < 0.30).astype(int)
    hyst = Hysteresis(config.PINCH_ENTER_RATIO, config.PINCH_EXIT_RATIO)
    hstate = np.array([hyst.update(v) for v in signal]).astype(int)
    n_single = int(np.sum(np.diff(single) == 1))
    n_hyst = int(np.sum(np.diff(hstate) == 1))
    fig, axes = plt.subplots(3, 1, figsize=(5.6, 3.6), dpi=200, sharex=True,
                             gridspec_kw={"height_ratios": [2.2, 1, 1]})
    ax = axes[0]
    ax.plot(t, signal, color=SERIES_1, linewidth=1.4)
    for thr, label in ((config.PINCH_ENTER_RATIO, "giriş eşiği"), (config.PINCH_EXIT_RATIO, "çıkış eşiği")):
        ax.axhline(thr, color=MUTED, linewidth=0.8, linestyle="--")
        ax.text(4.02, thr, label, fontsize=7, color=MUTED, va="center")
    ax.axhline(0.30, color=SERIES_2, linewidth=0.8, linestyle=":")
    ax.text(0.05, 0.315, "tek eşik (0,30)", fontsize=7, color=SERIES_2, va="bottom")
    ax.set_ylabel("pinch\nmesafesi", fontsize=8)
    ax.set_ylim(0, 0.75)
    for a, state, color, title in ((axes[1], single, SERIES_2, f"tek eşik: {n_single} komut"),
                                   (axes[2], hstate, SERIES_1, f"histerezis: {n_hyst} komut")):
        a.step(t, state, where="post", color=color, linewidth=1.4)
        a.set_yticks([0, 1], ["açık", "basılı"], fontsize=7)
        a.set_ylim(-0.2, 1.3)
        a.text(0.02, 1.05, title, transform=a.transAxes, fontsize=8, color=INK)
    axes[2].set_xlabel("zaman (saniye)")
    fig.tight_layout(h_pad=0.6)
    fig.savefig(OUT / "sekil_histerezis.png", bbox_inches="tight")
    plt.close(fig)
    return n_single, n_hyst


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    fig_regions()
    print("poz-oran:", fig_pose_ratio())
    print("tek eşik / histerezis komut sayısı:", fig_hysteresis())
