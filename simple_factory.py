import streamlit as st, os, tempfile, uuid
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="S&M Simple Factory", layout="centered")
st.title("🖼️ S&M Simple Ad Factory")
st.markdown("Upload product PNG → type text → download 3 sizes.")

# ---------- DEFAULTS ----------
DEFAULTS = {
    "headline": "Modern Corner Sofa",
    "discount": "50%",
    "tagline": "Best Selling Product",
    "website": "sminteriors.co.ke",
    "phone": "0710 338 377",
    "email": "info@sminteriors.co.ke",
    "address": "2nd Ave, Ngong Rd, Nairobi",
    "bg_colour": "#D92E2E",   # red from template
    "text_colour": "#FFFFFF",
    "accent_yellow": "#F4C542"
}

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

generate = st.button("Generate creatives", type="primary")

# ---------- DRAW ----------
def draw_template(product_png, size, headline, discount, tagline, website, phone, email, address, bg_col):
    W, H = size
    img = Image.new("RGB", (W, H), bg_col)
    draw = ImageDraw.Draw(img)
    # helper
    def_font = ImageFont.load_default()
    try:
        bold  = ImageFont.truetype("/System/Library/Fonts/HelveticaBold.ttf", 90)
        med   = ImageFont.truetype("/System/Library/Fonts/HelveticaBold.ttf", 60)
        small = ImageFont.truetype("/System/Library/Fonts/HelveticaBold.ttf", 40)
    except:
        bold = med = small = def_font

# TOP badge  (FIXED ALPHA)
    badge_size = 300
    badge = Image.new("RGBA", (badge_size, badge_size), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(badge)
    radius = badge_size // 2
    bdraw.ellipse([(0, 0), (badge_size, badge_size)], fill=(244, 197, 66, 255))
    bdraw.text((radius, radius - 30), discount, anchor="mm", font=bold, fill="white")
    bdraw.text((radius, radius + 30), "OFF", anchor="mm", font=med, fill="white")
    badge = badge.resize((180, 180), Image.LANCZOS)
    img.paste(badge, (W - 200, 50), badge)   # <- now safe

    # PRODUCT
    if product_png:
        prod = product_png.convert("RGBA").resize((int(W * 0.6), int(H * 0.5)), Image.LANCZOS)
        img.paste(prod, ((W - prod.width) // 2, H // 2 - prod.height // 2), prod)

    # TEXT blocks
    y_start = H - 400
    draw.text((W // 2, y_start), headline, anchor="mm", font=bold, fill="white")
    draw.text((W // 2, y_start + 80), tagline, anchor="mm", font=med, fill="white")
    draw.text((W // 2, y_start + 150), website, anchor="mm", font=small, fill="white")
    draw.text((W // 2, y_start + 200), f"Call {phone}", anchor="mm", font=small, fill="white")
    draw.text((W // 2, y_start + 240), f"{email}  •  {address}", anchor="mm", font=small, fill="white")
    return img

# ---------- GENERATE ----------
if generate:
    if uploaded is None:
        st.error("Upload a PNG first"); st.stop()
    product = Image.open(uploaded)
    sizes = {"9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350)}
    outputs = {}
    tmpdir = tempfile.mkdtemp()
    with st.spinner("Drawing creatives…"):
        for name, size in sizes.items():
            img = draw_template(product, size, headline, discount, tagline, website, phone, email, address, bg_col)
            path = os.path.join(tmpdir, f"{name.replace(':', '_')}.jpg")
            img.save(path, quality=95)
            outputs[name] = path
    # preview
    c1, c2, c3 = st.columns(3)
    with c1: st.image(outputs["9:16"]); st.caption("9:16 Story")
    with c2: st.image(outputs["1:1"]);  st.caption("1:1 Post")
    with c3: st.image(outputs["4:5"]);  st.caption("4:5 Portrait")
    # zip
    import zipfile, io
    zip_io = io.BytesIO()
    with zipfile.ZipFile(zip_io, 'w') as z:
        for f in outputs.values():
            z.write(f, arcname=os.path.basename(f))
    zip_io.seek(0)
    st.download_button("📦 Download all", data=zip_io, file_name="sminteriors_creatives.zip", mime="application/zip")
