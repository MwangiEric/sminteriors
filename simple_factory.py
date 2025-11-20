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
    """Removes Background via Rembg and applies sharpness/contrast enhancements."""
    with st.spinner("🚿 Removing background & enhancing..."):
        img_byte_arr = io.BytesIO()
        input_image.save(img_byte_arr, format='PNG') 
        input_image_bytes = img_byte_arr.getvalue()
        
        output_bytes = remove(input_image_bytes)
        clean_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")

    enhancer = ImageEnhance.Contrast(clean_img)
    clean_img = enhancer.enhance(1.15)
    
    enhancer = ImageEnhance.Sharpness(clean_img)
    clean_img = enhancer.enhance(1.5)
    
    return clean_img

# --- FONTS (Stable Local) ---
def get_font(size):
    """Loads a common bold font from system paths for stability."""
    possible_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "arial.ttf"
    ]
    for path in possible_fonts:
        try:
            return ImageFont.truetype(path, size)
        except: pass
    return ImageFont.load_default()

# --- MATH & ANIMATION ---
def ease_out_elastic(t):
    """Elastic easing function for animated entry."""
    c4 = (2 * math.pi) / 3
    return math.pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1 if t > 0 and t < 1 else (0 if t<=0 else 1)

def linear_fade(t, start, duration):
    """Linear fade in/out function."""
    if t < start: return 0.0
    if t > start + duration: return 1.0
    return (t - start) / duration

# --- TEMPLATES (Dynamic Brand Color Palettes) ---
BRAND_PRIMARY = "#4C3B30" # Deep Brown
BRAND_ACCENT = "#D2A544"  # Gold
BRAND_TEXT_LIGHT = "#FFFFFF" # White
BRAND_TEXT_DARK = "#000000"  # Black

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

# --- GROQ AI LOGIC ---
def ask_groq(payload):
    """Sends payload to Groq API and handles response/errors."""
    try:
        r = requests.post(GROQ_URL, json=payload, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        if hasattr(e, 'response') and e.response is not None:
             print(f"Groq HTTP Error: {e.response.status_code} {e.response.reason} for URL: {e.response.url}")
        else:
            print(f"Groq Error: {e}")
        return None

def get_data_groq(img, model_name):
    """Gets caption (Vision) and layout (Logic) from Groq."""
    
    # 1. Base64 Encoding for Vision (Convert RGBA to RGB for JPEG compatibility)
    buf = io.BytesIO()
    
    if img.mode == 'RGBA':
        rgb_img = Image.new("RGB", img.size, (255, 255, 255))
        rgb_img.paste(img, (0, 0), img)
    else:
        rgb_img = img.convert("RGB")
        
    rgb_img.save(buf, format="JPEG", quality=90) 
    b64 = base64.b64encode(buf.getvalue()).decode()
    
    # 2. Vision Task (Llama 3.2 Vision Preview) for caption
    p_hook = {
        "model": "llama-3.2-11b-vision-preview",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": f"Write a 4-word catchy luxury ad hook for this furniture model '{model_name}'."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}} 
        ]}],
        "temperature": 0.7,
        "max_tokens": 30
    }
    
    # 3. Logic Task (Llama 3 70B) for layout (Keep Llama 3 for JSON structure)
    p_layout = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "You are a JSON layout engine for 720x1280 video. Output JSON only."},
            {"role": "user", "content": f"Create a JSON list of objects for layout. Each object must have 'role', 'x', 'y', 'w', 'h'. Roles needed: logo, product, price, contact, caption. Prioritize the product in the center. Product: {model_name}."}
        ],
        "response_format": {"type": "json_object"}
    }

    caption = ask_groq(p_hook)
    caption = caption.replace('"', '') if caption else "Elevate Your Space" 
    
    layout_raw = ask_groq(p_layout)
    
    # Fallback Layout 
    default_layout = [
        {"role": "logo", "x": 50, "y": 50, "w": 200, "h": 100},
        {"role": "product", "x": 60, "y": 250, "w": 600, "h": 600},
        {"role": "caption", "x": 60, "y": 900, "w": 600, "h": 100},
        {"role": "price", "x": 160, "y": 1050, "w": 400, "h": 120},
        {"role": "contact", "x": 60, "y": 1200, "w": 600, "h": 60}
    ]
    
    try:
        j = json.loads(layout_raw)
        final_layout = j.get("layout", j) if isinstance(j, dict) else j
        
        if isinstance(final_layout, list) and all("role" in item for item in final_layout):
            return caption, final_layout
        else:
            return caption, default_layout
    except:
        return caption, default_layout

# =========================================================================
# === UPDATED CONTENT GENERATION LOGIC (Now using Mistral) ===

