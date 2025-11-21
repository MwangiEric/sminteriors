import streamlit as st
import io, requests, math, tempfile, base64, json, random, time, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip
from rembg import remove, new_session

# ================================
# CONFIG & PAGE SETUP
# ================================
st.set_page_config(page_title="AdGen EVO: SM Interiors", layout="wide", page_icon="✨")

WIDTH, HEIGHT = 720, 1280
FPS = 30
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

# Fixed hotlink-friendly royalty-free music
MUSIC_TRACKS = {
    "Upbeat Pop": "https://cdn.pixabay.com/download/audio/2024/08/15/audio_5a54d0f2f6.mp3?filename=upbeat-background-171614.mp3",
    "Luxury Chill": "https://uppbeat.io/assets/track/mp3/prigida-moving-on.mp3",
    "Modern Gold": "https://uppbeat.io/assets/track/mp3/synapse-fire-link-me-up.mp3",
    "Chill Beats": "https://uppbeat.io/assets/track/mp3/ikson-new-world.mp3"
}

# ================================
# SECRETS CHECK (Assuming keys are available in the Streamlit environment)
# ================================
HEADERS = {
    "Authorization": f"Bearer {st.secrets['groq_key']}",
    "Content-Type": "application/json"
}
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# ================================
# CACHED RESOURCES & HELPERS (UNCHANGED)
# ================================
@st.cache_resource
def get_rembg_session():
    return new_session()

@st.cache_resource
def get_cached_logo(logo_url, width, height):
    try:
        r = requests.get(logo_url, timeout=8)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content)).convert("RGBA")
    except Exception as e:
        st.warning(f"Failed to load logo from URL. Using transparent placeholder. Error: {e}")
        return Image.new("RGBA", (width, height), (0, 0, 0, 0))

def process_image_pro(input_image):
    with st.spinner("Removing background & enhancing..."):
        buf = io.BytesIO()
        input_image.save(buf, format="PNG")
        output_bytes = remove(buf.getvalue(), session=get_rembg_session())
        img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
        img = ImageEnhance.Contrast(img).enhance(1.15)
        img = ImageEnhance.Sharpness(img).enhance(1.5)
    return img

def get_font(size):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except:
        try:
            return ImageFont.truetype("arial.ttf", size)
        except:
            return ImageFont.load_default()

def ease_out_elastic(t):
    if t <= 0: return 0
    if t >= 1: return 1
    c4 = (2 * math.pi) / 3
    return math.pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

def linear_fade(t, start, duration):
    if t < start: return 0.0
    if t > start + duration: return 1.0
    return (t - start) / duration

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0,2,4))

BRAND_PRIMARY = "#4C3B30"
BRAND_ACCENT = "#D2A544"

