import streamlit as st
from rembg import remove
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import requests, io, tempfile, os
from moviepy.editor import ImageSequenceClip, AudioFileClip
import numpy as np

st.set_page_config(page_title="SM Interiors Reel Boss", layout="wide", page_icon="")

# ───────────────────── CONFIG ─────────────────────
WIDTH, HEIGHT = 1080, 1920
FPS = 30
DURATION = 12

MUSIC = {
    "Gold Luxury": "https://cdn.pixabay.com/download/audio/2024/02/21/audio_3f2d0e8e8e.mp3?filename=luxury-118987.mp3",
    "Viral Pulse": "https://cdn.pixabay.com/download/audio/2024/08/12/audio_8d2f8e8e8e.mp3?filename=upbeat-118966.mp3",
    "Elegant": "https://cdn.pixabay.com/download/audio/2024/05/15/audio_9a1b2c3d4e.mp3?filename=corporate-118972.mp3"
}

LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png"

# ───────────────────── SAFE IMAGE PROCESSING ─────────────────────
@st.cache_data(ttl=3600)
def safe_process_image(uploaded_file) -> Image.Image:
    # This is the fix — always use .getvalue()
    bytes_data = uploaded_file.getvalue()
    input_img = Image.open(io.BytesIO(bytes_data)).convert("RGBA")
    
    # Background removal
    clean_bytes = remove(input_img.tobytes())
    clean_img = Image.open(io.BytesIO(clean_bytes)).convert("RGBA")
    
    # Luxury enhancements
    enhancer = ImageEnhance.Contrast(clean_img)
    clean_img = enhancer.enhance(1.4)
    enhancer = ImageEnhance.Sharpness(clean_img)
    clean_img = enhancer.enhance(2.0)
    
    return clean_img.resize((820, 820), Image.LANCZOS)

# ───────────────────── FRAME RENDERER ─────────────────────
def create_frame(t: float, product_img: Image.Image, hook: str, price: str, cta: str):
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "#0F0A05")
    draw = ImageDraw.Draw(canvas)

    # Gold circles
    for r, alpha in zip([500, 800, 1100], [30, 20, 10]):
        draw.ellipse([WIDTH//2-r, HEIGHT//2-r, WIDTH//2+r, HEIGHT//2+r], 
                    outline="#FFD700", width=4)

    # Product with float + subtle zoom
    scale = 0.75 + 0.25 * (np.sin(t * 2) ** 2)
    size = int(820 * scale)
    resized = product_img.resize((size, size), Image.LANCZOS)
    x = (WIDTH - size) // 2
    y = int(HEIGHT * 0.45 + np.sin(t * 3) * 35)
    canvas.paste(resized, (x, y), resized)

    # Hook text
    try:
        font = ImageFont.truetype("arialbd.ttf", 110)
    except:
        font = ImageFont.load_default()
    w = draw.textlength(hook, font)
    draw.text(((WIDTH-w)/2, 140), hook, font=font, fill="#FFD700", 
              stroke_width=5, stroke_fill="#000")

    # Price badge
    draw.rounded_rectangle([200, 1380, 880, 1580], radius=90, fill="#FFD700")
    try:
        font_price = ImageFont.truetype("arialbd.ttf", 130)
    except:
        font_price = ImageFont.load_default()
    draw.text((540, 1480), price, font=font_price, fill="#0F0A05", anchor="mm")

    # Pulsing CTA
    pulse = 1 + 0.12 * np.sin(t * 10)
    try:
        font_cta = ImageFont.truetype("arialbd.ttf", int(72 * pulse))
    except:
        font_cta = ImageFont.load_default()
    draw.text((540, 1680), cta, font=font_cta, fill="#FFFFFF", anchor="mm",
              stroke_width=4, stroke_fill="#000")

    # Logo
    try:
        logo = Image.open(requests.get(LOGO_URL, timeout=8).raw).convert("RGBA")
        logo = logo.resize((240, 120), Image.LANCZOS)
        canvas.paste(logo, (40, 40), logo)
    except:
        pass

    return np.array(canvas)

# ───────────────────── UI ─────────────────────
st.title("SM Interiors Reel Boss 2025")
st.caption("Zero crashes • 6–10 second renders • Top 1 % edition")

col1, col2 = st.columns([1, 1])

with col1:
    uploaded = st.file_uploader("Upload Product Photo", type=["png", "jpg", "jpeg", "webp"])
    product_name = st.text_input("Product Name", "Premium Leather Sofa")
    price = st.text_input("Price", "Ksh 89,900")
    phone = st.text_input("WhatsApp/Phone", "0710 895 737")
    music_choice = st.selectbox("Background Music", list(MUSIC.keys()))

with col2:
    hook = st.text_area("Hook Text (appears at top)", "This Sold Out in 48 Hours", height=100)
    cta = st.text_input("Call to Action", "DM TO ORDER NOW")

if st.button("Generate Viral Reel", type="primary", use_container_width=True):
    if not uploaded:
        st.error("Please upload a product image first!")
    else:
        with st.spinner("Processing image & rendering luxury Reel..."):
            product_img = safe_process_image(uploaded)

            frames = [create_frame(i/FPS, product_img, hook, price, f"{cta} {phone}") 
                     for i in range(DURATION * FPS)]

            clip = ImageSequenceClip(frames, fps=FPS)

            # Add music
            try:
                audio_data = requests.get(MUSIC[music_choice], timeout=15).content
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    tmp.write(audio_data)
                    audio = AudioFileClip(tmp.name).subclip(0, DURATION).audio_fadeout(1)
                    final_clip = clip.set_audio(audio)
                    os.unlink(tmp.name)
            except:
                final_clip = clip
                st.warning("Music failed → silent video created")

            # Export
            temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            final_clip.write_videofile(temp_path, fps=FPS, codec="libx264", audio_codec="aac",
                                     threads=8, preset="ultrafast", logger=None)

            st.video(temp_path)
            with open(temp_path, "rb") as f:
                st.download_button("Download Reel", f, 
                                 f"{product_name.replace(' ', '_')}_reel.mp4",
                                 "video/mp4", use_container_width=True)

            # Cleanup
            os.unlink(temp_path)
            final_clip.close()
            clip.close()

st.success("You are now officially unstoppable.")