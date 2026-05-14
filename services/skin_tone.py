import os
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from fastapi import HTTPException

from utils.color_utils import rgb_to_lab, lab_to_hex, detect_undertone
from utils.constants import (
    LANDMARK_FOREHEAD,
    LANDMARK_LEFT_CHEEK,
    LANDMARK_RIGHT_CHEEK,
    SKIN_PATCH_SIZE,
)

# ── MediaPipe Tasks initialisation ───────────────────────────────────────────
# Model file path — moved to assets/ to keep root clean.
# main.py lifespan ensures this is downloaded if missing.
MODEL_PATH = "assets/face_landmarker.task"

_detector = None

def _get_detector():
    """Lazy-load the FaceLandmarker detector."""
    global _detector
    if _detector is None:
        if not os.path.exists(MODEL_PATH):
             # This should have been handled by main.py lifespan, but for safety:
             raise RuntimeError(f"MediaPipe model file '{MODEL_PATH}' not found.")
        
        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        _detector = vision.FaceLandmarker.create_from_options(options)
    return _detector


# ── Internal helpers ──────────────────────────────────────────────────────────

def _extract_patch_rgb(img_bgr: np.ndarray, landmark_indices: list[int], landmarks) -> tuple[int, int, int]:
    """
    For a list of landmark indices, compute their average pixel position,
    extract a SKIN_PATCH_SIZE×SKIN_PATCH_SIZE patch centred there,
    and return the mean RGB of that patch.
    """
    h, w = img_bgr.shape[:2]
    half = SKIN_PATCH_SIZE // 2

    # In Tasks API, landmarks are accessed by index directly from the list
    xs = [landmarks[i].x for i in landmark_indices]
    ys = [landmarks[i].y for i in landmark_indices]
    cx = int(sum(xs) / len(xs) * w)
    cy = int(sum(ys) / len(ys) * h)

    # Clamp patch to image bounds
    x1 = max(0, cx - half)
    x2 = min(w, cx + half + 1)
    y1 = max(0, cy - half)
    y2 = min(h, cy + half + 1)

    patch_bgr = img_bgr[y1:y2, x1:x2]
    if patch_bgr.size == 0:
        return (128, 128, 128) # Fallback if patch is somehow empty
        
    mean_bgr = patch_bgr.mean(axis=(0, 1))  # shape (3,)

    # BGR → RGB
    r = int(round(mean_bgr[2]))
    g = int(round(mean_bgr[1]))
    b = int(round(mean_bgr[0]))
    return (r, g, b)


# ── Public API ────────────────────────────────────────────────────────────────

def detect_skin(img_bgr: np.ndarray) -> dict:
    """
    Run Steps 2–4 on a decoded BGR image array using MediaPipe Tasks.

    Returns:
        {
            "lab":       {"L": float, "A": float, "B": float},
            "hex":       str,
            "undertone": "warm" | "cool" | "neutral"
        }

    Raises HTTPException(400) with error_code NO_FACE_DETECTED if MediaPipe
    finds no face landmarks.
    """
    # Step 2 — Face Detection: BGR → RGB for MediaPipe
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
    
    detector = _get_detector()
    detection_result = detector.detect(mp_image)

    if not detection_result.face_landmarks:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "NO_FACE_DETECTED",
                "message": "No face was detected in the image. Please ensure your face is clearly visible and well-lit.",
            },
        )

    # Use first (and only, num_faces=1) face
    landmarks = detection_result.face_landmarks[0]

    # Step 3 — Skin Sampling: extract 15×15px patch for each region
    rgb_forehead   = _extract_patch_rgb(img_bgr, LANDMARK_FOREHEAD,    landmarks)
    rgb_left_cheek = _extract_patch_rgb(img_bgr, LANDMARK_LEFT_CHEEK,  landmarks)
    rgb_right_cheek= _extract_patch_rgb(img_bgr, LANDMARK_RIGHT_CHEEK, landmarks)

    # Average the 3 region RGB triplets → single skin_rgb
    skin_r = int(round((rgb_forehead[0] + rgb_left_cheek[0] + rgb_right_cheek[0]) / 3))
    skin_g = int(round((rgb_forehead[1] + rgb_left_cheek[1] + rgb_right_cheek[1]) / 3))
    skin_b = int(round((rgb_forehead[2] + rgb_left_cheek[2] + rgb_right_cheek[2]) / 3))

    # Step 4 — LAB conversion, undertone, HEX preview
    lab = rgb_to_lab(skin_r, skin_g, skin_b)
    undertone = detect_undertone(lab)
    hex_value = lab_to_hex(lab)

    return {
        "lab": lab,
        "hex": hex_value,
        "undertone": undertone,
    }

