# main.py
# ShadeMate AI Layer — FastAPI entry point.
# SRS v1.2 | Handles auth middleware, /analyze route, and /health check.
# Run locally: uv run uvicorn main:app --reload
# Production:  uvicorn main:app --host 0.0.0.0 --port $PORT

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from auth.api_key import get_api_key
from models.complementary import build_complementary_range
from schemas.response import AnalyzeResponse, LabColor, ShadeResult, ShadeVariant, ComplementaryRange
from services import image_validator, skin_tone

# ── Logging (LAB values only — never image data or PII, per SRS §7.2) ─────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("shademate.ai")


import os
import urllib.request

# ── App lifecycle ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ShadeMate AI Layer v1.2 starting up…")
    
    # Ensure MediaPipe model is present
    model_path = "assets/face_landmarker.task"
    if not os.path.exists(model_path):
        logger.info("MediaPipe model missing. Downloading…")
        url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
        urllib.request.urlretrieve(url, model_path)
        logger.info("MediaPipe model downloaded ✓")
    
    yield
    logger.info("ShadeMate AI Layer shutting down.")


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="ShadeMate AI Layer",
    version="1.2.0",
    description=(
        "Accepts a selfie, detects skin tone via MediaPipe + OpenCV, "
        "returns skin LAB/HEX/undertone + complementary shade range as JSON."
    ),
    lifespan=lifespan,
)

# CORS — allow all origins; security enforced by API key + domain lock (SRS §6.4)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["Authorization", "Content-Type"],
)


# ── Global exception handler ──────────────────────────────────────────────────

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Wrap all HTTPExceptions in the standard error envelope."""
    detail = exc.detail
    if isinstance(detail, dict):
        body = {"status": "error", "detail": detail}
    else:
        body = {"status": "error", "detail": {"error_code": "INTERNAL_ERROR", "message": str(detail)}}
    return JSONResponse(status_code=exc.status_code, content=body)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["ops"], summary="Health check")
async def health():
    """Simple liveness probe — no auth required."""
    return {"status": "ok", "service": "shademate-ai", "version": "1.2.0"}


@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
    tags=["ai"],
    summary="Analyze selfie → skin tone + complementary shade range",
)
async def analyze(
    image: UploadFile = File(..., description="Selfie image (JPEG or PNG, max 5MB)"),
    client_id: str = Form(..., description="Merchant client identifier"),
    api_key: str = Depends(get_api_key),
):
    """
    Main AI pipeline endpoint. Steps per SRS §5:

    0. Auth validated via Depends(get_api_key) — before any image processing.
    1. Read & validate image bytes (format, size, brightness).
    2. Detect face landmarks via MediaPipe.
    3. Sample skin from forehead + cheeks → average RGB.
    4. Convert to LAB, classify undertone.
    5. Compute complementary primary shade + 5 variants.
    6. Assemble and return JSON response.

    No image data is stored or logged at any step (SRS §7.2).
    """
    logger.info("POST /analyze | client_id=%s", client_id)

    # Step 1 — Read image bytes
    image_bytes = await image.read()

    # Steps 1 — Server-side image validation (raises HTTPException on failure)
    img_array = image_validator.validate(image_bytes)

    # Steps 2–4 — Face detection + skin sampling + LAB + undertone
    skin = skin_tone.detect_skin(img_array)

    # Log LAB only — never image bytes, never face crops (SRS §7.2)
    logger.info(
        "Skin detected | client_id=%s | LAB=(%.2f, %.2f, %.2f) | undertone=%s",
        client_id, skin["lab"]["L"], skin["lab"]["A"], skin["lab"]["B"], skin["undertone"],
    )

    # Step 5 — Complementary shade range
    comp = build_complementary_range(skin["lab"], skin["undertone"])

    # Step 6 — Assemble and validate response via Pydantic
    detected_skin = ShadeResult(
        lab=LabColor(**skin["lab"]),
        hex=skin["hex"],
        undertone=skin["undertone"],
    )

    primary = ShadeResult(
        lab=LabColor(**comp["primary"]["lab"]),
        hex=comp["primary"]["hex"],
        undertone=comp["primary"]["undertone"],
    )

    range_variants = [
        ShadeVariant(
            lab=LabColor(**v["lab"]),
            hex=v["hex"],
            undertone=v["undertone"],
            delta_e_from_primary=v["delta_e_from_primary"],
        )
        for v in comp["range"]
    ]

    complementary_range = ComplementaryRange(
        primary=primary,
        range=range_variants,
        range_radius=comp["range_radius"],
    )

    return AnalyzeResponse(
        detected_skin=detected_skin,
        complementary_range=complementary_range,
    )
