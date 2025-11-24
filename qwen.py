import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import tempfile, os, numpy as np, io
from moviepy.editor import ImageSequenceClip, AudioFileClip
import requests
import base64
from groq import Groq

st.set_page_config(page_title="SM Interiors Reel Tool", layout="wide", page_icon="🎬")

WIDTH, HEIGHT = 1080, 1920
FPS, DURATION = 30, 12

# Reliable free audio
MUSIC_URLS = {
    "Gold Luxury": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",
    "Viral Pulse": "https://www.soundjay.com/misc/sounds/notification-10.wav",
    "Elegant Flow": "https://www.soundjay.com/misc/sounds/notification-3.wav"
}

LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png"

# Initialize Groq
GROQ_API_KEY = st.secrets["groq_key"]  # Store in Streamlit Cloud secrets
client = Groq(api_key=GROQ_API_KEY)

@st.cache_resource
def load_logo():
    try:
        resp = requests.get(LOGO_URL, timeout=5)
        if resp.status_code == 200:
            logo = Image.open(io.BytesIO(resp.content)).convert("RGBA").resize((300, 150))
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

        # Save to bytes for Groq
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        return img.resize((900, 900), Image.LANCZOS), img_bytes.getvalue()

    except Exception as e:
        st.error(f"Image failed: {e}. Try a simple JPG/PNG under 5MB.")
        return None, None

