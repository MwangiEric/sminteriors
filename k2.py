import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance, ImageFilter
from groq import Groq
import io
import os
import textwrap
import requests

# ---------------------------------------------------------
#  1.  DIAGNOSTICS:  always show traceback
# ---------------------------------------------------------
import traceback, sys
try:

    st.set_page_config(page_title="Social Media Post Generator", layout="wide")

    # ---------------------------------------------------------
    #  2.  LIVE LOG  (appears in Cloud logs + browser)
    # ---------------------------------------------------------
    def log(msg):
        st.write(f"🔍  {msg}")      # browser
        print(msg)                # Cloud console

    log("----  app start  ----")

    # ---------------------------------------------------------
    #  3.  SOLID BROWN BACKGROUND  (no CSS, no flashes)
    # ---------------------------------------------------------
    BACKGROUND_COLOUR = "#8B4513"   # saddle-brown – change here
    PAGE_MM = (210, 297)            # A4 portrait
    DPI     = 300
    MM_TO_PX = DPI / 25.4
    def mm_to_px(mm: float) -> int:
        return int(mm * MM_TO_PX)

    # ---------------------------------------------------------
    #  4.  SAFE OPEN + RESIZE  (max 5 MB pixel buffer)
    # ---------------------------------------------------------
    MAX_PIXELS = 5_000_000   # ~ 5 MB RGBA

    def safe_open(upload, name: str) -> Image.Image:
        if not upload:
            log(f"{name}: none → solid brown fallback")
            return Image.new("RGBA", (600, 900), BACKGROUND_COLOUR)
        if upload.size > 20 * 1024 * 1024:
            st.error(f"{name} must be < 20 MB")
            st.stop()
        try:
            img = Image.open(io.BytesIO(upload.read())).convert("RGBA")
            log(f"{name} original {img.size}  mode={img.mode}")
            if img.width * img.height > MAX_PIXELS:
                ratio = (MAX_PIXELS / (img.width * img.height)) ** 0.5
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.LANCZOS)
                log(f"{name} resized → {img.size}")
            return img
        except Exception as e:
            log(f"{name} open failed: {e}")
            st.error(f"{name} is corrupted or not an image")
            st.stop()

    # ---------------------------------------------------------
    #  5.  GROQ API SETUP
    # ---------------------------------------------------------
    try:
        groq_api_key = st.secrets["groq_key"]
        groq = Groq(api_key=groq_api_key)
    except KeyError:
        st.error("Groq API key not found. Please set it in Streamlit secrets.")
        groq = None

    def generate_text_from_image(image):
        if groq is None:
            return "Groq API key not configured."

        try:
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()

            # Create a simple prompt (you may need to refine this)
            prompt = f"Describe this product image in a way that would be used in a social media post. Focus on the product's features, benefits, and style."

            # Call Groq API (replace with the appropriate API call)
            chat_completion = groq.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.7,
                top_p=1,
                n=1,
                stream=False,
            )

            ai_text = chat_completion.choices[0].message.content
            return ai_text

        except Exception as e:
            return f"Error generating text: {e}"

    # ---------------------------------------------------------
    #  6.  UPLOADS  (re-open every run – no EOF)
    # ---------------------------------------------------------
    bg_file = st.file_uploader("Background (jpg/png) – optional", type=["jpg", "jpeg", "png"])
    bg_img  = safe_open(bg_file, "bg")

    # Multiple Product Image Upload
    uploaded_files = st.file_uploader("Upload Multiple Product Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    images = []
    if uploaded_files:
        for uploaded_file in uploaded_files:
            try:
                image = Image.open(uploaded_file)
                images.append(image)
                st.image(image, caption=uploaded_file.name, width=150)  # Display thumbnails
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")

        st.write(f"Number of images uploaded: {len(images)}")
    else:
        st.info("Please upload some product images.")

    sig_file = st.file_uploader("Signature PNG – optional", type=["png"])
    sig_img = safe_open(sig_file, "sig")

    # ---------------------------------------------------------
    #  7.  LAYOUT OPTIONS IN SIDEBAR
    # ---------------------------------------------------------
    st.sidebar.header("Layout Options")

    # Page Size
    page_size = st.sidebar.selectbox("Page Size", ["A4", "Letter"], index=0)
    if page_size == "A4":
        PAGE_MM = (210, 297)
    elif page_size == "Letter":
        PAGE_MM = (215.9, 279.4)

    # Product Image Size and Position
    st.sidebar.subheader("Product Image")
    product_width_percent = st.sidebar.slider("Width (%)", 10, 90, 70)
    product_height_percent = st.sidebar.slider("Height (%)", 10, 90, 40)
    product_x_offset = st.sidebar.number_input("X Offset", -200, 200, 0)
    product_y_offset = st.sidebar.number_input("Y Offset", -200, 200, 0)

    # Headline Font Size
    st.sidebar.subheader("Text Styles")
    headline_font_size = st.sidebar.slider("Headline Size", 10, 72, 36)

    # ---------------------------------------------------------
    #  8.  DYNAMIC DIMENSIONS
    # ---------------------------------------------------------
    DPI = 300
    MM_TO_PX = DPI / 25.4
    def mm_to_px(mm: float) -> int:
        return int(mm * MM_TO_PX)

    w_px, h_px = mm_to_px(PAGE_MM[0]), mm_to_px(PAGE_MM[1])

    # ---------------------------------------------------------
    #  9.  CANVAS CREATION
    # ---------------------------------------------------------
    canvas = Image.new("RGBA", (w_px, h_px), BACKGROUND_COLOUR)

    # background (fit to page)
    bg = ImageOps.fit(bg_img, (w_px, h_px), centering=(0.5, 0.5))
    canvas.paste(bg, (0, 0), bg)

    # ---------------------------------------------------------
    #  10. PRODUCT IMAGE HANDLING
    # ---------------------------------------------------------
    if images:
        # Use the first uploaded image as the main product image
        main_product_image = images[0]

        prod_w = int(w_px * (product_width_percent / 100))
        prod_h = int(h_px * (product_height_percent / 100))
        prod = ImageOps.fit(main_product_image, (prod_w, prod_h), centering=(0.5, 0.5))
        shadow = prod.filter(ImageFilter.GaussianBlur(8))
        offset = mm_to_px(2)
        canvas.paste(shadow, ((w_px - prod_w) // 2 + product_x_offset + offset, (h_px - prod_h) // 2 + product_y_offset + offset), shadow)
        canvas.paste(prod, ((w_px - prod_w) // 2 + product_x_offset, (h_px - prod_h) // 2 + product_y_offset), prod)

    # ---------------------------------------------------------
    #  11. SIGNATURE
    # ---------------------------------------------------------
    if sig_img:
        sign = sig_img.resize((int(sig_img.width * 0.20), int(sig_img.height * 0.20)))
        canvas.paste(sign, (w_px - sign.width - mm_to_px(15), h_px - sign.height - mm_to_px(15)), sign)

    # ---------------------------------------------------------
    #  12. TEXT GENERATION & DRAWING
    # ---------------------------------------------------------
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("arial.ttf", size=headline_font_size)
    except IOError:
        font = ImageFont.load_default()

    # Generate Text from Image
    if images:
        if st.button("Generate Text"):
            ai_text = generate_text_from_image(main_product_image)
            st.session_state.ai_text = ai_text
        if 'ai_text' in st.session_state:
            headline = st.session_state.ai_text
        else:
            headline = "Click Generate Text"
    else:
        headline = "Upload product image to generate text"

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
    #  13. SHOW PREVIEW
    # ---------------------------------------------------------
    st.image(canvas, use_column_width=True, caption="Preview – A4 210×297 mm")

    # ---------------------------------------------------------
    #  14. EXPORT
    # ---------------------------------------------------------
    if st.button("Generate JPEG"):
        out = canvas.convert("RGB")
        buf = io.BytesIO()
        out.save(buf, format="JPEG", quality=90, dpi=(300, 300))
        st.download_button("💾 Download", buf.getvalue(), "journal.jpg", "image/jpeg")

    log("----  render complete  ----")

# ---------------------------------------------------------
#  15. IF ANYTHING CRASHES – SHOW IT
# ---------------------------------------------------------
except Exception as e:
    st.error("⚠️  Unhandled exception")
    st.code(traceback.format_exc())
    print(traceback.format_exc())
    sys.exit(1)
