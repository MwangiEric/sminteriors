import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import tempfile, os, numpy as np, io
from moviepy.editor import ImageSequenceClip, AudioFileClip
import requests
import base64
from groq import Groq

st.set_page_config(page_title="SM Interiors Reel Tool", layout="wide", page_icon="🎬")

WIDTH, HEIGHT = 1080, 1920
FPS, DURATION = 30, 6  # 6 seconds

# Reliable MP3 audio (no codec issues)
MUSIC_URLS = {
    "Gold Luxury": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_5519b1a5b6.mp3",
    "Viral Pulse": "https://cdn.pixabay.com/download/audio/2022/06/02/audio_c0b387b3b3.mp3",
    "Elegant Flow": "https://cdn.pixabay.com/download/audio/2022/03/08/audio_3f3a1f8a7c.mp3",
}

LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png"

# Initialize Groq
GROQ_API_KEY = st.secrets["groq_key"]
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

        # Auto-resize for Groq (avoid 413 error)
        max_dim = 1024
        if max(img.width, img.height) > max_dim:
            ratio = max_dim / max(img.width, img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

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
                                "url": f"image/jpeg;base64,{image_b64}"
                            }
                        }
                    ],
                }
            ],
            model="meta-llama/llama-4-maverick-17b-128e-instruct",  # ✅ Best for object recognition
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

# --- TEMPLATES ---
TEMPLATES = {
    "Luxury": {
        "bg_color": "#0F0A05",
        "ring_color": "#FFD700",
        "text_color": "#FFFFFF",
        "price_bg": "#FFD700",
        "price_text": "#0F0A05",
        "cta_pulse": True,
    },
    "Bold": {
        "bg_color": "#000000",
        "ring_color": "#FF4500",
        "text_color": "#FFFFFF",
        "price_bg": "#FF4500",
        "price_text": "#000000",
        "cta_pulse": True,
    },
    "Minimalist": {
        "bg_color": "#FFFFFF",
        "ring_color": "#000000",
        "text_color": "#000000",
        "price_bg": "#000000",
        "price_text": "#FFFFFF",
        "cta_pulse": False,
    }
}

