# services/image_validator.py
# Step 1: Server-side image safety check.
# Per SRS §5.2 — runs 4 checks in order, stops at first failure.
# Returns decoded image array on success; raises HTTPException on failure.

import cv2
import numpy as np
from fastapi import HTTPException

from utils.constants import (
    BRIGHTNESS_MIN,
    BRIGHTNESS_MAX,
    MIN_IMAGE_DIMENSION,
    MAX_FILE_SIZE_BYTES,
)


def validate(image_bytes: bytes) -> np.ndarray:
    """
    Validate raw image bytes from the multipart upload.
    Runs checks in order (SRS §5.2):
      1. Decode → INVALID_IMAGE_FORMAT
      2. Dimensions → IMAGE_TOO_SMALL
      3. Grayscale mean < min → IMAGE_TOO_DARK
      4. Grayscale mean > max → IMAGE_TOO_BRIGHT
      5. All pass → return decoded BGR image array

    Also checks file size against MAX_FILE_SIZE_BYTES before decoding.
    """
    # Pre-check: file size (not in SRS pipeline order but prevents OOM)
    if len(image_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "FILE_TOO_LARGE",
                "message": f"Image exceeds maximum allowed size of 5MB.",
            },
        )

    # 1. Decode image
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_IMAGE_FORMAT",
                "message": "Could not decode image. Only JPEG and PNG are accepted.",
            },
        )

    # 2. Check minimum dimensions
    h, w = img.shape[:2]
    if w < MIN_IMAGE_DIMENSION or h < MIN_IMAGE_DIMENSION:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "IMAGE_TOO_SMALL",
                "message": f"Image must be at least {MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION}px. Got {w}x{h}.",
            },
        )

    # 3 & 4. Brightness check via grayscale mean
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mean_brightness = float(np.mean(gray))

    if mean_brightness < BRIGHTNESS_MIN:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "IMAGE_TOO_DARK",
                "message": f"Image is too dark (mean brightness {mean_brightness:.1f} < {BRIGHTNESS_MIN}). Please retake in better lighting.",
            },
        )

    if mean_brightness > BRIGHTNESS_MAX:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "IMAGE_TOO_BRIGHT",
                "message": f"Image is too bright (mean brightness {mean_brightness:.1f} > {BRIGHTNESS_MAX}). Please avoid harsh direct lighting.",
            },
        )

    return img
