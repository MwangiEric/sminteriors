import streamlit as st, io, requests, math, tempfile
from PIL import Image, ImageDraw
import numpy as np
import imageio

st.set_page_config(page_title="S&M Pixel-Perfect 6s", layout="centered")
st.title("🎯 Pixel-Perfect 6s Video")

WIDTH, HEIGHT = 720, 1280
FPS, DURATION = 30, 6
N_FRAMES = DURATION * FPS
NAVY, GOLD, WHITE = "#001F54", "#D4AF37", "#FFFFFF"
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

uploaded = st.file_uploader("Product PNG (transparent best)", type=["png"])
price   = st.text_input("Price (bottom-left)", "KES 14 500")
contact = st.text_input("Contact (bottom-right)", "0710 338 377 | sminteriors.co.ke")
generate = st.button("Generate 6s MP4", type="primary")

def draw_frame(t, img):
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # navy → gold gradient
    for y in range(HEIGHT):
        blend = y / HEIGHT
        r = int((0x00) * (1 - blend) + 0xD4 * blend)
        g = int((0x1F) * (1 - blend) + 0xAF * blend)
        b = int((0x54) * (1 - blend) + 0x37 * blend)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    # 1 LOGO (fixed top-left)
    logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
    logo = logo.resize((200, 80), Image.LANCZOS)
    canvas.paste(logo, (60, 60), logo)

    # 2 PRODUCT (fixed centre + pulse)
    if img:
        scale = 0.9 + 0.1 * math.sin(t * 2 * math.pi / DURATION)
        base = img.resize((420, 420), Image.LANCZOS)   # fixed box
        prod = base.resize((int(420 * scale), int(420 * scale)), Image.LANCZOS)
        x = (WIDTH - prod.width) // 2
        y = 420                                        # fixed vertical centre
        canvas.paste(prod, (x, y), prod)

    # 3 PRICE (fixed bottom-left)
    bounce = int(10 * math.sin(t * 3 * math.pi / DURATION))
    draw.rounded_rectangle([(80, HEIGHT - 200 + bounce), (WIDTH - 400, HEIGHT - 100 + bounce)], radius=18, fill=GOLD)
    draw.text((250, HEIGHT - 150 + bounce), price, fill=WHITE, anchor="mm", size=44)

    # 4 CONTACT (fixed bottom-right)
    draw.text((WIDTH - 400, HEIGHT - 150), contact, fill=WHITE, size=30)

    return np.array(canvas)

def make_6s_video(img):
    frames = []
    for i in range(N_FRAMES):
        t = i / FPS
        frame = draw_frame(t, img)
        frames.append(frame)
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        imageio.mimsave(tmp.name, frames, fps=FPS, codec="libx264", pixelformat="yuv420p")
        return tmp.name

if generate:
    if not uploaded:
        st.error("Upload product PNG"); st.stop()
    im = Image.open(uploaded)
    with st.spinner("Rendering 6s video…"):
        tmp_path = make_6s_video(im)
    st.video(tmp_path)
    with open(tmp_path, "rb") as f:
        st.download_button("⬇️ 6s MP4", data=f, file_name="sm_6s.mp4", mime="video/mp4")
