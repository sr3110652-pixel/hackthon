from io import BytesIO

import streamlit as st
from PIL import Image, UnidentifiedImageError

from app.main import analyze_image


st.set_page_config(page_title="Crop Health Check", page_icon="+", layout="centered")

st.title("Crop Health Check")
st.write("Upload a clear crop photo to estimate visible plant health.")

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
            result = analyze_image(image)
            st.subheader(result["status"].replace("_", " ").title())

            points_column, score_column, confidence_column = st.columns(3)
            points_column.metric("Healthy points", f'{result["healthy_points"]}/10')
            score_column.metric("Health score", f'{result["health_score"]}/100')
            confidence_column.metric("Confidence", f'{result["confidence"]:.0%}')
            st.progress(result["health_score"] / 100)

            signal_column, damage_column = st.columns(2)
            signal_column.metric("Green coverage", f'{result["signals"]["green_coverage"]:.1%}')
            damage_column.metric("Damage coverage", f'{result["signals"]["damage_coverage"]:.1%}')

            if result["concerns"]:
                for concern in result["concerns"]:
                    st.warning(concern)
            st.info(result["recommendation"])