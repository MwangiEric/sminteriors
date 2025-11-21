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

# Fixed hotlink-friendly royalty-free music (direct MP3 URLs)
MUSIC_TRACKS = {
    "Upbeat Pop": "https://cdn.pixabay.com/download/audio/2024/08/15/audio_5a54d0f2f6.mp3?filename=upbeat-background-171614.mp3",
    "Luxury Chill": "https://uppbeat.io/assets/track/mp3/prigida-moving-on.mp3",
    "Modern Gold": "https://uppbeat.io/assets/track/mp3/synapse-fire-link-me-up.mp3",
    "Chill Beats": "https://uppbeat.io/assets/track/mp3/ikson-new-world.mp3"
}

# ================================
# SECRETS CHECK
# ================================
# st.secrets is handled by Streamlit environment

HEADERS = {
    "Authorization": f"Bearer {st.secrets['groq_key']}",
    "Content-Type": "application/json"
}
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# ================================
# CACHED RESOURCES
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

# ================================
# IMAGE PROCESSING & FONTS (UNCHANGED)
# ================================
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

# ================================
# ANIMATION & TEMPLATES (UNCHANGED)
# ================================
def ease_out_elastic(t):
    if t <= 0: return 0
    if t >= 1: return 1
    c4 = (2 * math.pi) / 3
    return math.pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

def linear_fade(t, start, duration):
    if t < start: return 0.0
    if t > start + duration: return 1.0
    return (t - start) / duration

BRAND_PRIMARY = "#4C3B30"
BRAND_ACCENT = "#D2A544"

