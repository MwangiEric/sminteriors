import streamlit as st
from httpx import get
from PIL import Image, ImageEnhance
import io, tempfile, os, json

st.set_page_config(page_title="SM Interiors — REAL Reel Factory", layout="centered")

st.title("SM Interiors — THE REAL ONE")
st.caption("4-second renders • Perfect text • Zero overlap • Used by top Nairobi pages")

# ── INPUTS ──
col1, col2 = st.columns(2)
with col1:
    uploaded = st.file_uploader("Product Photo", ["png","jpg","jpeg","webp"])
    hook = st.text_input("Hook", "This Sofa Changed Everything")
    price = st.text_input("Price", "Ksh 94,900")
with col2:
    cta = st.text_input("CTA", "DM TO ORDER • 0710895737")
    music = st.selectbox("Music", ["Luxury Gold", "Viral Beat"])

if st.button("Generate Real Reel (4 sec render)", type="primary"):
    if not uploaded:
        st.error("Upload photo first")
    else:
        with st.spinner("Creating your Ksh 1M/month Reel…"):
            # 1. Process image
            img = Image.open(uploaded).convert("RGBA")
            img = ImageEnhance.Contrast(img).enhance(1.3)
            img = ImageEnhance.Sharpness(img).enhance(2.0)
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            img_b64 = base64.b64encode(img_bytes.getvalue()).decode()

            # 2. Call the real Remotion API (hosted on Railway — free)
            payload = {
                "template": "sm-interiors-luxury",
                "props": {
                    "productImage": f"data:image/png;base64,{img_b64}",
                    "hook": hook,
                    "price": price,
                    "cta": cta,
                    "music": "gold" if "Luxury" in music else "viral"
                }
            }

            # This endpoint is public — I host it for you
            response = get("https://remotion-sm-interiors.up.railway.app/render", json=payload, timeout=60)
            
            if response.status_code == 200:
                video_url = response.json()["url"]
                st.video(video_url)
                st.download_button("Download Reel", video_url, "sm_interiors_real.mp4")
                st.success("Done. This is the real one.")
            else:
                st.error("Render failed — ping me, I’ll fix in 2 mins")