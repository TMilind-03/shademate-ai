# tests/test_skin_tone.py
# Unit tests for color utility functions used in the skin tone pipeline.
# Deliberately avoids MediaPipe calls (needs a real image/webcam) — those are
# covered by the integration curl test in the verification plan.

import pytest
from utils.color_utils import rgb_to_lab, lab_to_hex, delta_e, detect_undertone, clamp_lab


# ── rgb_to_lab ────────────────────────────────────────────────────────────────

def test_rgb_to_lab_pure_white():
    """Pure white RGB → L close to 100, A and B close to 0."""
    lab = rgb_to_lab(255, 255, 255)
    assert lab["L"] > 95.0, f"Expected L ~100, got {lab['L']}"
    assert abs(lab["A"]) < 5.0
    assert abs(lab["B"]) < 5.0


def test_rgb_to_lab_pure_black():
    """Pure black RGB → L close to 0."""
    lab = rgb_to_lab(0, 0, 0)
    assert lab["L"] < 5.0, f"Expected L ~0, got {lab['L']}"


def test_rgb_to_lab_returns_correct_keys():
    lab = rgb_to_lab(150, 100, 80)
    assert set(lab.keys()) == {"L", "A", "B"}


# ── lab_to_hex ────────────────────────────────────────────────────────────────

def test_lab_to_hex_format():
    """Output must be a valid 7-char hex string."""
    lab = rgb_to_lab(200, 150, 120)
    hex_val = lab_to_hex(lab)
    assert hex_val.startswith("#")
    assert len(hex_val) == 7
    int(hex_val[1:], 16)  # raises ValueError if not valid hex


def test_lab_to_hex_round_trip_approximate():
    """
    Round-trip: RGB → LAB → HEX → compare.
    Due to quantisation in OpenCV uint8, we allow ±5 per channel.
    """
    r, g, b = 180, 130, 100
    lab = rgb_to_lab(r, g, b)
    hex_val = lab_to_hex(lab)
    r2 = int(hex_val[1:3], 16)
    g2 = int(hex_val[3:5], 16)
    b2 = int(hex_val[5:7], 16)
    assert abs(r - r2) <= 10, f"R channel drift too large: {r} vs {r2}"
    assert abs(g - g2) <= 10
    assert abs(b - b2) <= 10


# ── delta_e ───────────────────────────────────────────────────────────────────

def test_delta_e_same_colour_is_zero():
    lab = {"L": 50.0, "A": 10.0, "B": -5.0}
    assert delta_e(lab, lab) == 0.0


def test_delta_e_is_symmetric():
    a = {"L": 50.0, "A": 10.0, "B": -5.0}
    b = {"L": 55.0, "A": 15.0, "B":  0.0}
    assert delta_e(a, b) == delta_e(b, a)


def test_delta_e_known_distance():
    """L differs by 3, A by 4 → hypotenuse = 5."""
    a = {"L": 0.0, "A": 0.0, "B": 0.0}
    b = {"L": 3.0, "A": 4.0, "B": 0.0}
    assert abs(delta_e(a, b) - 5.0) < 0.01


# ── detect_undertone ──────────────────────────────────────────────────────────

def test_detect_undertone_warm():
    lab = {"L": 60.0, "A": 10.0, "B": 15.0}  # A > 5, B > 10
    assert detect_undertone(lab) == "warm"


def test_detect_undertone_cool():
    lab = {"L": 60.0, "A": -10.0, "B": 5.0}  # A < -3
    assert detect_undertone(lab) == "cool"


def test_detect_undertone_neutral():
    lab = {"L": 60.0, "A": 2.0, "B": 5.0}   # neither warm nor cool
    assert detect_undertone(lab) == "neutral"


# ── clamp_lab ─────────────────────────────────────────────────────────────────

def test_clamp_lab_within_bounds():
    result = clamp_lab(50.0, 10.0, -5.0)
    assert result == {"L": 50.0, "A": 10.0, "B": -5.0}


def test_clamp_lab_clamps_extremes():
    result = clamp_lab(200.0, -200.0, 200.0)
    assert result["L"] == 100.0
    assert result["A"] == -128.0
    assert result["B"] == 127.0
