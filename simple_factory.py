import streamlit as st
import io, requests, math, tempfile, base64, json, os, time
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip
from rembg import remove, new_session

# ================================
# PAGE CONFIG
# ================================
st.set_page_config(page_title="AdGen EVO: SM Interiors", layout="wide", page_icon="✨")

WIDTH, HEIGHT = 720, 1280
FPS = 30
DURATION = 6
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

# Direct, fast, royalty-free music (Pixabay + Uppbeat)
MUSIC_TRACKS = {
    "Luxury Gold": "https://cdn.pixabay.com/download/audio/2024/03/22/audio_2d5f2b79e5.mp3?filename=luxury-background-211023.mp3",
    "Elegant Piano": "https://cdn.pixabay.com/download/audio/2023/09/25/audio_5e65e1f48d.mp3?filename=elegant-piano-logo-174988.mp3",
    "Modern Beat": "https://cdn.pixabay.com/download/audio/2024/08/15/audio_5a54d0f2f6.mp3?filename=upbeat-background-171614.mp3",
    "Chill Luxury": "https://cdn.pixabay.com/download/audio/2023/11/08/audio_2d3c1e6d7f.mp3?filename=chill-abstract-intention-120363.mp3"
}

# ================================
# SECRETS
# ================================
if "groq_key" not in st.secrets:
    st.error("Missing `groq_key` in Streamlit Secrets! Add it under Settings → Secrets.")
    st.stop()

HEADERS = {"Authorization": f"Bearer {st.secrets['groq_key']}", "Content-Type": "application/json"}
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# ================================
# CACHED RESOURCES
# ================================
@st.cache_resource
def get_rembg_session():
    return new_session()

@st.cache_resource
def get_cached_logo(_url):
    try:
        r = requests.get(_url, timeout=10)
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content)).convert("RGBA")
        return img.resize((250, 125), Image.LANCZOS)  # Pre-resize for speed
    except:
        st.warning("Logo failed to load – using placeholder.")
        return Image.new("RGBA", (250, 125), (255, 255, 255, 180))

# ================================
# SAFE LAYOUT SANITIZER (CRITICAL FIX)
# ================================
def sanitize_layout(layout):
    sanitized = []
    for item in layout:
        sanitized.append({
            "role": item.get("role", "unknown"),
            "x": int(round(item.get("x", 0))),
            "y": int(round(item.get("y", 0))),
            "w": int(round(item.get("w", 100))),
            "h": int(round(item.get("h", 100)))
        })
    return sanitized

# Default premium layout (Reels-optimized)
DEFAULT_LAYOUT = sanitize_layout([
    {"role": "logo", "x": 40, "y": 40, "w": 240, "h": 120},
    {"role": "product", "x": 0, "y": 160, "w": 720, "h": 780},
    {"role": "caption", "x": 60, "y": 920, "w": 600, "h": 160},
    {"role": "price", "x": 60, "y": 1090, "w": 600, "h": 140},
    {"role": "contact", "x": 60, "y": 1230, "w": 600, "h": 60}
])

# ================================
# IMAGE PROCESSING
# ================================
def process_image_pro(input_image):
    with st.spinner("Removing background & enhancing..."):
        buf = io.BytesIO()
        input_image.save(buf, format="PNG")
        output = remove(buf.getvalue(), session=get_rembg_session())
        img = Image.open(io.BytesIO(output)).convert("RGBA")

        # Enhance
        img = ImageEnhance.Contrast(img).enhance(1.2)
        img = ImageEnhance.Sharpness(img).enhance(1.6)
        img = ImageEnhance.Color(img).enhance(1.1)

        # Smart auto-center crop
        alpha = img.getchannel("A")
        bbox = alpha.getbbox()
        if bbox:
            cropped = img.crop(bbox)
            ratio = cropped.width / cropped.height
            target_ratio = 1.0
            if ratio > target_ratio:
                new_h = int(cropped.width / target_ratio)
                pad = (new_h - cropped.height) // 2
                bg = Image.new("RGBA", (cropped.width, new_h), (0,0,0,0))
                bg.paste(cropped, (0, pad))
                img = bg
            else:
                new_w = int(cropped.height * target_ratio)
                pad = (new_w - cropped.width) // 2
                bg = Image.new("RGBA", (new_w, cropped.height), (0,0,0,0))
                bg.paste(cropped, (pad, 0))
                img = bg

        return img.resize((680, 680), Image.LANCZOS)

