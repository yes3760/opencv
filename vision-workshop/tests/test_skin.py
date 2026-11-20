import cv2
import numpy as np
import pytest

import config
from face.metrics import HeadPose
from skin.metrics import compute_metrics, render_heatmap
from skin.quality import check_quality, sharpness
from skin.regions import REGIONS, build_region_masks


def skin_image(h=400, w=400, seed=0):
    """Ten rengine yakın, hafif dokulu sentetik görüntü (BGR)."""
    rng = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), np.float32)
    img[:] = (120, 150, 200)
    img += rng.normal(0, 4, img.shape)
    return np.clip(img, 0, 255).astype(np.uint8)


def square_mask(shape, x1, y1, x2, y2):
    m = np.zeros(shape[:2], np.uint8)
    m[y1:y2, x1:x2] = 255
    return m


def test_redder_region_has_positive_delta_a():
    img = skin_image()
    img[50:150, 250:350] = np.clip(img[50:150, 250:350].astype(int) + (-10, -10, 25), 0, 255)
    masks = {"sol yanak": square_mask(img.shape, 250, 50, 350, 150),
             "sağ yanak": square_mask(img.shape, 50, 50, 150, 150),
             "alın": square_mask(img.shape, 150, 250, 250, 350)}
    m = compute_metrics(img, masks)
    assert m.regions["sol yanak"].delta_a > 3
    assert m.regions["sağ yanak"].delta_a < 1
    assert m.cheek_delta_e > 3


def test_highlight_counts_as_shine_but_uniform_brightness_does_not():
    img = skin_image()
    cv2.circle(img, (100, 100), 12, (245, 245, 245), -1)          # yansıma benzeri parlak leke
    mask = square_mask(img.shape, 50, 50, 150, 150)
    shine = compute_metrics(img, {"alın": mask}).regions["alın"].shine_percent
    assert shine > 1.0
    bright = np.clip(skin_image().astype(int) + 50, 0, 255).astype(np.uint8)   # her yer eşit parlak
    assert compute_metrics(bright, {"alın": mask}).regions["alın"].shine_percent < 0.5


def test_noise_raises_texture_value():
    clean = skin_image(seed=1)
    noisy = np.clip(clean.astype(int) + np.random.default_rng(3).normal(0, 10, clean.shape), 0, 255).astype(np.uint8)
    mask = square_mask(clean.shape, 50, 50, 350, 350)
    t_clean = compute_metrics(clean, {"alın": mask}).regions["alın"].texture
    t_noisy = compute_metrics(noisy, {"alın": mask}).regions["alın"].texture
    assert t_noisy > t_clean * 1.5     # doku değeri kamera gürültüsünden etkilenir


def test_heatmap_keeps_size_and_dims_outside():
    img = skin_image()
    mask = square_mask(img.shape, 100, 100, 200, 200)
    out = render_heatmap(img, np.zeros(img.shape[:2], np.float32), mask, "doku değişimi")
    assert out.shape == img.shape
    assert out[10, 10].mean() < img[10, 10].mean()


def test_sharpness_detects_blur_independent_of_brightness():
    # Doğal görüntülere benzer: yumuşak bir zemin üzerinde keskin kenarlı şekiller.
    # (Saf beyaz gürültüde bulanıklık toplam varyansı da düşürdüğü için oran değişmez;
    # bu, ölçünün raporda belirtilen bir sınırlamasıdır.)
    img = np.tile(np.linspace(60, 200, 600, dtype=np.uint8), (600, 1))
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    for i in range(12):
        cv2.circle(img, (50 + 45 * i, 150 + (i % 3) * 120), 18, (30, 30, 30) if i % 2 else (240, 240, 240), -1)
        cv2.rectangle(img, (30 + 48 * i, 480), (50 + 48 * i, 560), (20, 20, 20), -1)
    box = (0, 0, 600, 600)
    sharp = sharpness(img, box)
    assert sharpness(cv2.GaussianBlur(img, (0, 0), 4), box) < config.SKIN_MIN_SHARPNESS < sharp
    dark = (img * 0.3).astype(np.uint8)
    assert sharpness(dark, box) == pytest.approx(sharp, rel=0.25)


def test_regions_on_canonical_face(canonical_vertices, projector):
    pts = projector(canonical_vertices, scale=22, center=(300, 300))
    img = skin_image(600, 600)
    width = float(np.linalg.norm(pts[234] - pts[454]))
    rm = build_region_masks(img, pts, width, config.SKIN_ROI_EROSION_RATIO)
    assert set(rm.masks) == set(REGIONS)
    for name, mask in rm.masks.items():
        assert mask.any(), name
        assert not np.any((mask > 0) & (rm.exclusion > 0))           # göz/kaş/dudak dışarıda
    # kişinin sağ yanağı, aynalanmamış görüntüde solda kalır
    right_x = np.nonzero(rm.masks["sağ yanak"])[1].mean()
    left_x = np.nonzero(rm.masks["sol yanak"])[1].mean()
    assert right_x < left_x


def test_quality_rejects_bad_conditions():
    img = skin_image()
    mask = square_mask(img.shape, 100, 100, 300, 300)
    good = check_quality(img, 1, 250, HeadPose(0, 0, 0), (50, 50, 350, 350), mask, {"alın": 1.0, "sağ yanak": 1.0})
    assert good.ok
    assert not check_quality(img, 2, 250, HeadPose(0, 0, 0), (50, 50, 350, 350), mask, {}).ok
    turned = check_quality(img, 1, 250, HeadPose(0, 35, 0), (50, 50, 350, 350), mask, {"alın": 1.0, "sağ yanak": 1.0})
    assert not turned.ok and "Baş pozu" in turned.first_problem
    dark = (img * 0.15).astype(np.uint8)
    rep = check_quality(dark, 1, 250, HeadPose(0, 0, 0), (50, 50, 350, 350), mask, {"alın": 1.0, "sağ yanak": 1.0})
    assert not rep.ok and "Pozlama" in rep.first_problem
