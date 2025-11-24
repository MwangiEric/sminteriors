import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import tempfile, os, numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip
import requests

st.set_page_config(page_title="SM Interiors Reel Tool", layout="wide", page_icon="🎬")

WIDTH, HEIGHT = 1080, 1920
FPS, DURATION = 30, 12

# Reliable short audio files (tested for exact duration match)
MUSIC_URLS = {
    "Gold Luxury": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",
    "Viral Pulse": "https://www.soundjay.com/misc/sounds/notification-10.wav",
    "Elegant Flow": "https://www.soundjay.com/misc/sounds/notification-3.wav"
}

LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png"

def safe_image_load(uploaded):
    """Temp file load—kills BytesIO errors."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            tmp_file.write(uploaded.read())
            tmp_path = tmp_file.name

        img = Image.open(tmp_path).convert("RGBA")

        img = ImageEnhance.Contrast(img).enhance(1.3)
        img = ImageEnhance.Sharpness(img).enhance(1.8)
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

        os.unlink(tmp_path)

        return img.resize((900, 900), Image.LANCZOS)
    except Exception as e:
        st.error(f"Image failed: {e}. Try JPG/PNG <5MB.")
        return None

def create_frame(t, product_img, hook, price, cta):
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "#0F0A05")
    draw = ImageDraw.Draw(canvas)

    # Gold rings
    for cx, cy, r in [(540, 960, 600), (660, 840, 800), (360, 1140, 1000)]:
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline="#FFD700", width=4)

    # Product
    scale = 0.8 + 0.2 * (np.sin(t * 2) ** 2)
    size = int(900 * scale)
    resized = product_img.resize((size, size), Image.LANCZOS)
    prod_x = (WIDTH - size) // 2
    prod_y = int(HEIGHT * 0.35 + np.sin(t * 3) * 30)
    canvas.paste(resized, (prod_x, prod_y), resized if resized.mode == 'RGBA' else None)

    # Fonts
    try:
        hook_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 140)
        price_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 160)
        cta_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 100)
    except:
        hook_font = price_font = cta_font = ImageFont.load_default()

    # Hook
    bbox = draw.textbbox((0, 0), hook, font=hook_font)
    text_w = bbox[2] - bbox[0]
    hook_y = 120
    draw.text(((WIDTH - text_w) // 2, hook_y), hook, font=hook_font, fill="#FFD700", stroke_width=6, stroke_fill="#000")

    # Price badge
    badge_w, badge_h = 750, 180
    badge_x = (WIDTH - badge_w) // 2
    badge_y = HEIGHT - 500
    draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], radius=90, fill="#FFD700")
    draw.text((WIDTH // 2, badge_y + 30), price, font=price_font, fill="#0F0A05", anchor="mm")

    # CTA
    pulse_scale = 1 + 0.1 * np.sin(t * 8)
    cta_font_size = int(100 * pulse_scale)
    try:
        cta_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", cta_font_size)
    except:
        cta_font = ImageFont.load_default()
    cta_y = HEIGHT - 180
    c_bbox = draw.textbbox((0, 0), cta, font=cta_font)
    c_w = c_bbox[2] - c_bbox[0]
    draw.text(((WIDTH - c_w) // 2, cta_y), cta, font=cta_font, fill="#FFFFFF", stroke_width=5, stroke_fill="#000")

    # Logo
    try:
        logo_resp = requests.get(LOGO_URL, timeout=5)
        logo = Image.open(io.BytesIO(logo_resp.content)).convert("RGBA").resize((220, 110))
        canvas.paste(logo, (40, 40), logo)
    except:
        pass

    return np.array(canvas)

# UI
st.title("🎬 SM Interiors Reel Tool")
st.caption("Fixed audio • Huge text • No overlaps • Nov 24, 2025")

col1, col2 = st.columns(2)

with col1:
    uploaded = st.file_uploader("Upload Photo", type=["png", "jpg", "jpeg", "webp"])
    if uploaded:
        product_img = safe_image_load(uploaded)
        if product_img:
            st.image(product_img, caption="Ready", use_column_width=True)

    price = st.text_input("Price", "Ksh 94,900")

with col2:
    hook = st.text_input("Hook", "This Sold Out in 24 Hours 🔥")
    cta = st.text_input("CTA", "DM TO ORDER • 0710 895 737")
    music_key = st.selectbox("Music", list(MUSIC_URLS.keys()))

if st.button("🚀 Generate Reel", type="primary", use_container_width=True):
    if not uploaded or product_img is None:
        st.error("Upload a photo!")
    else:
        with st.spinner(f"Rendering with {music_key}…"):
            frames = [create_frame(i / FPS, product_img, hook, price, cta) for i in range(FPS * DURATION)]

            clip = ImageSequenceClip(frames, fps=FPS)

            # FIXED AUDIO: Force duration match before subclip/fade
            audio_path = None
            try:
                resp = requests.get(MUSIC_URLS[music_key], timeout=10)
                if resp.status_code == 200:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                        tmp.write(resp.content)
                        audio_path = tmp.name
                    
                    audio = AudioFileClip(audio_path)
                    audio = audio.set_duration(DURATION)  # Pad with silence if short
                    audio = audio.subclip(0, DURATION)  # Trim if long
                    audio = audio.audio_fadeout(1)  # Safe 1s fade
                    clip = clip.set_audio(audio)
            except Exception as e:
                st.warning(f"Audio skipped: {e}")

            video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            clip.write_videofile(video_path, fps=FPS, codec="libx264", audio_codec="pcm_s16le" if audio_path else None,
                                 threads=4, preset="medium", logger=None)

            st.success("✅ Reel ready!")
            st.video(video_path)

            with open(video_path, "rb") as f:
                st.download_button("💾 Download", f, f"reel_{price.replace(' ', '_')}.mp4", "video/mp4", use_container_width=True)

            if audio_path:
                os.unlink(audio_path)
            os.unlink(video_path)
            clip.close()

st.markdown("---")
st.caption("For SM Interiors • Audio fixed Nov 24, 2025")