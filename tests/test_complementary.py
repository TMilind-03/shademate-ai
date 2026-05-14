# tests/test_complementary.py
# Unit tests for models/complementary.py

import pytest
from models.complementary import compute_primary, compute_range, build_complementary_range
from utils.constants import RANGE_RADIUS, LAB_L_MIN, LAB_L_MAX, LAB_AB_MIN, LAB_AB_MAX


SAMPLE_WARM_SKIN = {"L": 55.0, "A": 12.0, "B": 18.0}
SAMPLE_COOL_SKIN = {"L": 55.0, "A": -8.0, "B":  3.0}
SAMPLE_NEUTRAL_SKIN = {"L": 55.0, "A":  2.0, "B":  5.0}


# ── compute_primary ───────────────────────────────────────────────────────────

def test_primary_warm_shifts_a_and_b_down():
    primary = compute_primary(SAMPLE_WARM_SKIN, "warm")
    assert primary["A"] < SAMPLE_WARM_SKIN["A"]   # A - 15
    assert primary["B"] < SAMPLE_WARM_SKIN["B"]   # B - 10


def test_primary_cool_shifts_a_and_b_up():
    primary = compute_primary(SAMPLE_COOL_SKIN, "cool")
    assert primary["A"] > SAMPLE_COOL_SKIN["A"]   # A + 12
    assert primary["B"] > SAMPLE_COOL_SKIN["B"]   # B + 12


def test_primary_preserves_l():
    """L channel must remain constant for all undertone types."""
    for undertone, skin in [("warm", SAMPLE_WARM_SKIN), ("cool", SAMPLE_COOL_SKIN), ("neutral", SAMPLE_NEUTRAL_SKIN)]:
        primary = compute_primary(skin, undertone)
        assert primary["L"] == skin["L"], f"L changed for {undertone}"


def test_primary_stays_within_lab_bounds():
    """Even with extreme skin LAB, primary must stay in valid LAB range."""
    extreme = {"L": 99.0, "A": 120.0, "B": 120.0}
    primary = compute_primary(extreme, "warm")
    assert LAB_L_MIN <= primary["L"] <= LAB_L_MAX
    assert LAB_AB_MIN <= primary["A"] <= LAB_AB_MAX
    assert LAB_AB_MIN <= primary["B"] <= LAB_AB_MAX


# ── compute_range ─────────────────────────────────────────────────────────────

def test_range_always_has_5_variants():
    """SRS §4.3.2: range must always have exactly 5 variants."""
    primary = compute_primary(SAMPLE_WARM_SKIN, "warm")
    variants = compute_range(primary)
    assert len(variants) == 5


def test_range_variants_have_required_keys():
    primary = compute_primary(SAMPLE_NEUTRAL_SKIN, "neutral")
    for v in compute_range(primary):
        assert "lab" in v
        assert "hex" in v
        assert "undertone" in v
        assert "delta_e_from_primary" in v


def test_range_delta_e_is_non_negative():
    primary = compute_primary(SAMPLE_COOL_SKIN, "cool")
    for v in compute_range(primary):
        assert v["delta_e_from_primary"] >= 0.0


def test_range_lab_values_within_bounds():
    primary = compute_primary(SAMPLE_WARM_SKIN, "warm")
    for v in compute_range(primary):
        assert LAB_L_MIN <= v["lab"]["L"] <= LAB_L_MAX
        assert LAB_AB_MIN <= v["lab"]["A"] <= LAB_AB_MAX
        assert LAB_AB_MIN <= v["lab"]["B"] <= LAB_AB_MAX


def test_range_hex_format():
    primary = compute_primary(SAMPLE_NEUTRAL_SKIN, "neutral")
    for v in compute_range(primary):
        assert v["hex"].startswith("#") and len(v["hex"]) == 7
        int(v["hex"][1:], 16)  # valid hex


# ── build_complementary_range ─────────────────────────────────────────────────

def test_build_complementary_range_structure():
    result = build_complementary_range(SAMPLE_WARM_SKIN, "warm")
    assert "primary" in result
    assert "range" in result
    assert "range_radius" in result


def test_build_range_radius_matches_constant():
    result = build_complementary_range(SAMPLE_COOL_SKIN, "cool")
    assert result["range_radius"] == RANGE_RADIUS


def test_build_primary_has_all_fields():
    result = build_complementary_range(SAMPLE_NEUTRAL_SKIN, "neutral")
    primary = result["primary"]
    assert "lab" in primary
    assert "hex" in primary
    assert "undertone" in primary