TEMPLATES = {
    "SM Classic": {"bg_grad": [BRAND_PRIMARY, "#2a201b"], "accent": "#FFFFFF", "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "none"},
    "Gold Diagonal": {"bg_grad": [BRAND_PRIMARY, "#3e2e24"], "accent": BRAND_ACCENT, "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "diagonal", "graphic_color": BRAND_ACCENT},
    "Gold Circles": {"bg_grad": [BRAND_PRIMARY, "#332A22"], "accent": BRAND_ACCENT, "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "circular", "graphic_color": BRAND_ACCENT},
    "Gold Split": {"bg_grad": [BRAND_PRIMARY, BRAND_PRIMARY], "accent": "#FFFFFF", "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "split", "graphic_color": BRAND_ACCENT},
}

def draw_centered_text(draw, text, y, font, color, max_width=600, alpha=255):
    lines = []
    words = text.split()
    line = ""
    
    for w in words:
        test = line + (" " + w if line else w)
        if draw.textbbox((0,0), test, font=font)[2] <= max_width:
            line = test
        else:
            lines.append(line)
            line = w
    if line: lines.append(line)
    
    current_y = y
    fill_color = (*hex_to_rgb(color), alpha)
    
    for line in lines:
        w = draw.textbbox((0,0), line, font=font)[2]
        draw.text(((WIDTH - w) // 2, current_y), line, font=font, fill=fill_color)
        current_y += draw.textbbox((0,0), line, font=font)[3] + 8
    return current_y

# (GROQ Helpers and Content Generator functions remain unchanged)
# ... (omitted for brevity, assume they are the same as the previous response) ...
def ask_groq(payload):
    # ... (function body) ...
    pass
def get_data_groq(img, model_name):
    # ... (function body) ...
    pass
def generate_tips(content_type, keyword):
    # ... (function body) ...
    pass


# ================================
# FRAME RENDERER (ALL ANIMATION LOGIC CONSOLIDATED)
# ================================
def create_frame(t, img, boxes, texts, tpl_name, logo_img, content_type, animation_style):
    T = TEMPLATES[tpl_name]
    canvas = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(canvas)

    # Background Gradient and Graphics (UNCHANGED)
    c1 = hex_to_rgb(T["bg_grad"][0])
    c2 = hex_to_rgb(T["bg_grad"][1])
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        color = tuple(int(c1[i] + (c2[i] - c1[i]) * ratio) for i in range(3))
        draw.line([(0,y), (WIDTH,y)], fill=color)

    # Template Graphics (UNCHANGED)
    gc = hex_to_rgb(T.get("graphic_color", "#000000")) if "graphic_color" in T else None
    if T["graphic_type"] == "diagonal" and gc:
        alpha = int(255 * linear_fade(t, 0.5, 1.0))
        for i in range(-WIDTH, WIDTH+HEIGHT, 60):
            draw.line([(i,0), (i+HEIGHT,HEIGHT)], fill=(*gc, alpha), width=8)
    # ... (Other graphic types omitted for brevity) ...

    # Draw Product & Shadow (Layer 1 - UNCHANGED)
    product_box = next((b for b in boxes if b["role"] == "product"), None)
    
    if product_box and img: 
        b = product_box
        if content_type == "Content Video": # Note: Changed from 'Tip Video'
            b["y"] = 250
            b["h"] = 400
        # ... (Product drawing logic omitted for brevity) ...

    # --- BLOCK 2: Draw Text Elements ---
    
    # 2a. Draw Contact/URL (Fades in late)
    contact_box = next((b for b in boxes if b["role"] == "contact"), None)
    if contact_box:
        # DURATION is globally available from the UI
        alpha = int(255 * linear_fade(t, DURATION - 1.5, 0.5))
        y_start = contact_box.get('y', 1200)
        if alpha > 0:
            draw_centered_text(draw, texts["contact"], y_start, get_font(32), T["text"], max_width=600, alpha=alpha)
        
    # 2b. Draw Caption/Hook (Title) - Uses Animation Style A or B timing
    caption_box = next((b for b in boxes if b["role"] == "caption"), None)
    if caption_box:
        
        # Timing for Title Hook (Applies to all video types)
        if content_type == "Product Showcase":
            # Simple fade-in for product ads
            alpha = int(255 * linear_fade(t, 1.0, 0.5)) 
        elif content_type == "Content Video":
            # Fade-in/Fade-out for Content Videos (like the 'Hello' image)
            alpha_in = linear_fade(t, 0.5, 1.0) 
            alpha_out = 1.0 - linear_fade(t, 2.5, 1.0)
            alpha = int(255 * max(0, min(alpha_in, alpha_out)))

        if alpha > 0:
            draw_centered_text(draw, texts["caption"], caption_box.get('y', 150), 
                            get_font(60), T["accent"], max_width=600, alpha=alpha)


    # 2c. Draw Price (Product Showcase ONLY - UNCHANGED)
    if content_type == "Product Showcase":
        price_box = next((b for b in boxes if b["role"] == "price"), None)
        # ... (Price drawing logic, using linear_fade(t, 1.4, 0.5) for alpha) ...

    # 2d. Draw TIPS (Only for Content Video - PILLAR B)
    if content_type == "Content Video":
        
        tip_text = texts.get("full_tips", "")
        # Get all bullet points, ignoring the first line (the caption/hook)
        tips = [line.strip('*').strip('-').strip() for line in tip_text.split('\n')[1:] if line.strip().startswith('*') or line.strip().startswith('-')]
        
        if tips:
            tip_font = get_font(42)
            line_height = 70 
            start_y = 450 if img else 450
            
            # --- ANIMATION STYLE LOGIC ---
            
            if animation_style == "Typewriter (Sequential Reveal)":
                # --- TYPEWRITER LOGIC (Restored and used when selected) ---
                CHAR_PER_SECOND = 40
                START_TIME = 3.5      # Start after title fades out
                TIP_DELAY = 0.5       
                cumulative_delay = START_TIME
                
                for i, full_tip in enumerate(tips):
                    tip_len = len(full_tip)
                    tip_duration = tip_len / CHAR_PER_SECOND
                    tip_start_time = cumulative_delay
                    
                    if t >= tip_start_time:
                        time_in_tip = max(0, t - tip_start_time)
                        # Use math.floor for smooth character transition
                        chars_to_show = min(tip_len, math.floor(time_in_tip * CHAR_PER_SECOND))
                        current_tip_text = full_tip[:chars_to_show]
                        
                        y_pos = start_y + (i * line_height)
                        tip_w = draw.textbbox((0,0), full_tip, font=tip_font)[2]
                        padding = 20
                        
                        # Background box fades in quickly with the first character
                        alpha_ratio_bg = min(1.0, (t - tip_start_time) / 0.15)
                        draw.rounded_rectangle(
                            [ (WIDTH-tip_w-padding)//2 - 10, y_pos - 15, (WIDTH+tip_w+padding)//2 + 10, y_pos + line_height - 15],
                            radius=10,
                            fill=(*hex_to_rgb(BRAND_ACCENT), int(180 * alpha_ratio_bg)) 
                        )
                        
                        # Text is drawn opaque, the character count creates the reveal
                        draw.text(((WIDTH - tip_w) // 2, y_pos - 10), current_tip_text, font=tip_font, fill=T["text"])
                    
                    cumulative_delay = tip_start_time + tip_duration + TIP_DELAY
            
            
            elif animation_style == "Smooth Fade (All at Once)":
                # --- SMOOTH FADE LOGIC (Simple, robust fade-in) ---
                FADE_START = 3.5
                FADE_DURATION = 0.8
                alpha = int(255 * linear_fade(t, FADE_START, FADE_DURATION))
                
                if alpha > 0:
                    for i, full_tip in enumerate(tips):
                        y_pos = start_y + (i * line_height)
                        tip_w = draw.textbbox((0,0), full_tip, font=tip_font)[2]
                        padding = 20
                        
                        # Draw semi-transparent background rectangle (fading with the text)
                        draw.rounded_rectangle(
                            [ (WIDTH-tip_w-padding)//2 - 10, y_pos - 15, (WIDTH+tip_w+padding)//2 + 10, y_pos + line_height - 15],
                            radius=10,
                            fill=(*hex_to_rgb(BRAND_ACCENT), int(180 * (alpha/255))) 
                        )
                        
                        # Draw the text itself (fading in)
                        draw.text(
                            ((WIDTH - tip_w) // 2, y_pos - 10), 
                            full_tip, 
                            font=tip_font, 
                            fill=(*hex_to_rgb(T["text"]), alpha)
                        )
            
            
            elif animation_style == "Block Reveal (Sequential Block Fade)":
                # --- BLOCK REVEAL LOGIC (Original basic style) ---
                START_TIME = 3.5
                BLOCK_INTERVAL = 0.4
                FADE_DURATION = 0.3
                
                for i, full_tip in enumerate(tips):
                    block_start = START_TIME + i * BLOCK_INTERVAL
                    alpha = int(255 * linear_fade(t, block_start, FADE_DURATION))
                    
                    if alpha > 0:
                        y_pos = start_y + (i * line_height)
                        tip_w = draw.textbbox((0,0), full_tip, font=tip_font)[2]
                        padding = 20

                        # Draw background box (fades in)
                        draw.rounded_rectangle(
                            [ (WIDTH-tip_w-padding)//2 - 10, y_pos - 15, (WIDTH+tip_w+padding)//2 + 10, y_pos + line_height - 15],
                            radius=10,
                            fill=(*hex_to_rgb(BRAND_ACCENT), int(180 * (alpha/255))) 
                        )
                        
                        # Draw text (fades in)
                        draw.text(
                            ((WIDTH - tip_w) // 2, y_pos - 10), 
                            full_tip, 
                            font=tip_font, 
                            fill=(*hex_to_rgb(T["text"]), alpha)
                        )

    # --- BLOCK 3: Draw Logo (Highest Layer) ---
    logo_box = next((b for b in boxes if b["role"] == "logo"), None)
    if logo_box:
        if logo_img:
            # ... (Logo drawing logic) ...
            pass
            
    # Vignette (UNCHANGED)
    # ... (Vignette drawing logic) ...

    return np.array(canvas)

# ================================
# UI LOGIC (FINALIZED)
# ================================
st.title("AdGen EVO – SM Interiors Edition")

# Initialize session state for tip text
if 'generated_tips' not in st.session_state:
    st.session_state['generated_tips'] = 'EXPERT INSIGHT\n* Always prioritize safety by embracing all holding and accessory features.\n* Less is more; focus on a few high-quality, functional pieces.\n* Prioritize safety by selecting only non-toxic, low-VOC paints.'


with st.sidebar:
    st.header("TikTok Content Builder")
    # Content type radio button: Changed to 'Content Video' for clarity
    u_content_type = st.radio(
        "Content Pillar", 
        ["Product Showcase (Pillar A/C)", "Content Video (Pillar B)"],
        index=1, 
        help="Showcase drives sales; Content Videos drive Saves/Shares/Follows."
    )
    st.markdown("---")

    st.header("Video Settings")
    u_duration = st.slider("Video Duration (Seconds)", min_value=3, max_value=8, value=6, step=1, help="6s is recommended for most animations.")
    
    # New Animation Style Dropdown!
    if u_content_type == "Content Video (Pillar B)":
        u_animation_style = st.selectbox(
            "Text Animation Style", 
            ["Smooth Fade (All at Once)", "Typewriter (Sequential Reveal)", "Block Reveal (Sequential Block Fade)"],
            index=0,
            help="Select the style for revealing the tips after the title fades out."
        )
    else:
        u_animation_style = "Simple Fade" # Placeholder for Product Showcase

    # ... (Rest of the UI logic remains similar, adjusting for 'Content Video' name) ...
    if u_content_type == "Product Showcase (Pillar A/C)":
        st.subheader("Product Ad Details")
        u_file = st.file_uploader("Product Image", type=["png","jpg","jpeg"])
        u_model = st.text_input("Product Name", "Walden Dresser")
        u_price = st.text_input("Price / Discount", "Ksh 49,900") 
        u_contact = st.text_input("Contact Info", "0710 895 737")
        u_style = st.selectbox("Template", list(TEMPLATES.keys()))
        u_music = st.selectbox("Music", list(MUSIC_TRACKS.keys()))
        btn_ad = st.button(f"Generate {u_duration}s Product Ad", type="primary")
        
    else: # Content Video (Now uses u_animation_style)
        st.subheader("Content Details")
        u_file = st.file_uploader("Background Image (Optional)", type=["png","jpg","jpeg"]) 
        u_model = st.text_input("Product/Topic for Tip", "Nursery safety")
        u_type = st.radio("Tip Category", ["DIY Tips", "Furniture Tips", "Interior Design Tips", "Maintenance Tips"])
        
        if st.button(f"Generate Tips for '{u_model}'", key="tip_gen_btn"):
            u_tips_text = generate_tips(u_type, u_model)
            st.session_state['generated_tips'] = u_tips_text
        
        u_caption_text = st.text_area("Final Caption/Tips", 
                                        value=st.session_state.get('generated_tips'),
                                        help="First line is the title/hook. Bullet points are the animated tips.")
        u_contact = st.text_input("Contact/URL (Small Footer)", "sm.co.ke")
        u_style = st.selectbox("Template", ["SM Classic", "Gold Diagonal"])
        u_music = st.selectbox("Music", list(MUSIC_TRACKS.keys()))
        
        u_price = "" 
        
        btn_ad = st.button(f"Generate {u_duration}s Content Video", type="primary")


# Video Ad Generation Logic (UNCHANGED in principle, uses new variables)
if btn_ad:
    DURATION = u_duration 
    status = st.status(f"Creating your {u_content_type} video...", expanded=True)

    # 1. Process image
    # ... (Image loading and processing) ...

    # 2. AI hook + smart layout mapping
    status.update(label="AI determining layout...")
    if u_content_type == "Product Showcase (Pillar A/C)":
        # ... (Product Showcase logic) ...
        pass
    else: # Content Video Logic
        hook = u_caption_text.split('\n')[0].strip() or 'EXPERT INSIGHT'
        # Force fixed layout
        fixed_layout = {'logo': 'LOGO_TOP', 'product': 'PRODUCT_CENTER', 'caption': 'CAPTION_HEADLINE', 'contact': 'CONTACT_FOOTER'}
        layout_map = {"LOGO_TOP": {"x": 50, "y": 50, "w": 200, "h": 100}, "PRODUCT_CENTER": {"x": 60, "y": 250, "w": 600, "h": 600}, "CAPTION_HEADLINE": {"x": 50, "y": 150, "w": 620, "h": 120}, "CONTACT_FOOTER": {"x": 60, "y": 1200, "w": 600, "h": 60}}
        layout = [layout_map[block_name].copy() | {'role': role} for role, block_name in fixed_layout.items() if role in ['logo', 'product', 'caption', 'contact']]

    st.write(f"**Video Hook:** {hook}")
    
    # 2.5 Load Logo
    logo_img = get_cached_logo(LOGO_URL, WIDTH, HEIGHT)

    # 3. Render frames
    status.update(label="Animating frames...")
    texts = {"caption": hook, "price": u_price, "contact": u_contact}
    if u_content_type == "Content Video (Pillar B)":
        texts["full_tips"] = u_caption_text
    
    frames = [create_frame(i/FPS, product_img, layout, texts, u_style, logo_img, u_content_type.split(' ')[0], u_animation_style) for i in range(FPS*DURATION)]
    clip = ImageSequenceClip(frames, fps=FPS)

    # 4. Add music & 5. Export (UNCHANGED)
    # ... (Music and Export logic) ...
    
    status.update(label="Done! Your ad is ready", state="complete")

st.caption("AdGen EVO by Grok × Streamlit – 2025 Edition")
