import streamlit as st, io, requests, math, tempfile, base64, json, random, time
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import imageio.v3 as imageio

st.set_page_config(page_title="S&M Canva Factory", layout="centered")
st.title("🎬 Canva-Quality AI Ads")
st.caption("Upload any photo → AI removes BG → writes hook → Canva animations → 6s MP4")

# ---------- CONFIG ----------
WIDTH, HEIGHT = 720, 1280
FPS = 30
DURATION = 6
N_FRAMES = FPS * DURATION
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

# ---------- Secrets ----------
if "mistral_key" not in st.secrets:
    st.error("Add `mistral_key` in Secrets (free at console.mistral.ai)")
    st.stop()
HEADERS = {"Authorization": f"Bearer {st.secrets['mistral_key']}", "Content-Type": "application/json"}

# ---------- HTTP helpers (no SDK) ----------
def ask_mistral(payload):
    for attempt in range(1, 6):
        try:
            r = requests.post("https://api.mistral.ai/v1/chat/completions", json=payload, headers=HEADERS, timeout=60)
            if r.status_code == 429:
                time.sleep(2 ** attempt + random.uniform(0, 1))
                continue
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except:
            if attempt == 5:
                st.error("Mistral API failed after 5 retries")
                st.stop()
            time.sleep(2 ** attempt)
    st.stop()

def get_caption(img_b64):
    payload = {
        "model": "pixtral-12b-2409",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": "Describe this furniture in one short, catchy TikTok hook (max 12 words)."},
            {"type": "image_url", "image_url": f"data:image/png;base64,{img_b64}"}
        ]}],
        "max_tokens": 30
    }
    return ask_mistral(payload)

def get_layout(model, price):
    payload = {
        "model": "mistral-large-latest",
        "messages": [{"role": "user", "content": f"""
720×1280 canvas. Return ONLY this JSON (no extra text):
[{{"role":"logo","x":0,"y":0,"w":0,"h":0}},
 {{"role":"product","x":0,"y":0,"w":0,"h":0}},
 {{"role":"price","x":0,"y":0,"w":0,"h":0}},
 {{"role":"contact","x":0,"y":0,"w":0,"h":0}}]
Product: {model} | Price: {price}
Keep elements away from edges. Make it premium.
"""}],
        "max_tokens": 400
    }
    text = ask_mistral(payload)
    try:
        return json.loads(text)
    except:
        # fallback grid
        return [
            {"role": "logo",    "x": 40,  "y": 40,  "w": 240, "h": 120},
            {"role": "product", "x": 60,  "y": 180, "w": 600, "h": 780},
            {"role": "price",   "x": 60,  "y": 1000,"w": 600, "h": 140},
            {"role": "contact", "x": 60,  "y": 1160,"w": 600, "h": 80}
        ]

# ---------- Canva-like templates ----------
TEMPLATES = {
    "Canva Pop": {
        "bg_grad": ["#071025", "#1e3fae"],
        "accent": "#00e6ff",
        "text": "#ffffff",
        "price_bg": "#001225",
        "price_text": "#00e6ff",
        "caption_size": 56,
        "price_size": 68,
        "contact_size": 36,
        "shadow": True,
        "parallax": 0.06
    },
    "Canva Luxury": {
        "bg_grad": ["#04080f", "#091426"],
        "accent": "#d4af37",
        "text": "#ffffff",
        "price_bg": "#d4af37",
        "price_text": "#000000",
        "caption_size": 52,
        "price_size": 72,
        "contact_size": 34,
        "shadow": True,
        "parallax": 0.04
    },
    "Canva Minimal": {
        "bg_grad": ["#f6f7f9", "#e9eef6"],
        "accent": "#1e3fae",
        "text": "#1e3fae",
        "price_bg": "#1e3fae",
        "price_text": "#ffffff",
        "caption_size": 50,
        "price_size": 66,
        "contact_size": 32,
        "shadow": False,
        "parallax": 0.02
    }
}

# ---------- UI ----------
col1, col2 = st.columns(2)
with col1:
    uploaded = st.file_uploader("Product photo (PNG/JPG)", type=["png", "jpg", "jpeg"])
with col2:
    model   = st.text_input("Product Name", "Modern Corner Sofa")
    price   = st.text_input("Price", "KES 14,500")
    contact = st.text_input("Contact", "0710 338 377 • sminteriors.co.ke")
    template_choice = st.selectbox("Template", list(TEMPLATES.keys()))

generate = st.button("Generate 6s Canva MP4", type="primary", use_container_width=True)

# ---------- Helpers ----------
def ease_out_bounce(t):
    n1, d1 = 7.5625, 2.75
    if t < 1 / d1: return n1 * t * t
    elif t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375

def auto_fit_text(draw, text, x, y, w, h, start_size, color):
    size = start_size
    while size > 16:
        font = ImageFont.load_default() if size < 20 else ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        lines = []
        words = text.split()
        line = ""
        for wrd in words:
            test = line + " " + wrd if line else wrd
            if draw.textlength(test, font=font) <= w - 20:
                line = test
            else:
                lines.append(line)
                line = wrd
        if line:
            lines.append(line)
        line_h = size + 4
        total_h = len(lines) * line_h
        if total_h <= h - 10:
            y_off = y + (h - total_h) // 2
            for ln in lines:
                lx = x + (w - draw.textlength(ln, font=font)) // 2
                draw.text((lx, y_off), ln.upper(), fill=color, font=font, stroke_width=2, stroke_fill="black")
                y_off += line_h
            break
        size -= 2

