import streamlit as st, tempfile, io, requests
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="S&M Exact Layout", layout="centered")
st.title("🎯 Exact 4-Item Layout")

# ---------- BRAND COLOURS ----------
NAVY  = "#001F54"
GOLD  = "#D4AF37"
WHITE = "#FFFFFF"

# ---------- DEFAULTS ----------
DEF_LOGO = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"
DEF_PRICE = "KES 14 500"
DEF_CONTACT = "0710 338 377\nsminteriors.co.ke"

# ---------- UI ----------
uploaded_prod = st.file_uploader("Product PNG (transparent best)", type=["png"])
price_in   = st.text_area("Price (bottom-left)", DEF_PRICE, height=60)
contact_in = st.text_area("Contact (bottom-right)", DEF_CONTACT, height=60)
size_choice = st.selectbox("Canvas size", ["9:16 (Story)", "1:1 (Post)", "4:5 (Portrait)"])
generate = st.button("Generate", type="primary")

# ---------- DRAW ----------
def exact_layout(prod_png, price, contact, size):
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
    # fonts
    try:
        font_big = ImageFont.truetype("/System/Library/Fonts/HelveticaBold.ttf", 120)
        font_med = ImageFont.truetype("/System/Library/Fonts/HelveticaBold.ttf", 70)
        font_sml = ImageFont.truetype("/System/Library/Fonts/HelveticaBold.ttf", 50)
    except:
        font_big = font_med = font_sml = ImageFont.load_default()

    # 1 LOGO (top-left)
    logo = Image.open(requests.get(DEF_LOGO, stream=True).raw).convert("RGBA")
    logo = logo.resize((220, 90), Image.LANCZOS)
    img.paste(logo, (60, 60), logo)

    # 2 PRODUCT (centre)
    if prod_png:
        prod = prod_png.convert("RGBA").resize((int(W * 0.65), int(H * 0.5)), Image.LANCZOS)
        img.paste(prod, ((W - prod.width) // 2, (H - prod.height) // 2), prod)

    # 3 PRICE (bottom-left)
    draw.multiline_text((80, H - 250), price, font=font_big, fill=GOLD, spacing=10)

    # 4 CONTACT (bottom-right)
    draw.multiline_text((W - 80, H - 250), contact, font=font_med, fill=WHITE, spacing=10, anchor="ra")

    return img

# ---------- RUN ----------
if generate:
    if not uploaded_prod:
        st.error("Upload product PNG"); st.stop()
    im = Image.open(uploaded_prod)
    size_map = {"9:16 (Story)": (1080, 1920), "1:1 (Post)": (1080, 1080), "4:5 (Portrait)": (1080, 1350)}
    final = exact_layout(im, price_in, contact_in, size_map[size_choice])
    st.image(final, use_column_width=True)
    buf = io.BytesIO()
    final.save(buf, format="JPEG", quality=95)
    st.download_button("⬇️ JPG", data=buf, file_name=f"sm_exact_{size_choice[:3].replace(':', '')}.jpg", mime="image/jpeg")
