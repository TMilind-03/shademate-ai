# models/complementary.py
# Step 5: Complementary shade range computation.
# Per SRS §5.6 — given a skin LAB + undertone, produce 1 primary + 5 range variants.

from utils.color_utils import lab_to_hex, detect_undertone, delta_e, clamp_lab
from utils.constants import (
    RANGE_RADIUS,
    VARIANT_OFFSETS,
    PRIMARY_WARM_OFFSET,
    PRIMARY_COOL_OFFSET,
    PRIMARY_NEUTRAL_OFFSET,
)


def compute_primary(skin_lab: dict, undertone: str) -> dict:
    """
    Compute the primary complementary LAB value from the skin tone reading.
    Per SRS §5.6.1 — adjusts A and B channels based on undertone, keeps L constant.
    Returns: { 'L': float, 'A': float, 'B': float }
    """
    L = skin_lab["L"]
    A = skin_lab["A"]
    B = skin_lab["B"]

    if undertone == "warm":
        adj_A = A + PRIMARY_WARM_OFFSET["A"]
        adj_B = B + PRIMARY_WARM_OFFSET["B"]
    elif undertone == "cool":
        adj_A = A + PRIMARY_COOL_OFFSET["A"]
        adj_B = B + PRIMARY_COOL_OFFSET["B"]
    else:  # neutral
        adj_A = A + PRIMARY_NEUTRAL_OFFSET["A"]
        adj_B = B + PRIMARY_NEUTRAL_OFFSET["B"]

    return clamp_lab(L, adj_A, adj_B)


def compute_range(primary_lab: dict) -> list[dict]:
    """
    Generate 5 range variants by applying VARIANT_OFFSETS to the primary LAB.
    Per SRS §5.6.2.
    Each variant includes: { lab, hex, undertone, delta_e_from_primary }
    """
    variants = []
    for offset in VARIANT_OFFSETS:
        v_lab = clamp_lab(
            primary_lab["L"] + offset["L"],
            primary_lab["A"] + offset["A"],
            primary_lab["B"] + offset["B"],
        )
        variants.append({
            "lab": v_lab,
            "hex": lab_to_hex(v_lab),
            "undertone": detect_undertone(v_lab),
            "delta_e_from_primary": delta_e(primary_lab, v_lab),
        })
    return variants


def build_complementary_range(skin_lab: dict, undertone: str) -> dict:
    """
    Top-level function that assembles the full complementary_range response block.
    Per SRS §5.7.
    Returns:
        {
            "primary":      { lab, hex, undertone },
            "range":        [ ... 5 variants ... ],
            "range_radius": float
        }
    """
    primary_lab = compute_primary(skin_lab, undertone)
    primary = {
        "lab": primary_lab,
        "hex": lab_to_hex(primary_lab),
        "undertone": detect_undertone(primary_lab),
    }
    range_variants = compute_range(primary_lab)

    return {
        "primary": primary,
        "range": range_variants,
        "range_radius": RANGE_RADIUS,
    }
