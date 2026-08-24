from io import BytesIO
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError


MAX_IMAGE_BYTES = 10 * 1024 * 1024

app = FastAPI(
    title="Crop Health API",
    description="Estimates visible crop health from an uploaded image.",
    version="1.0.0",
)


def analyze_image(image: Image.Image) -> dict[str, Any]:
    """Estimate crop health from broad color signals in an image."""
    rgb_image = image.convert("RGB")
    width, height = rgb_image.size
    total_pixels = width * height
    green_pixels = 0
    damage_pixels = 0

    for red, green, blue in rgb_image.getdata():
        is_green = green >= 30 and green > red * 1.05 and green > blue * 1.05
        is_brown = red > green * 1.15 and red > blue * 1.15
        is_yellow = red > 100 and green > 100 and blue < 100
        green_pixels += is_green
        damage_pixels += (is_brown or is_yellow) and not is_green

    green_coverage = green_pixels / total_pixels
    damage_coverage = min(damage_pixels / total_pixels, 1.0)
    other_coverage = max(0.0, 1.0 - green_coverage - damage_coverage)
    healthy_points = round(min(10.0, green_coverage * 10))

    if green_coverage < 0.05:
        status = "unhealthy"
        score = 0
        confidence = 0.2
        concerns = ["The image does not contain enough visible healthy vegetation."]
        recommendation = "The plant appears unhealthy. Inspect it and check watering, pests, and nutrient levels."
    else:
        score = round(max(0.0, min(100.0, green_coverage * 100 - damage_coverage * 75)))
        confidence = round(min(0.95, max(0.35, green_coverage + damage_coverage)), 2)
        concerns = []
        if damage_coverage >= 0.2:
            concerns.append("Large areas show brown or yellow discoloration.")
        elif damage_coverage >= 0.08:
            concerns.append("Some brown or yellow discoloration is visible.")

        if healthy_points >= 8:
            status = "healthy"
            recommendation = "The crop looks healthy. Continue regular monitoring."
        elif healthy_points >= 6:
            status = "mild_health"
            recommendation = "Inspect the leaves closely and check watering, pests, and nutrient levels."
        else:
            status = "unhealthy"
            recommendation = "Inspect the crop promptly and consult an agronomist if symptoms persist."

    return {
        "status": status,
        "confidence": confidence,
        "health_score": score,
        "healthy_points": healthy_points,
        "image": {"width": width, "height": height, "format": image.format},
        "signals": {
            "green_coverage": round(green_coverage, 3),
            "damage_coverage": round(damage_coverage, 3),
            "other_coverage": round(other_coverage, 3),
        },
        "concerns": concerns,
        "recommendation": recommendation,
    }


@app.get("/health")
def service_health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/crop-health")
async def crop_health(image: UploadFile = File(...)) -> dict[str, Any]:
    if image.content_type and not image.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="The uploaded file must be an image.")

    contents = await image.read(MAX_IMAGE_BYTES + 1)
    if len(contents) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 10 MB or smaller.")

    try:
        uploaded_image = Image.open(BytesIO(contents))
        uploaded_image.verify()
        uploaded_image = Image.open(BytesIO(contents))
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid image.")

    return analyze_image(uploaded_image)