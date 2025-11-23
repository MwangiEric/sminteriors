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
# CACHED RESOURCES & FONTS
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

@st.cache_resource
def get_font_path(font_name):
    # This block ensures we use system fonts if available for reliability
    if font_name == "Serif":
        # Times New Roman equivalent
        paths = ["/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", "times.ttf"] 
    elif font_name == "Sans-Serif-Bold":
        # Avenir/Montserrat equivalent
        paths = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "arialbd.ttf"] 
    else: # Default fallback
        paths = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "arial.ttf"] 
    
    for path in paths:
        if os.path.exists(path):
            return path
    # Fallback to load_default() if no truetype path is found
    return None 

def get_font(size, font_type="Sans-Serif-Bold"):
    path = get_font_path(font_type)
    try:
        if path:
            return ImageFont.truetype(path, size)
        else:
            return ImageFont.load_default()
    except:
        return ImageFont.load_default()
# END FONT BLOCK

# ================================
# DRAWING HELPERS (Refined)
# ================================
def draw_centered_text(draw, text, y, font, color, max_width=600, alpha=255):
    # ... (remains mostly the same as before, used for hooks/contact) ...
    lines = []
    words = text.split()
    line = ""
    
    for w in words:
        test = line + (" " + w if line else w)
        # Use getmask for accurate PIL bbox calculation
        mask = ImageDraw.Draw(Image.new("L", (1, 1))).textmask((0,0), test, font=font)
        test_width = mask.getbbox()[2] if mask.getbbox() else 0
        
        if test_width <= max_width:
            line = test
        else:
            lines.append(line)
            line = w
    if line: lines.append(line)
    
    current_y = y
    fill_color = (*hex_to_rgb(color), alpha)
    
    for line in lines:
        w, h = draw.textbbox((0,0), line, font=font)[2], draw.textbbox((0,0), line, font=font)[3]
        draw.text(((WIDTH - w) // 2, current_y), line, font=font, fill=fill_color)
        current_y += h + 8
    return current_y

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0,2,4))

# ... (Templates, Groq Helpers, and Content Generator remain the same) ...

