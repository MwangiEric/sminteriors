import streamlit as st, tempfile, io, requests, math
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import *

st.set_page_config(page_title="S&M Video Layout", layout="centered")
st.title("🎬 Video Layout Generator")

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
def draw_frame(ctx, img, t, idx, total, model, price, contact, features, template):
    # background gradient
    if template == "Pop":
        grad = ctx.linear_gradient(0, 0, 0, HEIGHT, [(0, "#071025"), (0.5, "#0f1c2f"), (1, "#1e3fae")])
    elif template == "Luxury":
        grad = ctx.linear_gradient(0, 0, 0, HEIGHT, [(0, "#04080f"), (1, "#091426")])
    else:  # Minimal
        grad = ctx.linear_gradient(0, 0, 0, HEIGHT, [(0, "#f6f7f9"), (1, "#e9eef6")])
    ctx.rectangle([(0, 0), (WIDTH, HEIGHT)], fill=grad)

    # soft background copy (blurred)
    if img:
        bg = img.resize((WIDTH, int(HEIGHT * 0.55)), Image.LANCZOS)).filter(ImageFilter.GaussianBlur(12))
        ctx.paste(bg, (0, int(HEIGHT * 0.22)), bg.convert("RGBA"))

    # product pulse
    if img:
        scale = 0.9 + 0.1 * math.sin(t * 1.2 + idx)
        w, h = img.size
        new_w, new_h = int(w * scale), int(h * scale)
        prod = img.resize((new_w, new_h)), Image.LANCZOS))
        x = (WIDTH - new_w) // 2
        y = int(HEIGHT * 0.28)
        ctx.paste(prod, (x, y), prod.convert("RGBA"))

    # logo top-right
    logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
    logo = logo.resize((180, 70), Image.LANCZOS))
    ctx.paste(logo, (WIDTH - 200, 50), logo)

    # price bottom-right
    draw = ImageDraw.Draw(ctx)
    font_big = ImageFont.load_default()
    badge = Image.new("RGBA", (260, 110), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(badge)
    bdraw.rounded_rectangle([(0, 0), (260, 110)], radius=18, fill=BRAND_GOLD)
    bdraw.text((130, 55), price, font=font_big, fill=BRAND_WHITE, anchor="mm", size=44)
    ctx.paste(badge, (WIDTH - 290, HEIGHT - 140), badge)

    # contact bottom-left
    draw.text((70, HEIGHT - 150), contact, font=font_big, fill=BRAND_WHITE, size=30)

    # features left strip
    y_start = 200
    for i, feat in enumerate(features[:3]):
        badge = Image.new("RGBA", (360, 60), (0, 0, 0, 0))
        bdraw = ImageDraw.Draw(badge)
        bdraw.rounded_rectangle([(0, 0), (360, 60)], radius=14, fill="#005ea8")
        bdraw.text((40, 30), feat, font=font_big, fill="#051019", anchor="lm", size=21)
        ctx.paste(badge, (40, y_start + i * 72), badge)

    return ctx

# ---------- MOVIEPY ----------
def make_video(imgs, model, price, contact, features, duration, template):
    def make_frame(t):
        idx = int(t // duration) % len(imgs)
        img = imgs[idx]
        canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        ctx = draw_frame(canvas, img, t, idx, len(imgs), model, price, contact, features, template)
        return np.array(canvas)

    clip = VideoClip(make_frame, duration=len(imgs) * duration)
    return clip

# ---------- RUN ----------
if generate:
    if not uploaded_imgs:
        st.error("Upload at least one PNG"); st.stop()
    imgs = [Image.open(f) for f in uploaded_imgs]
    with st.spinner("Rendering video…"):
        clip = make_video(imgs, model, price, contact, features, duration, template)
        buf = io.BytesIO()
        clip.write_videofile(buf, codec="libx264", audio_codec="aac", fps=FPS, preset="faster", threads=4, logger=None)
        buf.seek(0)
    st.video(buf)
    st.download_button("⬇️ MP4", data=buf, file_name="sm_promo.mp4", mime="video/mp4")
