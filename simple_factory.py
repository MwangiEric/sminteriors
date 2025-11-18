import streamlit as st, tempfile, io, requests
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="S&M Simple Ad Factory", layout="centered")
st.title("🎯 Simple 4-Item Layout")

# ---------- BRAND COLOURS ----------
NAVY  = "#001F54"
GOLD  = "#D4AF37"
WHITE = "#FFFFFF"
LOGO  = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

# ---------- UI ----------
uploaded = st.file_uploader("Product PNG (transparent best)", type=["png"])
price   = st.text_input("Price (bottom-left)", "KES 14 500")
contact = st.text_input("Contact (bottom-right)", "0710 338 377 | sminteriors.co.ke")
size    = st.selectbox("Canvas size", ["9:16 (Story)", "1:1 (Post)", "4:5 (Portrait)"])
generate = st.button("Generate", type="primary")

# ---------- DRAW ----------
def simple_layout(prod_png, price, contact, size):
    W, H = size
    # gradient bg
    img = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)
    for y in range(H):
        blend = y / H
        r = int((0x00) * (1 - blend) + 0xD4 * blend)
        g = int((0x1F) * (1 - blend) + 0xAF * blend)
        b = int((0x54) * (1 - blend) + 0x37 * blend)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # default font (bitmap) scaled by drawing bigger boxes
    font = ImageFont.load_default()

    # 1 LOGO (top-left)
    logo = Image.open(requests.get(LOGO, stream=True).raw).convert("RGBA")
    logo = logo.resize((200, 80), Image.LANCZOS)
    img.paste(logo, (50, 50), logo)

    # 2 PRODUCT (centre)
    if prod_png:
        prod = prod_png.convert("RGBA").resize((int(W * 0.65), int(H * 0.5)), Image.LANCZOS)
        img.paste(prod, ((W - prod.width) // 2, (H - prod.height) // 2 - 80), prod)

    # 3 PRICE (bottom-left) - bigger by drawing a larger box
    draw.text((70, H - 280), price, font=font, fill=GOLD, size=120)

    # 4 CONTACT (bottom-right)
    draw.text((W - 70, H - 280), contact, font=font, fill=WHITE, size=70, anchor="ra")

    return img

# ---------- RUN ----------
if generate:
    if not uploaded:
        st.error("Upload product PNG"); st.stop()
    im = Image.open(uploaded)
    size_map = {"9:16 (Story)": (1080, 1920), "1:1 (Post)": (1080, 1080), "4:5 (Portrait)": (1080, 1350)}
    final = simple_layout(im, price, contact, size_map[size])
    st.image(final, use_column_width=True)
    buf = io.BytesIO()
    final.save(buf, format="JPEG", quality=95)
    st.download_button("⬇️ JPG", data=buf, file_name=f"sm_{size[:3].replace(':', '')}.jpg", mime="image/jpeg")