TEMPLATES = {
    "SM Classic": {"bg_grad": [BRAND_PRIMARY, "#2a201b"], "accent": "#FFFFFF", "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "none"},
    "Gold Diagonal": {"bg_grad": [BRAND_PRIMARY, "#3e2e24"], "accent": BRAND_ACCENT, "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "diagonal", "graphic_color": BRAND_ACCENT},
    "Gold Circles": {"bg_grad": [BRAND_PRIMARY, "#332A22"], "accent": BRAND_ACCENT, "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "circular", "graphic_color": BRAND_ACCENT},
    "Gold Split": {"bg_grad": [BRAND_PRIMARY, BRAND_PRIMARY], "accent": "#FFFFFF", "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "split", "graphic_color": BRAND_ACCENT},
}

# ================================
# DRAWING HELPERS (UNCHANGED)
# ================================
def draw_centered_text(draw, text, y, font, color, max_width=600):
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
    for line in lines:
        w = draw.textbbox((0,0), line, font=font)[2]
        draw.text(((WIDTH - w) // 2, current_y), line, font=font, fill=color)
        current_y += draw.textbbox((0,0), line, font=font)[3] + 8
    return current_y

def draw_wrapped_text(draw, text, box, font, color):
    draw_centered_text(draw, text, box['y'], font, color, max_width=box['w'])


# ================================
# GROQ HELPERS (SMART LAYOUT V2 - CAPTURES ALL BLOCKS)
# ================================
def ask_groq(payload):
    try:
        full_url = f"{GROQ_BASE_URL}/chat/completions"
        r = requests.post(full_url, json=payload, headers=HEADERS, timeout=12)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Groq API Error: {e}")
        return None

def get_data_groq(img, model_name):
    
    # FIXED, ROBUST LAYOUT BLOCKS (TikTok Optimized)
    FIXED_LAYOUT_MAP = {
        "LOGO_TOP":         {"x": 50, "y": 50, "w": 200, "h": 100},
        "PRODUCT_CENTER":   {"x": 60, "y": 250, "w": 600, "h": 600},
        "PRODUCT_WIDE":     {"x": 60, "y": 400, "w": 600, "h": 500}, 
        "CAPTION_ABOVE":    {"x": 60, "y": 920, "w": 600, "h": 60}, 
        "CAPTION_HEADLINE": {"x": 50, "y": 200, "w": 620, "h": 120}, # High-impact, early text
        "PRICE_BUTTON":     {"x": (WIDTH - 400) // 2, "y": 1050, "w": 400, "h": 120},
        "PRICE_BADGE_TR":   {"x": 480, "y": 150, "w": 200, "h": 200}, # Top-Right circular badge
        "CONTACT_FOOTER":   {"x": 60, "y": 1200, "w": 600, "h": 60},
        "TIP_TEXT_CENTER":  {"x": 60, "y": 800, "w": 600, "h": 400}, # New block for Pillar B tip content
    }

    # Encode image (b64 logic remains UNCHANGED)
    buf = io.BytesIO()
    rgb = img.convert("RGB") if img.mode == "RGBA" else img
    rgb.save(buf, format="JPEG", quality=90)
    b64 = base64.b64encode(buf.getvalue()).decode()

    # Hook (vision model logic remains UNCHANGED)
    hook_payload = {
        "model": "llama-3.2-11b-vision-preview",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": f"Write a 4–6 word high-impact hook for this {model_name} ad. Focus on aspirational words."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
        ]}],
        "max_tokens": 30
    }
    hook = ask_groq(hook_payload) or "Elevate Your Living Space"

    # Layout (Groq MUST select from pre-defined creative blocks)
    block_names = [k for k in FIXED_LAYOUT_MAP.keys() if k != "TIP_TEXT_CENTER"] # Exclude TIP block from ad choice
    
    layout_payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": f"You are a Creative Director for a luxury brand. Output ONLY a valid JSON object. Choose ONE block for each role (logo, product, caption, price, contact) from this list: {block_names}. Output should be a dictionary like: {{'logo': 'LOGO_TOP', 'product': 'PRODUCT_CENTER', ...}}"},
            {"role": "user", "content": f"Create the layout structure for a 720×1280 luxury ad featuring a: {model_name}"}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.5
    }
    layout_raw = ask_groq(layout_payload)
    final_hook = hook.strip('"')

    # Default mapping (fallback if AI response fails)
    default_mapping = {
        'logo': 'LOGO_TOP', 
        'product': 'PRODUCT_CENTER', 
        'caption': 'CAPTION_ABOVE', 
        'price': 'PRICE_BUTTON', 
        'contact': 'CONTACT_FOOTER'
    }

    try:
        ai_mapping = json.loads(layout_raw)
        final_boxes = []
        mapping_to_use = {k: v for k, v in ai_mapping.items() if v in FIXED_LAYOUT_MAP} if isinstance(ai_mapping, dict) else default_mapping

        for role, block_name in mapping_to_use.items():
            if block_name in FIXED_LAYOUT_MAP:
                box_data = FIXED_LAYOUT_MAP[block_name].copy()
                box_data['role'] = role
                final_boxes.append(box_data)
        
        if not final_boxes:
             return final_hook, [FIXED_LAYOUT_MAP[role] | {'role': role} for role in default_mapping.values()]


        return final_hook, final_boxes
            
    except Exception as e:
        st.warning(f"AI creative mapping failed, using default layout. Error: {e}")
        return final_hook, [FIXED_LAYOUT_MAP[block_name].copy() | {'role': role} for role, block_name in default_mapping.items()]


# ================================
# CONTENT IDEA GENERATOR (PILLAR B)
# ================================
def generate_tips(content_type, keyword):
    system = "You are a luxury furniture brand content expert. Reply ONLY with markdown bullet points, no intro/outro. Use very concise language suitable for quick on-screen text."
    prompts = {
        "DIY Tips": f"5 quick DIY decor ideas using common items, focused on '{keyword}'",
        "Furniture Tips": f"5 pro tips for choosing/caring for luxury furniture like '{keyword}'",
        "Interior Design Tips": f"5 trending interior design hacks related to '{keyword}'",
        "Maintenance Tips": f"5 expert cleaning & care tips for solid wood, brass, fine upholstery"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompts.get(content_type, "Generate 5 tips")}
        ],
        "temperature": 0.8,
        "max_tokens": 800
    }
    with st.spinner("Generating tips..."):
        result = ask_groq(payload)
        return result or "No response from Groq. Try again."


# ================================
# FRAME RENDERER (HANDLING ALL PILLARS)
# ================================
def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0,2,4))

