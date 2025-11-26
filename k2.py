# journal_app.py  ––  final version  ––
import io, textwrap, math, requests, streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance, ImageFilter
from rembg import remove   # pip install rembg (only if you want auto-bg removal)

# ---------- EXTERNAL ASSETS ----------
@st.cache_data(show_spinner=False)
def load_url_image(url):
    return Image.open(requests.get(url, stream=True, timeout=10).raw).convert("RGBA")

LOGO_URL    = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"
PRODUCT_URL = "https://ik.imagekit.io/ericmwangi/product.png"
DEFAULT_LOGO  = load_url_image(LOGO_URL)
DEFAULT_PHOTO = load_url_image(PRODUCT_URL)

# ---------- PAGE SIZES (paper + social) ----------
PAGE = {
    "A4 portrait":  (210, 297),
    "A4 landscape": (297, 210),
    "A5 portrait":  (148, 210),
    "A5 landscape": (210, 148),
    "Letter":       (216, 279),
    "4×6 in":       (102, 152),
    "Square 1:1":   (200, 200),
    "Instagram 1:1":(200, 200),
    "FaceBook 1.91:1":(200, 105),  # 1.91 ≈ 200/105
    "Story 9:16":   (108, 192),
}
DPI = 300
MM_TO_PX = DPI / 25.4
def mm_to_px(mm): return int(mm * MM_TO_PX)

# ---------- TEXT UTILS ----------
def format_text(text, mode):
    if mode == "Title Case":    return text.title()
    if mode == "Sentence case": return text.capitalize()
    if mode == "UPPER CASE":    return text.upper()
    if mode == "lower case":    return text.lower()
    return text

