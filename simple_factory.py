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

# --- AUTH & API ENDPOINTS ---

# 1. Groq (Used for Video Ad Generation & Vision)
if "groq_key" not in st.secrets:
    st.error("🚨 Missing Secret: Add `groq_key` to your .streamlit/secrets.toml")
    st.stop()
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_HEADERS = {
    "Authorization": f"Bearer {st.secrets['groq_key']}",
    "Content-Type": "application/json"
}

# 2. Mistral AI (Used for Content Tip Generation)
if "mistral_key" not in st.secrets:
    st.error("🚨 Missing Secret: Add `mistral_key` to your .streamlit/secrets.toml")
    st.stop()
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_HEADERS = {
    "Authorization": f"Bearer {st.secrets['mistral_key']}",
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

# --- API HELPER FUNCTIONS ---

def ask_api(url, headers, payload):
    """Sends payload to a specified API endpoint (Mistral or Groq)."""
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else "N/A"
        reason = e.response.reason if e.response is not None else "Unknown Error"
        print(f"API HTTP Error ({url}): {status_code} {reason}")
        return None
    except Exception as e:
        print(f"API General Error ({url}): {e}")
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
    
    # 2. Vision Task (Llama 3.2 Vision Preview) for caption (Requires Groq)
    p_hook = {
        "model": "llama-3.2-11b-vision-preview",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": f"Write a 4-word catchy luxury ad hook for this furniture model '{model_name}'."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}} 
        ]}],
        "temperature": 0.7,
        "max_tokens": 30
    }
    
    # 3. Logic Task (Llama 3 70B) for layout (Requires Groq)
    p_layout = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "You are a JSON layout engine for 720x1280 video. Output JSON only."},
            {"role": "user", "content": f"Create a JSON list of objects for layout. Each object must have 'role', 'x', 'y', 'w', 'h'. Roles needed: logo, product, price, contact, caption. Prioritize the product in the center. Product: {model_name}."}
        ],
        "response_format": {"type": "json_object"}
    }

    caption = ask_api(GROQ_URL, GROQ_HEADERS, p_hook)
    caption = caption.replace('"', '') if caption else "Elevate Your Space" 
    
    layout_raw = ask_api(GROQ_URL, GROQ_HEADERS, p_layout)
    
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
# === CONTENT GENERATION LOGIC (Uses Mistral Direct API) ===

def generate_tips(content_type, keyword="interior design"):
    """Generates a list of content ideas (tips) using the Mistral API."""
    
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
        # Using a powerful native Mistral model
        "model": "mistral-large-latest",  
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 1024
    }
    
    with st.spinner(f"🧠 Mistral AI is generating {content_type} ideas..."):
        # CALLS THE MISTRAL API DIRECTLY
        return ask_api(MISTRAL_URL, MISTRAL_HEADERS, payload)

# =========================================================================


# --- RENDERING UTILITIES (omitted for brevity, assume they are the same as before) ---
# ... (draw_wrapped_text, create_frame, etc.) ...
# [NOTE: You will need to keep all your rendering code in the final script]


# --- RENDERING UTILITIES (INCLUDED MINIMUM FOR COMPLETENESS) ---

def draw_wrapped_text(draw, text, box, font, color, align="center"):
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
    """Draws a single animated frame of the video. (Placeholder logic)"""
    T = TEMPLATES[tpl_name]
    canvas = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(canvas)
    
    # 1. Background Gradient (simplified)
    c1 = tuple(int(T["bg_grad"][0][i:i+2], 16) for i in (1, 3, 5))
    c2 = tuple(int(T["bg_grad"][1][i:i+2], 16) for i in (1, 3, 5))
    for y in range(HEIGHT):
        r = int(c1[0] + (c2[0]-c1[0]) * y/HEIGHT)
        g = int(c1[1] + (c2[1]-c1[1]) * y/HEIGHT)
        b = int(c1[2] + (c2[2]-c1[2]) * y/HEIGHT)
        draw.line([(0,y), (WIDTH,y)], fill=(r,g,b))
    
    # 2. Product (simplified drawing)
    for b in boxes:
        if b["role"] == "product":
             scale = ease_out_elastic(min(t, 1.0))
             if scale > 0.01:
                pw, ph = int(b['w']*scale), int(b['h']*scale)
                p_rs = img.resize((pw, ph), Image.LANCZOS)
                cx = b['x'] + (b['w']-pw)//2
                cy = b['y'] + (b['h']-ph)//2
                canvas.paste(p_rs, (int(cx), int(cy)), p_rs)
        elif b["role"] == "caption" and t > 1.0:
            f = get_font(50)
            draw_wrapped_text(draw, texts["caption"], b, f, T["accent"])

    return np.array(canvas)

