import streamlit as st
import io, requests, math, tempfile, base64, json, os
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageOps, ImageFont
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip
from rembg import remove, new_session

st.set_page_config(page_title="AdGen EVO – SM Interiors", layout="wide", page_icon="luxury")

WIDTH, HEIGHT = 720, 1280
FPS = 30
DURATION = 6
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

MUSIC_TRACKS = {
    "Upbeat Pop": "https://cdn.pixabay.com/download/audio/2024/08/15/audio_5a54d0f2f6.mp3?filename=upbeat-background-171614.mp3",
    "Luxury Chill": "https://uppbeat.io/assets/track/mp3/prigida-moving-on.mp3",
    "Modern Gold": "https://uppbeat.io/assets/track/mp3/synapse-fire-link-me-up.mp3",
    "Chirpy": "https://uppbeat.io/assets/track/mp3/ikson-new-world.mp3"
}

if "groq_key" not in st.secrets:
    st.error("Add `groq_key` in Secrets!")
    st.stop()

HEADERS = {"Authorization": f"Bearer {st.secrets['groq_key']}", "Content-Type": "application/json"}
GROQ_BASE = "https://api.groq.com/openai/v1"

@st.cache_resource
def get_rembg_session():
    return new_session()

def process_image_pro(img):
    with st.spinner("Removing background..."):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        out = remove(buf.getvalue(), session=get_rembg_session())
        clean = Image.open(io.BytesIO(out)).convert("RGBA")
        clean = ImageEnhance.Contrast(clean).enhance(1.15)
        clean = ImageEnhance.Sharpness(clean).enhance(1.5)
    return clean

def get_font(size):
    for path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "arial.ttf"]:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()

def ease_out_elastic(t):
    if t <= 0: return 0
    if t >= 1: return 1
    c4 = (2 * math.pi) / 3
    return math.pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

BRAND_PRIMARY = "#4C3B30"
BRAND_ACCENT = "#D2A544"

