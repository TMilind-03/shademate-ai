# schemas/response.py
# Pydantic output models matching the exact JSON shape from SRS §4.3.2.
# Used by the /analyze endpoint to enforce type safety and auto-generate docs.

from pydantic import BaseModel, Field
from typing import Literal


class LabColor(BaseModel):
    """LAB colour representation (OpenCV-normalised)."""
    L: float = Field(..., ge=0.0, le=100.0, description="Lightness: 0 (black) to 100 (white)")
    A: float = Field(..., ge=-128.0, le=127.0, description="Green–Red axis")
    B: float = Field(..., ge=-128.0, le=127.0, description="Blue–Yellow axis")


class ShadeResult(BaseModel):
    """A single resolved shade with LAB, HEX, and undertone."""
    lab: LabColor
    hex: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex colour, e.g. '#C8956A'")
    undertone: Literal["warm", "cool", "neutral"]


class ShadeVariant(BaseModel):
    """One of the 5 range variants returned in complementary_range.range."""
    lab: LabColor
    hex: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    undertone: Literal["warm", "cool", "neutral"]
    delta_e_from_primary: float = Field(..., ge=0.0, description="CIE76 Delta-E distance from primary shade")


class ComplementaryRange(BaseModel):
    """The full complementary shade range: 1 primary + exactly 5 variants."""
    primary: ShadeResult
    range: list[ShadeVariant] = Field(..., min_length=5, max_length=5)
    range_radius: float = Field(..., description="Delta-E radius used to generate variants")


class AnalyzeResponse(BaseModel):
    """200 OK response from POST /analyze."""
    status: Literal["success"] = "success"
    detected_skin: ShadeResult
    complementary_range: ComplementaryRange


class ErrorDetail(BaseModel):
    """Structured error body returned on 400/401."""
    error_code: str = Field(..., description="Machine-readable error code, e.g. INVALID_API_KEY")
    message: str = Field(..., description="Human-readable explanation for the widget/developer")


class ErrorResponse(BaseModel):
    """Error envelope returned on non-200 responses."""
    status: Literal["error"] = "error"
    detail: ErrorDetail
