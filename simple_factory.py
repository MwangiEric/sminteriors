import streamlit as st, io, requests, math, tempfile, base64, json
from PIL import Image, ImageDraw
import numpy as np
import imageio

st.set_page_config(page_title="S&M Mistral Ads", layout="centered")
st.title("S&M Interiors × Mistral AI")
st.caption("Upload product → AI writes hook + designs layout → 6s TikTok MP4 in seconds")

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

# ---------- HTTP helpers ----------
def ask_mistral(payload):
    r = requests.post("https://api.mistral.ai/v1/chat/completions", json=payload, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

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

# ---------- UI ----------
uploaded = st.file_uploader("Product PNG (transparent best)", type=["png"])
model   = st.text_input("Product Name", "Modern Corner Sofa")
price   = st.text_input("Price", "KES 14,500")
contact = st.text_input("Contact", "0710 338 377 • sminteriors.co.ke")
generate = st.button("Generate 6s AI Video", type="primary", use_container_width=True)

# ---------- Draw one frame ----------
def draw_frame(t, img, boxes, price, contact, caption):
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
    draw = ImageDraw.Draw(canvas)

    # Navy → gold gradient
    for y in range(HEIGHT):
        blend = y / HEIGHT
        r = int(0 + 212 * blend)
        g = int(31 + 168 * blend)
        b = int(84 - 47 * blend)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
    for b in boxes:
        if b["role"] == "logo":
            logo_resized = logo.resize((b["w"], b["h"]))
            canvas.paste(logo_resized, (b["x"], b["y"]), logo_resized)

        if b["role"] == "product":
            scale = 0.94 + 0.06 * math.sin(t * math.pi * 2 / DURATION)
            w2 = int(b["w"] * scale)
            h2 = int(b["h"] * scale)
            prod = img.resize((w2, h2))
            canvas.paste(prod, (b["x"] + (b["w"]-w2)//2, b["y"] + (b["h"]-h2)//2), prod)

        if b["role"] == "price":
            bounce = 10 * math.sin(t * 3 * math.pi / DURATION)
            draw.rounded_rectangle([b["x"], b["y"]+bounce, b["x"]+b["w"], b["y"]+b["h"]+bounce], radius=20, fill="#D4AF37")
            draw.text((b["x"]+b["w"]//2, b["y"]+b["h"]//2+bounce), price, fill="white", anchor="mm", font_size=68)

        if b["role"] == "contact":
            draw.text((b["x"]+b["w"]//2, b["y"]+b["h"]//2), contact, fill="white", anchor="mm", font_size=36)

    # Caption at top
    draw.text((WIDTH//2, 100), caption.upper(), fill="white", anchor="mt", font_size=56, stroke_width=3, stroke_fill="black")
    return np.array(canvas)

# --- Generate ---
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

    st.success(f"AI Hook: **{caption}**")
    st.json(boxes)

    with st.spinner("Rendering video..."):
        frames = [draw_frame(i/FPS, img, boxes, price, contact, caption) for i in range(DURATION * FPS)]

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        imageio.imwrite(tmp.name, frames, fps=FPS, codec="libx264", pixelformat="yuv420p")
        video_path = tmp.name

    st.video(video_path)
    with open(video_path, "rb") as f:
        st.download_button("Download MP4", f, f"{model.replace(' ', '_')}_ad.mp4", "video/mp4")

    st.balloons()