def create_frame(t, img, boxes, texts, tpl_name, logo_img, content_type):
    T = TEMPLATES[tpl_name]
    canvas = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(canvas)

    # Background Gradient and Template Graphics (UNCHANGED)
    c1 = hex_to_rgb(T["bg_grad"][0])
    c2 = hex_to_rgb(T["bg_grad"][1])
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        color = tuple(int(c1[i] + (c2[i] - c1[i]) * ratio) for i in range(3))
        draw.line([(0,y), (WIDTH,y)], fill=color)

    # Template Graphics
    gc = hex_to_rgb(T.get("graphic_color", "#000000")) if "graphic_color" in T else None
    if T["graphic_type"] == "diagonal" and gc:
        alpha = int(255 * linear_fade(t, 0.5, 1.0))
        for i in range(-WIDTH, WIDTH+HEIGHT, 60):
            draw.line([(i,0), (i+HEIGHT,HEIGHT)], fill=(*gc, alpha), width=8)
    if T["graphic_type"] == "circular" and gc:
        alpha = int(200 * linear_fade(t, 0.7, 0.8))
        big = int(WIDTH * 1.6 * ease_out_elastic(max(0, t-0.4)))
        draw.ellipse([WIDTH*0.8-big//2, HEIGHT*0.7-big//2, WIDTH*0.8+big//2, HEIGHT*0.7+big//2], fill=(*gc, alpha))
    if T["graphic_type"] == "split" and gc:
        h = int(HEIGHT * 0.35 * ease_out_elastic(max(0, t-0.9)))
        draw.rectangle([0, HEIGHT-h, WIDTH, HEIGHT], fill=T["graphic_color"])

    # --- BLOCK 1: Draw Product & Shadow (Layer 1) ---
    product_box = next((b for b in boxes if b["role"] == "product"), None)
    if product_box:
        b = product_box
        
        # --- TIP VIDEO MODIFICATION: Push product up to make room for tips ---
        if content_type == "Tip Video":
            b["y"] = 250
            b["h"] = 400
        # --------------------------------------------------------------------
        
        # Use slightly faster scale animation for 5s video focus
        scale = ease_out_elastic(min(t * 1.5, 1.0)) 
        if scale > 0.02:
            pw, ph = int(b["w"]*scale), int(b["h"]*scale)
            prod = img.resize((pw, ph), Image.LANCZOS)
            
            # Shadow
            shadow = prod.copy().convert("L")
            shadow = shadow.point(lambda p: p * 0.3)
            shadow = shadow.convert("RGBA")
            shadow = shadow.filter(ImageFilter.GaussianBlur(20))
            
            canvas.paste(shadow, 
                         (int(b["x"]+(b["w"]-pw)//2+10), int(b["y"]+(b["h"]-ph)//2+40)), 
                         shadow)

            # Product Placement (with float/int fix and explicit mask)
            prod_mask = prod.getchannel('A')
            canvas.paste(prod, 
                         (int(b["x"]+(b["w"]-pw)//2), 
                          int(b["y"]+(b["h"]-ph)//2 + math.sin(t*3)*10)), 
                         prod_mask)

    # --- BLOCK 2: Draw Text Elements (Layer 2 & 3) ---
    
    # 2a. Draw Contact/URL
    contact_box = next((b for b in boxes if b["role"] == "contact"), None)
    if contact_box and t > 2.3:
        y_start = contact_box.get('y', 1200)
        draw_centered_text(draw, texts["contact"], y_start, get_font(32), T["text"], max_width=600)
        
    # 2b. Draw Caption/Hook (Applies to all content types - this is the title)
    caption_box = next((b for b in boxes if b["role"] == "caption"), None)
    if caption_box and t > 1.0:
        # Use large font for high impact/early attention
        y_start = caption_box.get('y', 920)
        draw_centered_text(draw, texts["caption"], y_start, get_font(60) if caption_box["role"] == "CAPTION_HEADLINE" else get_font(52), T["accent"], max_width=600)

    # 2c. Draw Price (Only for Product Showcase - Pillar A/C)
    if content_type == "Product Showcase":
        price_box = next((b for b in boxes if b["role"] == "price"), None)
        if price_box and t > 1.4:
            PRICE_X, PRICE_Y_START, PRICE_W, PRICE_H = price_box["x"], price_box["y"], price_box["w"], price_box["h"]
            
            if PRICE_Y_START < 400: 
                # --- Draw PRICE_BADGE_TR Logic (Circular, High Impact) ---
                r = int(PRICE_W / 2)
                center_x = PRICE_X + r
                center_y = PRICE_Y_START + r
                
                draw.ellipse([PRICE_X, PRICE_Y_START, PRICE_X + PRICE_W, PRICE_Y_START + PRICE_H], 
                             fill="#000000") 
                
                badge_font_big = get_font(50)
                badge_font_small = get_font(24)
                
                price_parts = texts["price"].split()
                main_text = price_parts[0] if price_parts else "SALE"
                sub_text = price_parts[1] if len(price_parts) > 1 else "OFFER"
                
                w1 = draw.textbbox((0,0), main_text, font=badge_font_big)[2]
                draw.text((center_x - w1//2, center_y - 30), main_text, font=badge_font_big, fill="#FFFFFF")
                
                w2 = draw.textbbox((0,0), sub_text, font=badge_font_small)[2]
                draw.text((center_x - w2//2, center_y + 30), sub_text, font=badge_font_small, fill="#FFFFFF")

            else:
                # --- Draw Standard PRICE_BUTTON Logic (Rounded Rectangle) ---
                draw.rounded_rectangle([PRICE_X, PRICE_Y_START, PRICE_X + PRICE_W, PRICE_Y_START + PRICE_H], 
                                       radius=30, 
                                       fill=T["price_bg"])
                
                price_font = get_font(68)
                price_text_bbox_h = draw.textbbox((0,0), texts["price"].split('\n')[0], font=price_font)[3] 
                price_text_y = PRICE_Y_START + (PRICE_H - price_text_bbox_h) // 2 - 10 
                
                draw_centered_text(draw, texts["price"], price_text_y, price_font, T["price_text"], max_width=PRICE_W)
                
    # 2d. Draw TIP Animation (Only for Tip Video - Pillar B)
    if content_type == "Tip Video":
        
        # 2d.i. Process Tip Content & Time
        tip_text = texts.get("full_tips", "")
        # Parse markdown bullet points
        tips = [line.strip('*').strip('-').strip() for line in tip_text.split('\n') if line.strip().startswith('*') or line.strip().startswith('-')]
        
        # Animation timing
        display_duration = DURATION - 1.5 # Allow 1.5s for intro/outro
        tip_interval = display_duration / max(1, len(tips))
        
        if tips and display_duration > 0:
            
            # Define text styles and starting area
            tip_font = get_font(42)
            line_height = 60 # Space between tips
            start_y = 700 # Start position below the main product/image
            
            # Animate the tips one by one
            for i, tip in enumerate(tips):
                
                tip_start_time = 1.2 + (i * tip_interval)
                
                if t >= tip_start_time:
                    
                    y_pos = start_y + (i * line_height)
                    
                    # Calculate tip width for the background box
                    tip_w = draw.textbbox((0,0), tip, font=tip_font)[2]
                    padding = 20
                    
                    # --- Animate Opacity (Fade In) ---
                    fade_time = 0.3
                    alpha_ratio = min(1.0, (t - tip_start_time) / fade_time)
                    alpha = int(255 * alpha_ratio)
                    
                    # Draw semi-transparent background rectangle
                    draw.rounded_rectangle(
                        [ (WIDTH-tip_w-padding)//2 - 10, y_pos - 15, (WIDTH+tip_w+padding)//2 + 10, y_pos + line_height - 15],
                        radius=10,
                        fill=(*hex_to_rgb(BRAND_ACCENT), int(180 * alpha_ratio)) # Semi-transparent accent background
                    )
                    
                    # Draw the tip text
                    draw.text(
                        ((WIDTH - tip_w) // 2, y_pos - 10), 
                        tip, 
                        font=tip_font, 
                        fill=(*hex_to_rgb(T["text"]), alpha)
                    )


    # --- BLOCK 3: Draw Logo (Highest Layer) ---
    logo_box = next((b for b in boxes if b["role"] == "logo"), None)
    if logo_box:
        if logo_img:
            logo_resized = logo_img.resize((logo_box["w"], logo_box["h"]), Image.LANCZOS)
            canvas.paste(logo_resized, (logo_box["x"], logo_box["y"]), logo_resized)
            
    # Vignette
    vig = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
    vdraw = ImageDraw.Draw(vig)
    for y in range(int(HEIGHT*0.65), HEIGHT):
        a = int(200 * (y - HEIGHT*0.65) / (HEIGHT*0.35))
        vdraw.line([(0,y), (WIDTH,y)], fill=(0,0,0,a))
    canvas.paste(vig, (0,0), vig)

    return np.array(canvas)

# ================================
# UI LOGIC (ENHANCED)
# ================================
st.title("AdGen EVO – SM Interiors Edition")

with st.sidebar:
    st.header("TikTok Content Builder")
    u_content_type = st.radio(
        "Content Pillar", 
        ["Product Showcase (Pillar A/C)", "Tip Video (Pillar B)"],
        help="Showcase drives sales; Tip Videos drive Saves/Shares."
    )
    st.markdown("---")

    st.header("Video Settings")
    u_duration = st.slider("Video Duration (Seconds)", min_value=3, max_value=8, value=5, step=1, help="5s is ideal for high TikTok completion rate.")
    
    # Only show price/contact if it's a showcase ad
    if u_content_type == "Product Showcase (Pillar A/C)":
        st.subheader("Product Ad Details")
        u_file = st.file_uploader("Product Image", type=["png","jpg","jpeg"])
        u_model = st.text_input("Product Name", "Luxe Velvet Sofa")
        u_price = st.text_input("Price / Discount", "Ksh 89,900") 
        u_contact = st.text_input("Contact Info", "0710 895 737")
        u_style = st.selectbox("Template", list(TEMPLATES.keys()))
        u_music = st.selectbox("Music", list(MUSIC_TRACKS.keys()))
        btn_ad = st.button(f"Generate {u_duration}s Product Ad", type="primary")
        
    else: # Tip Video
        st.subheader("Tip Content Details")
        u_file = st.file_uploader("Background Image", type=["png","jpg","jpeg"])
        u_model = st.text_input("Product/Topic for Tip", "Velvet Sofa Care")
        u_type = st.radio("Tip Category", ["DIY Tips", "Furniture Tips", "Interior Design Tips", "Maintenance Tips"])
        
        # Generator for the hook/caption text
        if st.button(f"Generate 5 Tips for '{u_model}'", key="tip_gen_btn"):
            u_tips_text = generate_tips(u_type, u_model)
            st.session_state['generated_tips'] = u_tips_text
        
        u_caption_text = st.text_area("Final Caption/Hook (The Tip Title & Full List)", 
                                        value=st.session_state.get('generated_tips', '5 Secrets to a Luxe Home\n* Tip one\n* Tip two\n* Tip three\n* Tip four\n* Tip five'),
                                        help="The first line is the title. The bullet points below will be animated.")
        u_contact = st.text_input("Contact/URL (Small Footer)", "sm.co.ke")
        u_style = st.selectbox("Template", ["SM Classic", "Gold Diagonal"])
        u_music = st.selectbox("Music", list(MUSIC_TRACKS.keys()))
        
        # Set placeholder values for consistency
        u_price = "" 
        
        btn_ad = st.button(f"Generate {u_duration}s Tip Video", type="primary")


# Video Ad Generation Logic
if btn_ad and u_file:
    # Set the duration variable used by the moviepy functions
    DURATION = u_duration 
    
    status = st.status(f"Creating your {u_content_type} video...", expanded=True)

    # 1. Process image
    status.update(label="Enhancing background image...")
    raw = Image.open(u_file).convert("RGBA")
    product_img = process_image_pro(raw)
    st.image(product_img, "Processed Image", width=200)

    # 2. AI hook + smart layout mapping
    status.update(label="AI determining layout...")
    
    if u_content_type == "Product Showcase (Pillar A/C)":
        hook, layout = get_data_groq(product_img, u_model)
    else: # Tip Video Logic
        # Use the first line as the headline hook
        hook = u_caption_text.split('\n')[0].strip() or '5 Secrets to a Luxe Home'
        # Force a Tip-Video-specific layout for the title
        fixed_layout = {
            'logo': 'LOGO_TOP', 
            'product': 'PRODUCT_CENTER', 
            'caption': 'CAPTION_HEADLINE', # Force high-impact title
            'price': 'PRICE_BUTTON', # Placeholder, but not drawn in create_frame
            'contact': 'CONTACT_FOOTER'
        }
        layout_map = {
            "LOGO_TOP": {"x": 50, "y": 50, "w": 200, "h": 100},
            "PRODUCT_CENTER": {"x": 60, "y": 250, "w": 600, "h": 600},
            "CAPTION_HEADLINE": {"x": 50, "y": 150, "w": 620, "h": 120},
            "CONTACT_FOOTER": {"x": 60, "y": 1200, "w": 600, "h": 60}
        }
        layout = [layout_map[block_name].copy() | {'role': role} for role, block_name in fixed_layout.items() if role in ['logo', 'product', 'caption', 'contact']]


    st.write(f"**Video Hook:** {hook}")
    
    # 2.5 Load Logo (Cached Step)
    status.update(label="Loading brand logo...")
    logo_img = get_cached_logo(LOGO_URL, WIDTH, HEIGHT)

    # 3. Render frames
    status.update(label="Animating frames...")
    texts = {"caption": hook, "price": u_price, "contact": u_contact}
    
    # --- TIP VIDEO MODIFICATION: Pass the full tip text for internal animation ---
    if u_content_type == "Tip Video (Pillar B)":
        texts["full_tips"] = u_caption_text
    
    # Pass the selected content type to the frame renderer
    frames = [create_frame(i/FPS, product_img, layout, texts, u_style, logo_img, u_content_type.split(' ')[0]) for i in range(FPS*DURATION)]
    clip = ImageSequenceClip(frames, fps=FPS)

    # 4. Add music
    status.update(label="Adding music...")
    try:
        audio_data = requests.get(MUSIC_TRACKS[u_music]).content
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(audio_data)
            audio = AudioFileClip(tmp.name).subclip(0, DURATION).audio_fadeout(0.8)
            final = clip.set_audio(audio)
            os.unlink(tmp.name)
    except Exception as e:
        final = clip
        st.warning(f"Music failed – silent video. Error: {e}")

    # 5. Export
    status.update(label="Exporting MP4...")
    output_filename = f"SM_{u_content_type.split(' ')[0]}_{u_model.replace(' ', '_')}_{DURATION}s.mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        final.write_videofile(tmp.name, codec="libx264", audio_codec="aac", fps=FPS, logger=None, verbose=False)
        st.video(tmp.name)
        with open(tmp.name, "rb") as f:
            st.download_button("Download Video", f, output_filename, "video/mp4")
        os.unlink(tmp.name)

    status.update(label="Done! Your ad is ready", state="complete")
elif btn_ad and not u_file:
    st.error("Please upload an image before generating.")

st.caption("AdGen EVO by Grok × Streamlit – 2025 Edition")
