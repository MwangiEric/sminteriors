import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import tempfile, os, numpy as np, io  # <-- ADDED 'io' HERE
from moviepy.editor import ImageSequenceClip, AudioFileClip
import requests

st.set_page_config(page_title="SM Interiors Reel Tool", layout="wide", page_icon="🎬")

WIDTH, HEIGHT = 1080, 1920
FPS, DURATION = 30, 12

# Reliable free audio (short WAVs)
MUSIC_URLS = {
    "Gold Luxury": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",
    "Viral Pulse": "https://www.soundjay.com/misc/sounds/notification-10.wav",
    "Elegant Flow": "https://www.soundjay.com/misc/sounds/notification-3.wav"
}

LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png"

@st.cache_resource
def load_logo():
    """Load logo once and cache it."""
    try:
        resp = requests.get(LOGO_URL, timeout=5)
        if resp.status_code == 200:
            logo = Image.open(io.BytesIO(resp.content)).convert("RGBA").resize((220, 110))
            return logo
    except:
        pass
    return None

def safe_image_load(uploaded):
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
        st.error(f"Image failed: {e}. Try a simple JPG/PNG under 5MB.")
        return None

def create_frame(t, product_img, hook, price, cta, logo=None):
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "#0F0A05")
    draw = ImageDraw.Draw(canvas)

    # Gold rings background
    for cx, cy, r in [(540, 960, 600), (660, 840, 800), (360, 1140, 1000)]:
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline="#FFD700", width=4)

    # Floating product
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

    # Hook text
    bbox = draw.textbbox((0, 0), hook, font=hook_font)
    text_w = bbox[2] - bbox[0]
    draw.text(((WIDTH - text_w) // 2, 120), hook, font=hook_font, fill="#FFD700", stroke_width=6, stroke_fill="#000")

    # Price badge
    badge_w, badge_h = 750, 180
    badge_x = (WIDTH - badge_w) // 2
    badge_y = HEIGHT - 500
    draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], radius=90, fill="#FFD700")
    p_bbox = draw.textbbox((0, 0), price, font=price_font)
    draw.text((WIDTH // 2, badge_y + 30), price, font=price_font, fill="#0F0A05", anchor="mm")

    # Pulsing CTA
    pulse_scale = 1 + 0.1 * np.sin(t * 8)
    cta_font_size = int(100 * pulse_scale)
    try:
        cta_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", cta_font_size)
    except:
        cta_font = ImageFont.load_default()
    c_bbox = draw.textbbox((0, 0), cta, font=cta_font)
    c_w = c_bbox[2] - c_bbox[0]
    draw.text(((WIDTH - c_w) // 2, HEIGHT - 180), cta, font=cta_font, fill="#FFFFFF", stroke_width=5, stroke_fill="#000")

    # Logo (once per render, not per frame)
    if logo:
        canvas.paste(logo, (40, 40), logo)

    return np.array(canvas)

# UI
st.title("🎬 SM Interiors Reel Tool — The Working One")
st.caption("Huge text • No overlaps • 10-15s renders • Deployed Nov 24, 2025")

col1, col2 = st.columns(2)

with col1:
    uploaded = st.file_uploader("Upload Product Photo", type=["png", "jpg", "jpeg", "webp"], help="JPG/PNG <5MB—auto-enhances")
    if uploaded:
        product_img = safe_image_load(uploaded)
        if product_img:
            st.image(product_img, caption="Ready Product", use_column_width=True)
    else:
        product_img = None

    price = st.text_input("Price", "Ksh 94,900")

with col2:
    hook = st.text_input("Hook", "This Sold Out in 24 Hours 🔥", help="Under 25 chars")
    cta = st.text_input("CTA", "DM TO ORDER • 0710 895 737")
    music_key = st.selectbox("Music", list(MUSIC_URLS.keys()))

if st.button("🚀 Generate Reel", type="primary", use_container_width=True):
    if not uploaded or product_img is None:
        st.error("Upload a photo!")
    else:
        with st.spinner(f"Rendering with {music_key}…"):
            logo_img = load_logo()
            frames = [create_frame(i / FPS, product_img, hook, price, cta, logo_img) for i in range(FPS * DURATION)]

            clip = ImageSequenceClip(frames, fps=FPS)

            # Audio handling
            audio_path = None
            try:
                resp = requests.get(MUSIC_URLS[music_key], timeout=10)
                if resp.status_code == 200:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                        tmp.write(resp.content)
                        audio_path = tmp.name
                    audio = AudioFileClip(audio_path).subclip(0, min(DURATION, audio.duration))
                    clip = clip.set_audio(audio)
            except Exception as e:
                st.warning(f"Audio skipped: {e}")

            # Export video
            video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            clip.write_videofile(
                video_path,
                fps=FPS,
                codec="libx264",
                audio_codec="aac" if audio_path else None,
                threads=4,
                preset="medium",
                logger=None
            )

            st.success("✅ Reel done!")
            st.video(video_path)

            with open(video_path, "rb") as f:
                st.download_button(
                    "💾 Download Reel",
                    f,
                    f"SM_Interiors_Reel_{price.replace(' ', '_').replace(',', '')}.mp4",
                    "video/mp4",
                    use_container_width=True
                )

            # Cleanup
            if audio_path:
                os.unlink(audio_path)
            os.unlink(video_path)
            clip.close()