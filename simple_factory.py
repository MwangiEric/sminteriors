import streamlit as st
import io, requests, math, tempfile, base64, json, random, time, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip
from rembg import remove

# --- GLOBAL CONFIGURATION ---
st.set_page_config(page_title="AdGen EVO: Content & Ads", layout="wide", page_icon="✨")

# --- CONSTANTS ---
WIDTH, HEIGHT = 720, 1280
FPS = 30
DURATION = 6
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

# --- ASSETS ---
MUSIC_TRACKS = {
    "Upbeat Pop": "https://archive.org/download/Bensound_-_Jazzy_Frenchy/Bensound_-_Jazzy_Frenchy.mp3",
    "Luxury Chill": "https://archive.org/download/bensound-adaytoremember/bensound-adaytoremember.mp3",
    "Modern Beats": "https://archive.org/download/bensound-sweet/bensound-sweet.mp3"
}

# --- AUTH ---
if "groq_key" not in st.secrets:
    st.error("🚨 Missing Secret: Add `groq_key` to your .streamlit/secrets.toml")
    st.stop()

# Groq API Endpoint & Headers
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {st.secrets['groq_key']}",
    "Content-Type": "application/json"
}

# --- IMAGE PROCESSING ENGINE (Rembg + Enhance) ---
def process_image_pro(input_image):
    """Removes background via rembg and applies enhancements."""
    with st.spinner("🚿 Removing background & enhancing..."):
        img_byte_arr = io.BytesIO()
        input_image.save(img_byte_arr, format="PNG")
        input_image_bytes = img_byte_arr.getvalue()

        output_bytes = remove(input_image_bytes)
        clean_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")

    # Slight contrast and sharpness tweaks
    clean_img = ImageEnhance.Contrast(clean_img).enhance(1.15)
    clean_img = ImageEnhance.Sharpness(clean_img).enhance(1.5)
    return clean_img

# --- FONTS ---
def get_font(size):
    possible_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "arial.ttf"
    ]
    for path in possible_fonts:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()

# --- EASING & HELPERS ---
def ease_out_elastic(t):
    c4 = (2 * math.pi) / 3
    if t <= 0: return 0
    if t >= 1: return 1
    return math.pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

def linear_fade(t, start, duration):
    if t < start: return 0.0
    if t > start + duration: return 1.0
    return (t - start) / duration

# --- TEMPLATES ---
BRAND_PRIMARY = "#4C3B30"
BRAND_ACCENT = "#D2A544"
BRAND_TEXT_LIGHT = "#FFFFFF"
BRAND_TEXT_DARK = "#000000"

TEMPLATES = {
    "SM Interiors Basic": {
        "bg_grad": [BRAND_PRIMARY, "#2a201b"],
        "accent": BRAND_ACCENT, "text": BRAND_TEXT_LIGHT,
        "price_bg": BRAND_ACCENT, "price_text": BRAND_TEXT_DARK,
        "graphic_type": "none"
    },
    "Brand Diagonal Slice": {
        "bg_grad": [BRAND_PRIMARY, "#3e2e24"],
        "accent": BRAND_ACCENT, "text": BRAND_TEXT_LIGHT,
        "price_bg": BRAND_ACCENT, "price_text": BRAND_TEXT_DARK,
        "graphic_type": "diagonal",
        "graphic_color": BRAND_ACCENT
    },
    "Brand Circular Flow": {
        "bg_grad": [BRAND_PRIMARY, "#332A22"],
        "accent": BRAND_ACCENT, "text": BRAND_TEXT_LIGHT,
        "price_bg": BRAND_ACCENT, "price_text": BRAND_TEXT_DARK,
        "graphic_type": "circular",
        "graphic_color": BRAND_ACCENT
    },
    "Brand Split Panel": {
        "bg_grad": [BRAND_PRIMARY, BRAND_PRIMARY],
        "accent": BRAND_TEXT_LIGHT, "text": BRAND_TEXT_LIGHT,
        "price_bg": BRAND_ACCENT, "price_text": BRAND_TEXT_DARK,
        "graphic_type": "split",
        "graphic_color": BRAND_ACCENT
    }
}

