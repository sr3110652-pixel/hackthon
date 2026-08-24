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
    :root { --ink: #17231d; --forest: #174d3c; --mint: #dff3e8; --lime: #b9e769; --coral: #ef8066; --sky: #dcecf2; }
    .stApp { background: #f7faf7; color: var(--ink); }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { max-width: 1100px; padding: 3rem 3rem 4rem; }
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; color: var(--ink); letter-spacing: 0; }
    p, label, .stMarkdown, .stCaption { font-family: 'DM Sans', sans-serif; }
    .brand { display: flex; justify-content: space-between; align-items: end; border-bottom: 1px solid #cbd9cf; padding-bottom: 1.2rem; margin-bottom: 2.2rem; }
    .brand-mark { color: var(--forest); font: 700 1rem 'Space Grotesk', sans-serif; letter-spacing: .08em; text-transform: uppercase; }
    .brand-note { color: #607168; font: 500 .8rem 'DM Sans', sans-serif; text-transform: uppercase; letter-spacing: .08em; }
    .hero h1 { font-size: clamp(2.4rem, 5vw, 4.6rem); line-height: .98; margin: 0; max-width: 700px; }
    .hero p { color: #5d6d64; font-size: 1.05rem; max-width: 570px; margin: 1.1rem 0 2.4rem; }
    .section-label { color: var(--forest); font: 700 .74rem 'DM Sans', sans-serif; letter-spacing: .12em; text-transform: uppercase; margin: .8rem 0 .4rem; }
    div[data-testid="stFileUploader"] { background: white; border: 1px dashed #7e9b87; border-radius: 12px; padding: .35rem; }
    div[data-testid="stFileUploader"] section { background: var(--mint); border-radius: 8px; }
    div[data-testid="stVerticalBlockBorderWrapper"] { border-color: #d4e1d7; border-radius: 12px; background: white; }
    .result-heading { display: flex; align-items: center; justify-content: space-between; gap: 1rem; margin: .4rem 0 1rem; }
    .result-heading h2 { margin: 0; font-size: 1.8rem; }
    .status-pill { border-radius: 999px; padding: .45rem .8rem; background: var(--lime); color: #203313; font: 700 .75rem 'DM Sans', sans-serif; text-transform: uppercase; letter-spacing: .08em; }
    .solution { background: var(--forest); color: white; border-radius: 10px; padding: 1rem 1.1rem; margin: 1.2rem 0 .8rem; }
    .solution strong { color: var(--lime); display: block; font: 700 .72rem 'DM Sans', sans-serif; letter-spacing: .12em; text-transform: uppercase; margin-bottom: .35rem; }
    .solution span { font: 500 1rem/1.45 'DM Sans', sans-serif; }
    .stButton > button { border-radius: 8px; min-height: 3rem; font-family: 'DM Sans', sans-serif; font-weight: 700; }
    div[data-testid="stMetric"] { background: #f3f7f3; border-radius: 8px; padding: .7rem; }
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
soil_type = condition_columns[0].selectbox("Soil type", ["Unknown", "Loamy", "Sandy", "Clay", "Silty", "Peaty"])
temperature = condition_columns[1].number_input("Temperature (C)", min_value=-20.0, max_value=60.0, value=25.0, step=0.5)
soil_ph = condition_columns[2].number_input("Soil pH", min_value=0.0, max_value=14.0, value=6.5, step=0.1)
humidity = condition_columns[3].number_input("Humidity (%)", min_value=0.0, max_value=100.0, value=60.0, step=1.0)

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
        except (UnidentifiedImageError, OSError):
            st.error("The uploaded file is not a valid image.")
        else:
            st.image(image, caption=uploaded_file.name, width="stretch")

            if st.button("Analyze crop", type="primary", width="stretch"):
                try:
                    result = analyze_image(image, soil_type, temperature, soil_ph, humidity)
                except (OSError, ValueError) as error:
                    st.error(f"Could not analyze this image: {error}")
                    st.stop()

                status_label = result["status"].replace("_", " ").title()
                status_style = ""
                if result["status"] == "unhealthy":
                    status_style = ' style="background: #f6c4b7; color: #6f2417;"'
                elif result["status"] == "mild_health":
                    status_style = ' style="background: #f7df98; color: #604b0b;"'
                st.markdown(
                    f'<div class="result-heading"><h2>{status_label}</h2><div class="status-pill"{status_style}>{result["healthy_points"]}/10 points</div></div>',
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