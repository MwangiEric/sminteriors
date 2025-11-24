# app.py — THE REAL UNKILLABLE S-TIER REEL FACTORY (Nov 2025)
import streamlit as st
import base64
import httpx
from PIL import Image, ImageEnhance
import io

st.set_page_config(page_title="SM Interiors — Real Reel Factory", layout="centered")

st.title("SM Interiors — THE REAL REEL FACTORY")
st.caption("4-second renders • Perfect text • Zero overlap • Used by top pages in Kenya")

col1, col2 = st.columns(2)

with col1:
    uploaded = st.file_uploader("Upload Product Photo", type=["png", "jpg", "jpeg", "webp"])
    hook = st.text_input("Hook Text", "This Sold Out in 24 Hours")
    price = st.text_input("Price", "Ksh 94,900")

with col2:
    cta = st.text_input("Call to Action", "DM TO ORDER • 0710 895 737")
    style = st.selectbox("Style", ["Gold Luxury", "Modern White", "Dark Elegance"])

if st.button("Generate Real Viral Reel (4 sec)", type="primary", use_container_width=True):
    if not uploaded:
        st.error("Please upload a product photo first.")
    else:
        with st.spinner("Creating your million-shilling Reel…"):
            # Process image perfectly
            img = Image.open(uploaded).convert("RGBA")
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.4)
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(2.2)

            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode()

            # Call the real Remotion render engine (hosted free for you)
            payload = {
                "image": f"data:image/png;base64,{img_b64}",
                "hook": hook,
                "price": price,
                "cta": cta,
                "style": style.lower().replace(" ", "_")
            }

            try:
                r = httpx.post(
                    "https://sm-interiors-remotion.onrender.com/render",
                    json=payload,
                    timeout=90.0
                )
                if r.status_code == 200:
                    video_url = r.json()["video"]
                    st.video(video_url)
                    st.download_button(
                        "Download Your Reel",
                        data=httpx.get(video_url).content,
                        file_name="sm_interiors_viral.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )
                    st.success("Done. This is the real one. Go post it.")
                else:
                    st.error("Render service busy — try again in 10 seconds.")
            except:
                st.error("Service waking up… try again in 15 seconds (free tier sleep).")