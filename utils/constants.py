# utils/constants.py
# All thresholds, offsets, and config values from ShadeMate AI Layer SRS v1.2
# Single source of truth — never hard-code these anywhere else.

# ── Image Validation ────────────────────────────────────────────────────────
BRIGHTNESS_MIN: int = 60          # Grayscale mean below this → IMAGE_TOO_DARK
BRIGHTNESS_MAX: int = 230         # Grayscale mean above this → IMAGE_TOO_BRIGHT
MIN_IMAGE_DIMENSION: int = 200    # Width or height below this → IMAGE_TOO_SMALL
MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB hard limit

ACCEPTED_MIME_TYPES: set[str] = {"image/jpeg", "image/png"}

# ── Skin Sampling ───────────────────────────────────────────────────────────
SKIN_PATCH_SIZE: int = 15         # 15×15 px patch extracted per landmark region

# MediaPipe Face Mesh landmark indices for each sampling region.
# Using well-established canonical indices from the 468-landmark map.
LANDMARK_FOREHEAD: list[int] = [10, 338, 297, 332, 284]
LANDMARK_LEFT_CHEEK: list[int] = [234, 93, 132, 58, 172]
LANDMARK_RIGHT_CHEEK: list[int] = [454, 323, 361, 288, 397]

# ── Undertone Classification ─────────────────────────────────────────────────
# Thresholds on OpenCV-normalised LAB channels (A: -128..+127, B: -128..+127)
# NOTE: These are starting calibration values. Validate against a diverse set of
#       Indian skin tone selfies (fair → deep brown) before pilot launch.
A_WARM_MIN: float = 5.0           # A > 5 AND B > 10  → warm
B_WARM_MIN: float = 10.0
A_COOL_MAX: float = -3.0          # A < -3            → cool
# Otherwise                        →                   neutral

# ── Complementary Shade ─────────────────────────────────────────────────────
RANGE_RADIUS: float = 8.0         # Delta-E radius reported in the response

# Offsets applied to primary LAB to generate the 5 range variants
VARIANT_OFFSETS: list[dict] = [
    {"L": +4, "A":  0, "B":  0},   # Lighter
    {"L": -4, "A":  0, "B":  0},   # Darker
    {"L":  0, "A": +5, "B":  0},   # Warmer A
    {"L":  0, "A":  0, "B": +5},   # Warmer B
    {"L": +2, "A": -3, "B": -3},   # Cooler-lighter
]

# Per SRS §5.6.1 — primary complementary adjustment per undertone
PRIMARY_WARM_OFFSET: dict = {"A": -15, "B": -10}
PRIMARY_COOL_OFFSET: dict = {"A": +12, "B": +12}
PRIMARY_NEUTRAL_OFFSET: dict = {"A": +5,  "B": +5}

# ── LAB Channel Clamp Bounds ─────────────────────────────────────────────────
LAB_L_MIN: float = 0.0
LAB_L_MAX: float = 100.0
LAB_AB_MIN: float = -128.0
LAB_AB_MAX: float = 127.0
