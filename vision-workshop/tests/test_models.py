"""Model dosyalarıyla uçtan uca testler. Modeller yoksa atlanır.

Gerçek yüz/el görüntüsüyle test için VISION_LAB_SAMPLES ortam değişkenine
business-person.png ve woman_hands.jpg dosyalarını içeren klasör verilebilir.
"""

import os
from pathlib import Path

import cv2
import numpy as np
import pytest

import config
from common.frame import FramePreparer
from common.models import ModelMissingError, require_model

needs_models = pytest.mark.skipif(not (config.FACE_MODEL.exists() and config.HAND_MODEL.exists()),
                                  reason="model dosyaları indirilmemiş")
SAMPLES = Path(os.environ.get("VISION_LAB_SAMPLES", "")) if os.environ.get("VISION_LAB_SAMPLES") else None


def test_missing_model_message(tmp_path):
    with pytest.raises(ModelMissingError) as info:
        require_model(tmp_path / "yok.task")
    assert "download_models.py" in str(info.value)


@needs_models
def test_blank_frame_gives_clear_status():
    from face.tracker import FaceTracker
    from hands.tracker import HandTracker
    frame = FramePreparer(640)(np.zeros((480, 640, 3), np.uint8))
    with FaceTracker() as faces, HandTracker() as hands:
        f, h = faces.process(frame), hands.process(frame)
    assert f.faces == [] and "bulunamadı" in f.status
    assert h.hands == [] and "bulunamadı" in h.status


@needs_models
def test_skin_analyzer_without_face_reports_reason():
    from skin.analyzer import SkinAnalyzer
    analyzer = SkinAnalyzer(use_segmenter=False)
    report = analyzer.analyze(np.zeros((480, 640, 3), np.uint8), [], 1.0)
    assert report.metrics is None and "Tek yüz" in report.message


@needs_models
@pytest.mark.skipif(SAMPLES is None, reason="VISION_LAB_SAMPLES verilmedi")
def test_real_face_and_hands():
    from face.tracker import FaceTracker
    from hands.tracker import HandTracker
    from skin.analyzer import SkinAnalyzer
    face_img = cv2.imread(str(SAMPLES / "business-person.png"))
    prepare = FramePreparer(640)
    with FaceTracker() as faces:
        for _ in range(3):
            frame = prepare(face_img)
            result = faces.process(frame)
    assert len(result.faces) == 1 and result.faces[0].points.shape == (478, 2)
    assert abs(result.faces[0].pose.yaw) < 15
    report = SkinAnalyzer().analyze(face_img, result.faces, frame.scale_to_full)
    assert report.quality.checks and report.crop is not None

    hand_img = cv2.imread(str(SAMPLES / "woman_hands.jpg"))
    with HandTracker(max_hands=2) as hands:
        res = hands.process(FramePreparer(640)(hand_img))
    assert len(res.hands) == 2
