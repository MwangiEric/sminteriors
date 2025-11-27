# streamlit_app.py
import io, os, textwrap, requests, hashlib, streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance, ImageFilter
from groq import Groq

# ---------------------------------------------------------
#  1.  FEATURE FLAGS & SESSION STATE
# ---------------------------------------------------------
if "saas_layout" not in st.session_state:
    st.session_state.saas_layout = False
if "prod_width_pct" not in st.session_state:
    st.session_state.prod_width_pct = 80
if "prod_height_pct" not in st.session_state:
    st.session_state.prod_height_pct = 40
if "auto_fit" not in st.session_state:
    st.session_state.auto_fit = True
if "note_text" not in st.session_state:   # dead key kept for backward compat
    st.session_state.note_text = "Today's reflections…"
if "preview_generated" not in st.session_state:
    st.session_state.preview_generated = False

# ---------------------------------------------------------
#  2.  GROQ VISION (cached)
# ---------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _groq_client():
    return Groq(api_key=os.getenv("groq_key"))

@st.cache_data(show_spinner=False, ttl=3600)
def describe_image_cached(_img_hash: str) -> str:
    with st.spinner("AI is writing your copy…"):
        client = _groq_client()
        completion = client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": (
                        "You are a creative copy-writer. Look at the image and return ONLY five short lines "
                        "separated by '|': 1) HEADLINE (4-6 words), 2) TAG-LINE (8-12 words), 3) SIDE-NOTE (3-5 words), "
                        "4) PRODUCT-DESCRIPTION (20-30 words), 5) CAPTION & HASHTAGS (15-25 words incl. 3-5 hashtags). "
                        "Do NOT add labels or numbers, just the five strings separated by '|'."
                    )},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{_img_hash.encode('utf-8').hex()}"}}
                ]
            }],
            temperature=0.7,
            max_tokens=400
        )
        return completion.choices[0].message.content

