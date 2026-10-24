"""A missing camera returns an error result instead of raising."""

import numpy as np

from ocr_app.infrastructure.camera import OpenCvCamera


def test_missing_camera_returns_error_instead_of_raising() -> None:
    result = OpenCvCamera(device_index=99).capture()
    assert result.image is None
    assert result.error
    assert "camera" in result.error.lower()


def test_unopened_camera_returns_error() -> None:
    class Closed:
        def isOpened(self) -> bool:
            return False

        def read(self):
            raise AssertionError("read should not be called when the device is closed")

        def release(self) -> None:
            self.released = True

    device = Closed()
    result = OpenCvCamera(device_index=0, opener=lambda _index: device).capture()
    assert result.image is None
    assert result.error
    assert device.released


def test_camera_exception_returns_error() -> None:
    def boom(_index: int):
        raise RuntimeError("device busy")

    result = OpenCvCamera(device_index=0, opener=boom).capture()
    assert result.image is None
    assert result.error
    assert "busy" in result.error


def test_camera_frame_is_converted_to_rgb() -> None:
    class BgrDevice:
        def isOpened(self) -> bool:
            return True

        def read(self):
            frame = np.zeros((2, 2, 3), dtype=np.uint8)
            frame[:, :, 0] = 10
            frame[:, :, 1] = 20
            frame[:, :, 2] = 30
            return True, frame

        def release(self) -> None:
            return None

    result = OpenCvCamera(device_index=0, opener=lambda _index: BgrDevice()).capture()
    assert result.error is None
    assert result.image is not None
    assert result.image.shape == (2, 2, 3)
    assert int(result.image[0, 0, 0]) == 30
    assert int(result.image[0, 0, 2]) == 10