def generate_tips(content_type, keyword="interior design"):
    """Generates a list of content ideas (tips) using Mistral 8x7b."""
    
    system_prompt = f"""You are a content creation expert for a luxury home furnishing brand named 'SM Interiors'. 
    Your tone must be authoritative, engaging, and suitable for short-form video content (TikTok/Reels).
    Respond using only markdown bullet points. Do not include any introductory or concluding sentences."""
    
    if content_type == "DIY Tips":
        user_prompt = f"Generate 5 quick, actionable DIY home decor tips or furniture restoration ideas that use common materials, focusing on high-impact visuals suitable for a video tutorial. The focus keyword is '{keyword}'."
    elif content_type == "Furniture Tips":
        user_prompt = f"Generate 5 high-value tips on how to properly care for, arrange, or choose high-end furniture (like the '{keyword}' product). Focus on luxury, longevity, and placement."
    elif content_type == "Interior Design Tips":
        user_prompt = f"Generate 5 creative and trending interior design tips or small-space hacks related to the theme of '{keyword}'. Focus on quick visual improvements and style."
    elif content_type == "Maintenance Tips":
        user_prompt = f"Generate 5 essential tips on cleaning, polishing, and long-term maintenance for luxury furniture materials like solid wood, brass, and fine upholstery, focused on the product '{keyword}'. The tips must be specific and actionable for a short video."
    else:
        return "*Select a content type to generate ideas.*"

    payload = {
        "model": "mixtral-8x7b-instruct",  # <-- MISTRAL MODEL USED HERE
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 1024
    }
    
    with st.spinner(f"🧠 Mistral is generating {content_type} ideas..."):
        return ask_groq(payload)

# === END UPDATED CONTENT GENERATION LOGIC ===
# =========================================================================


