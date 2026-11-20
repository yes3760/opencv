import cv2
import numpy as np
import pytest

from camera import Camera, CameraError, parse_source


def test_parse_source():
    assert parse_source("0") == 0
    assert parse_source("auto") == "auto"
    assert parse_source(" AUTO ") == "auto"
    assert parse_source("video.mp4") == "video.mp4"


def test_image_source_repeats_frame(tmp_path):
    path = tmp_path / "ornek.png"
    cv2.imwrite(str(path), np.full((48, 64, 3), 100, np.uint8))
    with Camera(str(path)) as cam:
        a, b = cam.read(), cam.read()
        assert a.shape == (48, 64, 3) and np.array_equal(a, b)
        assert cam.actual_size == (64, 48)
    assert not cam.is_open                       # with bloğundan çıkınca serbest bırakıldı


def test_video_source_loops(tmp_path):
    path = tmp_path / "ornek.avi"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10, (64, 48))
    for i in range(5):
        writer.write(np.full((48, 64, 3), i * 40, np.uint8))
    writer.release()
    with Camera(str(path)) as cam:
        frames = [cam.read() for _ in range(12)]  # 5 karelik video başa sarılarak okunur
    assert all(f is not None for f in frames)


def test_missing_file_raises():
    with pytest.raises(CameraError):
        Camera("olmayan_dosya.mp4").open()


def test_release_on_exception(tmp_path):
    path = tmp_path / "ornek.png"
    cv2.imwrite(str(path), np.zeros((10, 10, 3), np.uint8))
    cam = Camera(str(path))
    with pytest.raises(RuntimeError):
        with cam:
            raise RuntimeError("döngüde hata")
    assert not cam.is_open
