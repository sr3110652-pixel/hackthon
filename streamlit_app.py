from io import BytesIO

import streamlit as st
from PIL import Image, UnidentifiedImageError

from app.main import analyze_image


MAX_IMAGE_BYTES = 10 * 1024 * 1024

st.set_page_config(page_title="Verdant | Crop Health", page_icon="+", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --ink: #17251f; --forest: #075c4b; --mint: #e2f7d7; --lime: #e4fa73; --coral: #ffae96; --sky: #dff5f6; --sun: #fff0a8; }
    .stApp { background: #fffdf4; color: var(--ink); }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { max-width: 1100px; padding: 3rem 3rem 4rem; }
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; color: var(--ink); letter-spacing: 0; }
    p, label, .stMarkdown, .stCaption { font-family: 'DM Sans', sans-serif; }
    .brand { display: flex; justify-content: space-between; align-items: end; border-bottom: 1px solid #cbd9cf; padding-bottom: 1.2rem; margin-bottom: 2.2rem; }
    .brand-mark { color: var(--forest); font: 700 1rem 'Space Grotesk', sans-serif; letter-spacing: .08em; text-transform: uppercase; }
    .brand-note { color: #607168; font: 500 .8rem 'DM Sans', sans-serif; text-transform: uppercase; letter-spacing: .08em; }
    .input-unit { color: #708177; font-weight: 500; }
    .hero h1 { font-size: clamp(2.4rem, 5vw, 4.6rem); line-height: .98; margin: 0; max-width: 700px; }
    .hero p { color: #5d6d64; font-size: 1.05rem; max-width: 570px; margin: 1.1rem 0 2.4rem; }
    .section-label { color: var(--forest); font: 700 .74rem 'DM Sans', sans-serif; letter-spacing: .12em; text-transform: uppercase; margin: .8rem 0 .4rem; }
    div[data-testid="stFileUploader"] { background: white; border: 1px dashed #7e9b87; border-radius: 12px; padding: .35rem; }
    div[data-testid="stFileUploader"] section { background: var(--mint); border-radius: 8px; }
    div[data-testid="stVerticalBlockBorderWrapper"] { border-color: #d4e1d7; border-radius: 12px; background: white; }
    .solution { background: var(--mint); color: var(--ink); border: 1px solid #b7d98b; border-radius: 10px; padding: 1.1rem 1.2rem; margin: 1.2rem 0 .8rem; }
    .solution strong { color: var(--forest); display: block; font: 700 .72rem 'DM Sans', sans-serif; letter-spacing: .12em; text-transform: uppercase; margin-bottom: .35rem; }
    .solution span { font: 600 1rem/1.45 'DM Sans', sans-serif; }
    .stButton > button { border-radius: 8px; min-height: 3rem; font-family: 'DM Sans', sans-serif; font-weight: 700; }
    div[data-testid="stMetric"] { background: #f3f9ed; border: 1px solid #d1e5b4; border-radius: 8px; padding: .7rem; }
    div[data-testid="stMetricLabel"] { color: #496458; }
    div[data-testid="stMetricValue"] { color: var(--forest); font-family: 'Space Grotesk', sans-serif; }
    .health-hero { display: flex; align-items: center; justify-content: space-between; gap: 1rem; background: var(--sun); border: 2px solid #e0c94d; border-radius: 14px; padding: 1.2rem 1.4rem; margin: .6rem 0 1rem; }
    .health-hero-label { color: #695b0a; font: 700 .75rem 'DM Sans', sans-serif; letter-spacing: .12em; text-transform: uppercase; }
    .health-hero-status { color: var(--ink); font: 700 1.8rem/1.1 'Space Grotesk', sans-serif; margin-top: .25rem; }
    .health-points { color: var(--forest); font: 700 2.8rem/.9 'Space Grotesk', sans-serif; white-space: nowrap; }
    .health-points small { color: #526a5c; font: 700 .75rem 'DM Sans', sans-serif; letter-spacing: .08em; text-transform: uppercase; }
    @media (max-width: 700px) { .block-container { padding: 2rem 1.1rem 3rem; } .brand-note { display: none; } .hero h1 { font-size: 2.7rem; } }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="brand"><div class="brand-mark">Verdant / Field Desk</div><div class="brand-note">Plant health intelligence</div></div>'
    '<div class="hero"><h1>Read the health of your crop.</h1><p>A quick field assessment combining leaf color with the conditions your plants are growing in.</p></div>',
    unsafe_allow_html=True,
)

st.markdown('<div class="section-label">01 / Growing conditions</div>', unsafe_allow_html=True)
condition_columns = st.columns(4)
with condition_columns[0]:
    st.markdown("**Soil type**")
    soil_type = st.selectbox("Soil type", ["Unknown", "Loamy", "Sandy", "Clay", "Silty", "Peaty"], label_visibility="collapsed")
with condition_columns[1]:
    st.markdown("**Temperature** <span class='input-unit'>(C)</span>", unsafe_allow_html=True)
    temperature = st.number_input("Temperature (C)", min_value=-20.0, max_value=60.0, value=25.0, step=0.5, label_visibility="collapsed")
with condition_columns[2]:
    st.markdown("**Soil pH**")
    soil_ph = st.number_input("Soil pH", min_value=0.0, max_value=14.0, value=6.5, step=0.1, label_visibility="collapsed")
with condition_columns[3]:
    st.markdown("**Humidity** <span class='input-unit'>(%)</span>", unsafe_allow_html=True)
    humidity = st.number_input("Humidity (%)", min_value=0.0, max_value=100.0, value=60.0, step=1.0, label_visibility="collapsed")

st.markdown('<div class="section-label">01A / Plant details</div>', unsafe_allow_html=True)
detail_columns = st.columns(3)
with detail_columns[0]:
    st.markdown("**Crop type**")
    crop_type = st.text_input("Crop type", placeholder="e.g. Tomato", label_visibility="collapsed") or "Unknown"
with detail_columns[1]:
    st.markdown("**Growth stage**")
    growth_stage = st.selectbox("Growth stage", ["Unknown", "Seedling", "Vegetative", "Flowering", "Fruiting", "Harvest"], label_visibility="collapsed")
with detail_columns[2]:
    st.markdown("**Watering**")
    watering_frequency = st.selectbox("Watering", ["Unknown", "Daily", "Every 2-3 days", "Weekly", "Rarely"], label_visibility="collapsed")

detail_columns = st.columns(3)
with detail_columns[0]:
    st.markdown("**Sunlight**")
    sunlight = st.selectbox("Sunlight", ["Unknown", "Low", "Partial", "Full sun"], label_visibility="collapsed")
with detail_columns[1]:
    st.markdown("**Fertilizer used**")
    fertilizer_used = st.selectbox("Fertilizer used", ["Unknown", "None", "Organic", "Chemical", "Both"], label_visibility="collapsed")
with detail_columns[2]:
    st.markdown("**Visible symptoms**")
    symptoms = st.text_input("Visible symptoms", placeholder="e.g. yellow spots, curling leaves", label_visibility="collapsed") or "None reported"

crop_confirmed = st.checkbox("I confirm the selected crop type matches the uploaded photo.")
if not crop_confirmed:
    st.caption("Crop type is used as context. The current color-based analyzer cannot identify tomato, chili, or other crop species automatically.")

st.markdown('<div class="section-label">02 / Crop photograph</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Choose a crop image",
    type=["jpg", "jpeg", "png", "webp", "bmp", "tiff"],
)

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()

    if len(file_bytes) > MAX_IMAGE_BYTES:
        st.error("Image must be 10 MB or smaller.")
    else:
        try:
            image = Image.open(BytesIO(file_bytes))
            image.verify()
            image = Image.open(BytesIO(file_bytes))
        except (Image.DecompressionBombError, UnidentifiedImageError, OSError, SyntaxError, ValueError):
            st.error("The uploaded file is not a valid image.")
        else:
            st.image(image, caption=uploaded_file.name, width="stretch")

            if st.button("Analyze crop", type="primary", width="stretch", disabled=not crop_confirmed):
                try:
                    result = analyze_image(
                        image,
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
                except (OSError, ValueError) as error:
                    st.error(f"Could not analyze this image: {error}")
                    st.stop()

                status_label = result["status"].replace("_", " ").title()
                st.markdown(
                    f'<div class="health-hero"><div><div class="health-hero-label">Plant health status</div><div class="health-hero-status">{status_label}</div></div><div class="health-points">{result["healthy_points"]}<small> / 10<br>healthy points</small></div></div>',
                    unsafe_allow_html=True,
                )

                points_column, score_column, confidence_column = st.columns(3)
                points_column.metric("Healthy points", f'{result["healthy_points"]}/10')
                score_column.metric("Health score", f'{result["health_score"]}/100')
                confidence_column.metric("Confidence", f'{result["confidence"]:.0%}')
                st.progress(result["health_score"] / 100)

                signal_column, damage_column = st.columns(2)
                signal_column.metric("Green coverage", f'{result["signals"]["green_coverage"]:.1%}')
                damage_column.metric("Damage coverage", f'{result["signals"]["damage_coverage"]:.1%}')

                st.markdown(
                    f'<div class="solution"><strong>Recommended solution</strong><span>{result["solution"]}</span></div>',
                    unsafe_allow_html=True,
                )

                if result["concerns"]:
                    for concern in result["concerns"]:
                        st.warning(concern)
                st.info(result["recommendation"])