# --- RENDERING UTILITIES ---
def draw_wrapped_text(draw, text, box, font, color, align="center"):
    """Handles multi-line text wrapping within a bounding box."""
    lines = []
    words = text.split()
    line = ""
    for w in words:
        test_line = line + " " + w if line else w
        bbox = draw.textbbox((0, 0), test_line, font=font)
        text_width = bbox[2] - bbox[0]
        
        if text_width > box['w'] and line: 
            lines.append(line)
            line = w
        else:
            line = test_line
    lines.append(line)
    
    current_y = box['y'] 
    
    for l in lines:
        bbox = draw.textbbox((0,0), l, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        if align == "center":
            lx = box['x'] + (box['w'] - text_width) // 2
        elif align == "left":
            lx = box['x']
        
        draw.text((lx, current_y), l, font=font, fill=color)
        current_y += text_height + 5 

def create_frame(t, img, boxes, texts, tpl_name):
    """Draws a single animated frame of the video."""
    T = TEMPLATES[tpl_name]
    canvas = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(canvas)
    
    # 1. Background Gradient
    c1 = tuple(int(T["bg_grad"][0][i:i+2], 16) for i in (1, 3, 5))
    c2 = tuple(int(T["bg_grad"][1][i:i+2], 16) for i in (1, 3, 5))
    for y in range(HEIGHT):
        r = int(c1[0] + (c2[0]-c1[0]) * y/HEIGHT)
        g = int(c1[1] + (c2[1]-c1[1]) * y/HEIGHT)
        b = int(c1[2] + (c2[2]-c1[2]) * y/HEIGHT)
        draw.line([(0,y), (WIDTH,y)], fill=(r,g,b))

    # --- DYNAMIC TEMPLATE GRAPHICS ---
    graphic_color_rgb = tuple(int(T["graphic_color"][i:i+2], 16) for i in (1, 3, 5)) if "graphic_color" in T else None

    if T["graphic_type"] == "diagonal" and graphic_color_rgb:
        diag_alpha = int(255 * linear_fade(t, 0.5, 1.0))
        for i in range(-WIDTH, WIDTH + HEIGHT, 50): 
            draw.line([(i, 0), (i + HEIGHT, HEIGHT)], fill=(graphic_color_rgb[0], graphic_color_rgb[1], graphic_color_rgb[2], diag_alpha), width=10)
        
        if t > 0.8:
            solid_alpha = int(255 * linear_fade(t, 1.0, 0.5))
            draw.polygon([
                (0, 100), (WIDTH, 0), (WIDTH, 200), (0, 300)
            ], fill=(graphic_color_rgb[0], graphic_color_rgb[1], graphic_color_rgb[2], solid_alpha))


    elif T["graphic_type"] == "circular" and graphic_color_rgb:
        circle_alpha = int(255 * linear_fade(t, 0.8, 0.7))
        
        circle_size = int(WIDTH * 1.5 * ease_out_elastic(max(0, t - 0.5)))
        cx, cy = int(WIDTH * 0.8), int(HEIGHT * 0.7)
        draw.ellipse([cx - circle_size//2, cy - circle_size//2, cx + circle_size//2, cy + circle_size//2], 
                     fill=(graphic_color_rgb[0], graphic_color_rgb[1], graphic_color_rgb[2], int(circle_alpha * 0.6)))
        
        circle_size_small = int(WIDTH * 0.7 * ease_out_elastic(max(0, t - 1.0)))
        cx_s, cy_s = int(WIDTH * 0.2), int(HEIGHT * 0.3)
        
        draw.ellipse([cx_s - circle_size_small//2, cy_s - circle_size_small//2, 
                      cx_s + circle_size_small//2, cy_s + circle_size_small//2], 
                     fill=(graphic_color_rgb[0], graphic_color_rgb[1], graphic_color_rgb[2], int(circle_alpha * 0.4)))


    elif T["graphic_type"] == "split" and graphic_color_rgb:
        split_height = int(HEIGHT * 0.3 * ease_out_elastic(max(0, t - 1.0)))
        draw.rectangle([0, HEIGHT - split_height, WIDTH, HEIGHT], fill=T["graphic_color"])
        
        dot_fade = int(255 * linear_fade(t, 1.2, 0.5))
        dot_color = (graphic_color_rgb[0], graphic_color_rgb[1], graphic_color_rgb[2], dot_fade)
        for i in range(5):
            draw.ellipse([WIDTH - 60, 100 + i*40, WIDTH - 40, 120 + i*40], fill=dot_color)

    # 4. Elements
    for b in boxes:
        role = b["role"]
        
        if role == "product":
            float_y = math.sin(t * 2) * 12
            scale = ease_out_elastic(min(t, 1.0))
            
            if scale > 0.01:
                pw, ph = int(b['w']*scale), int(b['h']*scale)
                p_rs = img.resize((pw, ph), Image.LANCZOS)
                
                shadow = p_rs.copy()
                shadow_data = [(0,0,0, int(a*0.3)) for r,g,b,a in p_rs.getdata()]
                shadow.putdata(shadow_data)
                shadow = shadow.filter(ImageFilter.GaussianBlur(15))
                
                cx = b['x'] + (b['w']-pw)//2
                cy = b['y'] + (b['h']-ph)//2 + float_y
                
                canvas.paste(shadow, (int(cx), int(cy+30)), shadow)
                canvas.paste(p_rs, (int(cx), int(cy)), p_rs)

        elif role == "price":
            anim = linear_fade(t, 1.5, 0.5)
            if anim > 0:
                off_y = (1-ease_out_elastic(anim))*100
                draw.rounded_rectangle([b['x'], b['y']+off_y, b['x']+b['w'], b['y']+b['h']+off_y], radius=25, fill=T["price_bg"])
                f = get_font(65)
                
                draw_wrapped_text(draw, texts["price"], 
                                  {'x': b['x'], 'y': b['y']+off_y, 'w': b['w'], 'h': b['h']}, 
                                  f, T["price_text"])
                

        elif role == "caption":
            if t > 1.0:
                f = get_font(50)
                draw_wrapped_text(draw, texts["caption"], b, f, T["accent"])

        elif role == "contact":
            if t > 2.5:
                f = get_font(30)
                draw_wrapped_text(draw, texts["contact"], b, f, T["text"])
                
        elif role == "logo":
             try:
                logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
                logo = logo.resize((b['w'], b['h']), Image.LANCZOS)
                logo_shadow = Image.new('RGBA', logo.size, (0,0,0,0))
                logo_shadow_draw = ImageDraw.Draw(logo_shadow)
                logo_shadow_draw.ellipse([5,5,logo.width-5,logo.height-5], fill=(0,0,0,100))
                logo_shadow = logo_shadow.filter(ImageFilter.GaussianBlur(10))

                canvas.paste(logo_shadow, (b['x']+5, b['y']+5), logo_shadow)
                canvas.paste(logo, (b['x'], b['y']), logo)
             except: pass

    # 5. Vignette (Cinematic finish)
    vignette = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
    v_draw = ImageDraw.Draw(vignette)
    for y in range(int(HEIGHT*0.7), HEIGHT):
        alpha = int(180 * ((y - HEIGHT*0.7)/(HEIGHT*0.3)))
        v_draw.line([(0,y), (WIDTH,y)], fill=(0,0,0,alpha))
    canvas.paste(vignette, (0,0), vignette)

    return np.array(canvas)

# --- MAIN UI ---

# Initialize session state for content display management
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
    btn_ad = st.button("🚀 Generate Ad Video", type="primary")

    # TEST BUTTON 
    btn_test = st.button("🔑 Verify Groq Key") 

    st.markdown("---")
    
    # === CONTENT GENERATOR SECTION ===
    st.header("💡 Content Idea Generator")
    u_content_type = st.radio(
        "Select Content Type:",
        ["DIY Tips", "Furniture Tips", "Interior Design Tips", "Maintenance Tips"] 
    )
    u_content_keyword = st.text_input("Content Focus (e.g., 'Small living room')", value="Mid-Century Console")
    btn_content = st.button("🧠 Generate Tips")
    
st.title("AdGen EVO: Dynamic Brand Ads & Content")

# --- EXECUTION LOGIC ---

# 1. CONTENT GENERATION LOGIC
if btn_content:
    st.session_state.show_content = True
    st.session_state.content_type = u_content_type
    st.session_state.content_keyword = u_content_keyword

if st.session_state.show_content and btn_content:
    st.subheader(f"✨ Top 5 {st.session_state.content_type} on: *{st.session_state.content_keyword}*")
    
    generated_text = generate_tips(st.session_state.content_type, st.session_state.content_keyword)
    
    if generated_text:
        st.markdown(generated_text)
        st.success("Use these points as script ideas for your next TikTok/Reel!")
    else:
        st.error("Could not retrieve tips. Check your Groq key or try again.")
    
    st.markdown("---")
    st.session_state.show_content = False 

# 2. VIDEO AD GENERATION LOGIC
if btn_ad and u_file:
    st.session_state.show_content = False
    status = st.status("Initializing AI & Design Engine...", expanded=True)
    
    # 1. Background Removal & Enhancement
    status.write("🚿 Cleaning & Enhancing Product Image...")
    raw_img = Image.open(u_file).convert("RGBA")
    pro_img = process_image_pro(raw_img)
    st.image(pro_img, caption="AI Processed Product", width=200)
    
    # 2. Groq AI for Hook & Layout
    status.write("🚀 Groq AI: Crafting Ad Copy & Layout...")
    
    start_time = time.time()
    caption, layout = get_data_groq(pro_img, u_model)
    end_time = time.time()
    
    status.write(f"✅ Groq AI Response Time: {round(end_time-start_time, 2)}s")
    status.write(f"Hook: '{caption}'")
    
    # 3. Render Video Frames
    status.write("🎨 Animating Design Elements & Product...")
    texts = {"caption": caption, "price": u_price, "contact": u_contact}
    frames = []
    bar = status.progress(0)
    
    for i in range(FPS*DURATION):
        frames.append(create_frame(i/FPS, pro_img, layout, texts, u_style))
        bar.progress((i+1)/(FPS*DURATION))
        
    # 4. Audio Mixing
    status.write("🎵 Mixing Audio Track...")
    clip = ImageSequenceClip(frames, fps=FPS)
    try:
        r_aud = requests.get(MUSIC_TRACKS[u_music])
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tf:
            tf.write(r_aud.content)
            tf_name = tf.name
        aclip = AudioFileClip(tf_name).subclip(0, DURATION).audio_fadeout(1)
        fclip = clip.set_audio(aclip)
        os.unlink(tf_name)
    except Exception as e: 
        st.warning(f"Audio failed, rendering silent video. Error: {e}")
        fclip = clip

    # 5. Finalize Video
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as vf:
        fclip.write_videofile(vf.name, codec="libx264", audio_codec="aac", logger=None)
        final_path = vf.name
    
    status.update(label="✨ Ad Video Ready!", state="complete", expanded=False)
    st.video(final_path)
    with open(final_path, "rb") as f:
        st.download_button("Download Ad", f, "ad_dynamic_brand.mp4")
        os.unlink(final_path)

elif btn_ad:
    st.error("Please upload a product image to start!")

# 3. GROQ KEY TEST LOGIC 
def test_groq_connection():
    """Tests the Groq API key validity with a simple request."""
    st.subheader("🔑 Groq Key Test Results")
    
    test_payload = {
        "model": "llama3-8b-8192", 
        "messages": [{"role": "user", "content": "Say hello in one word."}],
        "max_tokens": 5
    }
    
    try:
        r = requests.post(GROQ_URL, json=test_payload, headers=HEADERS, timeout=5)
        r.raise_for_status()
        
        response = r.json()["choices"][0]["message"]["content"].strip()
        
        if "hello" in response.lower():
            st.success("✅ **Groq Key is Valid and Connection is Good!**")
        else:
            st.warning(f"⚠️ **Key is valid, but received unexpected response:** *{response}*")
            
    except requests.exceptions.HTTPError as e:
        if r.status_code == 401:
            st.error("❌ **Authentication Failed (401).** Your Groq Key is likely **incorrect or expired.**")
        elif r.status_code == 429:
            st.error("❌ **Rate Limit Exceeded (429).** Try again later or check your quota.")
        else:
            st.error(f"❌ **HTTP Error {r.status_code}.** Check Groq usage or try again. Details: {e}")
    except Exception as e:
        st.error(f"❌ **Connection Failed.** Check network connection. Error: {e}")

if btn_test:
    st.session_state.show_content = False 
    test_groq_connection()