# --- LAYOUT HELPERS ---
def sanitize_layout(layout):
    sanitized = []
    for item in layout:
        sanitized.append({
            "role": item.get("role", "unknown"),
            "x": int(round(item.get("x", 0))),
            "y": int(round(item.get("y", 0))),
            "w": int(round(item.get("w", 100))),
            "h": int(round(item.get("h", 100)))
        })
    return sanitized

def center_layout_items(layout):
    for item in layout:
        if item["role"] in ["product", "caption", "price", "contact"]:
            item["x"] = (WIDTH - item["w"]) // 2
    return layout

# --- GROQ AI LOGIC ---
def ask_groq(payload):
    """Send payload to Groq and return content or None on failure."""
    try:
        r = requests.post(GROQ_URL, json=payload, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
        # defensive extraction
        choices = data.get("choices") or []
        if choices and isinstance(choices, list):
            message = choices[0].get("message") or {}
            content = message.get("content") or message.get("text") or ""
            return content
        return None
    except requests.exceptions.HTTPError as e:
        msg = ""
        try:
            msg = f"Groq API error {e.response.status_code}: {e.response.text[:300]}"
        except Exception:
            msg = f"Groq API HTTP error: {e}"
        st.error(msg)
        return None
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None

def get_data_groq(img, model_name):
    """Get a short caption and a layout JSON array from Groq (with safe fallbacks)."""
    # Convert image to JPEG base64
    buf = io.BytesIO()
    if img.mode == "RGBA":
        rgb_img = Image.new("RGB", img.size, (255,255,255))
        rgb_img.paste(img, (0,0), img)
    else:
        rgb_img = img.convert("RGB")
    rgb_img.save(buf, format="JPEG", quality=90)
    b64 = base64.b64encode(buf.getvalue()).decode()

    # Hook prompt (vision+text) - simple textual prompt (format can be adapted if Groq expects different)
    p_hook = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {"role":"user", "content": f"Write a 4-word catchy luxury ad hook for this furniture model '{model_name}'. Image is provided as base64."},
            {"role":"user", "content": f"data:image/jpeg;base64,{b64}"}
        ],
        "temperature": 0.7,
        "max_tokens": 30
    }

    # Layout prompt: request JSON array only
    p_layout = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role":"system", "content": "Output ONLY a valid JSON array of 5 objects. Each object must have role,x,y,w,h (integers). No extra text."},
            {"role":"user", "content": f"Design a 720×1280 vertical luxury ad layout. Required roles: logo, product, caption, price, contact. Center the product. Product name: {model_name}"}
        ],
        "temperature": 0.3,
        "max_tokens": 400
    }

    caption = ask_groq(p_hook) or "Elevate Your Space"
    # cleanup caption
    caption = caption.strip().strip('"')

    layout_raw = ask_groq(p_layout)
    default_layout = [
        {"role":"logo","x":50,"y":50,"w":200,"h":100},
        {"role":"product","x":60,"y":250,"w":600,"h":600},
        {"role":"caption","x":60,"y":900,"w":600,"h":100},
        {"role":"price","x":160,"y":1050,"w":400,"h":120},
        {"role":"contact","x":60,"y":1200,"w":600,"h":60}
    ]

    try:
        j = json.loads(layout_raw) if layout_raw else default_layout
        final_layout = j if isinstance(j, list) and len(j) == 5 else default_layout
        sanitized = sanitize_layout(final_layout)
        return caption, center_layout_items(sanitized)
    except Exception:
        sanitized_default = sanitize_layout(default_layout)
        return caption, center_layout_items(sanitized_default)

