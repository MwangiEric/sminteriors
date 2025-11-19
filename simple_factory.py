import streamlit as st, io, requests, math, tempfile, base64, json, random, time
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import imageio.v3 as imageio

st.set_page_config(page_title="S&M Canva Factory", layout="centered")
st.title("🎬 Canva-Quality AI Ads")
st.caption("Upload any photo → AI removes BG → writes hook → Canva animations → 6s MP4")

WIDTH, HEIGHT = 720, 1280
FPS = 30
DURATION = 6
N_FRAMES = FPS * DURATION
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

if "mistral_key" not in st.secrets:
    st.error("Add `mistral_key` in Secrets (free at console.mistral.ai)")
    st.stop()
HEADERS = {"Authorization": f"Bearer {st.secrets['mistral_key']}", "Content-Type": "application/json"}

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
720×1280 canvas. Return ONLY this JSON (no overlap):
[{{"role":"logo","x":0,"y":0,"w":0,"h":0}},
 {{"role":"product","x":0,"y":0,"w":0,"h":0}},
 {{"role":"price","x":0,"y":0,"w":0,"h":0}},
 {{"role":"contact","x":0,"y":0,"w":0,"h":0}}]
Product: {model} | Price: {price}
Ensure **no overlap** between boxes. Keep 50 px margin.
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

# ---------- Remove BG (free) ----------
def remove_bg(pil_im):
    buf = io.BytesIO()
    pil_im.save(buf, format="PNG")
    buf.seek(0)
    r = requests.post("https://api.pixian.ai/remove", files={"image": ("in.png", buf, "image/png")})
    if r.headers.get("Content-Type") != "image/png":
        return pil_im  # fallback
    return Image.open(io.BytesIO(r.content))

# ---------- Proportional logo ----------
def proportional_resize(im, max_h):
    aspect = im.width / im.height
    new_h = max_h
    new_w = int(aspect * new_h)
    return im.resize((new_w, new_h), Image.LANCZOS)

# ---------- Animated background ----------
def draw_circles(draw, t, template):
    T = TEMPLATES[template]
    n = 8
    for i in range(n):
        angle = t * 0.3 + i * 0.8
        x = int(WIDTH // 2 + math.cos(angle) * 400)
        y = int(HEIGHT * 0.5 + math.sin(angle) * 300)
        r = 20 + i * 6
        alpha = int(255 * (0.15 - i * 0.01))
        color = T["accent"] + f"{alpha:02x}"
        draw.ellipse([(x - r, y - r), (x + r, y + r)], fill=color)

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

    # 3. Logo (proportional + shadow)
    logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
    for b in boxes:
        if b["role"] == "logo":
            logo = proportional_resize(logo, b["h"])
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

    # 7. Animated circles (free)
    draw_circles(draw, t, template)

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