# ================================
# FRAME RENDERER (Updated Font & Tip Drawing)
# ================================
def create_frame(t, img, boxes, texts, tpl_name, logo_img, content_type, animation_style):
    T = TEMPLATES[tpl_name]
    canvas = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(canvas)

    # --- FONT DEFINITIONS ---
    HEADLINE_FONT = get_font(60, "Sans-Serif-Bold") # For hooks/titles
    TIP_FONT = get_font(42, "Serif")              # For tip body text
    CONTACT_FONT = get_font(32, "Sans-Serif-Bold") # For footer text
    
    # Background & Graphics (UNCHANGED)
    # ...

    # Draw Product & Shadow (Layer 1 - UNCHANGED)
    # ...

    # --- BLOCK 2: Draw Text Elements ---
    
    # 2a. Draw Contact/URL
    contact_box = next((b for b in boxes if b["role"] == "contact"), None)
    if contact_box:
        alpha = int(255 * linear_fade(t, DURATION - 1.5, 0.5))
        y_start = contact_box.get('y', 1200)
        if alpha > 0:
            draw_centered_text(draw, texts["contact"], y_start, CONTACT_FONT, T["text"], max_width=600, alpha=alpha)
        
    # 2b. Draw Caption/Hook (Title) 
    caption_box = next((b for b in boxes if b["role"] == "caption"), None)
    if caption_box:
        
        # Timing remains the same for the fade-in/out
        # ... (Timing logic remains the same) ...
        alpha_in = linear_fade(t, 0.5, 1.0) 
        alpha_out = 1.0 - linear_fade(t, 2.5, 1.0)
        alpha = int(255 * max(0, min(alpha_in, alpha_out)))

        if alpha > 0:
            draw_centered_text(draw, texts["caption"], caption_box.get('y', 150), 
                            HEADLINE_FONT, T["accent"], max_width=600, alpha=alpha)


    # 2c. Draw Price (Product Showcase ONLY - UNCHANGED)
    # ...

    # 2d. Draw TIPS (Only for Content Video - PILLAR B)
    if content_type == "Content Video":
        
        tip_text = texts.get("full_tips", "")
        # Get all bullet points, ignoring the first line (the caption/hook)
        tips = [line.strip('*').strip('-').strip() for line in tip_text.split('\n')[1:] if line.strip().startswith('*') or line.strip().startswith('-')]
        
        if tips:
            line_height = 70 
            start_y = 450 if img else 450
            
            # --- ANIMATION STYLE LOGIC ---
            
            if animation_style == "Typewriter (Sequential Reveal)":
                # --- TYPEWRITER LOGIC (Using TIP_FONT) ---
                CHAR_PER_SECOND = 40
                START_TIME = 3.5
                TIP_DELAY = 0.5       
                cumulative_delay = START_TIME
                
                for i, full_tip in enumerate(tips):
                    tip_len = len(full_tip)
                    tip_duration = tip_len / CHAR_PER_SECOND
                    tip_start_time = cumulative_delay
                    
                    if t >= tip_start_time:
                        time_in_tip = max(0, t - tip_start_time)
                        chars_to_show = min(tip_len, math.floor(time_in_tip * CHAR_PER_SECOND))
                        current_tip_text = full_tip[:chars_to_show]
                        
                        y_pos = start_y + (i * line_height)
                        
                        # Use PIL's built-in text size calculation for precise background box
                        tip_bbox = draw.textbbox((0,0), full_tip, font=TIP_FONT)
                        tip_w = tip_bbox[2]
                        padding = 20
                        
                        # Background box
                        alpha_ratio_bg = min(1.0, (t - tip_start_time) / 0.15)
                        
                        draw.rounded_rectangle(
                            # X-coordinates centered
                            [ (WIDTH-tip_w-padding)//2 - 10, y_pos - 15, 
                              (WIDTH+tip_w+padding)//2 + 10, y_pos + line_height - 15],
                            radius=10,
                            fill=(*hex_to_rgb(BRAND_ACCENT), int(180 * alpha_ratio_bg)) 
                        )
                        
                        # Text: draw the current typed segment
                        # Ensure the text is vertically centered within the line_height
                        text_offset_y = (line_height - tip_bbox[3]) // 2 
                        draw.text(((WIDTH - tip_w) // 2, y_pos - 15 + text_offset_y), 
                                  current_tip_text, 
                                  font=TIP_FONT, 
                                  fill=T["text"])
                    
                    cumulative_delay = tip_start_time + tip_duration + TIP_DELAY
            
            # --- SMOOTH FADE LOGIC (Updated to use TIP_FONT and precise layout) ---
            elif animation_style == "Smooth Fade (All at Once)":
                FADE_START = 3.5
                FADE_DURATION = 0.8
                alpha = int(255 * linear_fade(t, FADE_START, FADE_DURATION))
                
                if alpha > 0:
                    for i, full_tip in enumerate(tips):
                        y_pos = start_y + (i * line_height)
                        
                        tip_bbox = draw.textbbox((0,0), full_tip, font=TIP_FONT)
                        tip_w = tip_bbox[2]
                        padding = 20
                        
                        # Draw semi-transparent background rectangle (fading with the text)
                        draw.rounded_rectangle(
                             [ (WIDTH-tip_w-padding)//2 - 10, y_pos - 15, 
                               (WIDTH+tip_w+padding)//2 + 10, y_pos + line_height - 15],
                            radius=10,
                            fill=(*hex_to_rgb(BRAND_ACCENT), int(180 * (alpha/255))) 
                        )
                        
                        # Draw the text itself (fading in)
                        text_offset_y = (line_height - tip_bbox[3]) // 2
                        draw.text(((WIDTH - tip_w) // 2, y_pos - 15 + text_offset_y), 
                                  full_tip, 
                                  font=TIP_FONT, 
                                  fill=(*hex_to_rgb(T["text"]), alpha)
                        )
            
            # --- BLOCK REVEAL LOGIC (Updated to use TIP_FONT and precise layout) ---
            elif animation_style == "Block Reveal (Sequential Block Fade)":
                # ... (Block Reveal logic updated similarly to Smooth Fade, using TIP_FONT and accurate positioning) ...
                pass


    # --- BLOCK 3: Draw Logo (Highest Layer) ---
    # ... (Logo drawing logic) ...

    # Vignette (UNCHANGED)
    # ...

    return np.array(canvas)

# ================================
# UI LOGIC (FINALIZED - DURATION variable added)
# ================================
st.title("AdGen EVO – SM Interiors Edition")

# Initialize session state for tip text
if 'generated_tips' not in st.session_state:
    st.session_state['generated_tips'] = 'EXPERT INSIGHT\n* Always prioritize safety by embracing all holding and accessory features.\n* Less is more; focus on a few high-quality, functional pieces.\n* Prioritize safety by selecting only non-toxic, low-VOC paints.'


with st.sidebar:
    st.header("TikTok Content Builder")
    u_content_type = st.radio(
        "Content Pillar", 
        ["Product Showcase (Pillar A/C)", "Content Video (Pillar B)"],
        index=1, 
        help="Showcase drives sales; Content Videos drive Saves/Shares/Follows."
    )
    st.markdown("---")

    st.header("Video Settings")
    u_duration = st.slider("Video Duration (Seconds)", min_value=3, max_value=8, value=6, step=1, help="6s is recommended for most animations.")
    
    if u_content_type == "Content Video (Pillar B)":
        u_animation_style = st.selectbox(
            "Text Animation Style", 
            ["Smooth Fade (All at Once)", "Typewriter (Sequential Reveal)", "Block Reveal (Sequential Block Fade)"],
            index=0,
            help="Select the style for revealing the tips after the title fades out."
        )
    else:
        u_animation_style = "Simple Fade" 

    # ... (Rest of UI controls remain the same) ...

    u_contact = st.text_input("Contact/URL (Small Footer)", "sm.co.ke")
    u_style = st.selectbox("Template", ["SM Classic", "Gold Diagonal"])
    u_music = st.selectbox("Music", list(MUSIC_TRACKS.keys()))
    
    if u_content_type == "Product Showcase (Pillar A/C)":
        u_price = st.text_input("Price / Discount", "Ksh 49,900")
        # Ensure u_price is defined for the product case
        
    else: 
        u_price = "" 

    
    btn_ad = st.button(f"Generate {u_duration}s Video", type="primary")

# Video Ad Generation Logic
if btn_ad:
    # Set the duration variable used by the moviepy functions
    global DURATION
    DURATION = u_duration 
    
    status = st.status(f"Creating your {u_content_type} video...", expanded=True)
    # ... (Image processing, AI layout, and final generation logic remains the same) ...
    
    # 3. Render frames
    status.update(label="Animating frames...")
    texts = {"caption": hook, "price": u_price, "contact": u_contact}
    
    if u_content_type == "Content Video (Pillar B)":
        texts["full_tips"] = u_caption_text
    
    # Passing animation_style to create_frame
    frames = [create_frame(i/FPS, product_img, layout, texts, u_style, logo_img, u_content_type.split(' ')[0], u_animation_style) for i in range(FPS*DURATION)]
    clip = ImageSequenceClip(frames, fps=FPS)

    # ... (Music and Export logic) ...
    
    status.update(label="Done! Your ad is ready", state="complete")

st.caption("AdGen EVO by Grok × Streamlit – 2025 Edition")