# --- CONTENT GENERATOR ---
def generate_tips(content_type, keyword="interior design"):
    system_prompt = (
        "You are a content creation expert for a luxury home furnishing brand named 'SM Interiors'.\n"
        "Tone: authoritative, engaging, and suitable for short-form video content (TikTok/Reels).\n"
        "Respond using only markdown bullet points. Do not include any introductory or concluding sentences."
    )

    if content_type == "DIY Tips":
        user_prompt = f"Generate 5 quick, actionable DIY home decor tips or furniture restoration ideas that use common materials, focusing on high-impact visuals. Keyword: '{keyword}'."
    elif content_type == "Furniture Tips":
        user_prompt = f"Generate 5 high-value tips on care, arrangement, or selection for high-end furniture. Focus on luxury and visuals. Product: '{keyword}'."
    elif content_type == "Interior Design Tips":
        user_prompt = f"Generate 5 creative and trending interior design tips or small-space hacks related to '{keyword}'."
    elif content_type == "Maintenance Tips":
        user_prompt = f"Generate 5 essential tips on cleaning, polishing, and long-term maintenance for luxury materials (wood, brass, upholstery) related to '{keyword}'."
    else:
        return "*Select a content type to generate ideas.*"

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role":"system","content": system_prompt},
            {"role":"user","content": user_prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 512
    }

    with st.spinner(f"🧠 Generating {content_type} ideas..."):
        return ask_groq(payload) or "No ideas returned."

# --- RENDERING UTILITIES ---
def draw_wrapped_text(draw, text, box, font, color, align="center"):
    words = text.split()
    lines = []
    line = ""
    for w in words:
        test_line = (line + " " + w).strip() if line else w
        bbox = draw.textbbox((0,0), test_line, font=font)
        text_width = bbox[2] - bbox[0]
        if text_width > box['w'] and line:
            lines.append(line)
            line = w
        else:
            line = test_line
    if line:
        lines.append(line)

    current_y = box['y']
    for l in lines:
        bbox = draw.textbbox((0,0), l, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        if align == "center":
            lx = box['x'] + (box['w'] - text_width) // 2
        else:
            lx = box['x']
        draw.text((lx, current_y), l, font=font, fill=color)
        current_y += text_height + 6

def hex_to_rgb_tuple(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0,2,4))

