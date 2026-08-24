# Crop Health API

A small backend that accepts a crop photo and returns an estimated health status and healthy points from 0 to 10.
The current analyzer is a lightweight baseline based on visible green, brown, and
yellow pixel coverage. Healthy points use these thresholds: 8-10 is healthy, 6-7
is mild health and needs care, and 0-5 is unhealthy. It is intended as a working
API contract that can later be backed by a trained crop-disease model.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The interactive API documentation is available at `http://localhost:8000/docs`.

## Analyze an image

```bash
curl -X POST http://localhost:8000/api/crop-health \
	-F "image=@/path/to/crop.jpg"
```

Example response:

```json
{
	"status": "healthy",
	"confidence": 0.84,
	"health_score": 84,
	"healthy_points": 8,
	"growing_conditions": {"soil_type": "Loamy", "temperature_c": 25, "soil_ph": 6.5, "humidity_percent": 60},
	"image": {"width": 1280, "height": 720, "format": "JPEG"},
	"signals": {"green_coverage": 0.91, "damage_coverage": 0.03},
	"concerns": [],
	"recommendation": "The crop looks healthy. Continue regular monitoring.",
	"solution": "The crop looks healthy. Continue regular monitoring. Confirm that the loamy soil drains well and matches the crop's needs."
}
```

The Streamlit screen asks the farmer for soil type, temperature, soil pH, and
humidity. Temperature, pH, and humidity outside the general crop ranges reduce
healthy points and are included in the solution.

It also accepts optional crop type, growth stage, watering frequency, sunlight,
fertilizer use, and visible symptoms. These details are returned with the result
and used to make the solution more specific without changing the health score.

The endpoint accepts common image formats supported by Pillow and rejects files
larger than 10 MB. This baseline should not be treated as a definitive diagnosis.

## Run with Streamlit

```bash
streamlit run streamlit_app.py
```

Streamlit provides a browser-based upload and results screen and calls the same
analyzer directly, so the FastAPI server is not required for this mode.