# ---------------------------------------------------------
#  3.  COSMETIC BG (glowing circles – never over photo)
# ---------------------------------------------------------
_BRAND = {"aqua": "#00F5FF", "lime": "#ADFF2F", "magenta": "#FF00FF", "dark": "#111827"}
st.set_page_config(page_title="Journal Composer", layout="wide")
st.markdown(f"""
<style>
.stApp {{background: {_BRAND["dark"]}; overflow-x: hidden;}}
.geo-bg {{position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -1; pointer-events: none;}}
.geo-bg circle {{animation: pulse 6s ease-in-out infinite;}}
@keyframes pulse {{0% {{opacity: .25; transform: scale(1);}} 50% {{opacity: .65; transform: scale(1.15);}} 100% {{opacity: .25; transform: scale(1);}}}}
</style>
<svg class="geo-bg" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="g1" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="{_BRAND["aqua"]}" stop-opacity="0.7"/><stop offset="100%" stop-opacity="0"/></radialGradient>
    <radialGradient id="g2" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="{_BRAND["lime"]}" stop-opacity="0.6"/><stop offset="100%" stop-opacity="0"/></radialGradient>
    <radialGradient id="g3" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="{_BRAND["magenta"]}" stop-opacity="0.5"/><stop offset="100%" stop-opacity="0"/></radialGradient>
  </defs>
  <circle cx="15%" cy="20%" r="22%" fill="url(#g1)"/><circle cx="80%" cy="70%" r="18%" fill="url(#g2)"/><circle cx="50%" cy="90%" r="25%" fill="url(#g3)"/>
  <circle cx="70%" cy="15%" r="12%" fill="none" stroke="{_BRAND["aqua"]}" stroke-width="2" opacity="0.4"/><circle cx="25%" cy="80%" r="15%" fill="none" stroke="{_BRAND["lime"]}" stroke-width="3" opacity="0.5"/><circle cx="90%" cy="45%" r="10%" fill="none" stroke="{_BRAND["magenta"]}" stroke-width="2" opacity="0.6"/>
</svg>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
#  4.  CACHED HELPERS
# ---------------------------------------------------------
@st.cache_data(show_spinner=False, max_entries=50)
def load_url_image(url: str) -> Image.Image:
    return Image.open(requests.get(url, stream=True, timeout=10).raw).convert("RGBA")

LOGO_URL    = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"
PRODUCT_URL = "https://ik.imagekit.io/ericmwangi/product.png"
DEFAULT_LOGO  = load_url_image(LOGO_URL)
DEFAULT_PHOTO = load_url_image(PRODUCT_URL)

PAGE = {
    "A4 portrait": (210, 297), "A4 landscape": (297, 210), "A5 portrait": (148, 210),
    "A5 landscape": (210, 148), "Letter": (216, 279), "4×6 in": (102, 152),
    "Square 1:1": (200, 200), "Instagram 1:1": (200, 200), "FaceBook 1.91:1": (200, 105), "Story 9:16": (108, 192),
}
DPI = 300
MM_TO_PX = DPI / 25.4
def mm_to_px(mm: float) -> int:
    return int(mm * MM_TO_PX)

def format_text(text: str, mode: str) -> str:
    if mode == "Title Case":    return text.title()
    if mode == "Sentence case": return text.capitalize()
    if mode == "UPPER CASE":    return text.upper()
    if mode == "lower case":    return text.lower()
    return text

@st.cache_data(show_spinner=False)
def add_drop_shadow(img: Image.Image, offset_mm=2, blur=3, opacity=40) -> Image.Image:
    shadow = Image.new("RGBA", (img.width + mm_to_px(offset_mm)*2, img.height + mm_to_px(offset_mm)*2), (0,0,0,0))
    draw = ImageDraw.Draw(shadow)
    draw.rectangle([mm_to_px(offset_mm), mm_to_px(offset_mm),
                    img.width + mm_to_px(offset_mm), img.height + mm_to_px(offset_mm)],
                   fill=(0,0,0,opacity))
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    shadow.paste(img, (mm_to_px(offset_mm), mm_to_px(offset_mm)), img)
    return shadow

@st.cache_data(show_spinner=False)
def auto_enhance(img: Image.Image) -> Image.Image:
    img = ImageOps.autocontrast(img)
    return ImageEnhance.Color(img).enhance(1.15)

PRESETS = {
    "Morning light": {"bg_col": "#FFFFFF", "note_col": "#4F4F4F", "sig_opacity": 90},
    "Night dark":    {"bg_col": "#1E1E1E", "note_col": "#E0E0E0", "sig_opacity": 80},
    "Vintage":       {"bg_col": "#FFF8E1", "note_col": "#795548", "sig_opacity": 85},
    "Minimal b&w":   {"bg_col": "#FFFFFF", "note_col": "#000000", "sig_opacity": 70},
}

# ---------------------------------------------------------
#  5.  SESSION STATE (layout + SaaS flags)
# ---------------------------------------------------------
if "layout" not in st.session_state:
    st.session_state.layout = dict(
        page="A4 portrait", sig_scale=25, sig_x=20, sig_y=20,
        note_x=50, note_y=200, note_size=50, note_wrap=35,
        note_col="#4F4F4F", enhance=False, preset="Morning light",
        export_dpi=300, text_format="Sentence case", warp=False,
        logo_scale=30, logo_x=15, logo_y=15
    )
if "page" not in st.session_state.layout:
    st.session_state.layout["page"] = "A4 portrait"
if "preview_generated" not in st.session_state:
    st.session_state.preview_generated = False

L = st.session_state.layout

# ---------------------------------------------------------
#  6.  AUTO-FIT TEXT  (cached)
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def fit_text(draw: ImageDraw.Draw,
             text: str,
             max_w_mm: float, max_h_mm: float,
             start_pt: int = 200,
             min_pt: int = 20,
             wrap_width: int = 40) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """Return font and wrapped lines that fit inside max_mm rectangle."""
    max_w_px = mm_to_px(max_w_mm)
    max_h_px = mm_to_px(max_h_mm)
    for pt in range(start_pt, min_pt - 1, -2):
        try:
            font = ImageFont.truetype("arial.ttf", pt)
        except IOError:
            font = ImageFont.load_default()
        lines = textwrap.wrap(text, width=wrap_width)
        if not lines:
            return font, [""]
        w = max(font.getbbox(line)[2] for line in lines)
        h = sum(font.getbbox(line)[3] + 5 for line in lines)
        if w <= max_w_px and h <= max_h_px:
            return font, lines
    return font, lines

# ---------------------------------------------------------
#  7.  SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    st.title("📔 Journal Composer")
    mode = st.radio("Mode", ["Edit", "Preview"], index=0)
    if mode == "Edit":
        st.header("1. Images")
        bg_file = st.file_uploader("Upload background (jpg/png) – optional", type=["jpg", "jpeg", "png"])
        sig_file = st.file_uploader("Upload signature (optional)", type=["png"])
        fg_file  = st.file_uploader("Upload foreground PNG (transparent) – optional", type=["png"])

        # ---- guard 10 MB ----
        for f in [bg_file, sig_file, fg_file]:
            if f and f.size > 10 * 1024 * 1024:
                st.error(f"{f.name} must be < 10 MB")
                st.stop()

        # ---- handle uploads (bytes only) ----
        if bg_file:
            bg_bytes = bg_file.read()
            st.session_state.bg_bytes = bg_bytes
        else:
            bg_bytes = None
            st.session_state.bg_bytes = None

        if sig_file:
            sig_bytes = sig_file.read()
            st.session_state.sig_bytes = sig_bytes
        else:
            sig_bytes = None
            st.session_state.sig_bytes = None

        if fg_file:
            fg_bytes = fg_file.read()
            st.session_state.fg_bytes = fg_bytes
        else:
            fg_bytes = None
            st.session_state.fg_bytes = None

        # ---- old rectangle sliders (still work) ----
        if fg_file:
            st.subheader("Foreground / Product rectangle")
            base_w_mm, base_h_mm = 100, 140
            w_area_mm = base_w_mm * (st.session_state.get("area_scale", 100) / 100)
            h_area_mm = base_h_mm * (st.session_state.get("area_scale", 100) / 100)
            area_preset = st.selectbox("Area anchor", ["Top-left", "Top-right", "Bottom-left", "Bottom-right", "Centre"], index=4)
            area_scale  = st.slider("Area scale %", 50, 200, 100, key="area_scale")
            area_nudge_x = st.slider("Area nudge X (mm)", -20, 20, 0, key="area_nudge_x")
            area_nudge_y = st.slider("Area nudge Y (mm)", -20, 20, 0, key="area_nudge_y")

        page_name = st.selectbox("Document size", list(PAGE.keys()), index=list(PAGE.keys()).index(L["page"]))
        L["page"] = page_name
        w_mm, h_mm = PAGE[page_name]
        st.caption(f"{w_mm} × {h_mm} mm  →  {mm_to_px(w_mm)} × {mm_to_px(h_mm)} px @ 300 dpi")

        preset_name = st.selectbox("Preset", list(PRESETS.keys()), index=list(PRESETS.keys()).index(L["preset"]))
        L.update(PRESETS[preset_name])
        L["preset"] = preset_name

        st.header("2. Logo / Signature")
        c1, c2 = st.columns(2)
        with c1:
            L["logo_scale"] = st.slider("Logo size %", 5, 100, L["logo_scale"])
            L["logo_x"]     = st.slider("Logo X (mm)", 0, w_mm, L["logo_x"])
        with c2:
            L["logo_y"]     = st.slider("Logo Y (mm)", 0, h_mm, L["logo_y"])
            L["sig_scale"]  = st.slider("Sig size %", 5, 100, L["sig_scale"])
            L["sig_x"]      = st.slider("Sig X (mm)", 0, w_mm, L["sig_x"])
            L["sig_y"]      = st.slider("Sig Y (mm)", 0, h_mm, L["sig_y"])

        st.header("3. Text blocks")
        left_mm = st.slider("Text left indent (mm)", 0, 50, 20)

        # ---- auto-fit section ----
        with st.sidebar.expander("🔍 Auto-fit text (optional)", expanded=False):
            auto_fit = st.checkbox("Auto-size text to box", value=True, key="auto_fit")
            if auto_fit:
                c1, c2 = st.columns(2)
                with c1:
                    head_box_w = st.number_input("Headline box width (mm)", 30, 200, 100, 5, key="head_box_w")
                    head_box_h = st.number_input("Headline box height (mm)", 10, 100, 25, 5, key="head_box_h")
                with c2:
                    tag_box_w  = st.number_input("Tag box width (mm)", 30, 200, 120, 5, key="tag_box_w")
                    tag_box_h  = st.number_input("Tag box height (mm)", 10, 100, 20, 5, key="tag_box_h")
                # contrast check
                bg_rgb   = tuple(int(PRESETS[L["preset"]]["bg_col"][i:i+2], 16) for i in (1,3,5))
                head_rgb = tuple(int(st.session_state.get("header_col", "#000000")[i:i+2], 16) for i in (1,3,5))
                contrast = (max(bg_rgb + head_rgb) + 0.05) / (min(bg_rgb + head_rgb) + 0.05)
                if contrast < 4.5:
                    st.warning(f"Headline contrast {contrast:.1f} < 4.5 (WCAG)")

        st.subheader("Header")
        header_text = st.text_input("Header", "My Product", key="header_in")
        header_size = st.slider("Header size (pt)", 12, 200, 125, key="header_size")
        header_col  = st.color_picker("Header colour", "#000000", key="header_col")
        header_y_mm = st.slider("Header Y (mm)", 0, PAGE[L["page"]][1], 30, key="header_y")

        st.subheader("Tag-line")
        tag_text = st.text_input("Tag-line", "The best thing since sliced bread.", key="tag_in")
        tag_size = st.slider("Tag-line size (pt)", 8, 150, 65, key="tag_size")
        tag_col  = st.color_picker("Tag-line colour", "#555555", key="tag_col")
        tag_y_mm = st.slider("Tag-line Y (mm)", 0, PAGE[L["page"]][1], 50, key="tag_y")

        st.subheader("Product info (side-note)")
        info_text = st.text_area("Info", "Describe your product here.\nYou can write several sentences.", key="info_in")
        info_size = st.slider("Info size (pt)", 8, 180, 85, key="info_size")
        info_col  = st.color_picker("Info colour", "#333333", key="info_col")
        info_y_mm = st.slider("Info Y (mm)", 0, PAGE[L["page"]][1], 70, key="info_y")
        info_wrap = st.slider("Info wrap width", 20, 80, 45, key="info_wrap")

        st.subheader("Contact")
        contact_text = st.text_area("Contact", "Email: hello@example.com\nPhone: +1 234 567 890", key="contact_in")
        contact_size = st.slider("Contact size (pt)", 8, 150, 70, key="contact_size")
        contact_col  = st.color_picker("Contact colour", "#444444", key="contact_col")
        contact_y_mm = st.slider("Contact Y (mm)", 0, PAGE[L["page"]][1], PAGE[L["page"]][1] - 30, key="contact_y")
        contact_wrap = st.slider("Contact wrap width", 20, 100, 60, key="contact_wrap")

        text_format = st.selectbox("Text format", ["Sentence case", "Title Case", "UPPER CASE", "lower case"], index=["Sentence case", "Title Case", "UPPER CASE", "lower case"].index(L["text_format"]))
        L["text_format"] = text_format
        L["enhance"] = st.checkbox("Auto-enhance photo", L["enhance"])
        L["export_dpi"] = st.radio("Export DPI", [72, 150, 300], index=2)

        # ---- SaaS toggle + new controls ----
        st.header("5. SaaS predefined layout")
        saas_on = st.checkbox("Use SaaS layout (logo TL, headline TM, product centre, price BL, cta BR, contact BC)", value=st.session_state.saas_layout)
        st.session_state.saas_layout = saas_on
        if saas_on:
            st.subheader("SaaS texts")
            price_text = st.text_input("Price", "$49.99", key="price_in")
            price_col  = st.color_picker("Price colour", "#FF0000", key="price_col")
            cta_text   = st.text_input("CTA", "Buy Now →", key="cta_in")
            cta_col    = st.color_picker("CTA colour", "#FFFFFF", key="cta_col")

            st.subheader("Product-image geometry")
            prod_w_pct = st.slider("Product width % of page", 50, 95, st.session_state.prod_width_pct, 5, key="prod_width_pct")
            prod_h_pct = st.slider("Product height % of page", 20, 70, st.session_state.prod_height_pct, 5, key="prod_height_pct")
            st.caption("Anchor & nudge use the same sliders as the foreground rectangle above.")

        # ---- AI copy ----
        if st.button("Generate headline / tag / note / description / caption from image"):
            bg_bytes = st.session_state.get("bg_bytes")
            if not bg_bytes:
                st.error("Please upload a background image first.")
                st.stop()
            img_hash = hashlib.md5(bg_bytes).hexdigest()
            answer = describe_image_cached(img_hash)
            try:
                headline, tag, note, desc, capt = [a.strip() for a in answer.split("|", 4)]
            except ValueError:
                headline, tag, note, desc, capt = "Fresh drop", "Check it out", "Limited", "Amazing product you will love", "#new #fresh #musthave"
            st.session_state["header_in"]  = headline
            st.session_state["tag_in"]     = tag
            st.session_state["info_in"]    = f"{note}\n{desc}"
            st.session_state["contact_in"] = capt
            st.rerun()

# ---------------------------------------------------------
#  8.  CACHED PREVIEW BUILDERS
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def build_old_preview(
    page_mm: tuple[int, int],
    bg_bytes: bytes | None,
    fg_bytes: bytes | None,
    sig_bytes: bytes | None,
    preset_name: str,
    enhance: bool,
    logo_scale: int, logo_xy: tuple[int, int],
    sig_scale: int, sig_xy: tuple[int, int],
    left_mm: int,
    header_txt: str, header_sz: int, header_col: str, header_y_mm: int,
    tag_txt: str, tag_sz: int, tag_col: str, tag_y_mm: int,
    info_txt: str, info_sz: int, info_col: str, info_y_mm: int, info_wrap: int,
    contact_txt: str, contact_sz: int, contact_col: str, contact_y_mm: int, contact_wrap: int,
    text_format: str,
    area_preset: str, area_scale: int, nudge_x: int, nudge_y: int,
    auto_fit: bool,
    head_box: tuple[float, float], tag_box: tuple[float, float]
) -> Image.Image:
    """Free-layout builder (no gradient over photo)."""
    w_mm, h_mm = page_mm
    w_px, h_px = mm_to_px(w_mm), mm_to_px(h_mm)

    # background
    if bg_bytes:
        bg = Image.open(io.BytesIO(bg_bytes)).convert("RGBA")
    else:
        bg = DEFAULT_PHOTO
    bg = ImageOps.fit(bg, (w_px, h_px), centering=(0.5, 0.5))
    if enhance:
        bg = auto_enhance(bg.convert("RGB")).convert("RGBA")
    canvas = Image.new("RGBA", (w_px, h_px), PRESETS[preset_name]["bg_col"])
    canvas.paste(bg, (0, 0), bg)

    # foreground rectangle (old sliders still work)
    if fg_bytes:
        fg = Image.open(io.BytesIO(fg_bytes)).convert("RGBA")
        base_w_mm, base_h_mm = 100, 140
        w_area_mm = base_w_mm * (area_scale / 100)
        h_area_mm = base_h_mm * (area_scale / 100)
        anchors = {
            "Top-left": (0, 0),
            "Top-right": (w_mm - w_area_mm, 0),
            "Bottom-left": (0, h_mm - h_area_mm),
            "Bottom-right": (w_mm - w_area_mm, h_mm - h_area_mm),
            "Centre": ((w_mm - w_area_mm) / 2, (h_mm - h_area_mm) / 2),
        }
        anchor_x_mm, anchor_y_mm = anchors[area_preset]
        anchor_x_mm += nudge_x
        anchor_y_mm += nudge_y
        anchor_x_px = mm_to_px(anchor_x_mm)
        anchor_y_px = mm_to_px(anchor_y_mm)
        w_area_px = mm_to_px(w_area_mm)
        h_area_px = mm_to_px(h_area_mm)
        fg_sized = ImageOps.fit(fg, (w_area_px, h_area_px), centering=(0.5, 0.5))
        shadow = add_drop_shadow(fg_sized, offset_mm=2, blur=3, opacity=40)
        canvas.paste(shadow, (anchor_x_px - mm_to_px(2), anchor_y_px - mm_to_px(2)), shadow)

    # logo / signature
    logo = DEFAULT_LOGO.resize((int(DEFAULT_LOGO.width * logo_scale / 100), int(DEFAULT_LOGO.height * logo_scale / 100)))
    canvas.paste(logo, (mm_to_px(logo_xy[0]), mm_to_px(logo_xy[1])), logo)
    if sig_bytes:
        sig = Image.open(io.BytesIO(sig_bytes)).convert("RGBA")
    else:
        sig = DEFAULT_LOGO
    # duplicate guard
    if sig_bytes and hashlib.md5(sig_bytes).hexdigest() != hashlib.md5(DEFAULT_LOGO.tobytes()).hexdigest():
        sign = sig.resize((int(sig.width * sig_scale / 100), int(sig.height * sig_scale / 100)))
        alpha = sign.split()[-1].point(lambda p: p * 85 // 100)
        sign.putalpha(alpha)
        canvas.paste(sign, (mm_to_px(sig_xy[0]), mm_to_px(sig_xy[1])), sign)

    # text
    draw = ImageDraw.Draw(canvas)
    left_px = mm_to_px(left_mm)

    # headline
    if auto_fit:
        font_head, head_lines = fit_text(draw, header_txt, head_box[0], head_box[1], start_pt=200, min_pt=36, wrap_width=30)
        y_head = mm_to_px(header_y_mm)
        for line in head_lines:
            w, h = font_head.getbbox(line)[2:4]
            draw.text(((mm_to_px(w_mm) - w) // 2, y_head), line, font=font_head, fill=header_col)
            y_head += h + 5
    else:
        try:
            font_head = ImageFont.truetype("arial.ttf", header_sz)
        except IOError:
            font_head = ImageFont.load_default()
        lines = textwrap.wrap(format_text(header_txt, "Title Case"), width=30)
        y_offset = 0
        for line in lines:
            draw.text((left_px, mm_to_px(header_y_mm) + y_offset), line, font=font_head, fill=header_col)
            y_offset += font_head.getbbox(line)[3] + 5

    # tag
    if auto_fit:
        font_tag, tag_lines = fit_text(draw, tag_txt, tag_box[0], tag_box[1], start_pt=100, min_pt=28, wrap_width=40)
        y_tag = mm_to_px(tag_y_mm)
        for line in tag_lines:
            w, h = font_tag.getbbox(line)[2:4]
            draw.text(((mm_to_px(w_mm) - w) // 2, y_tag), line, font=font_tag, fill=tag_col)
            y_tag += h + 5
    else:
        try:
            font_tag = ImageFont.truetype("arial.ttf", tag_sz)
        except IOError:
            font_tag = ImageFont.load_default()
        lines = textwrap.wrap(tag_txt, width=40)
        y_offset = 0
        for line in lines:
            draw.text((left_px, mm_to_px(tag_y_mm) + y_offset), line, font=font_tag, fill=tag_col)
            y_offset += font_tag.getbbox(line)[3] + 5

    # info & contact (manual for brevity)
    try:
        font_info = ImageFont.truetype("arial.ttf", info_sz)
    except IOError:
        font_info = ImageFont.load_default()
    lines = textwrap.wrap(info_txt, width=info_wrap)
    y_offset = 0
    for line in lines:
        draw.text((left_px, mm_to_px(info_y_mm) + y_offset), line, font=font_info, fill=info_col)
        y_offset += font_info.getbbox(line)[3] + 5

    try:
        font_contact = ImageFont.truetype("arial.ttf", contact_sz)
    except IOError:
        font_contact = ImageFont.load_default()
    contact_lines = textwrap.wrap(contact_txt, width=contact_wrap)
    y_offset = 0
    for line in contact_lines:
        draw.text((left_px, mm_to_px(contact_y_mm) + y_offset), line, font=font_contact, fill=contact_col)
        y_offset += font_contact.getbbox(line)[3] + 4

    return canvas.convert("RGB")

@st.cache_data(show_spinner=False)
def build_saas_preview(
    page_mm: tuple[int, int],
    bg_bytes: bytes | None,
    fg_bytes: bytes | None,
    sig_bytes: bytes | None,
    preset_name: str,
    enhance: bool,
    logo_scale: int, logo_xy: tuple[int, int],
    sig_scale: int, sig_xy: tuple[int, int],
    header_txt: str, header_sz: int, header_col: str, header_y_mm: int,
    price_txt: str, price_sz: int, price_col: str, price_x_mm: int, price_y_mm: int,
    cta_txt: str, cta_sz: int, cta_col: str, cta_x_mm: int, cta_y_mm: int,
    contact_txt: str, contact_sz: int, contact_col: str, contact_y_mm: int, contact_wrap: int,
    prod_w_pct: int, prod_h_pct: int,
    area_preset: str, area_scale: int, nudge_x: int, nudge_y: int,
    text_format: str
) -> Image.Image:
    """SaaS layout: logo TL, headline TM, product centre block, price BL, cta BR, contact BC."""
    w_mm, h_mm = page_mm
    w_px, h_px = mm_to_px(w_mm), mm_to_px(h_mm)

    # background (plain colour – no gradient over photo)
    if bg_bytes:
        bg = Image.open(io.BytesIO(bg_bytes)).convert("RGBA")
    else:
        bg = DEFAULT_PHOTO
    bg = ImageOps.fit(bg, (w_px, h_px), centering=(0.5, 0.5))
    if enhance:
        bg = auto_enhance(bg.convert("RGB")).convert("RGBA")
    canvas = Image.new("RGBA", (w_px, h_px), PRESETS[preset_name]["bg_col"])
    canvas.paste(bg, (0, 0), bg)

    # product image (user % + old anchor/nudge)
    if fg_bytes:
        prod = Image.open(io.BytesIO(fg_bytes)).convert("RGBA")
        prod_w_px = int(w_px * prod_w_pct / 100)
        prod_h_px = int(h_px * prod_h_pct / 100)
        # apply old rectangle anchor + nudge for fine placement
        base_w_mm, base_h_mm = 100, 140
        w_area_mm = base_w_mm * (area_scale / 100)
        h_area_mm = base_h_mm * (area_scale / 100)
        anchors = {
            "Top-left": (0, 0),
            "Top-right": (w_mm - w_area_mm, 0),
            "Bottom-left": (0, h_mm - h_area_mm),
            "Bottom-right": (w_mm - w_area_mm, h_mm - h_area_mm),
            "Centre": ((w_mm - w_area_mm) / 2, (h_mm - h_area_mm) / 2),
        }
        anchor_x_mm, anchor_y_mm = anchors[area_preset]
        anchor_x_mm += nudge_x
        anchor_y_mm += nudge_y
        anchor_x_px = mm_to_px(anchor_x_mm)
        anchor_y_px = mm_to_px(anchor_y_mm)
        prod = ImageOps.fit(prod, (prod_w_px, prod_h_px), centering=(0.5, 0.5))
        shadow = add_drop_shadow(prod, offset_mm=1, blur=2, opacity=30)
        canvas.paste(shadow, (anchor_x_px, anchor_y_px), shadow)

    # logo / signature (sliders still work)
    logo = DEFAULT_LOGO.resize((int(DEFAULT_LOGO.width * logo_scale / 100), int(DEFAULT_LOGO.height * logo_scale / 100)))
    canvas.paste(logo, (mm_to_px(logo_xy[0]), mm_to_px(logo_xy[1])), logo)
    if sig_bytes:
        sig = Image.open(io.BytesIO(sig_bytes)).convert("RGBA")
    else:
        sig = DEFAULT_LOGO
    # duplicate guard
    if sig_bytes and hashlib.md5(sig_bytes).hexdigest() != hashlib.md5(DEFAULT_LOGO.tobytes()).hexdigest():
        sign = sig.resize((int(sig.width * sig_scale / 100), int(sig.height * sig_scale / 100)))
        alpha = sign.split()[-1].point(lambda p: p * 85 // 100)
        sign.putalpha(alpha)
        canvas.paste(sign, (mm_to_px(sig_xy[0]), mm_to_px(sig_xy[1])), sign)

    # text – SaaS sizes (but sliders still control them)
    draw = ImageDraw.Draw(canvas)
    try:
        font_head   = ImageFont.truetype("arial.ttf", header_sz)
        font_price  = ImageFont.truetype("arial.ttf", price_sz)
        font_cta    = ImageFont.truetype("arial.ttf", cta_sz)
        font_contact= ImageFont.truetype("arial.ttf", contact_sz)
    except IOError:
        font_head = font_price = font_cta = font_contact = ImageFont.load_default()

    # headline top-middle (slider controls y)
    head_lines = textwrap.wrap(format_text(header_txt, "Title Case"), width=30)
    y_head = mm_to_px(header_y_mm)
    for line in head_lines:
        w, h = font_head.getbbox(line)[2:4]
        draw.text(((w_px - w) // 2, y_head), line, font=font_head, fill=header_col)
        y_head += h + 5

    # price (slider controls x/y)
    draw.text((mm_to_px(price_x_mm), mm_to_px(price_y_mm)),
              format_text(price_txt, "UPPER CASE"), font=font_price, fill=price_col)

    # cta (slider controls x/y)
    cta_lines = textwrap.wrap(cta_txt, width=20)
    for i, line in enumerate(cta_lines):
        w, h = font_cta.getbbox(line)[2:4]
        x = mm_to_px(cta_x_mm)
        y = mm_to_px(cta_y_mm) + i * (h + 5)
        draw.text((x, y), line, font=font_cta, fill=cta_col)

    # contact (slider controls y, always centred)
    contact_lines = textwrap.wrap(contact_txt, width=contact_wrap)
    y_contact = mm_to_px(contact_y_mm)
    for line in contact_lines:
        w, h = font_contact.getbbox(line)[2:4]
        draw.text(((w_px - w) // 2, y_contact), line, font=font_contact, fill=contact_col)
        y_contact += h + 4

    return canvas.convert("RGB")
