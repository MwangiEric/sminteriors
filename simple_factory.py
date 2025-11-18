import streamlit as st, io, requests, math, tempfile, base64, json
from PIL import Image, ImageDraw
import numpy as np
import imageio

st.set_page_config(page_title="S&M Mistral Layout", layout="centered")
st.title("🎬 Mistral AI Layout + 6s Video")

# ---------- CONFIG ----------
WIDTH, HEIGHT = 720, 1280
FPS, DURATION = 30, 6
N_FRAMES = DURATION * FPS
BRAND_NAVY = "#001F54"
BRAND_GOLD = "#D4AF37"
BRAND_WHITE = "#FFFFFF"
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

# ---------- MISTRAL ----------
if "mistral_key" not in st.secrets:
    st.error("Add mistral_key to Secrets (https://console.mistral.ai → free tier)"); st.stop()

from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

client = MistralClient(api_key=st.secrets["mistral_key"])

def mistral_caption(img_b64):
    msgs = [ChatMessage(role="user", content=[
        {"type": "text", "text": "Describe this furniture in one catchy sentence for a TikTok ad (≤15 words)."},
        {"type": "image_url", "image_url": f"data:image/png;base64,{img_b64}"}
    ])]
    resp = client.chat(model="pixtral-12b-2409", messages=msgs)
    return resp.choices[0].message.content.strip()

def mistral_layout(model, price):
    msgs = [ChatMessage(role="user", text=f"""
Canvas 720×1280 px.
Elements: logo, product image, price text, contact text.
Return ONLY a JSON list:
[{{"role":"logo","x":int,"y":int,"w":int,"h":int}},
 {{"role":"product","x":int,"y":int,"w":int,"h":int}},
 {{"role":"price","x":int,"y":int,"w":int,"h":int}},
 {{"role":"contact","x":int,"y":int,"w":int,"h":int}}]
Model: {model}, Price: {price}.
Avoid centre-safe-zone (100 px margin).
""")]
    resp = client.chat(model="mistral-large-latest", messages=msgs)
    return json.loads(resp.choices[0].message.content)

# ---------- UI ----------
uploaded = st.file_uploader("Product PNG (transparent best)", type=["png"])
model   = st.text_input("Product name", "Modern Corner Sofa")
price   = st.text_input("Price", "KES 14 500")
contact = st.text_input("Contact", "0710 338 377 | sminteriors.co.ke")
generate = st.button("Generate AI Layout + 6s MP4", type="primary")

# ---------- DRAW ----------
def draw_frame(t, img, boxes, price, contact):
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # navy → gold gradient
    for y in range(HEIGHT):
        blend = y / HEIGHT
        r = int((0x00) * (1 - blend) + 0xD4 * blend)
        g = int((0x1F) * (1 - blend) + 0xAF * blend)
        b = int((0x54) * (1 - blend) + 0x37 * blend)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    # logo (AI coords)
    logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
    for b in boxes:
        if b["role"] == "logo":
            logo = logo.resize((b["w"], b["h"]), Image.LANCZOS)
            canvas.paste(logo, (b["x"], b["y"]), logo)

    # product (AI coords + pulse)
    for b in boxes:
        if b["role"] == "product":
            scale = 0.9 + 0.1 * math.sin(t * 2 * math.pi / 6)
            w, h = int(b["w"] * scale), int(b["h"] * scale)
            prod = img.resize((w, h), Image.LANCZOS)
            x = b["x"] + (b["w"] - w) // 2
            y = b["y"] + (b["h"] - h) // 2
            canvas.paste(prod, (x, y), prod.convert("RGBA"))

    # price (AI coords + bounce)
    for b in boxes:
        if b["role"] == "price":
            bounce = int(10 * math.sin(t * 3 * math.pi / 6))
            draw.rounded_rectangle([(b["x"], b["y"] + bounce), (b["x"] + b["w"], b["y"] + b["h"] + bounce)], radius=18, fill=BRAND_GOLD)
            draw.text((b["x"] + b["w"] // 2, b["y"] + b["h"] // 2 + bounce), price, fill=BRAND_WHITE, anchor="mm", size=44)

    # contact (AI coords)
    for b in boxes:
        if b["role"] == "contact":
            draw.text((b["x"], b["y"] + b["h"] // 2), contact, fill=BRAND_WHITE, size=30)

    return np.array(canvas)

def make_6s_video(img, model, price, contact):
    # AI layout
    with st.spinner("AI choosing layout…"):
        caption = mistral_caption(base64.b64encode(img.tobytes()).decode())
        boxes = mistral_layout(model, price)
    st.success("AI caption: " + caption)
    st.json(boxes)

    # frames
    frames = []
    for i in range(N_FRAMES):
        t = i / FPS
        frame = draw_frame(t, img, boxes, price, contact)
        frames.append(frame)

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        imageio.mimsave(tmp.name, frames, fps=FPS, codec="libx264", pixelformat="yuv420p")
        return tmp.name, caption

# ---------- RUN ----------
if generate:
    if not uploaded:
        st.error("Upload product PNG"); st.stop()
    im = Image.open(uploaded)
    tmp_path, ai_caption = make_6s_video(im, model, price, contact)
    st.video(tmp_path)
    with open(tmp_path, "rb") as f:
        st.download_button("⬇️ AI-layout MP4", data=f, file_name="sm_ai_layout.mp4", mime="video/mp4")
