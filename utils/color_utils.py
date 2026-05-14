# utils/color_utils.py
# Pure color-space utility functions — no side effects, no I/O.
# Used by skin_tone.py and complementary.py

import math
import cv2
import numpy as np

from utils.constants import (
    A_WARM_MIN, B_WARM_MIN, A_COOL_MAX,
    LAB_L_MIN, LAB_L_MAX, LAB_AB_MIN, LAB_AB_MAX,
)


def rgb_to_lab(r: int, g: int, b: int) -> dict:
    """
    Convert an RGB triplet to OpenCV-normalised LAB.
    Returns: { 'L': float (0-100), 'A': float (-128..+127), 'B': float (-128..+127) }
    """
    bgr_pixel = np.uint8([[[b, g, r]]])
    lab_raw = cv2.cvtColor(bgr_pixel, cv2.COLOR_BGR2LAB)
    L_cv, A_cv, B_cv = int(lab_raw[0][0][0]), int(lab_raw[0][0][1]), int(lab_raw[0][0][2])

    L = L_cv * (100.0 / 255.0)
    A = float(A_cv) - 128.0
    B = float(B_cv) - 128.0
    return {"L": round(L, 4), "A": round(A, 4), "B": round(B, 4)}


def lab_to_hex(lab: dict) -> str:
    """
    Convert a LAB dict (L, A, B) back to a hex colour string like '#C8956A'.
    Uses OpenCV LAB→BGR conversion.
    """
    L = lab["L"]
    A = lab["A"]
    B = lab["B"]

    # Clamp to valid OpenCV LAB uint8 space
    L_cv = int(round(L * (255.0 / 100.0)))
    A_cv = int(round(A + 128.0))
    B_cv = int(round(B + 128.0))

    L_cv = max(0, min(255, L_cv))
    A_cv = max(0, min(255, A_cv))
    B_cv = max(0, min(255, B_cv))

    lab_pixel = np.uint8([[[L_cv, A_cv, B_cv]]])
    bgr_back = cv2.cvtColor(lab_pixel, cv2.COLOR_LAB2BGR)
    b_out = int(bgr_back[0][0][0])
    g_out = int(bgr_back[0][0][1])
    r_out = int(bgr_back[0][0][2])

    return "#{:02X}{:02X}{:02X}".format(r_out, g_out, b_out)


def delta_e(lab1: dict, lab2: dict) -> float:
    """
    CIE76 Delta-E: Euclidean distance in LAB space.
    Sufficient for the shade-matching use case in Phase 1.
    """
    dL = lab1["L"] - lab2["L"]
    dA = lab1["A"] - lab2["A"]
    dB = lab1["B"] - lab2["B"]
    return round(math.sqrt(dL**2 + dA**2 + dB**2), 4)


def detect_undertone(lab: dict) -> str:
    """
    Classify undertone from LAB values per SRS §5.5.
    Returns: 'warm' | 'cool' | 'neutral'
    """
    A = lab["A"]
    B = lab["B"]
    if A > A_WARM_MIN and B > B_WARM_MIN:
        return "warm"
    elif A < A_COOL_MAX:
        return "cool"
    return "neutral"


def clamp_lab(L: float, A: float, B: float) -> dict:
    """Clamp LAB values to their valid ranges."""
    return {
        "L": max(LAB_L_MIN, min(LAB_L_MAX, L)),
        "A": max(LAB_AB_MIN, min(LAB_AB_MAX, A)),
        "B": max(LAB_AB_MIN, min(LAB_AB_MAX, B)),
    }
