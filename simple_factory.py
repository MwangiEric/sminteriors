import streamlit as st, os, tempfile, uuid, requests
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="S&M Simple Ad Factory", layout="centered")
st.title("🖼️ S&M Simple Ad Factory")
st.markdown("Upload product PNG → type text → preview → download 3 sizes.")

# ---------- DEFAULTS ----------
DEFAULTS = {
    "headline": "Modern Corner Sofa",
    "discount": "50%",
    "tagline": "Best Selling Product",
    "website": "sminteriors.co.ke",
    "phone": "0710 338 377",
    "email": "info@sminteriors.co.ke",
    "address": "2nd Ave, Ngong Rd, Nairobi",
    "bg_colour": "#D92E2E",
    "accent_yellow": (244, 197, 66),
    "text_colour": (255, 255, 255)
}
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

# ---------- UI ----------
uploaded = st.file_uploader("Product PNG (transparent bg best)", type=["png"])
c1, c2 = st.columns(2)
with c1:
    headline = st.text_input("Headline", DEFAULTS["headline"])
    discount = st.text_input("Discount text", DEFAULTS["discount"])
    tagline  = st.text_input("Tagline", DEFAULTS["tagline"])
    website  = st.text_input("Website", DEFAULTS["website"])
with c2:
    phone   = st.text_input("Phone", DEFAULTS["phone"])
    email   = st.text_input("Email", DEFAULTS["email"])
    address = st.text_input("Address", DEFAULTS["address"])
    bg_col  = st.color_picker("Background red", DEFAULTS["bg_colour"])

preview = st.button("Preview", type="secondary")
generate = st.button("Generate & download", type="primary")

# ---------- DRAW ----------
def draw_template(product_png, size, headline, discount, tagline, website, phone, email, address, bg_col):
    W, H = size
    img = Image.new("RGB", (W, H), bg_col)
    draw = ImageDraw.Draw(img)
    # fonts (larger)
    try:
        font_b = ImageFont.truetype("/System/Library/Fonts/HelveticaBold.ttf", 140)
        font_m = ImageFont.truetype("/System/Library/Fonts/HelveticaBold.ttf", 90)
        font_s = ImageFont.truetype("/System/Library/Fonts/HelveticaBold.ttf", 60)
    except:
        font_b = font_m = font_s = ImageFont.load_default()

    # LOGO (top-left)
    logo_im = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
    logo_im = logo_im.resize((200, 80), Image.LANCZOS)
    img.paste(logo_im, (50, 50), logo_im)

    # BADGE (top-right)
    badge_size = 350
    badge = Image.new("RGBA", (badge_size, badge_size), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(badge)
    bdraw.ellipse([(0, 0), (badge_size, badge_size)], fill=DEFAULTS["accent_yellow"] + (255,))
    bdraw.text((badge_size // 2, badge_size // 2 - 40), discount, anchor="mm", font=font_b, fill="white")
    bdraw.text((badge_size // 2, badge_size // 2 + 40), "OFF", anchor="mm", font=font_m, fill="white")
    badge = badge.resize((220, 220), Image.LANCZOS)
    img.paste(badge, (W - 250, 50), badge)

    # PRODUCT (centre)
    if product_png:
        prod = product_png.convert("RGBA").resize((int(W * 0.65), int(H * 0.5)), Image.LANCZOS)
        img.paste(prod, ((W - prod.width) // 2, (H - prod.height) // 2 - 100), prod)

    # TEXT (bottom)
    y_start = H - 600
    draw.text((W // 2, y_start), headline, anchor="mm", font=font_b, fill="white")
    draw.text((W // 2, y_start + 160), tagline, anchor="mm", font=font_m, fill="white")
    draw.text((W // 2, y_start + 280), website, anchor="mm", font=font_s, fill="white")
    draw.text((W // 2, y_start + 380), f"Call {phone}", anchor="mm", font=font_s, fill="white")
    draw.text((W // 2, y_start + 480), f"{email}  •  {address}", anchor="mm", font=font_s, fill="white")
    return img

# ---------- PREVIEW ----------
if preview or generate:
    if not uploaded:
        st.error("Upload a PNG first"); st.stop()
    product = Image.open(uploaded)
    sizes = {"9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350)}
    outputs = {}
    tmpdir = tempfile.mkdtemp()
    for name, size in sizes.items():
        img = draw_template(product, size, headline, discount, tagline, website, phone, email, address, bg_col)
        path = os.path.join(tmpdir, f"{name.replace(':', '_')}.jpg")
        img.save(path, quality=95)
        outputs[name] = path
    # show preview
    c1, c2, c3 = st.columns(3)
    with c1: st.image(outputs["9:16"], use_column_width=True); st.caption("9:16 Story")
    with c2: st.image(outputs["1:1"], use_column_width=True);  st.caption("1:1 Post")
    with c3: st.image(outputs["4:5"], use_column_width=True);  st.caption("4:5 Portrait")

    if generate:
        import zipfile, io
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, 'w') as z:
            for f in outputs.values():
                z.write(f, arcname=os.path.basename(f))
        zip_io.seek(0)
        st.download_button("📦 Download all", data=zip_io, file_name="sminteriors_creatives.zip", mime="application/zip")
