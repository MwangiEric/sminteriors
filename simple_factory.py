import streamlit as st, tempfile, io, requests, math
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import imageio

st.set_page_config(page_title="S&M Video Layout", layout="centered")
st.title("🎬 S&M Video Layout (Cloud-safe)")

# ---------- CONFIG ----------
WIDTH, HEIGHT = 720, 1280
FPS = 30
BRAND_NAVY = "#001F54"
BRAND_GOLD = "#D4AF37"
BRAND_WHITE = "#FFFFFF"
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

# ---------- UI ----------
uploaded_imgs = st.file_uploader("Product PNGs (1-5)", type=["png"], accept_multiple_files=True)
model   = st.text_input("Product name", "Modern Corner Sofa")
price   = st.text_input("Price", "KES 14 500")
contact = st.text_input("Contact", "0710 338 377 | sminteriors.co.ke")
features = st.text_area("Features (one per line)", "ALL-WHEEL DRIVE\nADVANCED SAFETY\nPANORAMIC ROOF").splitlines()
duration = st.slider("Seconds per photo", 4, 8, 6)
template = st.selectbox("Background style", ["Pop", "Luxury", "Minimal"])
generate = st.button("Generate Video", type="primary")

# ---------- DRAW ----------
def draw_frame(t, idx, total, img, model, price, contact, features, template):
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # background gradient
    if template == "Pop":
        grad = ImageDraw.LinearGradient((0, 0, 0, HEIGHT), [(0, "#071025"), (0.5, "#0f1c2f"), (1, "#1e3fae")])
    elif template == "Luxury":
        grad = ImageDraw.LinearGradient((0, 0, 0, HEIGHT), [(0, "#04080f"), (1, "#091426")])
    else:
        grad = ImageDraw.LinearGradient((0, 0, 0, HEIGHT), [(0, "#f6f7f9"), (1, "#e9eef6")])
    draw.rectangle([(0, 0), (WIDTH, HEIGHT)], fill=grad)

    # soft background copy (blurred)
    if img:
        bg = img.resize((WIDTH, int(HEIGHT * 0.55)), Image.LANCZOS).filter(ImageFilter.GaussianBlur(12))
        canvas.paste(bg, (0, int(HEIGHT * 0.22)), bg.convert("RGBA"))

    # product pulse
    if img:
        scale = 0.9 + 0.1 * math.sin(t * 1.2 + idx)
        w, h = img.size
        new_w, new_h = int(w * scale), int(h * scale)
        prod = img.resize((new_w, new_h), Image.LANCZOS)
        x = (WIDTH - new_w) // 2
        y = int(HEIGHT * 0.28)
        canvas.paste(prod, (x, y), prod.convert("RGBA"))

    # logo top-right
    logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
    logo = logo.resize((180, 70), Image.LANCZOS)
    canvas.paste(logo, (WIDTH - 200, 50), logo)

    # price bottom-right
    draw.rectangle([(WIDTH - 290, HEIGHT - 140), (WIDTH - 30, HEIGHT - 30)], fill=BRAND_GOLD, radius=18)
    draw.text((WIDTH - 160, HEIGHT - 85), price, fill=BRAND_WHITE, anchor="mm", size=44)

    # contact bottom-left
    draw.text((70, HEIGHT - 150), contact, fill=BRAND_WHITE, size=30)

    # features left strip
    y_start = 200
    for i, feat in enumerate(features[:3]):
        badge = Image.new("RGBA", (360, 60), (0, 0, 0, 0))
        bdraw = ImageDraw.Draw(badge)
        bdraw.rounded_rectangle([(0, 0), (360, 60)], radius=14, fill="#005ea8")
        bdraw.text((40, 30), feat, fill="#051019", anchor="lm", size=21)
        canvas.paste(badge, (40, y_start + i * 72), badge)

    return np.array(canvas)

# ---------- IMAGEIO VIDEO ----------
def make_video(imgs, model, price, contact, features, duration, template):
    total_frames = int(len(imgs) * duration * FPS)
    frames = []
    for i in range(total_frames):
        t = i / FPS
        idx = int(t // duration) % len(imgs)
        frame = draw_frame(t, idx, len(imgs), imgs[idx], model, price, contact, features, template)
        frames.append(frame)
    # write MP4 with imageio-ffmpeg (pre-installed on Cloud)
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        imageio.mimsave(tmp.name, frames, fps=FPS, codec="libx264", pixelformat="yuv420p")
        return tmp.name

# ---------- RUN ----------
if generate:
    if not uploaded_imgs:
        st.error("Upload at least one PNG"); st.stop()
    imgs = [Image.open(f) for f in uploaded_imgs]
    with st.spinner("Rendering video…"):
        tmp_path = make_video(imgs, model, price, contact, features, duration, template)
    st.video(tmp_path)
    with open(tmp_path, "rb") as f:
        st.download_button("⬇️ MP4", data=f, file_name="sm_promo.mp4", mime="video/mp4")
