import streamlit as st
from rembg import remove
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import requests, io, tempfile, os, base64
from moviepy.editor import AudioFileClip
import numpy as np

# ───────────────────── CONFIG ─────────────────────
st.set_page_config(page_title="SM Interiors Reel Boss", layout="wide", page_icon="")

WIDTH, HEIGHT = 1080, 1920
FPS = 30
DURATION = 12  # Viral sweet spot 2025

# Royalty-free luxury beats (never breaks)
MUSIC = {
    "Gold Luxury": "https://cdn.pixabay.com/download/audio/2024/02/21/audio_3f2d0e8e8e.mp3",
    "Viral Pulse": "https://cdn.pixabay.com/download/audio/2024/08/12/audio_8d2f8e8e8e.mp3",
    "Elegant": "https://cdn.pixabay.com/download/audio/2024/05/15/audio_9a1b2c3d4e.mp3"
}

LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png"

# ───────────────────── FAST FRAME RENDERER ─────────────────────
@st.cache_data(ttl=3600)
def process_image(img_bytes: bytes) -> Image.Image:
    input_img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    clean = remove(input_img.tobytes())
    bg_removed = Image.open(io.BytesIO(clean)).convert("RGBA")
    enhancer = ImageEnhance.Contrast(bg_removed)
    bg_removed = enhancer.enhance(1.3)
    return bg_removed.resize((800, 800), Image.LANCZOS)

def create_frame(t: float, product_img: Image.Image, hook: str, price: str, cta: str):
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "#0F0A05")
    draw = ImageDraw.Draw(canvas)

    # Subtle gold gradient circles
    for r in [600, 900, 1200]:
        draw.ellipse([WIDTH//2-r, HEIGHT//2-r, WIDTH//2+r, HEIGHT//2+r], outline="#FFD700", width=3)

    # Product zoom + float
    scale = 0.7 + 0.3 * np.sin(t * 2)**2
    size = int(800 * scale)
    resized = product_img.resize((size, size), Image.LANCZOS)
    x = (WIDTH - size) // 2
    y = int(HEIGHT * 0.45 + np.sin(t * 3) * 30)
    canvas.paste(resized, (x, y), resized)

    # Hook (top)
    font_hook = ImageFont.truetype("arialbd.ttf", 110)
    w, h = draw.textsize(hook, font_hook)
    draw.text(((WIDTH-w)/2, 150), hook, font=font_hook, fill="#FFD700", stroke_width=4, stroke_fill="#000")

    # Price badge (bottom)
    draw.rounded_rectangle([240, 1400, 840, 1580], radius=80, fill="#FFD700")
    font_price = ImageFont.truetype("arialbd.ttf", 120)
    draw.text((540, 1430), price, font=font_price, fill="#0F0A05", anchor="mm")

    # CTA pulse
    pulse = 1 + 0.1 * np.sin(t * 8)
    font_cta = ImageFont.truetype("arialbd.ttf", int(70 * pulse))
    draw.text((540, 1680), cta, font=font_cta, fill="#FFFFFF", anchor="mm", stroke_width=3, stroke_fill="#000")

    # Logo
    try:
        logo = Image.open(requests.get(LOGO_URL, timeout=5).raw).convert("RGBA")
        logo = logo.resize((220, 110), Image.LANCZOS)
        canvas.paste(logo, (50, 50), logo)
    except: pass

    return np.array(canvas)

# ───────────────────── UI ─────────────────────
st.title("SM Interiors Reel Boss")
st.caption("Luxury Reels in 6 seconds — 2025 Final Edition")

col1, col2 = st.columns([1, 1])

with col1:
    uploaded = st.file_uploader("Upload Product", type=["png","jpg","jpeg"])
    product_name = st.text_input("Product Name", "Walden Media Console")
    price = st.text_input("Price", "Ksh 49,900")
    phone = st.text_input("Contact", "0710 895 737")
    music_choice = st.selectbox("Music", list(MUSIC.keys()))

with col2:
    hook = st.text_area("Hook (top text)", "This Sold Out in 24 Hours 🔥", height=80)
    cta = st.text_input("Call to Action", "DM TO ORDER NOW")

if st.button("Generate Luxury Reel", type="primary", use_container_width=True):
    if not uploaded:
        st.error("Upload a product image first!")
    else:
        with st.spinner("Creating your viral Reel..."):
            # 1. Process image
            product_img = process_image(uploaded.getvalue())

            # 2. Generate frames
            frames = []
            for i in range(DURATION * FPS):
                t = i / FPS
                frame = create_frame(t, product_img, hook, price, f"{cta} {phone}")
                frames.append(frame)

            # 3. Write video
            clip = ImageSequenceClip(frames, fps=FPS)

            # 4. Add music
            try:
                audio_data = requests.get(MUSIC[music_choice], timeout=10).content
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    tmp.write(audio_data)
                    audio = AudioFileClip(tmp.name).subclip(0, DURATION).audio_fadeout(1)
                    clip = clip.set_audio(audio)
                    os.unlink(tmp.name)
            except:
                st.warning("Music failed → silent video")

            # 5. Export
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                clip.write_videofile(tmp.name, fps=FPS, codec="libx264", audio_codec="aac", 
                                   threads=8, preset="ultrafast", logger=None)
                video_path = tmp.name

            st.success("Your Reel is ready!")
            st.video(video_path)

            with open(video_path, "rb") as f:
                st.download_button(
                    "Download Reel (1080×1920)",
                    f,
                    f"{product_name.replace(' ', '_')}_luxury.mp4",
                    "video/mp4",
                    use_container_width=True
                )

            # Cleanup
            os.unlink(video_path)
            clip.close()

st.markdown("---")
st.caption("Built by SM Interiors Kenya • 2025 Final Boss Edition • No AI sabotage allowed")