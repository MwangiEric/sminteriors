import streamlit as st
import io, requests, math, tempfile, base64, json, random, time, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip
from rembg import remove, new_session

# ================================
# CONFIG & PAGE SETUP
# ================================
st.set_page_config(page_title="AdGen EVO: SM Interiors", layout="wide", page_icon="✨")

WIDTH, HEIGHT = 720, 1280
FPS = 30
DURATION = 6
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

# Fixed hotlink-friendly royalty-free music (direct MP3 URLs)
MUSIC_TRACKS = {
    "Upbeat Pop": "https://cdn.pixabay.com/download/audio/2024/08/15/audio_5a54d0f2f6.mp3?filename=upbeat-background-171614.mp3",
    "Luxury Chill": "https://uppbeat.io/assets/track/mp3/prigida-moving-on.mp3",
    "Modern Gold": "https://uppbeat.io/assets/track/mp3/synapse-fire-link-me-up.mp3",
    "Chill Beats": "https://uppbeat.io/assets/track/mp3/ikson-new-world.mp3"
}

# ================================
# SECRETS CHECK
# ================================
if "groq_key" not in st.secrets:
    st.error("Missing `groq_key` in Secrets! Add it in Streamlit settings.")
    st.stop()

HEADERS = {
    "Authorization": f"Bearer {st.secrets['groq_key']}",
    "Content-Type": "application/json"
}
GROQ_BASE_URL = "https://api.groq.com/openai/v1"  # Base URL only

# ================================
# CACHED REMBG SESSION
# ================================
@st.cache_resource
def get_rembg_session():
    return new_session()

# ================================
# IMAGE PROCESSING
# ================================
def process_image_pro(input_image):
    with st.spinner("Removing background & enhancing..."):
        buf = io.BytesIO()
        input_image.save(buf, format="PNG")
        output_bytes = remove(buf.getvalue(), session=get_rembg_session())
        img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")

        img = ImageEnhance.Contrast(img).enhance(1.15)
        img = ImageEnhance.Sharpness(img).enhance(1.5)
    return img

# ================================
# FONTS
# ================================
def get_font(size):
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "arial.ttf",
        "DejaVuSans-Bold.ttf"
    ]:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()

# ================================
# ANIMATION HELPERS
# ================================
def ease_out_elastic(t):
    if t <= 0: return 0
    if t >= 1: return 1
    c4 = (2 * math.pi) / 3
    return math.pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

def linear_fade(t, start, duration):
    if t < start: return 0.0
    if t > start + duration: return 1.0
    return (t - start) / duration

# ================================
# BRAND TEMPLATES
# ================================
BRAND_PRIMARY = "#4C3B30"
BRAND_ACCENT = "#D2A544"

