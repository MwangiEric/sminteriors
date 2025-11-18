import streamlit as st, tempfile, uuid, requests, io
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="S&M Place-4", layout="centered")
st.title("🎯 Place 4 Assets")
st.markdown("Logo • Price • Product • Contact — on canvas.")

# ---------- DEFAULTS ----------
DEF = {
    "bg_navy"  : "#001F54",
    "gold"     : "#D4AF37",
    "white"    : "#FFFFFF",
    "grey"     : "#F5F5F5",
    "price"    : "KES 14 500",
    "contact"  : "0710 338 377 | sminteriors.co.ke",
    "logo_url" : "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"
}

# ---------- UI ----------
uploaded_prod = st.file_uploader("Product PNG (transparent best)", type=["png"])
price_in      = st.text_input("Price text", DEF["price"])
contact_in    = st.text_input("Contact line", DEF["contact"])
size_choice   = st.selectbox("Canvas size", ["9:16 (Story)", "1:1 (Post)", "4:5 (Portrait)"])
generate      = st.button("Generate", type="primary")

# ---------- DRAW ----------
def place_four(prod_png, price, contact, size):
    W, H = size
    img  = Image.new("RGB", (W, H), DEF["bg_navy"])
    draw = ImageDraw.Draw(img)
    font_b = font_m = font_s = ImageFont.load_default()
    try:
        font_b = ImageFont.truetype("/System/Library/Fonts/HelveticaBold.ttf", 120)
        font_m = ImageFont.truetype("/System/Library/Fonts/HelveticaBold.ttf", 80)
        font_s = ImageFont.truetype("/System/Library/Fonts/HelveticaBold.ttf", 50)
    except: pass

    # 1 LOGO (top-left)
    logo = Image.open(requests.get(DEF["logo_url"], stream=True).raw).convert("RGBA")
    logo = logo.resize((200, 80), Image.LANCZOS)
    img.paste(logo, (50, 50), logo)

    # 2 PRICE BADGE (top-right)
    badge_sz = 300
    badge = Image.new("RGBA", (badge_sz, badge_sz), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(badge)
    bdraw.ellipse([(0, 0), (badge_sz, badge_sz)], fill=DEF["gold"] + (255,))
    bdraw.text((badge_sz//2, badge_sz//2), price, anchor="mm", font=font_b, fill="white")
    badge = badge.resize((180, 180), Image.LANCZOS)
    img.paste(badge, (W - 230, 50), badge)

    # 3 PRODUCT (centre)
    if prod_png:
        prod = prod_png.convert("RGBA").resize((int(W * 0.7), int(H * 0.5)), Image.LANCZOS)
        img.paste(prod, ((W - prod.width) // 2, (H - prod.height) // 2 - 80), prod)

    # 4 CONTACT (bottom)
    draw.text((W // 2, H - 150), contact, anchor="mm", font=font_s, fill=DEF["white"])
    return img

# ---------- RUN ----------
if generate:
    if not uploaded_prod:
        st.error("Upload product PNG"); st.stop()
    im = Image.open(uploaded_prod)
    size_map = {"9:16 (Story)": (1080, 1920), "1:1 (Post)": (1080, 1080), "4:5 (Portrait)": (1080, 1350)}
    final = place_four(im, price_in, contact_in, size_map[size_choice])
    st.image(final, use_column_width=True)
    buf = io.BytesIO()
    final.save(buf, format="JPEG", quality=95)
    st.download_button("⬇️ JPG", data=buf, file_name=f"sm_{size_choice[:3].replace(':', '')}.jpg", mime="image/jpeg")