# --- KEY TEST FUNCTION (for Mistral) ---
def test_mistral_connection():
    """Tests the Mistral API key validity with a simple request."""
    st.subheader("🔑 Mistral Key Test Results")
    
    test_payload = {
        "model": "mistral-tiny", 
        "messages": [{"role": "user", "content": "Say hello in one word."}],
        "max_tokens": 5
    }
    
    try:
        r = requests.post(MISTRAL_URL, json=test_payload, headers=MISTRAL_HEADERS, timeout=5)
        r.raise_for_status()
        
        response = r.json()["choices"][0]["message"]["content"].strip()
        
        if "hello" in response.lower() or "hi" in response.lower():
            st.success("✅ **Mistral Key is Valid and Connection is Good!**")
        else:
            st.warning(f"⚠️ **Key is valid, but received unexpected response:** *{response}*")
            
    except requests.exceptions.HTTPError as e:
        if r.response is not None and r.response.status_code == 401:
            st.error("❌ **Authentication Failed (401).** Your Mistral Key is likely **incorrect or expired.**")
        else:
            st.error(f"❌ **HTTP Error.** Check Mistral usage or try again. Details: {e}")
    except Exception as e:
        st.error(f"❌ **Connection Failed.** Check network connection. Error: {e}")


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
    btn_ad = st.button("🚀 Generate Ad Video (GROQ)", type="primary")

    # NEW MISTRAL TEST BUTTON
    btn_test_mistral = st.button("🔑 Verify Mistral Key") 

    st.markdown("---")
    
    # === CONTENT GENERATOR SECTION ===
    st.header("💡 Content Idea Generator (Mistral)")
    u_content_type = st.radio(
        "Select Content Type:",
        ["DIY Tips", "Furniture Tips", "Interior Design Tips", "Maintenance Tips"] 
    )
    u_content_keyword = st.text_input("Content Focus", value="Mid-Century Console")
    btn_content = st.button("🧠 Generate Tips (Mistral)")
    
st.title("AdGen EVO: Dynamic Brand Ads & Content")

# --- EXECUTION LOGIC ---

# 1. CONTENT GENERATION LOGIC (MISTRAL)
if btn_content:
    st.session_state.show_content = True
    st.session_state.content_type = u_content_type
    st.session_state.content_keyword = u_content_keyword

if st.session_state.show_content and btn_content:
    st.subheader(f"✨ Top 5 {st.session_state.content_type} on: *{st.session_state.content_keyword}*")
    
    # MISTRAL CALL
    generated_text = generate_tips(st.session_state.content_type, st.session_state.content_keyword)
    
    if generated_text:
        st.markdown(generated_text)
        st.success("Use these points as script ideas for your next TikTok/Reel!")
    else:
        st.error("Could not retrieve tips from Mistral. Check your Mistral key or quota.")
    
    st.markdown("---")
    st.session_state.show_content = False 

# 2. VIDEO AD GENERATION LOGIC (GROQ)
if btn_ad and u_file:
    st.session_state.show_content = False
    status = st.status("Initializing AI & Design Engine...", expanded=True)
    
    status.write("🚿 Cleaning & Enhancing Product Image...")
    raw_img = Image.open(u_file).convert("RGBA")
    pro_img = process_image_pro(raw_img)
    st.image(pro_img, caption="AI Processed Product", width=200)
    
    status.write("🚀 Groq AI: Crafting Ad Copy & Layout...")
    
    start_time = time.time()
    caption, layout = get_data_groq(pro_img, u_model)
    end_time = time.time()
    
    status.write(f"✅ Groq AI Response Time: {round(end_time-start_time, 2)}s")
    
    # ... (Rest of the video generation logic remains the same)

    # 3. Render Video Frames
    status.write("🎨 Animating Design Elements & Product...")
    texts = {"caption": caption, "price": u_price, "contact": u_contact}
    frames = []
    bar = status.progress(0)
    
    for i in range(FPS*DURATION):
        frames.append(create_frame(i/FPS, pro_img, layout, texts, u_style))
        bar.progress((i+1)/(FPS*DURATION))
        
    # 4. Audio Mixing (simplified)
    clip = ImageSequenceClip(frames, fps=FPS)
    fclip = clip # Assume silent if audio fails
    
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

# 3. MISTRAL KEY TEST LOGIC 
if btn_test_mistral:
    st.session_state.show_content = False 
    test_mistral_connection()
