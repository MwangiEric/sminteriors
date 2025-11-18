import streamlit as st, io, requests
from PIL import Image, ImageDraw

st.set_page_config(page_title="S&M 4-Item JPG", layout="centered")
st.title("🎯 4-Item JPG Generator")

# ---------- CONFIG ----------
NAVY  = "#001F54"
GOLD  = "#D4AF37"
WHITE = "#FFFFFF"
LOGO  = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

# ---------- UI ----------
uploaded = st.file_uploader("Product PNG (transparent best)", type=["png"])
price   = st.text_input("Price (bottom-left)", "KES 14 500")
contact = st.text_input("Contact (bottom-right)", "0710 338 377 | sminteriors.co.ke")
size    = st.selectbox("Size", ["9:16", "1:1", "4:5"])
go      = st.button("Generate JPG", type="primary")

# ---------- DRAW ----------
def four_item_jpg(prod, price, contact, size):
    W, H = size
    img  = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)
    # simple gradient
    for y in range(H):
        blend = y / H
        r = int((0x00) * (1 - blend) + 0xD4 * blend)
        g = int((0x1F) * (1 - blend) + 0xAF * blend)
        b = int((0x54) * (1 - blend) + 0x37 * blend)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # logo top-left
    logo = Image.open(requests.get(LOGO, stream=True).raw).convert("RGBA")
    logo = logo.resize((200, 80), Image.LANCZOS)
    img.paste(logo, (60, 60), logo)

    # product centre
    if prod:
        prod = prod.convert("RGBA").resize((int(W * 0.65), int(H * 0.5)), Image.LANCZOS)
        img.paste(prod, ((W - prod.width) // 2, (H - prod.height) // 2 - 80), prod)

    # price bottom-left
    draw.text((80, H - 250), price, fill=GOLD, size=120)
    # contact bottom-right
    draw.text((W - 80, H - 250), contact, fill=WHITE, size=70, anchor="ra")

    return img

# ---------- RUN ----------
if go:
    if not uploaded:
        st.error("Upload product PNG"); st.stop()
    im = Image.open(uploaded)
    size_map = {"9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350)}
    final = four_item_jpg(im, price, contact, size_map[size])
    st.image(final, use_column_width=True)
    buf = io.BytesIO()
    final.save(buf, format="JPEG", quality=95)
    st.download_button("⬇️ JPG", data=buf, file_name=f"sm_{size}.jpg", mime="image/jpeg")