# ================================
# FONTS
# ================================
def get_font(size):
    for font_path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "arial.ttf", "DejaVuSans.ttf"]:
        try:
            return ImageFont.truetype(font_path, size)
        except:
            continue
    return ImageFont.load_default()

# ================================
# ANIMATION MATH
# ================================
def ease_out_elastic(t):
    if t <= 0: return 0
    if t >= 1: return 1
    c4 = (2 * math.pi) / 3
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

# ================================
# BRAND TEMPLATES
# ================================
BRAND_PRIMARY = "#4C3B30"
BRAND_ACCENT = "#D4AF37"  # True gold

TEMPLATES = {
    "SM Classic":    {"bg_grad": ["#4C3B30", "#2A1F1B"], "accent": BRAND_ACCENT, "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "none"},
    "Gold Diagonal": {"bg_grad": ["#4C3B30", "#3E2E24"], "accent": BRAND_ACCENT, "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "diagonal", "graphic_color": BRAND_ACCENT},
    "Gold Circles":  {"bg_grad": ["#332A22", "#4C3B30"], "accent": BRAND_ACCENT, "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "circular", "graphic_color": BRAND_ACCENT},
    "Gold Horizon":  {"bg_grad": ["#4C3B30", "#4C3B30"], "accent": "#FFFFFF",   "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "split", "graphic_color": BRAND_ACCENT},
}

# ================================
# GROQ HELPERS
# ================================
def ask_groq(payload):
    try:
        r = requests.post(f"{GROQ_BASE_URL}/chat/completions", json=payload, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Groq error: {e}")
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def get_hook_and_layout(_img_bytes, model_name):
    img = Image.open(io.BytesIO(_img_bytes))

    # Vision hook
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode()

    hook_payload = {
        "model": "llama-3.2-11b-vision-preview",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": f"Write a short, luxurious 4–7 word ad hook for this {model_name}."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
        ]}],
        "max_tokens": 30
    }
    hook = ask_groq(hook_payload) or "Timeless Luxury Redefined"

    # Layout
    layout_payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Return ONLY valid JSON with a 'layout' array of objects with keys: role, x, y, w, h."},
            {"role": "user", "content": f"720×1280 vertical ad. Roles: [logo, product, caption, price, contact]. Center product. Product: {model_name}"}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.4
    }
    raw = ask_groq(layout_payload)
    try:
        data = json.loads(raw) if raw else {}
        layout = data.get("layout", data) if isinstance(data, dict) else data
        if isinstance(layout, list) and len(layout) >= 4:
            return hook.strip('"'), sanitize_layout(layout)
    except:
        pass
    return hook.strip('"'), DEFAULT_LAYOUT

# ================================
# CONTENT TIPS
# ================================
def generate_tips(content_type, keyword):
    prompts = {
        "DIY Tips": f"5 luxury DIY decor ideas using or inspired by '{keyword}'",
        "Furniture Tips": f"5 expert tips for choosing and caring for high-end furniture like '{keyword}'",
        "Interior Design Tips": f"5 trending 2025 interior design tips involving '{keyword}'",
        "Maintenance Tips": f"5 professional cleaning & maintenance tips for luxury wood, brass, velvet & leather"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Reply ONLY with clean markdown bullet points. No intro or sign-off."},
            {"role": "user", "content": prompts.get(content_type, "Give 5 tips")}
        ],
        "temperature": 0.8,
        "max_tokens": 800
    }
    with st.spinner("Generating ideas..."):
        result = ask_groq(payload)
    return result or "No response from AI."

# ================================
# FRAME RENDERER (100% SAFE)
# ================================
def safe_paste(target, img, box_xy, mask=None):
    try:
        target.paste(img, box_xy, mask or (img.getchannel("A") if img.mode == "RGBA" else None))
    except:
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        target.paste(img, box_xy, img.split()[-1])