def create_frame(t, img, boxes, texts, tpl_name):
    T = TEMPLATES.get(tpl_name, list(TEMPLATES.values())[0])
    canvas = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(canvas)

    # Background gradient
    try:
        c1 = hex_to_rgb_tuple(T["bg_grad"][0])
        c2 = hex_to_rgb_tuple(T["bg_grad"][1])
    except Exception:
        c1 = (76,59,48)
        c2 = (42,32,27)
    for y in range(HEIGHT):
        r = int(c1[0] + (c2[0]-c1[0]) * y/HEIGHT)
        g = int(c1[1] + (c2[1]-c1[1]) * y/HEIGHT)
        b = int(c1[2] + (c2[2]-c1[2]) * y/HEIGHT)
        draw.line([(0,y),(WIDTH,y)], fill=(r,g,b))

    graphic_color_rgb = None
    if "graphic_color" in T:
        try:
            graphic_color_rgb = hex_to_rgb_tuple(T["graphic_color"])
        except Exception:
            graphic_color_rgb = None

    # Graphics based on template
    if T.get("graphic_type") == "diagonal" and graphic_color_rgb:
        diag_alpha = int(255 * linear_fade(t, 0.5, 1.0))
        for i in range(-WIDTH, WIDTH + HEIGHT, 60):
            draw.line([(i,0),(i+HEIGHT,HEIGHT)], fill=(graphic_color_rgb[0], graphic_color_rgb[1], graphic_color_rgb[2], diag_alpha), width=10)
        if t > 0.8:
            solid_alpha = int(255 * linear_fade(t, 1.0, 0.5))
            draw.polygon([(0,100),(WIDTH,0),(WIDTH,200),(0,300)], fill=(graphic_color_rgb[0], graphic_color_rgb[1], graphic_color_rgb[2], solid_alpha))

    elif T.get("graphic_type") == "circular" and graphic_color_rgb:
        circle_alpha = int(255 * linear_fade(t, 0.8, 0.7))
        circle_size = int(WIDTH * 1.2 * ease_out_elastic(max(0, t - 0.5)))
        cx, cy = int(WIDTH * 0.8), int(HEIGHT * 0.7)
        draw.ellipse([cx - circle_size//2, cy - circle_size//2, cx + circle_size//2, cy + circle_size//2],
                     fill=(graphic_color_rgb[0], graphic_color_rgb[1], graphic_color_rgb[2], int(circle_alpha * 0.6)))
        circle_size_small = int(WIDTH * 0.6 * ease_out_elastic(max(0, t - 1.0)))
        cx_s, cy_s = int(WIDTH * 0.2), int(HEIGHT * 0.3)
        draw.ellipse([cx_s - circle_size_small//2, cy_s - circle_size_small//2, cx_s + circle_size_small//2, cy_s + circle_size_small//2],
                     fill=(graphic_color_rgb[0], graphic_color_rgb[1], graphic_color_rgb[2], int(circle_alpha * 0.35)))

    elif T.get("graphic_type") == "split" and graphic_color_rgb:
        split_height = int(HEIGHT * 0.3 * ease_out_elastic(max(0, t - 1.0)))
        draw.rectangle([0, HEIGHT - split_height, WIDTH, HEIGHT], fill=(graphic_color_rgb[0], graphic_color_rgb[1], graphic_color_rgb[2], 255))
        dot_fade = int(255 * linear_fade(t, 1.2, 0.5))
        for i in range(5):
            draw.ellipse([WIDTH - 60, 100 + i*40, WIDTH - 40, 120 + i*40], fill=(graphic_color_rgb[0], graphic_color_rgb[1], graphic_color_rgb[2], dot_fade))

    # Elements
    for b in boxes:
        role = b["role"]
        if role == "product":
            float_y = math.sin(t * 2) * 12
            scale = ease_out_elastic(min(t, 1.0))
            if scale > 0.01:
                pw, ph = int(b['w']*scale), int(b['h']*scale)
                p_rs = img.resize((max(1,pw), max(1,ph)), Image.LANCZOS)

                # shadow
                shadow = Image.new("RGBA", p_rs.size, (0,0,0,0))
                alpha_mask = p_rs.split()[-1].point(lambda a: int(a*0.4))
                shadow_draw = ImageDraw.Draw(shadow)
                shadow_draw.bitmap((0,0), p_rs, fill=(0,0,0,255))
                shadow = shadow.filter(ImageFilter.GaussianBlur(12))

                cx = b['x'] + (b['w']-pw)//2
                cy = b['y'] + (b['h']-ph)//2 + int(float_y)

                canvas.paste(shadow, (int(cx), int(cy+25)), shadow)
                canvas.paste(p_rs, (int(cx), int(cy)), p_rs)

        elif role == "price":
            anim = linear_fade(t, 1.5, 0.5)
            if anim > 0:
                off_y = (1 - ease_out_elastic(anim)) * 100
                price_bg_rgb = hex_to_rgb_tuple(T.get("price_bg", BRAND_ACCENT))
                rect = [b['x'], int(b['y']+off_y), b['x']+b['w'], int(b['y']+b['h']+off_y)]
                radius = min(25, b['h']//4)
                # Draw rounded rectangle manually if not supported
                draw.rounded_rectangle(rect, radius=radius, fill=(price_bg_rgb[0], price_bg_rgb[1], price_bg_rgb[2], 255))
                f = get_font(48)
                draw_wrapped_text(draw, texts.get("price",""), {'x':b['x'],'y':int(b['y']+off_y),'w':b['w'],'h':b['h']}, f, T.get("price_text", "#000000"))

        elif role == "caption":
            if t > 1.0:
                f = get_font(46)
                accent_rgb = T.get("accent", BRAND_ACCENT)
                draw_wrapped_text(draw, texts.get("caption",""), b, f, accent_rgb)

        elif role == "contact":
            if t > 2.5:
                f = get_font(28)
                draw_wrapped_text(draw, texts.get("contact",""), b, f, T.get("text", BRAND_TEXT_LIGHT))

        elif role == "logo":
            try:
                logo = Image.open(requests.get(LOGO_URL, stream=True, timeout=10).raw).convert("RGBA")
                logo = logo.resize((max(1,b['w']), max(1,b['h'])), Image.LANCZOS)
                # small shadow
                logo_shadow = Image.new("RGBA", logo.size, (0,0,0,0))
                ls_draw = ImageDraw.Draw(logo_shadow)
                ls_draw.ellipse([3,3,logo.width-3,logo.height-3], fill=(0,0,0,120))
                logo_shadow = logo_shadow.filter(ImageFilter.GaussianBlur(8))
                canvas.paste(logo_shadow, (b['x']+4, b['y']+4), logo_shadow)
                canvas.paste(logo, (b['x'], b['y']), logo)
            except Exception:
                pass

    # Vignette
    vignette = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
    v_draw = ImageDraw.Draw(vignette)
    start_v = int(HEIGHT*0.7)
    for y in range(start_v, HEIGHT):
        alpha = int(180 * ((y - start_v)/(HEIGHT-start_v)))
        v_draw.line([(0,y),(WIDTH,y)], fill=(0,0,0,alpha))
    canvas = Image.alpha_composite(canvas, vignette)

    return np.array(canvas.convert("RGB"))

# --- STREAMLIT UI ---
if 'show_content' not in st.session_state:
    st.session_state.show_content = False

with st.sidebar:
    st.header("⚡ Turbo Ad Generator")
    u_file = st.file_uploader("1. Product Image", type=["jpg", "png"])
    u_model = st.text_input("Product Name", "Walden Media Console")
    u_price = st.text_input("Price", "Ksh 49,900")
    u_contact = st.text_input("Contact Info", "0710895737")

    u_style = st.selectbox("Design Template", list(TEMPLATES.keys()), index=0)
    u_music = st.selectbox("Background Music", list(MUSIC_TRACKS.keys()))
    btn_ad = st.button("🚀 Generate Ad Video")
    btn_test = st.button("🔑 Verify Groq Key")

    st.markdown("---")
    st.header("💡 Content Idea Generator")
    u_content_type = st.radio("Select Content Type:", ["DIY Tips", "Furniture Tips", "Interior Design Tips", "Maintenance Tips"])
    u_content_keyword = st.text_input("Content Focus (e.g., 'Small living room')", value="Mid-Century Console")
    btn_content = st.button("🧠 Generate Tips")

st.title("AdGen EVO: Dynamic Brand Ads & Content")

# CONTENT GENERATION
if btn_content:
    st.session_state.show_content = True
    st.session_state.content_type = u_content_type
    st.session_state.content_keyword = u_content_keyword

if st.session_state.show_content and btn_content:
    st.subheader(f"✨ Top 5 {st.session_state.content_type} for: *{st.session_state.content_keyword}*")
    generated_text = generate_tips(st.session_state.content_type, st.session_state.content_keyword)
    if generated_text:
        st.markdown(generated_text)
        st.success("Use these points as script ideas for your next TikTok/Reel!")
    else:
        st.error("Could not retrieve tips. Check your Groq key or try again.")
    st.markdown("---")
    st.session_state.show_content = False

# VIDEO AD GENERATION
if btn_ad:
    if not u_file:
        st.error("Please upload a product image to start!")
    else:
        status = st.empty()
        status.text("Initializing AI & Design Engine...")
        # 1. Background removal & enhancement
        status.text("🚿 Cleaning & Enhancing Product Image...")
        raw_img = Image.open(u_file).convert("RGBA")
        pro_img = process_image_pro(raw_img)
        st.image(pro_img, caption="AI Processed Product", width=220)

        # 2. Groq AI for Hook & Layout
        status.text("🚀 Groq AI: Crafting Ad Copy & Layout...")
        start_time = time.time()
        caption, layout = get_data_groq(pro_img, u_model)
        end_time = time.time()
        status.text(f"✅ Groq AI Response Time: {round(end_time-start_time, 2)}s — Hook: '{caption}'")

        # 3. Render frames
        status.text("🎨 Animating Design & Product...")
        texts = {"caption": caption, "price": u_price, "contact": u_contact}
        frames = []
        total_frames = FPS * DURATION
        progress_bar = st.progress(0)

        for i in range(int(total_frames)):
            frames.append(create_frame(i / FPS, pro_img, layout, texts, u_style))
            progress_bar.progress(int(((i + 1) / total_frames) * 100))

        # 4. Audio mixing
        status.text("🎵 Mixing Audio Track...")
        clip = ImageSequenceClip(frames, fps=FPS)
        fclip = clip  # default fallback (silent)
        audio_temp = None
        try:
            r_aud = requests.get(MUSIC_TRACKS[u_music], timeout=15)
            r_aud.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tf:
                tf.write(r_aud.content)
                audio_temp = tf.name
            aclip_full = AudioFileClip(audio_temp)
            aclip = aclip_full.subclip(0, min(DURATION, aclip_full.duration))
            # MoviePy provides audio_fadeout via audio_fadeout, but to be robust we'll use set_end if needed
            try:
                aclip = aclip.audio_fadeout(1)
            except Exception:
                pass
            fclip = clip.set_audio(aclip)
        except Exception as e:
            st.warning(f"Audio failed, rendering silent video. Error: {e}")

        # 5. Finalize Video
        status.text("💾 Rendering video (this may take a moment)...")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as vf:
            temp_video_path = vf.name
        try:
            # write_videofile prints to console; logger=None reduces noise
            fclip.write_videofile(temp_video_path, codec="libx264", audio_codec="aac", logger=None)
            status.text("✨ Ad Video Ready!")
            st.video(temp_video_path)
            with open(temp_video_path, "rb") as f:
                st.download_button("Download Ad", f, "ad_dynamic_brand.mp4")
        finally:
            # cleanup temp files
            try:
                if os.path.exists(temp_video_path):
                    os.unlink(temp_video_path)
            except Exception:
                pass
            if audio_temp and os.path.exists(audio_temp):
                try:
                    os.unlink(audio_temp)
                except Exception:
                    pass

# GROQ KEY TEST
def test_groq_connection():
    st.subheader("🔑 Groq Key Test Results")
    test_payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": "Say hello in one word."}],
        "max_tokens": 5
    }
    try:
        r = requests.post(GROQ_URL, json=test_payload, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        choices = data.get("choices") or []
        response = ""
        if choices:
            response = choices[0].get("message", {}).get("content", "").strip()
        if "hello" in response.lower() or response:
            st.success("✅ Groq Key appears valid and connection is good.")
        else:
            st.warning(f"⚠️ Key responded but in unexpected format: {response}")
    except requests.exceptions.HTTPError as e:
        code = None
        try:
            code = e.response.status_code
        except Exception:
            pass
        if code == 401:
            st.error("❌ Authentication Failed (401). Your Groq Key is likely incorrect or expired.")
        elif code == 429:
            st.error("❌ Rate Limit Exceeded (429). Check your quota.")
        else:
            st.error(f"❌ HTTP Error. Details: {e}")
    except Exception as e:
        st.error(f"❌ Connection Failed. Error: {e}")

if btn_test:
    test_groq_connection()
