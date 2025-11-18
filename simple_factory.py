import streamlit as st, io, requests, math
from PIL import Image, ImageDraw
import numpy as np
import imageio

st.set_page_config(page_title="S&M 6s Video", layout="centered")
st.title("🎬 6-second Video Generator")

# ---------- CONFIG ----------
WIDTH, HEIGHT = 720, 1280
FPS = 30
DURATION = 6  # seconds
N_FRAMES = DURATION * FPS
BRAND_NAVY = "#001F54"
BRAND_GOLD = "#D4AF37"
BRAND_WHITE = "#FFFFFF"
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

# ---------- UI ----------
uploaded = st.file_uploader("Product PNG (transparent best)", type=["png"])
model   = st.text_input("Product name", "Modern Corner Sofa")
price   = st.text_input("Price", "KES 14 500")
contact = st.text_input("Contact", "0710 338 377 | sminteriors.co.ke")
generate = st.button("Generate 6s MP4", type="primary")

# ---------- DRAW ----------
def draw_frame(t, img, model, price, contact):
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # navy → gold gradient
    for y in range(HEIGHT):
        blend = y / HEIGHT
        r = int((0x00) * (1 - blend) + 0xD4 * blend)
        g = int((0x1F) * (1 - blend) + 0xAF * blend)
        b = int((0x54) * (1 - blend) + 0x37 * blend)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    # logo top-left
    logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
    logo = logo.resize((180, 70), Image.LANCZOS)
    canvas.paste(logo, (60, 60), logo)

    # product centre + pulse
    if img:
        scale = 0.9 + 0.1 * math.sin(t * 2 * math.pi / DURATION)
        w, h = img.size
        new_w, new_h = int(w * scale), int(h * scale)
        prod = img.convert("RGBA").resize((new_w, new_h), Image.LANCZOS)
        x = (WIDTH - new_w) // 2
        y = int(HEIGHT * 0.28)
        canvas.paste(prod, (x, y), prod)

    # price bottom-right + bounce
    bounce = int(10 * math.sin(t * 3 * math.pi / DURATION))
    draw.rounded_rectangle([(WIDTH - 290, HEIGHT - 140 + bounce), (WIDTH - 30, HEIGHT - 30 + bounce)], radius=18, fill=BRAND_GOLD)
    draw.text((WIDTH - 160, HEIGHT - 85 + bounce), price, fill=BRAND_WHITE, anchor="mm", size=44)

    # contact bottom-left
    draw.text((70, HEIGHT - 150), contact, fill=BRAND_WHITE, size=30)

    return np.array(canvas)

# ---------- IMAGEIO VIDEO ----------
def make_6s_video(img):
    frames = []
    for i in range(N_FRAMES):
        t = i / FPS
        frame = draw_frame(t, img, "Modern Corner Sofa", "KES 14 500", "0710 338 377 | sminteriors.co.ke")
        frames.append(frame)
    # write MP4 with imageio-ffmpeg (pre-installed on Cloud)
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        imageio.mimsave(tmp.name, frames, fps=FPS, codec="libx264", pixelformat="yuv420p")
        return tmp.name

# ---------- RUN ----------
if generate:
    if not uploaded:
        st.error("Upload product PNG"); st.stop()
    im = Image.open(uploaded)
    with st.spinner("Rendering 6s video…"):
        tmp_path = make_6s_video(im)
    st.video(tmp_path)
    with open(tmp_path, "rb") as f:
        st.download_button("⬇️ 6s MP4", data=f, file_name="sm_6s.mp4", mime="video/mp4")
