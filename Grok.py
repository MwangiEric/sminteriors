# app.py — Streamlit Pro Layout Editor (Drag + Sliders + Upload)
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io

st.set_page_config(page_title="SM Interiors Layout Editor", layout="centered")
st.title("SM Interiors — Pro Reel Layout Editor")
st.caption("Drag • Resize • Upload • Real-time 1080×1920 preview")

# Initialize session state
if "elements" not in st.session_state:
    st.session_state.elements = {
        "sofa":  {"x": 540, "y": 900, "w": 860, "h": 860, "img": None},
        "logo":  {"x": 100, "y": 100, "w": 200, "h": 100, "img": None},
        "hook":  {"x": 540, "y": 300, "text": "This Sold Out in 24 Hours", "size": 100},
        "price": {"x": 540, "y": 1460,"text": "Ksh 94,900", "size": 120},
        "cta":   {"x": 540, "y": 1700,"text": "DM 0710 895 737", "size": 90},
    }

el = st.session_state.elements

# Uploads
col1, col2 = st.columns(2)
with col1:
    sofa_file = st.file_uploader("Upload Sofa Photo", type=["png","jpg","jpeg"])
    if sofa_file:
        img = Image.open(sofa_file).convert("RGBA")
        img = img.resize((el["sofa"]["w"], el["sofa"]["h"]), Image.LANCZOS)
        el["sofa"]["img"] = img
with col2:
    logo_file = st.file_uploader("Upload Logo", type=["png","jpg","jpeg"])
    if logo_file:
        img = Image.open(logo_file).convert("RGBA")
        img = img.resize((el["logo"]["w"], el["logo"]["h"]), Image.LANCZOS)
        el["logo"]["img"] = img

# Sliders
st.subheader("Resize Everything")
c1, c2, c3 = st.columns(3)
with c1:
    el["sofa"]["w"] = st.slider("Sofa Width", 400, 1000, el["sofa"]["w"], 10)
    el["sofa"]["h"] = st.slider("Sofa Height", 400, 1400, el["sofa"]["h"], 10)
    if el["sofa"]["img"]:
        el["sofa"]["img"] = el["sofa"]["img"].resize((el["sofa"]["w"], el["sofa"]["h"]), Image.LANCZOS)
with c2:
    el["logo"]["w"] = st.slider("Logo Width", 100, 400, el["logo"]["w"], 10)
    el["logo"]["h"] = st.slider("Logo Height", 50, 300, el["logo"]["h"], 10)
    if el["logo"]["img"]:
        el["logo"]["img"] = el["logo"]["img"].resize((el["logo"]["w"], el["logo"]["h"]), Image.LANCZOS)
with c3:
    el["hook"]["size"] = st.slider("Hook Size", 60, 180, el["hook"]["size"])
    el["price"]["size"] = st.slider("Price Size", 80, 200, el["price"]["size"])
    el["cta"]["size"] = st.slider("CTA Size", 60, 140, el["cta"]["size"])

# Canvas with drag
canvas_result = st_canvas(
    fill_color="rgba(255, 215, 0, 0.1)",
    stroke_width=0,
    background_color="#0F0A05",
    background_image=None,
    update_streamlit=True,
    height=960,
    width=540,
    drawing_mode="rect",
    key="canvas",
)

# Draw everything
bg = Image.new("RGB", (1080, 1920), (15,10,5))
draw = ImageDraw.Draw(bg)

# Gold rings
for r in [500, 750, 1000]:
    draw.ellipse([540-r, 960-r, 540+r, 960+r], outline=(255,215,0), width=6)

# Sofa
if el["sofa"]["img"]:
    x = el["sofa"]["x"] - el["sofa"]["w"]//2
    y = el["sofa"]["y"] - el["sofa"]["h"]//2
    bg.paste(el["sofa"]["img"], (x, y), el["sofa"]["img"])

# Logo
if el["logo"]["img"]:
    bg.paste(el["logo"]["img"], (el["logo"]["x"], el["logo"]["y"]), el["logo"]["img"])

# Text
for name in ["hook", "price", "cta"]:
    text = el[name]["text"]
    size = el[name]["size"]
    try:
        font = ImageFont.truetype("arialbd.ttf", size)
    except:
        font = ImageFont.load_default()
    w = draw.textlength(text, font=font)
    x = el[name]["x"] - w//2
    y = el[name]["y"] - size//2
    draw.text((x, y), text, fill=(255,255,255), font=font,
              stroke_width=6, stroke_fill=(0,0,0))

# Display
st.image(bg.resize((540,960)), use_column_width=True)

# Drag logic (from canvas clicks)
if canvas_result.json_data:
    objects = canvas_result.json_data["objects"]
    if objects:
        obj = objects[-1]
        if obj["type"] == "rect":
            name = st.selectbox("Move which element?", ["sofa", "logo", "hook", "price", "cta"])
            el[name]["x"] = int(obj["left"] * 2 + obj["width"])
            el[name]["y"] = int(obj["top"] * 2 + obj["height"]//2)
            st.experimental_rerun()

# Final output
if st.button("PRINT FINAL LAYOUT CODE"):
    st.code(f"elements = {st.session_state.elements}", language="python")
    st.success("Copy this into your Reel generator → perfect every time")

st.caption("You now control pixels like a pro. Charge Ksh 80,000 per Reel.")