# streamlit_app.py
import io, os, textwrap, math, requests, streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance, ImageFilter
from groq import Groq
from typing import Tuple

# ---------------------------------------------------------
#  GROQ VISION  (cached singleton + call)
# ---------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _groq_client():
    return Groq(api_key=os.getenv("groq_key"))

@st.cache_data(show_spinner=False, ttl=3600)
def describe_image_cached(_img_bytes: bytes) -> str:
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
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{_img_bytes.encode('utf-8').hex()}"}}
            ]
        }],
        temperature=0.7,
        max_tokens=400
    )
    return completion.choices[0].message.content

# ---------------------------------------------------------
#  COSMETIC BG  (glowing circles – never touches photo)
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
#  CACHED IMAGE HELPERS
# -----------------------------------------------------------
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
    if mode == "Title Case": return text.title()
    if mode == "Sentence case": return text.capitalize()
    if mode == "UPPER CASE": return text.upper()
    if mode == "lower case": return text.lower()
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
#  SESSION STATE
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
if "note_text" not in st.session_state:
    st.session_state.note_text = "Today's reflections…"
if "preview_generated" not in st.session_state:
    st.session_state.preview_generated = False

L = st.session_state.layout

# ---------------------------------------------------------
#  SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    st.title("📔 Journal Composer")
    mode = st.radio("Mode", ["Edit", "Preview"], index=0)
    if mode == "Edit":
        st.header("1. Images")
        bg_file = st.file_uploader("Upload background (jpg/png) – optional", type=["jpg", "jpeg", "png"])
        sig_file = st.file_uploader("Upload signature (optional)", type=["png"])
        fg_file  = st.file_uploader("Upload foreground PNG (transparent) – optional", type=["png"])

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

        if fg_file:
            st.subheader("Foreground area")
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

        # ---------- AI COPY FROM IMAGE ----------
        st.header("4. ✨ AI copy from image")
        if st.button("Generate headline / tag / note / description / caption from image"):
            bg_bytes = st.session_state.get("bg_bytes")
            if not bg_bytes:
                st.error("Please upload a background image first.")
                st.stop()
            composite = build_preview(
                PAGE[L["page"]],
                bg_bytes,
                st.session_state.get("fg_bytes"),
                st.session_state.get("sig_bytes"),
                L["preset"],
                L["enhance"],
                st.session_state.get("area_scale", 100),
                st.session_state.get("area_preset", "Centre"),
                st.session_state.get("area_nudge_x", 0),
                st.session_state.get("area_nudge_y", 0),
                L["logo_scale"], (L["logo_x"], L["logo_y"]),
                L["sig_scale"], (L["sig_x"], L["sig_y"]),
                20,
                "", 0, "", 0,  # header dummy
                "", 0, "", 0,  # tag dummy
                "", 0, "", 0, 45,
                "", 0, "", 0, 60,
                L["text_format"]
            )
            buf = io.BytesIO()
            composite.save(buf, format="PNG")
            answer = describe_image_cached(buf.getvalue())
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
#  PREVIEW  (cached)
# ---------------------------------------------------------
bg_bytes = st.session_state.get("bg_bytes")
fg_bytes = st.session_state.get("fg_bytes")
sig_bytes = st.session_state.get("sig_bytes")

header_text  = st.session_state.get("header_in", "My Product")
header_size  = st.session_state.get("header_size", 125)
header_col   = st.session_state.get("header_col", "#000000")
header_y_mm  = st.session_state.get("header_y_mm", 30)

tag_text     = st.session_state.get("tag_in", "The best thing since sliced bread.")
tag_size     = st.session_state.get("tag_size", 65)
tag_col      = st.session_state.get("tag_col", "#555555")
tag_y_mm     = st.session_state.get("tag_y_mm", 50)

info_text    = st.session_state.get("info_in", "Describe your product here.\nYou can write several sentences.")
info_size    = st.session_state.get("info_size", 85)
info_col     = st.session_state.get("info_col", "#333333")
info_y_mm    = st.session_state.get("info_y_mm", 70)
info_wrap    = st.session_state.get("info_wrap", 45)

contact_text = st.session_state.get("contact_in", "Email: hello@example.com\nPhone: +1 234 567 890")
contact_size = st.session_state.get("contact_size", 70)
contact_col  = st.session_state.get("contact_col", "#444444")
contact_y_mm = st.session_state.get("contact_y_mm", PAGE[L["page"]][1] - 30)
contact_wrap = st.session_state.get("contact_wrap", 60)

page_img = build_preview(
    PAGE[L["page"]],
    bg_bytes,
    fg_bytes,
    sig_bytes,
    L["preset"],
    L["enhance"],
    st.session_state.get("area_scale", 100),
    st.session_state.get("area_preset", "Centre"),
    st.session_state.get("area_nudge_x", 0),
    st.session_state.get("area_nudge_y", 0),
    L["logo_scale"], (L["logo_x"], L["logo_y"]),
    L["sig_scale"], (L["sig_x"], L["sig_y"]),
    20,
    header_text, header_size, header_col, header_y_mm,
    tag_text, tag_size, tag_col, tag_y_mm,
    info_text, info_size, info_col, info_y_mm, info_wrap,
    contact_text, contact_size, contact_col, contact_y_mm, contact_wrap,
    L["text_format"]
)

st.image(page_img, use_column_width=True, caption=f"Preview – {L['page']}  {PAGE[L['page']][0]}×{PAGE[L['page']][1]} mm")

# ---------------------------------------------------------
#  EXPORT  (JPEG only – no GIF)
# ---------------------------------------------------------
if st.button("Generate file", key="gen_final"):
    st.session_state.preview_generated = True

if st.session_state.get("preview_generated", False):
    dpi_out = L["export_dpi"]
    scale   = dpi_out / 300.0
    out_size = (int(page_img.width * scale), int(page_img.height * scale))
    out_img  = page_img.resize(out_size, Image.LANCZOS)
    buf = io.BytesIO()
    out_img.save(buf, format="JPEG", quality=90, dpi=(dpi_out, dpi_out))
    st.download_button("💾 Download JPEG", buf.getvalue(),
                       file_name=f"journal_{L['page'].replace(' ','_')}_{dpi_out}dpi.jpg",
                       mime="image/jpeg")