TEMPLATES = {
    "SM Classic": {"bg_grad": [BRAND_PRIMARY, "#2a201b"], "accent": BRAND_ACCENT, "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "none"},
    "Gold Diagonal": {"bg_grad": [BRAND_PRIMARY, "#3e2e24"], "accent": BRAND_ACCENT, "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "diagonal", "graphic_color": BRAND_ACCENT},
    "Gold Circles": {"bg_grad": [BRAND_PRIMARY, "#332A22"], "accent": BRAND_ACCENT, "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "circular", "graphic_color": BRAND_ACCENT},
    "Gold Split": {"bg_grad": [BRAND_PRIMARY, BRAND_PRIMARY], "accent": "#FFFFFF", "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "split", "graphic_color": BRAND_ACCENT},
}

# ================================
# GROQ HELPERS (FIXED URL & MODELS)
# ================================
def ask_groq(payload):
    try:
        full_url = f"{GROQ_BASE_URL}/chat/completions"  # Correct endpoint
        r = requests.post(full_url, json=payload, headers=HEADERS, timeout=12)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            st.error("404: Invalid Groq model or endpoint. Check model names (e.g., llama-3.3-70b-versatile).")
        elif e.response.status_code == 401:
            st.error("401: Invalid API key. Regenerate at console.groq.com.")
        else:
            st.error(f"HTTP {e.response.status_code}: {e.response.reason}")
        return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

# ================================
# AI HOOK & LAYOUT (WITH HARDENED JSON PARSING)
# ================================
def get_data_groq(img, model_name):
    # Encode image as JPEG for vision model
    buf = io.BytesIO()
    rgb = img.convert("RGB") if img.mode == "RGBA" else img
    rgb.save(buf, format="JPEG", quality=90)
    b64 = base64.b64encode(buf.getvalue()).decode()

    # Hook (vision model)
    hook_payload = {
        "model": "llama-3.2-11b-vision-preview",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": f"Write a 4–6 word catchy, luxury ad hook for this {model_name}."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
        ]}],
        "max_tokens": 30
    }
    hook = ask_groq(hook_payload) or "Elevate Your Living Space"

    # Layout (fixed 70B model)
    layout_payload = {
        "model": "llama3-70b-8192",  # Using highly stable Llama 3 70B
        "messages": [
            {"role": "system", "content": "Output ONLY a valid JSON array of layout objects. Each object must have 'role', 'x', 'y', 'w', 'h'."},
            {"role": "user", "content": f"720×1280 ad layout for: logo, product, caption, price, contact. Center the product. Product: {model_name}"}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.3
    }
    layout_raw = ask_groq(layout_payload)

    default = [
        {"role": "logo", "x": 50, "y": 50, "w": 200, "h": 100},
        {"role": "product", "x": 60, "y": 250, "w": 600, "h": 600},
        {"role": "caption", "x": 60, "y": 900, "w": 600, "h": 100},
        {"role": "price", "x": 160, "y": 1050, "w": 400, "h": 120},
        {"role": "contact", "x": 60, "y": 1200, "w": 600, "h": 60}
    ]
    final_hook = hook.strip('"')

    try:
        data = json.loads(layout_raw)
        
        # 1. Check for nested structure (e.g., {"layout": [...]})
        potential_layout = data.get("layout", data) if isinstance(data, dict) else data

        # 2. Final validation: must be a list of dictionaries with 'role'
        is_valid_layout = (
            isinstance(potential_layout, list) and 
            all(isinstance(item, dict) and "role" in item for item in potential_layout)
        )
        
        if is_valid_layout:
            return final_hook, potential_layout
        else:
            # Fallback if JSON is returned but fails structural validation
            return final_hook, default
            
    except:
        # Fallback if json.loads() fails entirely (e.g., malformed JSON)
        return final_hook, default

# ================================
# CONTENT IDEA GENERATOR (FIXED MODEL)
# ================================
def generate_tips(content_type, keyword):
    system = "You are a luxury furniture brand content expert. Reply ONLY with markdown bullet points, no intro/outro."
    prompts = {
        "DIY Tips": f"5 quick DIY decor ideas using common items, focused on '{keyword}'",
        "Furniture Tips": f"5 pro tips for choosing/caring for luxury furniture like '{keyword}'",
        "Interior Design Tips": f"5 trending interior design hacks related to '{keyword}'",
        "Maintenance Tips": f"5 expert cleaning & care tips for solid wood, brass, fine upholstery"
    }
    payload = {
        "model": "llama3-70b-8192",  # Using highly stable Llama 3 70B
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompts.get(content_type, "Generate 5 tips")}
        ],
        "temperature": 0.8,
        "max_tokens": 800
    }
    with st.spinner("Generating tips..."):
        result = ask_groq(payload)
        return result or "No response from Groq. Check your API key and connection."