# ---------- DROP-SHADOW ----------
def add_drop_shadow(img, offset_mm=2, blur=3, opacity=40):
    """Return img with minimal shadow behind transparent areas."""
    shadow = Image.new("RGBA", (img.width + mm_to_px(offset_mm)*2, img.height + mm_to_px(offset_mm)*2), (0,0,0,0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rectangle([mm_to_px(offset_mm), mm_to_px(offset_mm),
                           img.width + mm_to_px(offset_mm), img.height + mm_to_px(offset_mm)],
                          fill=(0,0,0,opacity))
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    shadow.paste(img, (mm_to_px(offset_mm), mm_to_px(offset_mm)), img)
    return shadow

# ---------- SOCIAL GIF ----------
def make_gif(frame_base, fg_sized, anchor, frames=10, duration=100):
    imgs = []
    for i in range(frames):
        frame = frame_base.copy()
        angle = i * 360 // frames
        fg_rot = fg_sized.rotate(angle, expand=True)
        frame.paste(fg_rot, anchor, fg_rot)
        imgs.append(frame.convert("RGB"))
    buf = io.BytesIO()
    imgs[0].save(buf, format="GIF", append_images=imgs[1:], save_all=True, duration=duration, loop=0)
    return buf.getvalue()

# ---------- UTILS ----------
def mood_gradient(size, top_col, bottom_col):
    w, h = size
    grad = Image.new("RGBA", (w, h), top_col)
    top_rgb    = tuple(int(top_col[i:i+2], 16) for i in (1,3,5))
    bottom_rgb = tuple(int(bottom_col[i:i+2], 16) for i in (1,3,5))
    for y in range(h):
        ratio = y / h
        r = int(top_rgb[0]*(1-ratio) + bottom_rgb[0]*ratio)
        g = int(top_rgb[1]*(1-ratio) + bottom_rgb[1]*ratio)
        b = int(top_rgb[2]*(1-ratio) + bottom_rgb[2]*ratio)
        ImageDraw.Draw(grad).line([(0, y), (w, y)], fill=(r, g, b, 180))
    return grad

def auto_enhance(img):
    img = ImageOps.autocontrast(img)
    return ImageEnhance.Color(img).enhance(1.15)

# ---------- PRESETS ----------
PRESETS = {
    "Morning light": {"top_col": "#FFD700", "bottom_col": "#8B4513", "note_col": "#4F4F4F", "sig_opacity": 90},
    "Night dark"   : {"top_col": "#1E1E1E", "bottom_col": "#3E2723", "note_col": "#E0E0E0", "sig_opacity": 80},
    "Vintage"      : {"top_col": "#FFE4B5", "bottom_col": "#A0522D", "note_col": "#795548", "sig_opacity": 85},
    "Minimal b&w"  : {"top_col": "#FFFFFF", "bottom_col": "#CCCCCC", "note_col": "#000000", "sig_opacity": 70},
}

# ---------- SESSION ----------
if "layout" not in st.session_state:
    st.session_state.layout = dict(
        page="A4 portrait", sig_scale=25, sig_x=20, sig_y=20,
        note_x=50, note_y=200, note_size=35, note_wrap=35,
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

# ---------- SIDEBAR ----------
with st.sidebar:
    st.title("📔 Journal Composer")
    mode = st.radio("Mode", ["Edit", "Preview"], index=0)
    if mode == "Edit":
        st.header("1. Images")
        bg_file = st.file_uploader("Upload background (jpg/png) – optional", type=["jpg", "jpeg", "png"])
        sig_file = st.file_uploader("Upload signature (optional)", type=["png"])
        fg_file  = st.file_uploader("Upload foreground PNG (transparent) – optional", type=["png"])
        # load ONCE and cache
        if bg_file is not None:
            st.session_state.user_bg = Image.open(bg_file).convert("RGBA")
            st.session_state.bg      = st.session_state.user_bg
        else:
            st.session_state.bg = DEFAULT_PHOTO
        if sig_file is not None:
            st.session_state.user_sig = Image.open(sig_file).convert("RGBA")
            st.session_state.sig      = st.session_state.user_sig
        else:
            st.session_state.sig = DEFAULT_LOGO
        if fg_file is not None:
            st.session_state.user_fg = Image.open(fg_file).convert("RGBA")
            st.session_state.fg      = st.session_state.user_fg
        else:
            st.session_state.fg = None

        # ---------- 1a. FOREGROUND PRE-DEFINED AREA + DROP-SHADOW ----------
        if fg_file is not None:
            st.subheader("Foreground area (pre-defined rectangle)")
            # base rectangle size (change here if you want)
            base_w_mm, base_h_mm = 100, 140
            w_area_mm = base_w_mm * (st.session_state.get("area_scale", 100) / 100)
            h_area_mm = base_h_mm * (st.session_state.get("area_scale", 100) / 100)
            area_preset = st.selectbox("Area anchor", ["Top-left", "Top-right", "Bottom-left", "Bottom-right", "Centre"], index=4)
            area_scale  = st.slider("Area scale %", 50, 200, 100, key="area_scale")
            area_nudge_x = st.slider("Area nudge X (mm)", -20, 20, 0, key="area_nudge_x")
            area_nudge_y = st.slider("Area nudge Y (mm)", -20, 20, 0, key="area_nudge_y")
            # quick anchors
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("Centre area", key="centre_area"):
                    st.session_state.area_preset = "Centre"
            with c2:
                if st.button("Top-right", key="topright_area"):
                    st.session_state.area_preset = "Top-right"
            with c3:
                if st.button("Bottom-left", key="bottomleft_area"):
                    st.session_state.area_preset = "Bottom-left"

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
            sig_opacity    = st.slider("Sig opacity", 10, 100, 85)

        st.header("3. Text blocks")
        left_mm = st.slider("Text left indent (mm)", 0, 50, 20)

        # HEADER
        st.subheader("Header")
        header_text = st.text_input("Header", "My Product", key="header_in")
        header_size = st.slider("Header size (pt)", 12, 200, 94, key="header_size")   # default 94
        header_col  = st.color_picker("Header colour", "#000000", key="header_col")
        header_y_mm = st.slider("Header Y (mm)", 0, PAGE[L["page"]][1], 30, key="header_y")

        # TAG-LINE
        st.subheader("Tag-line")
        tag_text = st.text_input("Tag-line", "The best thing since sliced bread.", key="tag_in")
        tag_size = st.slider("Tag-line size (pt)", 8, 150, 48, key="tag_size")       # default 48
        tag_col  = st.color_picker("Tag-line colour", "#555555", key="tag_col")
        tag_y_mm = st.slider("Tag-line Y (mm)", 0, PAGE[L["page"]][1], 50, key="tag_y")

        # PRODUCT INFO
        st.subheader("Product info")
        info_text = st.text_area("Info", "Describe your product here.\nYou can write several sentences.", key="info_in")
        info_size = st.slider("Info size (pt)", 8, 180, 62, key="info_size")        # default 62
        info_col  = st.color_picker("Info colour", "#333333", key="info_col")
        info_y_mm = st.slider("Info Y (mm)", 0, PAGE[L["page"]][1], 70, key="info_y")
        info_wrap = st.slider("Info wrap width", 20, 80, 45, key="info_wrap")

        # CONTACT
        st.subheader("Contact")
        contact_text = st.text_area("Contact", "Email: hello@example.com\nPhone: +1 234 567 890", key="contact_in")
        contact_size = st.slider("Contact size (pt)", 8, 150, 50, key="contact_size")  # default 50
        contact_col  = st.color_picker("Contact colour", "#444444", key="contact_col")
        contact_y_mm = st.slider("Contact Y (mm)", 0, PAGE[L["page"]][1], PAGE[L["page"]][1] - 30, key="contact_y")
        contact_wrap = st.slider("Contact wrap width", 20, 100, 60, key="contact_wrap")

        # global text tools
        text_format = st.selectbox("Text format", ["Sentence case", "Title Case", "UPPER CASE", "lower case"], index=["Sentence case", "Title Case", "UPPER CASE", "lower case"].index(L["text_format"]))
        L["text_format"] = text_format
        L["warp"]        = st.checkbox("Warp text (sine wave)", L["warp"])

        L["enhance"] = st.checkbox("Auto-enhance photo", L["enhance"])
        L["export_dpi"] = st.radio("Export DPI", [72, 150, 300], index=2)

# ---------- PREVIEW ----------
bg = st.session_state.get("bg", DEFAULT_PHOTO)
fg = st.session_state.get("fg", None)
sig = st.session_state.get("sig", DEFAULT_LOGO)
logo = DEFAULT_LOGO

w_px, h_px = mm_to_px(PAGE[L["page"]][0]), mm_to_px(PAGE[L["page"]][1])
page = Image.new("RGBA", (w_px, h_px), (255, 255, 255, 255))

# 1. background fills page (with preset gradient)
bg = ImageOps.fit(bg, (w_px, h_px), centering=(0.5, 0.5))
if L["enhance"]:
    bg = auto_enhance(bg.convert("RGB")).convert("RGBA")
grad = mood_gradient(bg.size, PRESETS[L["preset"]]["top_col"], PRESETS[L["preset"]]["bottom_col"])
bg = Image.alpha_composite(bg, grad)
page.paste(bg, (0, 0), bg)

# 2. pre-defined rectangle for foreground + minimal drop-shadow
if fg is not None:
    base_w_mm, base_h_mm = 100, 140   # change here if you want
    w_area_mm = base_w_mm * (st.session_state.get("area_scale", 100) / 100)
    h_area_mm = base_h_mm * (st.session_state.get("area_scale", 100) / 100)
    w_area_px = mm_to_px(w_area_mm)
    h_area_px = mm_to_px(h_area_mm)
    anchors = {
        "Top-left":     (0, 0),
        "Top-right":    (PAGE[L["page"]][0] - w_area_mm, 0),
        "Bottom-left":  (0, PAGE[L["page"]][1] - h_area_mm),
        "Bottom-right": (PAGE[L["page"]][0] - w_area_mm, PAGE[L["page"]][1] - h_area_mm),
        "Centre":       ((PAGE[L["page"]][0] - w_area_mm) / 2, (PAGE[L["page"]][1] - h_area_mm) / 2),
    }
    anchor_x_mm, anchor_y_mm = anchors[st.session_state.get("area_preset", "Centre")]
    anchor_x_mm += st.session_state.get("area_nudge_x", 0)
    anchor_y_mm += st.session_state.get("area_nudge_y", 0)
    anchor_x_px = mm_to_px(anchor_x_mm)
    anchor_y_px = mm_to_px(anchor_y_mm)

    fg_sized = ImageOps.fit(fg, (w_area_px, h_area_px), centering=(0.5, 0.5))
    # minimal drop-shadow
    shadow = add_drop_shadow(fg_sized, offset_mm=2, blur=3, opacity=40)
    page.paste(shadow, (anchor_x_px - mm_to_px(2), anchor_y_px - mm_to_px(2)), shadow)

# 3. logo & signature (unchanged)
logo = logo.resize((int(logo.width * L["logo_scale"]/100), int(logo.height * L["logo_scale"]/100)))
page.paste(logo, (mm_to_px(L["logo_x"]), mm_to_px(L["logo_y"])), logo)
sign = sig.resize((int(sig.width * L["sig_scale"]/100), int(sig.height * L["sig_scale"]/100)))
alpha = sign.split()[-1].point(lambda p: p * 85 / 100)
sign.putalpha(alpha)
page.paste(sign, (mm_to_px(L["sig_x"]), mm_to_px(L["sig_y"])), sign)

# 4. text blocks (unchanged)
draw = ImageDraw.Draw(page)
left_px = mm_to_px(left_mm)

header_font = ImageFont.truetype("arial.ttf", header_size)
draw.text((left_px, mm_to_px(header_y_mm)), format_text(header_text, "Title Case"), font=header_font, fill=header_col)

tag_font = ImageFont.truetype("arial.ttf", tag_size)
draw.text((left_px, mm_to_px(tag_y_mm)), tag_text, font=tag_font, fill=tag_col)

info_font = ImageFont.truetype("arial.ttf", info_size)
lines = textwrap.wrap(info_text, width=info_wrap)
y_offset = 0
for line in lines:
    draw.text((left_px, mm_to_px(info_y_mm) + y_offset), line, font=info_font, fill=info_col)
    y_offset += info_font.getbbox(line)[3] + 5

contact_font = ImageFont.truetype("arial.ttf", contact_size)
contact_lines = textwrap.wrap(contact_text, width=contact_wrap)
y_offset = 0
for line in contact_lines:
    draw.text((left_px, mm_to_px(contact_y_mm) + y_offset), line, font=contact_font, fill=contact_col)
    y_offset += contact_font.getbbox(line)[3] + 4)

st.image(page, use_column_width=True, caption=f"Preview – {L['page']}  {PAGE[L['page']][0]}×{PAGE[L['page']][1]} mm")

# ---------- SOCIAL EXPORT ----------
if st.button("Generate file", key="gen_final"):
    st.session_state.preview_generated = True

if st.session_state.get("preview_generated", False):
    dpi_out = L["export_dpi"]
    scale   = dpi_out / 300.0
    out_size = (int(page.width * scale), int(page.height * scale))
    out_img  = page.resize(out_size, Image.LANCZOS).convert("RGB")
    buf = io.BytesIO()
    out_img.save(buf, format="JPEG", quality=95, dpi=(dpi_out, dpi_out))
    st.download_button("💾 Download JPEG", buf.getvalue(),
                       file_name=f"journal_{L['page'].replace(' ','_')}_{dpi_out}dpi.jpg",
                       mime="image/jpeg")
    # GIF export (only if foreground exists)
    if fg is not None:
        gif_bytes = make_gif(page, fg_sized, (anchor_x_px, anchor_y_px))
        st.download_button("📥 Download GIF (spin)", gif_bytes,
                           file_name=f"journal_{L['page'].replace(' ','_')}.gif",
                           mime="image/gif")