def create_frame(t, product_img, hook, price, cta, title, template, logo=None):
    canvas = Image.new("RGB", (WIDTH, HEIGHT), template["bg_color"])
    draw = ImageDraw.Draw(canvas)

    # Gold rings
    for cx, cy, r in [(540, 960, 600), (660, 840, 800), (360, 1140, 1000)]:
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=template["ring_color"], width=4)

    # Product with adjustments
    base_scale = st.session_state.get("product_scale", 1.0)
    scale = base_scale * (0.8 + 0.2 * (np.sin(t * 2) ** 2))
    size = int(900 * scale)
    resized = product_img.resize((size, size), Image.LANCZOS)
    angle = np.sin(t * 0.5) * 3
    rotated = resized.rotate(angle, expand=True, resample=Image.BICUBIC)
    prod_x = (WIDTH - rotated.width) // 2
    prod_y_offset = st.session_state.get("prod_y_offset", 0)
    prod_y = int(HEIGHT * 0.35 + prod_y_offset + np.sin(t * 3) * 30)
    canvas.paste(rotated, (prod_x, prod_y), rotated if rotated.mode == 'RGBA' else None)

    # Fonts (fixed sizes per template)
    font_sizes = {
        "Luxury": (100, 140, 160, 100),
        "Bold": (100, 140, 160, 100),
        "Minimalist": (90, 120, 140, 90),
    }
    tfs, hfs, pfs, cfs = font_sizes[template_choice]

    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", tfs)
        hook_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", hfs)
        price_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", pfs)
        cta_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", cfs)
    except:
        title_font = hook_font = price_font = cta_font = ImageFont.load_default()

    # Text positions (adjustable)
    title_y = st.session_state.get("title_y", 80)
    hook_y = st.session_state.get("hook_y", 120)
    price_y = st.session_state.get("price_y", HEIGHT - 500)
    cta_y = st.session_state.get("cta_y", HEIGHT - 180)

    # Title
    bbox = draw.textbbox((0, 0), title, font=title_font)
    text_w = bbox[2] - bbox[0]
    safe_x = max(50, (WIDTH - text_w) // 2)
    draw.text((safe_x, title_y), title, font=title_font, fill=template["text_color"], stroke_width=4, stroke_fill="#000")

    # Hook
    bbox = draw.textbbox((0, 0), hook, font=hook_font)
    text_w = bbox[2] - bbox[0]
    safe_x = max(50, (WIDTH - text_w) // 2)
    draw.text((safe_x, hook_y), hook, font=hook_font, fill=template["ring_color"], stroke_width=6, stroke_fill="#000")

    # Price
    badge_w, badge_h = 750, 180
    badge_x = (WIDTH - badge_w) // 2
    draw.rounded_rectangle([badge_x, price_y, badge_x + badge_w, price_y + badge_h], radius=90, fill=template["price_bg"])
    p_bbox = draw.textbbox((0, 0), price, font=price_font)
    draw.text((WIDTH // 2, price_y + 30), price, font=price_font, fill=template["price_text"], anchor="mm")

    # CTA
    if template["cta_pulse"]:
        pulse_scale = 1 + 0.1 * np.sin(t * 8)
        cta_font_size = int(cfs * pulse_scale)
        try:
            cta_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", cta_font_size)
        except:
            cta_font = ImageFont.load_default()
    c_bbox = draw.textbbox((0, 0), cta, font=cta_font)
    c_w = c_bbox[2] - c_bbox[0]
    draw.text(((WIDTH - c_w) // 2, cta_y), cta, font=cta_font, fill=template["text_color"], stroke_width=5, stroke_fill="#000")

    # Logo
    if logo:
        canvas.paste(logo, (30, 30), logo)

    return np.array(canvas)

# --- UI ---
st.title("🎬 SM Interiors Reel Tool — Pro Templates + AI Vision")
st.caption("6s reels • Preview before render • Adjust layout • MP3 audio")

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

    template_choice = st.selectbox("Template", list(TEMPLATES.keys()), index=0)

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

# --- ADJUSTMENTS ---
st.markdown("---")
st.subheader("🔧 Adjust Layout (Optional)")

with st.expander("Position & Size Controls"):
    col_adj1, col_adj2 = st.columns(2)
    with col_adj1:
        prod_y_offset = st.slider("Product Vertical Position", -200, 200, 0, help="Move product up/down")
        title_y = st.slider("Title Y", 50, 200, 80)
        hook_y = st.slider("Hook Y", 50, 200, 120)
    with col_adj2:
        product_scale = st.slider("Product Scale", 0.5, 1.5, 1.0, step=0.1)
        cta_y = st.slider("CTA Y", HEIGHT - 300, HEIGHT - 100, HEIGHT - 180)
        price_y = st.slider("Price Y", HEIGHT - 600, HEIGHT - 300, HEIGHT - 500)

# Save to session state
st.session_state.prod_y_offset = prod_y_offset
st.session_state.product_scale = product_scale
st.session_state.title_y = title_y
st.session_state.hook_y = hook_y
st.session_state.cta_y = cta_y
st.session_state.price_y = price_y
st.session_state.template_choice = template_choice

# --- PREVIEW ---
if uploaded and product_img is not None:
    st.markdown("---")
    st.subheader("🖼️ Preview (Before Rendering)")
    logo_img = load_logo()
    template = TEMPLATES[template_choice]
    preview_frame = create_frame(0, product_img, hook, price, cta, title, template, logo_img)
    preview_img = Image.fromarray(preview_frame)
    st.image(preview_img, caption="Preview Frame", use_column_width=True)
    st.info("✅ Adjust sliders above if needed, then click 'Generate Reel'.")

# --- RENDER ---
if st.button("🚀 Generate Reel", type="primary", use_container_width=True):
    if not uploaded or product_img is None:
        st.error("Upload a photo!")
    else:
        with st.spinner(f"Rendering 6s video with {music_key}…"):
            logo_img = load_logo()
            template = TEMPLATES[template_choice]
            frames = [create_frame(i / FPS, product_img, hook, price, cta, title, template, logo_img) for i in range(FPS * DURATION)]

            clip = ImageSequenceClip(frames, fps=FPS)

            # Audio handling (MP3)
            audio = None
            audio_path = None
            try:
                resp = requests.get(MUSIC_URLS[music_key], timeout=10)
                if resp.status_code == 200:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                        tmp.write(resp.content)
                        audio_path = tmp.name
                    full_audio = AudioFileClip(audio_path)
                    audio = full_audio.subclip(0, min(DURATION, full_audio.duration))
                    clip = clip.set_audio(audio)
            except Exception as e:
                st.warning(f"Audio skipped: {e}")

            video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            clip.write_videofile(
                video_path,
                fps=FPS,
                codec="libx264",
                audio_codec="aac" if audio else None,
                threads=4,
                preset="medium",
                logger=None
            )

            st.success("✅ Reel done!")
            st.video(video_path)

            with open(video_path, "rb") as f:
                st.download_button("💾 Download Reel", f, "SM_Reel.mp4", "video/mp4", use_container_width=True)

            # Cleanup
            if audio_path and os.path.exists(audio_path):
                os.unlink(audio_path)
            if os.path.exists(video_path):
                os.unlink(video_path)
            clip.close()

st.markdown("---")
st.caption("For SM Interiors • Tested & shipped Nov 24, 2025")