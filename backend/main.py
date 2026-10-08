import asyncio
import base64
import os
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl

FASHN_API_KEY = os.getenv("FASHN_API_KEY", "").strip()
FASHN_BASE_URL = "https://api.fashn.ai/v1"
MODEL_NAME = os.getenv("FASHN_MODEL_NAME", "tryon-max")
MAX_GARMENTS = int(os.getenv("MAX_GARMENTS", "5"))

app = FastAPI(title="Dress Up Camera V2 API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

Category = Literal["top", "bottom", "outerwear", "one-piece", "shoes", "headwear", "accessory"]

class Garment(BaseModel):
    category: Category
    image: str = Field(min_length=20, description="Image data URI or public HTTPS image URL")
    name: str = Field(default="Garment", max_length=120)

class TryOnRequest(BaseModel):
    person_image: str = Field(min_length=20, description="Person photo as image data URI or public HTTPS URL")
    garments: list[Garment] = Field(min_length=1, max_length=5)
    quality: Literal["fast", "balanced", "quality"] = "balanced"

class TryOnResponse(BaseModel):
    result_image: str
    processed_items: list[str]
    model: str
    note: str

def check_image_source(value: str, field_name: str) -> None:
    if value.startswith("data:image/"):
        if ";base64," not in value:
            raise HTTPException(status_code=400, detail=f"{field_name} must be a valid base64 image data URI")
        try:
            base64.b64decode(value.split(";base64,", 1)[1], validate=True)
        except Exception:
            raise HTTPException(status_code=400, detail=f"{field_name} contains invalid base64 image data")
        return
    if value.startswith("https://"):
        return
    raise HTTPException(status_code=400, detail=f"{field_name} must be an image data URI or HTTPS URL")

async def run_prediction(client: httpx.AsyncClient, person_image: str, garment_image: str, quality: str) -> str:
    request_body = {
        "model_name": MODEL_NAME,
        "inputs": {
            "model_image": person_image,
            "product_image": garment_image,
            "generation_mode": quality,
            "resolution": "1k",
            "output_format": "png",
        },
    }
    response = await client.post(f"{FASHN_BASE_URL}/run", json=request_body)
    if response.status_code >= 400:
        detail = response.text[:1200]
        raise HTTPException(status_code=502, detail=f"Virtual try-on provider rejected the request ({response.status_code}): {detail}")
    body = response.json()
    prediction_id = body.get("id")
    if not prediction_id:
        raise HTTPException(status_code=502, detail=f"Provider did not return a prediction ID: {body}")

    # Poll provider status; overall timeout is bounded to keep server resources predictable.
    for _ in range(90):
        await asyncio.sleep(2)
        status_response = await client.get(f"{FASHN_BASE_URL}/status/{prediction_id}")
        if status_response.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Could not read provider job status: {status_response.text[:600]}")
        status_body = status_response.json()
        status = status_body.get("status")
        if status == "completed":
            output = status_body.get("output") or []
            if not output:
                raise HTTPException(status_code=502, detail="Provider completed the job without an output image")
            return output[0]
        if status == "failed":
            error = status_body.get("error") or {}
            message = error.get("message", "Try-on generation failed")
            raise HTTPException(status_code=502, detail=message)
    raise HTTPException(status_code=504, detail="Virtual try-on timed out. Please try again with fewer items or a smaller image.")

@app.get("/api/health")
async def health():
    return {"ok": True, "provider_configured": bool(FASHN_API_KEY), "model": MODEL_NAME}

@app.post("/api/try-on", response_model=TryOnResponse)
async def try_on(payload: TryOnRequest):
    if not FASHN_API_KEY:
        raise HTTPException(status_code=503, detail="FASHN_API_KEY is not configured on the server. Add it to backend/.env.")
    if len(payload.garments) > MAX_GARMENTS:
        raise HTTPException(status_code=400, detail=f"Select no more than {MAX_GARMENTS} items per generation.")
    check_image_source(payload.person_image, "person_image")
    for garment in payload.garments:
        check_image_source(garment.image, f"{garment.name} image")

    # Provider's try-on endpoint applies one product image per prediction. For Whole Outfit,
    # chain predictions in order, using each generated result as the person image for the next item.
    current_image = payload.person_image
    processed = []
    headers = {"Authorization": f"Bearer {FASHN_API_KEY}", "Content-Type": "application/json"}
    timeout = httpx.Timeout(210.0, connect=20.0)
    async with httpx.AsyncClient(headers=headers, timeout=timeout) as client:
        for garment in payload.garments:
            current_image = await run_prediction(client, current_image, garment.image, payload.quality)
            processed.append(garment.name)

    return TryOnResponse(
        result_image=current_image,
        processed_items=processed,
        model=MODEL_NAME,
        note="Items were applied sequentially. Results can vary by garment order; use a clear full-body person photo and clean product images.",
    )