TEMPLATES = {
    "SM Classic": {"bg_grad": [BRAND_PRIMARY, "#2a201b"], "accent": BRAND_ACCENT, "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "none"},
    "Gold Diagonal": {"bg_grad": [BRAND_PRIMARY, "#3e2e24"], "accent": BRAND_ACCENT, "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "diagonal", "graphic_color": BRAND_ACCENT},
    "Gold Circles": {"bg_grad": [BRAND_PRIMARY, "#332A22"], "accent": BRAND_ACCENT, "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "circular", "graphic_color": BRAND_ACCENT},
    "Gold Split": {"bg_grad": [BRAND_PRIMARY, BRAND_PRIMARY], "accent": "#FFFFFF", "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "split", "graphic_color": BRAND_ACCENT},
}

def ask_groq(payload):
    try:
        r = requests.post(f"{GROQ_BASE}/chat/completions", json=payload, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except:
        return None

def get_data_groq(img, model_name):
    buf = io.BytesIO()
    rgb = img.convert("RGB")
    rgb.save(buf, format="JPEG", quality=90)
    b64 = base64.b64encode(buf.getvalue()).decode()

    hook_payload = {
        "model": "llama-3.2-11b-vision-preview",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": f"Write a 4–6 word luxury hook for this {model_name}."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
        ]}],
        "max_tokens": 30
    }
    hook = ask_groq(hook_payload) or "Timeless Comfort Awaits"

    layout_payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Return ONLY a JSON list of layout objects with keys: role, x, y, w, h"},
            {"role": "user", "content": f"720×1280 ad. Roles: logo, product, caption, price, contact. Center product. Product: {model_name}"}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2
    }
    raw = ask_groq(layout_payload)

    # BULLETPROOF DEFAULT LAYOUT
    DEFAULT_LAYOUT = [
        {"role": "logo", "x": 50, "y": 50, "w": 200, "h": 100},
        {"role": "product", "x": 60, "y": 250, "w": 600, "h": 600},
        {"role": "caption", "x": 60, "y": 900, "w": 600, "h": 100},
        {"role": "price", "x": 160, "y": 1050, "w": 400, "h": 120},
        {"role": "contact", "x": 60, "y": 1200, "w": 600, "h": 60}
    ]

    if not raw:
        return hook, DEFAULT_LAYOUT

    try:
        data = json.loads(raw)
        layout = data if isinstance(data, list) else data.get("layout", DEFAULT_LAYOUT)
        # Ensure every box has x,y,w,h
        for box in layout:
            box.setdefault("x", 0)
            box.setdefault("y", 0)
            box.setdefault("w", 100)
            box.setdefault("h", 100)
        return hook.strip('"'), layout
    except:
        return hook, DEFAULT_LAYOUT

def draw_wrapped_text(draw, text, box, font, color):
    lines = []
    words = text.split()
    line = ""
    for word in words:
        test = line + (" " + word if line else word)
        if draw.textbbox((0,0), test, font=font)[2] <= box['w']:
            line = test
        else:
            lines.append(line)
            line = word
    if line: lines.append(line)
    y = box['y']
    for line in lines:
        w = draw.textbbox((0,0), line, font=font)[2]
        draw.text((box['x'] + (box['w'] - w)//2, y), line, font=font, fill=color)
        y += draw.textbbox((0,0), line, font=font)[3] + 10

def create_frame(t, img, boxes, texts, tpl_name):
    T = TEMPLATES[tpl_name]
    canvas = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(canvas)

    # Gradient background
    def hex_to_rgb(h): 
        h = h.lstrip('#'); return tuple(int(h[i:i+2], 16) for i in (0,2,4))
    c1 = hex_to_rgb(T["bg_grad"][0])
    c2 = hex_to_rgb(T["bg_grad"][1])
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        col = tuple(int(c1[i] + (c2[i] - c1[i]) * ratio) for i in range(3))
        draw.line([(0,y), (WIDTH,y)], fill=col)

    gc = hex_to_rgb(T.get("graphic_color", "#000000")) if "graphic_color" in T else None

    if T["graphic_type"] == "diagonal" and gc:
        alpha = int(255 * (t > 0.5))
        for i in range(-WIDTH, WIDTH+HEIGHT, 80):
            draw.line([(i,0), (i+HEIGHT,HEIGHT)], fill=(*gc, alpha), width=10)

    if T["graphic_type"] == "circular" and gc:
        alpha = int(180 * (t > 0.7))
        big = int(WIDTH * 1.6 * ease_out_elastic(max(0, t-0.4)))
        draw.ellipse([WIDTH*0.8-big//2, HEIGHT*0.7-big//2, WIDTH*0.8+big//2, HEIGHT*0.7+big//2], fill=(*gc, alpha))

    # SAFE BOX LOOP — THIS FIXES YOUR KEYERROR
    for b in boxes:
        role = b.get("role", "")
        x = b.get("x", 0)
        y = b.get("y", 0)
        w = b.get("w", 100)
        h = b.get("h", 100)

        if role == "product":
            scale = ease_out_elastic(min(t * 1.3, 1.0))
            if scale > 0.02:
                pw, ph = int(w * scale), int(h * scale)
                prod = img.resize((pw, ph), Image.LANCZOS)
                shadow = prod.copy().convert("L")
                shadow = ImageOps.invert(shadow).point(lambda p: p * 0.3).convert("RGBA")
                shadow = shadow.filter(ImageFilter.GaussianBlur(20))
                canvas.paste(shadow, (x + (w-pw)//2 + 15, y + (h-ph)//2 + 50), shadow)
                canvas.paste(prod, (x + (w-pw)//2, y + (h-ph)//2 + int(math.sin(t*3)*12)), prod)

        elif role == "price" and t > 1.4:
            draw.rounded_rectangle([x, y, x+w, y+h], radius=30, fill=T["price_bg"])
            draw_wrapped_text(draw, texts["price"], {"x": x, "y": y, "w": w, "h": h}, get_font(68), T["price_text"])

        elif role == "caption" and t > 1.0:
            draw_wrapped_text(draw, texts["caption"], {"x": x, "y": y, "w": w, "h": h}, get_font(52), T["accent"])

        elif role == "contact" and t > 2.3:
            draw_wrapped_text(draw, texts["contact"], {"x": x, "y": y, "w": w, "h": h}, get_font(32), T["text"])

        elif role == "logo":
            try:
                logo = Image.open(io.BytesIO(requests.get(LOGO_URL, timeout=8).content)).convert("RGBA").resize((w, h), Image.LANCZOS)
                canvas.paste(logo, (x, y), logo)
            except: pass

    # Vignette
    vig = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
    vdraw = ImageDraw.Draw(vig)
    for y in range(int(HEIGHT*0.65), HEIGHT):
        a = int(220 * (y - HEIGHT*0.65) / (HEIGHT*0.35))
        vdraw.line([(0,y), (WIDTH,y)], fill=(0,0,0,a))
    canvas.paste(vig, (0,0), vig)

    return np.array(canvas)

# ================================
# UI
# ================================
st.title("AdGen EVO – SM Interiors")
with st.sidebar:
    st.header("Generator")
    u_file = st.file_uploader("Product Image", ["png","jpg","jpeg"])
    u_model = st.text_input("Name", "Serenity Sleeper Crib")
    u_price = st.text_input("Price", "Ksh 12,500")
    u_contact = st.text_input("Contact", "0710895737")
    u_style = st.selectbox("Template", list(TEMPLATES.keys()))
    u_music = st.selectbox("Music", list(MUSIC_TRACKS.keys()))
    btn = st.button("Generate Luxury Ad", type="primary")

if btn and u_file:
    status = st.status("Working...", expanded=True)
    raw = Image.open(u_file).convert("RGBA")
    status.update(label="Processing image...")
    product_img = process_image_pro(raw)
    st.image(product_img, "Clean Product", width=250)

    status.update(label="AI thinking...")
    hook, layout = get_data_groq(product_img, u_model)
    st.write(f"**Hook:** {hook}")

    status.update(label="Rendering animation...")
    texts = {"caption": hook, "price": u_price, "contact": u_contact}
    frames = [create_frame(i/FPS, product_img, layout, texts, u_style) for i in range(FPS*DURATION)]
    clip = ImageSequenceClip(frames, fps=FPS)

    status.update(label="Adding music...")
    try:
        audio = requests.get(MUSIC_TRACKS[u_music]).content
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(audio)
            final = clip.set_audio(AudioFileClip(tmp.name).subclip(0, DURATION).audio_fadeout(0.8))
            os.unlink(tmp.name)
    except:
        final = clip

    status.update(label="Exporting...")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        final.write_videofile(tmp.name, codec="libx264", audio_codec="aac", fps=FPS, logger=None, verbose=False)
        st.video(tmp.name)
        with open(tmp.name, "rb") as f:
            st.download_button("Download Ad", f, f"SM_{u_model.replace(' ', '_')}.mp4", "video/mp4")
        os.unlink(tmp.name)

    status.update(label="Done!", state="complete")
    st.balloons()
elif btn:
    st.error("Upload image first!")

st.caption("AdGen EVO – 2025 Fixed & Unbreakable")