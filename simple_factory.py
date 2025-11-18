import streamlit as st, tempfile, io, requests
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="S&M Exact Layout", layout="centered")
st.title("🎯 Exact 4-Item Layout")

NAVY  = "#001F54"
GOLD  = "#D4AF37"
WHITE = "#FFFFFF"
LOGO  = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

uploaded = st.file_uploader("Product PNG (transparent best)", type=["png"])
price   = st.text_input("Price (bottom-left)", "KES 14 500")
contact = st.text_input("Contact (bottom-right)", "0710 338 377 | sminteriors.co.ke")
size    = st.selectbox("Canvas size", ["9:16 (Story)", "1:1 (Post)", "4:5 (Portrait)"])
go      = st.button("Generate", type="primary")

def place_exact(prod, price, contact, size):
    W, H = size
    img  = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)
    # gradient
    for y in range(H):
        blend = y / H
        r = int((0x00) * (1 - blend) + 0xD4 * blend)
        g = int((0x1F) * (1 - blend) + 0xAF * blend)
        b = int((0x54) * (1 - blend) + 0x37 * blend)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    font_big = ImageFont.truetype("/System/Library/Fonts/HelveticaBold.ttf", 120) if os.path.exists("/System/Library/Fonts/HelveticaBold.ttf") else ImageFont.load_default()
    font_med = ImageFont.truetype("/System/Library/Fonts/HelveticaBold.ttf", 70)  if os.path.exists("/System/Library/Fonts/HelveticaBold.ttf") else ImageFont.load_default()

    # logo
    logo = Image.open(requests.get(LOGO, stream=True).raw).convert("RGBA")
    logo = logo.resize((220, 90), Image.LANCZOS)
    img.paste(logo, (60, 60), logo)

    # product centre
    if prod:
        prod = prod.convert("RGBA").resize((int(W * 0.65), int(H * 0.5)), Image.LANCZOS)
        img.paste(prod, ((W - prod.width) // 2, (H - prod.height) // 2), prod)

    # price bottom-left
    draw.text((80, H - 250), price, font=font_big, fill=GOLD)
    # contact bottom-right
    draw.text((W - 80, H - 250), contact, font=font_med, fill=WHITE, anchor="ra")
    return img

if go:
    if not uploaded:
        st.error("Upload product PNG"); st.stop()
    im = Image.open(uploaded)
    sz = {"9:16 (Story)": (1080, 1920), "1:1 (Post)": (1080, 1080), "4:5 (Portrait)": (1080, 1350)}[size]
    final = place_exact(im, price, contact, sz)
    st.image(final, use_column_width=True)
    buf = io.BytesIO()
    final.save(buf, format="JPEG", quality=95)
    st.download_button("⬇️ JPG", data=buf, file_name=f"sm_exact_{size[:3].replace(':', '')}.jpg", mime="image/jpeg")