# ================================
# FRAME RENDERER
# ================================
def draw_wrapped_text(draw, text, box, font, color):
    lines = []
    words = text.split()
    line = ""
    for w in words:
        test = line + (" " + w if line else w)
        if draw.textbbox((0,0), test, font=font)[2] <= box['w']:
            line = test
        else:
            lines.append(line)
            line = w
    if line: lines.append(line)
    y = box['y']
    for line in lines:
        w = draw.textbbox((0,0), line, font=font)[2]
        draw.text((box['x'] + (box['w']-w)//2, y), line, font=font, fill=color)
        y += draw.textbbox((0,0), line, font=font)[3] + 8

def create_frame(t, img, boxes, texts, tpl_name):
    T = TEMPLATES[tpl_name]
    canvas = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(canvas)

    # Fixed gradient hex parsing
    def hex_to_rgb(hex_str):
        hex_str = hex_str.lstrip('#')
        return tuple(int(hex_str[i:i+2], 16) for i in (0,2,4))

    c1 = hex_to_rgb(T["bg_grad"][0])
    c2 = hex_to_rgb(T["bg_grad"][1])
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        color = tuple(int(c1[i] + (c2[i] - c1[i]) * ratio) for i in range(3))
        draw.line([(0,y), (WIDTH,y)], fill=color)

    # Template graphics
    gc = hex_to_rgb(T.get("graphic_color", "#000000")) if "graphic_color" in T else None

    if T["graphic_type"] == "diagonal" and gc:
        alpha = int(255 * linear_fade(t, 0.5, 1.0))
        for i in range(-WIDTH, WIDTH+HEIGHT, 60):
            draw.line([(i,0), (i+HEIGHT,HEIGHT)], fill=(*gc, alpha), width=8)

    if T["graphic_type"] == "circular" and gc:
        alpha = int(200 * linear_fade(t, 0.7, 0.8))
        big = int(WIDTH * 1.6 * ease_out_elastic(max(0, t-0.4)))
        draw.ellipse([WIDTH*0.8-big//2, HEIGHT*0.7-big//2, WIDTH*0.8+big//2, HEIGHT*0.7+big//2], fill=(*gc, alpha))

    if T["graphic_type"] == "split" and gc:
        h = int(HEIGHT * 0.35 * ease_out_elastic(max(0, t-0.9)))
        draw.rectangle([0, HEIGHT-h, WIDTH, HEIGHT], fill=T["graphic_color"])

    # Elements
    for b in boxes:
        if b["role"] == "product":
            scale = ease_out_elastic(min(t * 1.3, 1.0))
            if scale > 0.02:
                pw, ph = int(b["w"]*scale), int(b["h"]*scale)
                prod = img.resize((pw, ph), Image.LANCZOS)
                # Fixed shadow (using ImageOps)
                shadow = prod.copy().convert("L")
                shadow = ImageOps.invert(shadow)
                shadow = shadow.point(lambda p: p * 0.3)
                shadow = shadow.convert("RGBA")
                shadow = shadow.filter(ImageFilter.GaussianBlur(20))
                canvas.paste(shadow, (b["x"]+(b["w"]-pw)//2+10, b["y"]+(b["h"]-ph)//2+40), shadow)
                canvas.paste(prod, (b["x"]+(b["w"]-pw)//2, b["y"]+(b["h"]-ph)//2 + math.sin(t*3)*10), prod)

        elif b["role"] == "price":
            if t > 1.4:
                draw.rounded_rectangle([b["x"], b["y"], b["x"]+b["w"], b["y"]+b["h"]], radius=30, fill=T["price_bg"])
                draw_wrapped_text(draw, texts["price"], b, get_font(68), T["price_text"])

        elif b["role"] == "caption":
            if t > 1.0:
                draw_wrapped_text(draw, texts["caption"], b, get_font(52), T["accent"])

        elif b["role"] == "contact":
            if t > 2.3:
                draw_wrapped_text(draw, texts["contact"], b, get_font(32), T["text"])

        elif b["role"] == "logo":
            try:
                r = requests.get(LOGO_URL, timeout=8)
                r.raise_for_status()
                logo = Image.open(io.BytesIO(r.content)).convert("RGBA").resize((b["w"], b["h"]), Image.LANCZOS)
                canvas.paste(logo, (b["x"], b["y"]), logo)
            except:
                pass

    # Vignette
    vig = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
    vdraw = ImageDraw.Draw(vig)
    for y in range(int(HEIGHT*0.65), HEIGHT):
        a = int(200 * (y - HEIGHT*0.65) / (HEIGHT*0.35))
        vdraw.line([(0,y), (WIDTH,y)], fill=(0,0,0,a))
    canvas.paste(vig, (0,0), vig)

    return np.array(canvas)

# ================================
# UI & MAIN LOGIC
# ================================
st.title("AdGen EVO – SM Interiors Edition")

with st.sidebar:
    st.header("Turbo Ad Generator")
    u_file = st.file_uploader("Product Image", type=["png","jpg","jpeg"])
    u_model = st.text_input("Product Name", "Luxe Velvet Sofa")
    u_price = st.text_input("Price", "Ksh 89,900")
    u_contact = st.text_input("Contact", "0710 895 737")
    u_style = st.selectbox("Template", list(TEMPLATES.keys()))
    u_music = st.selectbox("Music", list(MUSIC_TRACKS.keys()))
    btn_ad = st.button("Generate 6s Luxury Ad", type="primary")

    st.markdown("---")
    st.header("Content Idea Generator")
    u_type = st.radio("Type", ["DIY Tips", "Furniture Tips", "Interior Design Tips", "Maintenance Tips"])
    u_kw = st.text_input("Keyword / Product", "Velvet Sofa")
    btn_tips = st.button("Generate Tips")

# Content Tips
if btn_tips:
    with st.spinner("Thinking..."):
        tips = generate_tips(u_type, u_kw)
        st.markdown(f"### {u_type} – {u_kw}")
        st.markdown(tips)

# Video Ad Generation
if btn_ad and u_file:
    status = st.status("Creating your luxury ad...", expanded=True)

    # 1. Process image
    status.update(label="Enhancing product image...")
    raw = Image.open(u_file).convert("RGBA")
    product_img = process_image_pro(raw)
    st.image(product_img, "Processed Product", width=200)

    # 2. AI hook + layout
    status.update(label="AI generating hook & layout...")
    hook, layout = get_data_groq(product_img, u_model)
    st.write(f"**AI Hook:** {hook}")

    # 3. Render frames
    status.update(label="Animating frames...")
    texts = {"caption": hook, "price": u_price, "contact": u_contact}
    frames = [create_frame(i/FPS, product_img, layout, texts, u_style) for i in range(FPS*DURATION)]
    clip = ImageSequenceClip(frames, fps=FPS)

    # 4. Add music
    status.update(label="Adding music...")
    try:
        audio_data = requests.get(MUSIC_TRACKS[u_music], timeout=8).content
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(audio_data)
            audio = AudioFileClip(tmp.name).subclip(0, DURATION).audio_fadeout(0.8)
            final = clip.set_audio(audio)
            os.unlink(tmp.name)
    except Exception as e:
        final = clip
        st.warning(f"Music failed – silent video. Error: {e}")

    # 5. Export
    status.update(label="Exporting MP4...")
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            final.write_videofile(tmp.name, codec="libx264", audio_codec="aac", fps=FPS, logger=None, verbose=False)
            st.video(tmp.name)
            with open(tmp.name, "rb") as f:
                st.download_button("Download Luxury Ad", f, f"SM_{u_model.replace(' ', '_')}.mp4", "video/mp4")
            os.unlink(tmp.name)
    except Exception as e:
        st.error(f"Video finalization failed: {e}")

    status.update(label="Done! Your ad is ready", state="complete")
elif btn_ad:
    st.error("Upload a product image first!")

st.caption("AdGen EVO by Grok × Streamlit – Final Working Version")