# ---------- Remove BG (free) ----------
def remove_bg(pil_im):
    # 1. remove BG
    buf = io.BytesIO()
    pil_im.save(buf, format="PNG")
    buf.seek(0)
    r = requests.post("https://api.pixian.ai/remove", files={"image": ("in.png", buf, "image/png")})
    if r.headers.get("Content-Type") != "image/png":
        return pil_im  # fallback
    transparent = Image.open(io.BytesIO(r.content))

    # 2. upscale 4×
    buf2 = io.BytesIO()
    transparent.save(buf2, format="PNG")
    buf2.seek(0)
    out = replicate.run("nightmareai/real-esrgan:latest", input={"image": buf2, "scale": 4})
    return Image.open(requests.get(out, stream=True).raw)

# ---------- Draw one frame (RGBA → RGB) ----------
def draw_frame(t, img, boxes, price, contact, caption, template):
    T = TEMPLATES[template]
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # 1. Canva gradient background
    for y in range(HEIGHT):
        blend = y / HEIGHT
        r = int((int(T["bg_grad"][0][1:3], 16)) * (1 - blend) + int(T["bg_grad"][1][1:3], 16) * blend)
        g = int((int(T["bg_grad"][0][3:5], 16)) * (1 - blend) + int(T["bg_grad"][1][3:5], 16) * blend)
        b = int((int(T["bg_grad"][0][5:7], 16)) * (1 - blend) + int(T["bg_grad"][1][5:7], 16) * blend)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    # 2. Soft background copy (parallax)
    if img:
        bg = img.resize((WIDTH, int(HEIGHT * 0.55)), Image.LANCZOS).filter(ImageFilter.GaussianBlur(12))
        offset = int(T["parallax"] * WIDTH * math.sin(t * math.pi / DURATION))
        canvas.paste(bg, (offset, int(HEIGHT * 0.22)), bg.convert("RGBA"))

    # 3. Logo (Canva shadow + pulse)
    logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
    for b in boxes:
        if b["role"] == "logo":
            logo = logo.resize((b["w"], b["h"]), Image.LANCZOS)
            if T["shadow"]:
                shadow = logo.copy()
                shadow = shadow.filter(ImageFilter.GaussianBlur(6))
                canvas.paste(shadow, (b["x"] + 4, b["y"] + 4), shadow)
            canvas.paste(logo, (b["x"], b["y"]), logo)

    # 4. Product (Canva bounce + shadow)
    for b in boxes:
        if b["role"] == "product":
            scale = 0.94 + 0.06 * ease_out_bounce(t / DURATION)
            w2, h2 = int(b["w"] * scale), int(b["h"] * scale)
            prod = img.resize((w2, h2), Image.LANCZOS)
            x = b["x"] + (b["w"] - w2) // 2
            y = b["y"] + (b["h"] - h2) // 2
            if T["shadow"]:
                shadow = prod.copy()
                shadow = shadow.filter(ImageFilter.GaussianBlur(8))
                canvas.paste(shadow, (x + 8, y + 8), shadow)
            canvas.paste(prod, (x, y), prod.convert("RGBA"))

    # 5. Price (Canva badge + bounce)
    for b in boxes:
        if b["role"] == "price":
            bounce = int(10 * ease_out_bounce((t % 1) / 1))
            draw.rounded_rectangle([(b["x"], b["y"] + bounce), (b["x"] + b["w"], b["y"] + b["h"] + bounce)], radius=20, fill=T["price_bg"])
            draw.text((b["x"] + b["w"] // 2, b["y"] + b["h"] // 2 + bounce), price, fill=T["price_text"], anchor="mm", font_size=T["price_size"])

    # 6. Contact (Canva style)
    for b in boxes:
        if b["role"] == "contact":
            draw.text((b["x"] + b["w"] // 2, b["y"] + b["h"] // 2), contact, fill=T["text"], anchor="mm", font_size=T["contact_size"])

    # 7. Caption (auto-fit inside AI box)
    for b in boxes:
        if b["role"] == "caption":
            auto_fit_text(draw, caption, b["x"], b["y"], b["w"], b["h"], T["caption_size"], T["text"])

    # --- DROP ALPHA → RGB only ---
    rgb = np.array(canvas)[:, :, :3]
    return rgb

# ---------- Generate ----------
if generate:
    if not uploaded:
        st.error("Upload a product image first!")
        st.stop()

    img = Image.open(uploaded).convert("RGBA")

    with st.spinner("AI thinking..."):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        caption = get_caption(b64)
        boxes = get_layout(model, price)
        boxes.append({"role": "caption", "x": 60, "y": 80, "w": 600, "h": 100})  # add caption box

    st.success(f"AI Hook: **{caption}**")
    st.json(boxes)

    with st.spinner("Rendering Canva-style video..."):
        frames = [draw_frame(i / FPS, img, boxes, price, contact, caption, template_choice) for i in range(DURATION * FPS)]

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        imageio.imwrite(tmp.name, frames, fps=FPS, codec="libx264", pixelformat="yuv420p")
        video_path = tmp.name

    st.video(video_path)
    with open(video_path, "rb") as f:
        st.download_button("Download Canva MP4", f, f"{model.replace(' ', '_')}_canva.mp4", "video/mp4")

    st.balloons()
