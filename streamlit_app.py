from io import BytesIO

import streamlit as st
from PIL import Image, UnidentifiedImageError

from app.main import analyze_image


st.set_page_config(page_title="Crop Health Check", page_icon="+", layout="centered")

st.title("Crop Health Check")
st.write("Upload a crop photo and enter its growing conditions for a combined estimate.")

soil_type = st.selectbox("Soil type", ["Unknown", "Loamy", "Sandy", "Clay", "Silty", "Peaty"])
temperature = st.number_input("Temperature (C)", min_value=-20.0, max_value=60.0, value=25.0, step=0.5)
soil_ph = st.number_input("Soil pH", min_value=0.0, max_value=14.0, value=6.5, step=0.1)
humidity = st.number_input("Humidity (%)", min_value=0.0, max_value=100.0, value=60.0, step=1.0)

uploaded_file = st.file_uploader(
    "Choose a crop image",
    type=["jpg", "jpeg", "png", "webp", "bmp", "tiff"],
)

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()

    try:
        image = Image.open(BytesIO(file_bytes))
        image.verify()
        image = Image.open(BytesIO(file_bytes))
    except (UnidentifiedImageError, OSError):
        st.error("The uploaded file is not a valid image.")
    else:
        st.image(image, caption=uploaded_file.name, use_container_width=True)

        if st.button("Analyze crop", type="primary", use_container_width=True):
            result = analyze_image(image, soil_type, temperature, soil_ph, humidity)
            st.subheader(result["status"].replace("_", " ").title())

            points_column, score_column, confidence_column = st.columns(3)
            points_column.metric("Healthy points", f'{result["healthy_points"]}/10')
            score_column.metric("Health score", f'{result["health_score"]}/100')
            confidence_column.metric("Confidence", f'{result["confidence"]:.0%}')
            st.progress(result["health_score"] / 100)

            signal_column, damage_column = st.columns(2)
            signal_column.metric("Green coverage", f'{result["signals"]["green_coverage"]:.1%}')
            damage_column.metric("Damage coverage", f'{result["signals"]["damage_coverage"]:.1%}')

            st.write("**Solution:**", result["solution"])

            if result["concerns"]:
                for concern in result["concerns"]:
                    st.warning(concern)
            st.info(result["recommendation"])