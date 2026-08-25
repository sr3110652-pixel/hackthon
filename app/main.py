from io import BytesIO
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError


MAX_IMAGE_BYTES = 10 * 1024 * 1024

app = FastAPI(
    title="Crop Health API",
    description="Estimates visible crop health from an uploaded image.",
    version="1.0.0",
)


def analyze_image(
    image: Image.Image,
    soil_type: str = "Unknown",
    temperature: float | None = None,
    soil_ph: float | None = None,
    humidity: float | None = None,
    crop_type: str = "Unknown",
    growth_stage: str = "Unknown",
    watering_frequency: str = "Unknown",
    sunlight: str = "Unknown",
    fertilizer_used: str = "Unknown",
    symptoms: str = "None reported",
) -> dict[str, Any]:
    """Estimate crop health from image and farmer-provided growing conditions."""
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
    image_points = round(min(10.0, green_coverage * 10))
    environmental_concerns = []
    if temperature is not None and not 15 <= temperature <= 35:
        environmental_concerns.append("Temperature is outside the general 15-35 C crop range.")
    if soil_ph is not None and not 5.5 <= soil_ph <= 7.5:
        environmental_concerns.append("Soil pH is outside the general 5.5-7.5 crop range.")
    if humidity is not None and not 40 <= humidity <= 80:
        environmental_concerns.append("Humidity is outside the general 40-80% crop range.")

    healthy_points = max(0, image_points - len(environmental_concerns))
    growing_conditions = {
        "soil_type": soil_type,
        "temperature_c": temperature,
        "soil_ph": soil_ph,
        "humidity_percent": humidity,
        "crop_type": crop_type,
        "growth_stage": growth_stage,
        "watering_frequency": watering_frequency,
        "sunlight": sunlight,
        "fertilizer_used": fertilizer_used,
        "symptoms": symptoms,
        "crop_type_verification": "not_available_with_color_analysis",
    }

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
        concerns.extend(environmental_concerns)

        if healthy_points >= 8:
            status = "healthy"
            recommendation = "The crop looks healthy. Continue regular monitoring."
        elif healthy_points >= 6:
            status = "mild_health"
            recommendation = "Inspect the leaves closely and check watering, pests, and nutrient levels."
        else:
            status = "unhealthy"
            recommendation = "Inspect the crop promptly and consult an agronomist if symptoms persist."

    solution = recommendation
    if environmental_concerns:
        solution += " " + " ".join(environmental_concerns)
    if soil_type != "Unknown":
        solution += f" Confirm that the {soil_type.lower()} soil drains well and matches the crop's needs."
    if symptoms != "None reported":
        solution += f" Monitor the reported symptoms: {symptoms}."

    return {
        "status": status,
        "confidence": confidence,
        "health_score": score,
        "healthy_points": healthy_points,
        "image_points": image_points,
        "growing_conditions": growing_conditions,
        "image": {"width": width, "height": height, "format": image.format},
        "signals": {
            "green_coverage": round(green_coverage, 3),
            "damage_coverage": round(damage_coverage, 3),
            "other_coverage": round(other_coverage, 3),
        },
        "concerns": concerns,
        "recommendation": recommendation,
        "solution": solution,
    }


@app.get("/health")
def service_health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/crop-health")
async def crop_health(
    image: UploadFile = File(...),
    soil_type: str = Form("Unknown"),
    temperature: float | None = Form(None),
    soil_ph: float | None = Form(None),
    humidity: float | None = Form(None),
    crop_type: str = Form("Unknown"),
    growth_stage: str = Form("Unknown"),
    watering_frequency: str = Form("Unknown"),
    sunlight: str = Form("Unknown"),
    fertilizer_used: str = Form("Unknown"),
    symptoms: str = Form("None reported"),
) -> dict[str, Any]:
    if image.content_type and not image.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="The uploaded file must be an image.")

    contents = await image.read(MAX_IMAGE_BYTES + 1)
    if len(contents) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 10 MB or smaller.")

    try:
        uploaded_image = Image.open(BytesIO(contents))
        uploaded_image.verify()
        uploaded_image = Image.open(BytesIO(contents))
    except (Image.DecompressionBombError, UnidentifiedImageError, OSError, SyntaxError, ValueError):
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid image.")

    return analyze_image(
        uploaded_image,
        soil_type,
        temperature,
        soil_ph,
        humidity,
        crop_type,
        growth_stage,
        watering_frequency,
        sunlight,
        fertilizer_used,
        symptoms,
    )