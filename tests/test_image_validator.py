# tests/test_image_validator.py
# Unit tests for services/image_validator.py
# Uses synthetic images built with NumPy — no real selfies needed.

import io
import numpy as np
import pytest
import cv2
from fastapi import HTTPException

from services.image_validator import validate
from utils.constants import MIN_IMAGE_DIMENSION, BRIGHTNESS_MIN, BRIGHTNESS_MAX


def _encode_image(img_bgr: np.ndarray, fmt: str = ".jpg") -> bytes:
    """Helper: encode a NumPy BGR array to JPEG or PNG bytes."""
    success, buf = cv2.imencode(fmt, img_bgr)
    assert success, "cv2.imencode failed in test helper"
    return buf.tobytes()


def _make_image(width: int, height: int, brightness: int) -> np.ndarray:
    """Helper: create a solid-colour BGR image of given size and brightness."""
    return np.full((height, width, 3), brightness, dtype=np.uint8)


# ── Valid image ───────────────────────────────────────────────────────────────

def test_valid_jpeg_returns_array():
    img = _make_image(300, 300, 128)
    data = _encode_image(img, ".jpg")
    result = validate(data)
    assert isinstance(result, np.ndarray)
    assert result.shape[0] >= MIN_IMAGE_DIMENSION
    assert result.shape[1] >= MIN_IMAGE_DIMENSION


def test_valid_png_returns_array():
    img = _make_image(400, 400, 150)
    data = _encode_image(img, ".png")
    result = validate(data)
    assert result is not None


# ── Corrupt / undecodable bytes ───────────────────────────────────────────────

def test_invalid_format_raises():
    with pytest.raises(HTTPException) as exc_info:
        validate(b"not an image at all")
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["error_code"] == "INVALID_IMAGE_FORMAT"


# ── Image too small ───────────────────────────────────────────────────────────

def test_image_too_small_raises():
    img = _make_image(100, 100, 128)
    data = _encode_image(img, ".jpg")
    with pytest.raises(HTTPException) as exc_info:
        validate(data)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["error_code"] == "IMAGE_TOO_SMALL"


# ── Brightness checks ─────────────────────────────────────────────────────────

def test_image_too_dark_raises():
    """All-black image → mean brightness 0 → IMAGE_TOO_DARK"""
    img = _make_image(300, 300, 0)
    data = _encode_image(img, ".jpg")
    with pytest.raises(HTTPException) as exc_info:
        validate(data)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["error_code"] == "IMAGE_TOO_DARK"


def test_image_too_bright_raises():
    """All-white image → mean brightness 255 → IMAGE_TOO_BRIGHT"""
    img = _make_image(300, 300, 255)
    data = _encode_image(img, ".jpg")
    with pytest.raises(HTTPException) as exc_info:
        validate(data)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["error_code"] == "IMAGE_TOO_BRIGHT"


# ── File size limit ───────────────────────────────────────────────────────────

def test_file_too_large_raises():
    """Bytes exceeding 5MB limit → FILE_TOO_LARGE"""
    oversized = b"x" * (5 * 1024 * 1024 + 1)
    with pytest.raises(HTTPException) as exc_info:
        validate(oversized)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["error_code"] == "FILE_TOO_LARGE"
