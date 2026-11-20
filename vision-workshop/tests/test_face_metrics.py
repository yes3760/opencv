import math
from collections import deque

import numpy as np
import pytest

from face.metrics import (LEFT_EYE_EAR, RIGHT_EYE_EAR, BlinkDetector, HeadPose, approximate_shape_tendency,
                          eye_aspect_ratio, face_ratios, head_pose_from_matrix, is_frontal, mouth_aspect_ratio)


def rotation(pitch=0.0, yaw=0.0, roll=0.0):
    p, y, r = map(math.radians, (pitch, yaw, roll))
    rx = np.array([[1, 0, 0], [0, math.cos(p), -math.sin(p)], [0, math.sin(p), math.cos(p)]])
    ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    rz = np.array([[math.cos(r), -math.sin(r), 0], [math.sin(r), math.cos(r), 0], [0, 0, 1]])
    m = np.eye(4)
    m[:3, :3] = rz @ ry @ rx
    return m


@pytest.mark.parametrize("pitch,yaw,roll", [(0, 0, 0), (10, -20, 5), (-15, 30, -8)])
def test_head_pose_recovers_angles(pitch, yaw, roll):
    pose = head_pose_from_matrix(rotation(pitch, yaw, roll))
    assert pose.pitch == pytest.approx(pitch, abs=1e-6)
    assert pose.yaw == pytest.approx(yaw, abs=1e-6)
    assert pose.roll == pytest.approx(roll, abs=1e-6)


def test_ratios_do_not_depend_on_distance(canonical_vertices, projector):
    near = face_ratios(projector(canonical_vertices, scale=30))
    far = face_ratios(projector(canonical_vertices, scale=10))
    for key in near:
        assert near[key] == pytest.approx(far[key], rel=1e-4)
    assert near["uzunluk/genişlik"] == pytest.approx(1.29, abs=0.02)


def test_turning_the_head_changes_ratios(canonical_vertices, projector):
    frontal = face_ratios(projector(canonical_vertices))["uzunluk/genişlik"]
    turned = face_ratios(projector(canonical_vertices, yaw=30))["uzunluk/genişlik"]
    assert turned > frontal * 1.08         # bu yüzden şekil eğilimi yalnızca önden pozda gösterilir


def test_eye_and_mouth_ratios_are_positive(canonical_vertices, projector):
    pts = projector(canonical_vertices)
    assert 0.1 < eye_aspect_ratio(pts, RIGHT_EYE_EAR) < 0.5
    assert 0.1 < eye_aspect_ratio(pts, LEFT_EYE_EAR) < 0.5
    assert mouth_aspect_ratio(pts) >= 0.0


def test_frontal_check():
    assert is_frontal(HeadPose(0, 0, 0))
    assert not is_frontal(HeadPose(0, 40, 0))
    assert not is_frontal(None)


def test_shape_tendency_labels_are_tendencies():
    label = approximate_shape_tendency({"uzunluk/genişlik": 1.29, "çene/elmacık": 0.80, "üst alın/elmacık": 0.87})
    assert "eğilim" in label


def test_blink_detector_uses_personal_baseline():
    det = BlinkDetector(history=30)
    for _ in range(25):
        det.update(0.20)                   # bu kişinin açık göz değeri 0,20
    assert det.update(0.19) is False       # sabit 0,20 eşiği burada "kapalı" derdi
    assert det.update(0.10) is True
    assert det.blinks == 1