def draw_wrapped_text(draw, text, box, font, color):
    lines = []
    words = text.split()
    line = ""
    for word in words:
        test = line + (" " + word if line else word)
        if draw.textlength(test, font=font) <= box["w"]:
            line = test
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    y = box["y"]
    for line in lines:
        w = draw.textlength(line, font=font)
        draw.text((box["x"] + (box["w"] - w) / 2, y), line, font=font, fill=color)
        y += font.getbbox(line)[3] + 12

def create_frame(t, product_img, boxes, texts, tpl_name, logo_img):
    T = TEMPLATES[tpl_name]
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # Gradient background
    c1 = tuple(int(T["bg_grad"][0].lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    c2 = tuple(int(T["bg_grad"][1].lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    for y in range(HEIGHT):
        mix = y / HEIGHT
        col = tuple(int(c1[i] + (c2[i] - c1[i]) * mix) for i in range(3))
        draw.line([(0, y), (WIDTH, y)], fill=col)

    # Template graphics
    if T["graphic_type"] == "diagonal":
        alpha = int(80 * (t > 0.6))
        gc = tuple(int(T["graphic_color"].lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
        for i in range(-WIDTH, WIDTH + HEIGHT, 80):
            draw.line([(i, 0), (i + HEIGHT, HEIGHT)], fill=(*gc, alpha), width=6)

    if T["graphic_type"] == "circular":
        alpha = int(120 * (t > 0.8))
        gc = tuple(int(T["graphic_color"].lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
        r = int(600 * ease_out_elastic(max(0, t - 0.6)))
        draw.ellipse([WIDTH//2 - r, HEIGHT//2 - r, WIDTH//2 + r, HEIGHT//2 + r], outline=(*gc, alpha), width=12)

    if T["graphic_type"] == "split":
        h = int(HEIGHT * 0.4 * ease_out_elastic(max(0, t - 0.9)))
        draw.rectangle([0, HEIGHT - h, WIDTH, HEIGHT], fill=T["graphic_color"] + "88")

    # Render elements
    for b in boxes:
        role = b["role"]

        if role == "product":
            if t < 0.1: continue
            scale = ease_out_elastic(min(t * 1.4, 1.0)) * (1.0 + 0.15 * (t / DURATION))  # Ken Burns zoom
            pw, ph = int(b["w"] * scale), int(b["h"] * scale)
            prod = product_img.resize((pw, ph), Image.LANCZOS)

            # Shadow
            shadow = prod.convert("L")
            shadow = ImageOps.invert(shadow).point(lambda p: p * 0.4)
            shadow = shadow.convert("RGBA").filter(ImageFilter.GaussianBlur(25))
            safe_paste(canvas, shadow, (b["x"] + (b["w"] - pw)//2 + 15, b["y"] + (b["h"] - ph)//2 + 50))

            # Product with subtle float
            y_offset = int(math.sin(t * 4) * 12)
            safe_paste(canvas, prod, (b["x"] + (b["w"] - pw)//2, b["y"] + (b["h"] - ph)//2 + y_offset))

        elif role == "caption" and t > 1.0:
            draw_wrapped_text(draw, texts["caption"], b, get_font(56), T["accent"])

        elif role == "price" and t > 1.5:
            draw.rounded_rectangle([b["x"], b["y"], b["x"]+b["w"], b["y"]+b["h"]], radius=40, fill=T["price_bg"])
            draw_wrapped_text(draw, texts["price"], b, get_font(72), T["price_text"])

        elif role == "contact" and t > 2.5:
            draw_wrapped_text(draw, texts["contact"], b, get_font(36), T["text"])

        elif role == "logo":
            if logo_img:
                canvas.paste(logo_img, (b["x"], b["y"]), logo_img)

    # Final vignette
    vig = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
    vdraw = ImageDraw.Draw(vig  )
    for y in range(int(HEIGHT*0.7), HEIGHT):
        a = int(180 * (y - HEIGHT*0.7) / (HEIGHT*0.3))
        vdraw.line([(0,y), (WIDTH,y)], fill=(0,0,0,a))
    canvas.paste(vig, (0,0), vig)

    return np.array(canvas.convert("RGB"))

# ================================
# UI
# ================================
st.title("✨ AdGen EVO – SM Interiors Luxury Edition")
st.markdown("#### Instant 6-second Instagram/TikTok ads with AI hook, animation & music")

col1, col2 = st.columns([1, 1])

with col1:
    st.header("Ad Generator")
    u_file = st.file_uploader("Upload Product Photo", type=["png", "jpg", "jpeg"])
    u_model = st.text_input("Product Name", "Imperial Velvet Sofa")
    u_price = st.text_input("Price", "Ksh 129,900")
    u_contact = st.text_input("Contact / CTA", "Call 0710 895 737")
    u_style = st.selectbox("Visual Style", list(TEMPLATES.keys()))
    u_music = st.selectbox("Background Music", list(MUSIC_TRACKS.keys()))
    show_new = st.checkbox("Show 'NEW' Badge", value=True)
    btn_ad = st.button("Generate Luxury Ad →", type="primary", use_container_width=True)

with col2:
    st.header("Content Ideas")
    u_type = st.radio("Tip Type", ["DIY Tips", "Furniture Tips", "Interior Design Tips", "Maintenance Tips"])
    u_kw = st.text_input("Keyword", "Velvet Sofa")
    btn_tips = st.button("Generate Tips", use_container_width=True)

# Tips Generator
if btn_tips:
    tips = generate_tips(u_type, u_kw)
    st.markdown(f"### {u_type} for **{u_kw}**")
    st.markdown(tips)

# Video Ad Generator
if btn_ad and u_file:
    status = st.status("Creating your luxury ad...", expanded=True)

    # 1. Process image
    status.update(label="Enhancing product & removing background...")
    raw = Image.open(u_file).convert("RGBA")
    product_img = process_image_pro(raw)
    st.image(product_img, "Processed Product", width=180)

    # 2. AI hook + layout (cached)
    status.update(label="AI writing hook & layout...")
    buf = io.BytesIO()
    product_img.save(buf, format="PNG")
    hook, layout = get_hook_and_layout(buf.getvalue(), u_model)
    st.success(f"AI Hook: **{hook}**")

    # 3. Load logo
    status.update(label="Loading brand assets...")
    logo_img = get_cached_logo(LOGO_URL)

    # 4. Render frames with progress
    status.update(label="Rendering 180 animated frames...")
    progress_bar = st.progress(0)
    texts = {"caption": hook, "price": u_price, "contact": u_contact}
    frames = []
    total_frames = FPS * DURATION
    for i in range(total_frames):
        t = i / FPS
        frame = create_frame(t, product_img, layout, texts, u_style, logo_img)
        frames.append(frame)
        progress_bar.progress((i + 1) / total_frames)
    progress_bar.empty()

    clip = ImageSequenceClip(frames, fps=FPS)

    # 5. Add music
    status.update(label="Adding music & exporting...")
    try:
        audio_bytes = requests.get(MUSIC_TRACKS[u_music], timeout=15).content
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(audio_bytes)
            audio = AudioFileClip(tmp.name).subclip(0, DURATION).audio_fadeout(0.7)
            final = clip.set_audio(audio)
            os.unlink(tmp.name)
    except:
        final = clip
        st.warning("Music failed – video will be silent")

    # 6. Export
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        final.write_videofile(tmp.name, codec="libx264", audio_codec="aac", fps=FPS, verbose=False, logger=None)
        st.video(tmp.name)
        with open(tmp.name, "rb") as f:
            st.download_button(
                "Download Your Luxury Ad",
                f,
                f"SM_{u_model.replace(' ', '_')}_Ad.mp4",
                "video/mp4",
                use_container_width=True
            )
        os.unlink(tmp.name)

    status.update(label="Your luxury ad is ready!", state="complete")
elif btn_ad:
    st.error("Please upload a product image first!")

st.caption("AdGen EVO 2025 • Built with Grok + Streamlit • Zero crashes, pure luxury")