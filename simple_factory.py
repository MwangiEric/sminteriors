import streamlit as st
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageOps
import io, requests, math, tempfile, random, os
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip
from rembg import remove, new_session

st.set_page_config(page_title="AdGen ULTRA – SM Interiors", layout="centered", page_icon="✨")

# ================================
# ULTRA CONFIG – YOUR WINNING LOOK
# ================================
WIDTH, HEIGHT = 1080, 1920
FPS = 30
DURATION = 9
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

MUSIC = [
    "https://uppbeat.io/assets/track/mp3/synapse-fire-link-me-up.mp3",
    "https://uppbeat.io/assets/track/mp3/ikson-new-world.mp3",
    "https://uppbeat.io/assets/track/mp3/prigida-moving-on.mp3"
]

@st.cache_resource
def get_rembg():
    return new_session()
    return new_session()

def ultra_process(img):
    with st.spinner("Creating magic..."):
        # 1. Remove background
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        out = remove(buf.getvalue(), session=get_rembg())
        clean = Image.open(io.BytesIO(out)).convert("RGBA")

        # 2. Enhance
        clean = ImageEnhance.Contrast(clean).enhance(1.2)
        clean = ImageEnhance.Color(clean).enhance(1.1)
        clean = ImageEnhance.Sharpness(clean).enhance(1.4)

        # 3. Smart resize to fit 70% of height, keep ratio
        max_h = int(HEIGHT * 0.72)
        ratio = max_h / clean.height
        new_w = int(clean.width * ratio)
        new_h = int(clean.height * ratio)
        clean = clean.resize((new_w, new_h), Image.LANCZOS)

        return clean

def create_ultra_frame(t, product_img):
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), "#0B0E17")  # Deep luxury navy
    draw = ImageDraw.Draw(canvas)

    # Gold circles background
    gold = (212, 175, 55)
    sizes = [800, 600, 1000, 400, 700]
    poss = [(200, 300), (850, 200), (100, 1600), (900, 1400), (540, 1000)]
    for i, (cx, cy) in enumerate(poss):
        alpha = int(40 + 30 * math.sin(t * 2 + i))
        size = sizes[i] + int(100 * math.sin(t * 3 + i))
        draw.resize
        draw.ellipse([cx-size//2, cy-size//2, cx+size//2, cy+size//2], fill=(*gold, alpha))

    # Product with floating + bounce
    bounce = math.sin(t * 4) * 20
    scale = 0.95 + 0.05 * math.sin(t * 3)
    pw, ph = int(product_img.width * scale), int(product_img.height * scale)
    prod = product_img.resize((pw, ph), Image.LANCZOS)

    x = (WIDTH - pw) // 2
    # Perfect center
    y = int(HEIGHT * 0.52) - ph // 2 + int(bounce)

    # Real drop shadow
    shadow = prod.copy()
    shadow = shadow.convert("L")
    shadow = ImageOps.invert(shadow)
    shadow = shadow.point(lambda p: min(p * 1.8, 255))
    shadow = shadow.convert("RGBA")
    shadow_data = [(0,0,0,a//3) for *_, a in shadow.getdata()]
    shadow.putdata(shadow_data)
    shadow = shadow.filter(ImageFilter.GaussianBlur(35))
    canvas.paste(shadow, (x+20, y+60), shadow)

    # Inner glow
    glow = Image.new("RGBA", prod.size, (255, 220, 150, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.rectangle([20,20,pw-20,ph-20], fill=(255, 240, 200, 40))
    glow = glow.filter(ImageFilter.GaussianBlur(30))
    canvas.paste(glow, (x, y), glow)

    # Product
    canvas.paste(prod, (x, y), prod)

    # Logo top right
    try:
        logo = Image.open(io.BytesIO(requests.get(LOGO_URL, timeout=8).content)).convert("RGBA")
        logo = logo.resize((280, 140), Image.LANCZOS)
        canvas.paste(logo, (WIDTH-320, 60), logo)
    except: pass

    return np.array(canvas)

# ================================
# UI – CLEAN & PRO
# ================================
st.title("AdGen ULTRA")
st.markdown("### SM Interiors – Premium Reel Generator 2025")

col1, col2 = st.columns([1,1])
with col1:
    uploaded = st.file_uploader("Upload Product Photo", type=["png","jpg","jpeg"])
with col2:
    price = st.text_input("Price", "Ksh 12,500")
    contact = st.text_input("Contact", "0710 895 737")

if st.markdown("---")

if uploaded:
    raw = Image.open(uploaded)
    st.image(raw, "Original", width=300)

    if st.button("✨ Generate Premium Reel", type="primary", use_container_width=True):
        with st.spinner("Creating your masterpiece..."):
            # Process image
            product = ultra_process(raw)

            # Generate frames
            frames = []
            for i in range(FPS * DURATION):
                frames.append(create_ultra_frame(i/FPS, product))

            clip = ImageSequenceClip(frames, fps=FPS)

            # Add music
            try:
                audio_data = requests.get(random.choice(MUSIC)).content
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    tmp.write(audio_data)
                    audio_clip = AudioFileClip(tmp.name).subclip(0, DURATION).audio_fadeout(1)
                    final_clip = clip.set_audio(audio_clip)
                    os.unlink(tmp.name)
            except:
                final_clip = clip

            # Export
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                final_clip.write_videofile(tmp.name, codec="libx264", audio_codec="aac", fps=FPS, logger=None)
                st.video(tmp.name)
                with open(tmp.name, "rb") as f:
                    st.download_button("⬇️ Download Reel", f, f"SM_Serenity_Crib_{price.replace(' ', '')}.mp4", "video/mp4")
                os.unlink(tmp.name)

        st.success("Done! Your reel is ready for TikTok domination.")
        st.balloons()

st.caption("AdGen ULTRA by Grok × SM Interiors – November 2025")