def analyze_image_with_groq(image_bytes):
    """Send image to Groq for visual analysis"""
    try:
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """
Analyze this furniture product image and return ONLY in this format:

PRODUCT_TYPE: [e.g., Wingback Armchair]
COLOR: [e.g., Teal Velvet]
STYLE: [e.g., Modern, Classic, Luxury]
MOOD: [e.g., Cozy, Elegant, Bold]

Then suggest:
HOOK: [short, urgent, under 25 chars]
TITLE: [clean, descriptive]
CTA: [action-oriented, includes contact if possible]

Example:
PRODUCT_TYPE: Wingback Armchair
COLOR: Teal Velvet
STYLE: Luxury
MOOD: Bold

HOOK: This Sold Out in 24 H
TITLE: Teal Wingback Chair
CTA: Order Now • 0710 895 737
"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            }
                        }
                    ],
                }
            ],
            model="llama-3.1-70b-versatile",
            temperature=0.7,
            max_tokens=200,
        )

        response = chat_completion.choices[0].message.content.strip()
        return parse_groq_response(response)

    except Exception as e:
        st.warning(f"Image analysis failed: {e}. Using defaults.")
        return {
            "product_type": "Furniture",
            "color": "Grey",
            "style": "Modern",
            "mood": "Elegant",
            "hook": "This Sold Out in 24 H",
            "title": "Luxury Furniture",
            "cta": "DM TO ORDER • 0710 895 737"
        }

def parse_groq_response(text):
    lines = text.split("\n")
    data = {}
    for line in lines:
        if ": " in line:
            key, value = line.split(": ", 1)
            data[key.strip()] = value.strip()
    return data

def smart_text_size(draw, text, font, max_width, max_height=None):
    """Scale font to fit within max_width, max_height"""
    original_font = font
    size = font.size
    while True:
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        if w <= max_width and (max_height is None or h <= max_height):
            break
        size -= 1
        if size < 10:
            break
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        except:
            font = ImageFont.load_default()
    return font

def create_frame(t, product_img, hook, price, cta, title, ai_data, logo=None):
    # Base brand color
    bg_color = "#0F0A05"  # Dark brown — never changes

    # Creative background enhancements based on AI analysis
    canvas = Image.new("RGB", (WIDTH, HEIGHT), bg_color)
    draw = ImageDraw.Draw(canvas)

    # --- CREATIVE BACKGROUND ELEMENTS (AI-ENHANCED) ---
    color = ai_data.get("color", "Grey").lower()
    mood = ai_data.get("mood", "Elegant").lower()

    # Add subtle glowing orbs around product (color-tinted based on product)
    orb_colors = {
        "teal": "#00CED1",
        "blue": "#1E90FF",
        "grey": "#A9A9B0",
        "gold": "#FFD700",
        "brown": "#8B4513",
        "white": "#FFFFFF",
        "black": "#000000"
    }
    main_orb_color = "#FFD700"  # Always use gold for brand consistency
    accent_orb_color = orb_colors.get(color.split()[0], "#FFD700")  # First word of color

    # Floating orbs (size varies with time for gentle motion)
    for i in range(3):
        angle = t * 0.5 + i * 2
        radius = 300 + 50 * np.sin(angle)
        x = WIDTH // 2 + int(200 * np.cos(angle))
        y = HEIGHT // 2 + int(150 * np.sin(angle))
        # Draw semi-transparent orb
        draw.ellipse([x-radius, y-radius, x+radius, y+radius],
                     outline=main_orb_color, width=4, fill=None)

    # Add soft gradient glow behind product (based on mood)
    if "bold" in mood:
        # Stronger glow
        for r in [600, 800, 1000]:
            draw.ellipse([WIDTH//2-r, HEIGHT//2-r, WIDTH//2+r, HEIGHT//2+r],
                         outline="#FFD700", width=2, fill=None)
    elif "cozy" in mood:
        # Softer, warmer glow
        for r in [500, 700, 900]:
            draw.ellipse([WIDTH//2-r, HEIGHT//2-r, WIDTH//2+r, HEIGHT//2+r],
                         outline="#FFD700", width=1, fill=None)

    # --- PRODUCT WITH SLOW ROTATION ---
    scale = 0.8 + 0.2 * (np.sin(t * 2) ** 2)
    size = int(900 * scale)
    resized = product_img.resize((size, size), Image.LANCZOS)
    angle = np.sin(t * 0.5) * 3
    rotated = resized.rotate(angle, expand=True, resample=Image.BICUBIC)
    prod_x = (WIDTH - rotated.width) // 2
    prod_y = int(HEIGHT * 0.35 + np.sin(t * 3) * 30)
    canvas.paste(rotated, (prod_x, prod_y), rotated if rotated.mode == 'RGBA' else None)

    # --- FONTS ---
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 100)
        hook_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 140)
        price_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 160)
        cta_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 100)
    except:
        title_font = hook_font = price_font = cta_font = ImageFont.load_default()

    # --- TITLE (above product) ---
    title_max_w = WIDTH - 100
    title_font = smart_text_size(draw, title, title_font, title_max_w)
    bbox = draw.textbbox((0, 0), title, font=title_font)
    text_w = bbox[2] - bbox[0]
    safe_x = max(50, (WIDTH - text_w) // 2)
    draw.text((safe_x, 80), title, font=title_font, fill="#FFFFFF", stroke_width=4, stroke_fill="#000")

    # --- HOOK ---
    hook_max_w = WIDTH - 100
    hook_font = smart_text_size(draw, hook, hook_font, hook_max_w)
    bbox = draw.textbbox((0, 0), hook, font=hook_font)
    text_w = bbox[2] - bbox[0]
    safe_x = max(50, (WIDTH - text_w) // 2)
    draw.text((safe_x, 120), hook, font=hook_font, fill="#FFD700", stroke_width=6, stroke_fill="#000")

    # --- PRICE BADGE ---
    badge_w, badge_h = 750, 180
    badge_x = (WIDTH - badge_w) // 2
    badge_y = HEIGHT - 500
    draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], radius=90, fill="#FFD700")
    p_bbox = draw.textbbox((0, 0), price, font=price_font)
    draw.text((WIDTH // 2, badge_y + 30), price, font=price_font, fill="#FFFFFF", anchor="mm")

    # --- PULSING CTA ---
    pulse_scale = 1 + 0.1 * np.sin(t * 8)
    cta_font_size = int(100 * pulse_scale)
    try:
        cta_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", cta_font_size)
    except:
        cta_font = ImageFont.load_default()
    cta_max_w = WIDTH - 100
    cta_font = smart_text_size(draw, cta, cta_font, cta_max_w)
    c_bbox = draw.textbbox((0, 0), cta, font=cta_font)
    c_w = c_bbox[2] - c_bbox[0]
    draw.text(((WIDTH - c_w) // 2, HEIGHT - 180), cta, font=cta_font, fill="#FFFFFF", stroke_width=5, stroke_fill="#000")

    # --- LOGO ---
    if logo:
        canvas.paste(logo, (30, 30), logo)
        glow = Image.new("RGBA", logo.size, (255, 255, 255, 30))
        canvas.paste(glow, (25, 25), glow)
        canvas.paste(logo, (30, 30), logo)

    return np.array(canvas)

# --- UI ---
st.title("🎬 SM Interiors Reel Tool — AI-Powered & Layout-Smart")
st.caption("Auto-scales text • AI analyzes image • Brand-consistent • Deployed Nov 24, 2025")

col1, col2 = st.columns(2)

with col1:
    uploaded = st.file_uploader("Upload Product Photo", type=["png", "jpg", "jpeg", "webp"], help="JPG/PNG <5MB—auto-enhances")
    if uploaded:
        product_img, img_bytes = safe_image_load(uploaded)
        if product_img:
            st.image(product_img, caption="Ready Product", use_column_width=True)
    else:
        product_img = None
        img_bytes = None

    price = st.text_input("Price", "Ksh 18,999")

with col2:
    product_name = st.text_input("Product Name (optional)", "")
    image_desc = st.text_area("Image Description (optional)", "")

    if uploaded and img_bytes and st.button("✨ Analyze Image + Get AI Copy", type="secondary", use_container_width=True):
        ai_data = analyze_image_with_groq(img_bytes)
        st.session_state.hook = ai_data.get("hook", "This Sold Out in 24 H")
        st.session_state.title = ai_data.get("title", "Luxury Furniture")
        st.session_state.cta = ai_data.get("cta", "DM TO ORDER • 0710 895 737")
        st.session_state.ai_data = ai_data
        st.success("✅ AI analyzed image and generated copy!")

    hook = st.text_input("Hook", value=st.session_state.get("hook", "This Sold Out in 24 H"))
    title = st.text_input("Title", value=st.session_state.get("title", "Wingback Armchair"))
    cta = st.text_input("CTA", value=st.session_state.get("cta", "DM TO ORDER • 0710 895 737"))
    music_key = st.selectbox("Music", list(MUSIC_URLS.keys()))

if st.button("🚀 Generate Reel", type="primary", use_container_width=True):
    if not uploaded or product_img is None:
        st.error("Upload a photo!")
    else:
        with st.spinner(f"Rendering with {music_key}…"):
            logo_img = load_logo()
            ai_data = st.session_state.get("ai_data", {"color": "Grey", "mood": "Elegant"})
            frames = [create_frame(i / FPS, product_img, hook, price, cta, title, ai_data, logo_img) for i in range(FPS * DURATION)]

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

st.markdown("---")
st.caption("For SM Interiors • Tested & shipped Nov 24, 2025")