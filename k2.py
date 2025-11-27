# streamlit_app.py  –  crash-resistant starter
import io, os, textwrap, requests, streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance, ImageFilter
from groq import Groq

# ---------------------------------------------------------
#  1.  DIAGNOSTICS:  always show traceback
# ---------------------------------------------------------
import traceback, sys
try:

    st.set_page_config(page_title="Journal Composer", layout="wide")

    # ---------------------------------------------------------
    #  2.  LIVE LOG  (appears in Cloud logs)
    # ---------------------------------------------------------
    def log(msg):
        st.write(f"🔍  {msg}")      # also visible in browser
        print(msg)                # Cloud console

    log("----  app start  ----")

    # ---------------------------------------------------------
    #  3.  USER UPLOADS BACKGROUND
    # ---------------------------------------------------------
    bg_file = st.file_uploader("Upload background (jpg/png) – optional", type=["jpg", "jpeg", "png"])
    if bg_file:
        bg_img = Image.open(bg_file).convert("RGBA")
        log(f"user bg  {bg_img.size}")
    else:
        # solid colour fallback – no external URL
        bg_img = Image.new("RGBA", (600, 900), "#FFFFFF")
        log("using solid-white fallback bg")

    # ---------------------------------------------------------
    #  4.  OPTIONAL FOREGROUND  (product)
    # ---------------------------------------------------------
    fg_file = st.file_uploader("Upload product PNG (transparent) – optional", type=["png"])
    if fg_file:
        fg_img = Image.open(fg_file).convert("RGBA")
        log(f"user fg  {fg_img.size}")
    else:
        fg_img = None

    # ---------------------------------------------------------
    #  5.  OPTIONAL SIGNATURE  (logo)
    # ---------------------------------------------------------
    sig_file = st.file_uploader("Upload signature PNG – optional", type=["png"])
    if sig_file:
        sig_img = Image.open(sig_file).convert("RGBA")
        log(f"user sig  {sig_img.size}")
    else:
        sig_img = None

    # ---------------------------------------------------------
    #  6.  SIMPLE LAYOUT  (hard-coded for now)
    # ---------------------------------------------------------
    PAGE_MM = (210, 297)          # A4 portrait
    DPI     = 300
    MM_TO_PX = DPI / 25.4
    def mm_to_px(mm): return int(mm * MM_TO_PX)

    w_px, h_px = mm_to_px(PAGE_MM[0]), mm_to_px(PAGE_MM[1])
    canvas = Image.new("RGBA", (w_px, h_px), "#FFFFFF")

    # background (fit to page)
    bg = ImageOps.fit(bg_img, (w_px, h_px), centering=(0.5, 0.5))
    canvas.paste(bg, (0, 0), bg)

    # product (centre, 70 % width, 40 % height)
    if fg_img:
        prod_w = int(w_px * 0.70)
        prod_h = int(h_px * 0.40)
        prod = ImageOps.fit(fg_img, (prod_w, prod_h), centering=(0.5, 0.5))
        shadow = prod.filter(ImageFilter.GaussianBlur(8))
        offset = mm_to_px(2)
        canvas.paste(shadow, ((w_px - prod_w) // 2 + offset, (h_px - prod_h) // 2 + offset), shadow)
        canvas.paste(prod, ((w_px - prod_w) // 2, (h_px - prod_h) // 2), prod)

    # signature (bottom-right, 20 % size)
    if sig_img:
        sign = sig_img.resize((int(sig_img.width * 0.20), int(sig_img.height * 0.20)))
        canvas.paste(sign, (w_px - sign.width - mm_to_px(15), h_px - sign.height - mm_to_px(15)), sign)

    # ---------------------------------------------------------
    #  7.  TEXT  (default font only)
    # ---------------------------------------------------------
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()

    headline = st.text_input("Headline", "My Product")
    header_y = mm_to_px(25)
    for line in textwrap.wrap(headline, width=25):
        w, h = font.getbbox(line)[2:4]
        draw.text(((w_px - w) // 2, header_y), line, font=font, fill="#000000")
        header_y += h + 5

    price = st.text_input("Price", "$49.99")
    price_y = h_px - mm_to_px(25)
    draw.text((mm_to_px(20), price_y), price, font=font, fill="#FF0000")

    cta = st.text_input("CTA", "Buy Now")
    cta_w, cta_h = font.getbbox(cta)[2:4]
    draw.text((w_px - cta_w - mm_to_px(20), price_y), cta, font=font, fill="#FFFFFF")

    contact = st.text_area("Contact", "hello@example.com\n+1 234 567 890")
    contact_y = h_px - mm_to_px(10)
    for line in textwrap.wrap(contact, width=30):
        w, h = font.getbbox(line)[2:4]
        draw.text(((w_px - w) // 2, contact_y), line, font=font, fill="#444444")
        contact_y += h + 4

    # ---------------------------------------------------------
    #  8.  SHOW PREVIEW
    # ---------------------------------------------------------
    st.image(canvas, use_column_width=True, caption="Preview – A4 210×297 mm")

    # ---------------------------------------------------------
    #  9.  EXPORT
    # ---------------------------------------------------------
    if st.button("Generate JPEG"):
        out = canvas.convert("RGB")
        buf = io.BytesIO()
        out.save(buf, format="JPEG", quality=90, dpi=(300, 300))
        st.download_button("💾 Download", buf.getvalue(), "journal.jpg", "image/jpeg")

    log("----  render complete  ----")

# ---------------------------------------------------------
#  10.  IF ANYTHING CRASHES – SHOW IT
# ---------------------------------------------------------
except Exception as e:
    st.error("⚠️  Unhandled exception")
    st.code(traceback.format_exc())
    print(traceback.format_exc())
    sys.exit(1)
