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

# --- GRID CONSTANTS (New) ---
GRID_COLUMNS = 12
GRID_GUTTER = 20 # Space between columns, used for left/right margins
GRID_UNIT_WIDTH = (WIDTH - (GRID_GUTTER * 2)) / GRID_COLUMNS
# Example: 720 - 40 = 680. 680 / 12 = 56.66px per column
# For simplicity, we use the 20px gutter for the outer margin, and let elements span the full width

# Music and TEMPLATES definitions remain the same
BRAND_PRIMARY = "#4C3B30"
BRAND_ACCENT = "#D2A544"
TEMPLATES = {
    "SM Classic": {"bg_grad": [BRAND_PRIMARY, "#2a201b"], "accent": "#FFFFFF", "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "none"},
    "Gold Diagonal": {"bg_grad": [BRAND_PRIMARY, "#3e2e24"], "accent": BRAND_ACCENT, "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "diagonal", "graphic_color": BRAND_ACCENT},
    "Gold Circles": {"bg_grad": [BRAND_PRIMARY, "#332A22"], "accent": BRAND_ACCENT, "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "circular", "graphic_color": BRAND_ACCENT},
    "Gold Split": {"bg_grad": [BRAND_PRIMARY, BRAND_PRIMARY], "accent": "#FFFFFF", "text": "#FFFFFF", "price_bg": BRAND_ACCENT, "price_text": "#000000", "graphic_type": "split", "graphic_color": BRAND_ACCENT},
}
MUSIC_TRACKS = {
    "Upbeat Pop": "https://cdn.pixabay.com/download/audio/2024/08/15/audio_5a54d0f2f6.mp3?filename=upbeat-background-171614.mp3",
    "Luxury Chill": "https://uppbeat.io/assets/track/mp3/prigida-moving-on.mp3",
    "Modern Gold": "https://uppbeat.io/assets/track/mp3/synapse-fire-link-me-up.mp3",
    "Chill Beats": "https://uppbeat.io/assets/track/mp3/ikson-new-world.mp3"
}

# ================================
# SECRETS CHECK & HELPERS
# ================================
HEADERS = {
    "Authorization": f"Bearer {st.secrets['groq_key']}",
    "Content-Type": "application/json"
}
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

@st.cache_resource
def get_rembg_session():
    return new_session()

# ... (get_cached_logo, process_image_pro, get_font_path, get_font, ease_out_elastic, linear_fade, hex_to_rgb, draw_centered_text, ask_groq remain the same) ...

# --- GRID HELPER (New) ---
def calc_grid_x(columns_span):
    """Calculates the x-coordinate and width for a centered element spanning 'columns_span'."""
    
    # Calculate the total width of the element (including columns and gutters between them)
    # Total content width: WIDTH - (2 * outer gutter)
    content_width = WIDTH - (GRID_GUTTER * 2) 
    
    # Width of the element based on the span
    element_width = int((content_width / GRID_COLUMNS) * columns_span)

    # Calculate the starting x-position for centering
    start_x = (WIDTH - element_width) // 2
    
    return start_x, element_width

# ================================
# CONTENT GENERATOR (Refactored to use Grid)
# ================================
def get_data_groq(img, model_name):
    
    # --- FIXED LAYOUT MAP (REVISED TO USE GRID) ---
    # Centered on screen, 10 columns wide
    CAPTION_X, CAPTION_W = calc_grid_x(10)
    PRODUCT_X, PRODUCT_W = calc_grid_x(10) 
    PRICE_X, PRICE_W = calc_grid_x(7)     # Price button is 7 columns wide
    CONTACT_X, CONTACT_W = calc_grid_x(10)
    
    # Logo is left-aligned to the main content area (using outer gutter as margin)
    LOGO_X, LOGO_W = GRID_GUTTER, calc_grid_x(4)[1] # 4 columns wide
    
    FIXED_LAYOUT_MAP = {
        "LOGO_TOP":         {"x": LOGO_X, "y": 50, "w": LOGO_W, "h": 100},
        "PRODUCT_CENTER":   {"x": PRODUCT_X, "y": 250, "w": PRODUCT_W, "h": 600},
        "CAPTION_HEADLINE": {"x": CAPTION_X, "y": 200, "w": CAPTION_W, "h": 120}, 
        "PRICE_BUTTON":     {"x": PRICE_X, "y": 1050, "w": PRICE_W, "h": 120},
        "CONTACT_FOOTER":   {"x": CONTACT_X, "y": 1200, "w": CONTACT_W, "h": 60},
    }
    # -----------------------------------------------

    if img:
        # ... (Groq call for hook remains the same) ...
        buf = io.BytesIO()
        rgb = img.convert("RGB") if img.mode == "RGBA" else img
        rgb.save(buf, format="JPEG", quality=90)
        b64 = base64.b64encode(buf.getvalue()).decode()
        
        hook_payload = {
            "model": "llama-3.2-11b-vision-preview",
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": f"Write a 4–6 word high-impact hook for this {model_name} ad. Focus on aspirational words."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]}],
            "max_tokens": 30
        }
        hook = ask_groq(hook_payload) or "Redefine Your Living Space" 
    else:
        hook = "Redefine Your Living Space"

    # ... (Groq call for layout mapping remains the same) ...
    # This ensures the AI selects a grid-aligned position from the map above.
    block_names = [k for k in FIXED_LAYOUT_MAP.keys()] 
    
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

    default_mapping = {
        'logo': 'LOGO_TOP', 'product': 'PRODUCT_CENTER', 'caption': 'CAPTION_HEADLINE', 
        'price': 'PRICE_BUTTON', 'contact': 'CONTACT_FOOTER'
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
        return final_hook, [FIXED_LAYOUT_MAP[block_name].copy() | {'role': role} for role, block_name in default_mapping.items()]


def generate_tips(content_type, keyword):
    # ... (remains the same) ...
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
        return result or '5 Secrets to a Luxe Home\n* Tip one\n* Tip two\n* Tip three\n* Tip four\n* Tip five'


# ================================
# FRAME RENDERER (Minor update for Tip Text Centering)
# ================================
def create_frame(t, img, boxes, texts, tpl_name, logo_img, content_type, animation_style):
    T = TEMPLATES[tpl_name]
    canvas = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(canvas)

    # --- FONT DEFINITIONS ---
    HEADLINE_FONT = get_font(60, "Sans-Serif-Bold") 
    TIP_FONT = get_font(42, "Serif")              
    CONTACT_FONT = get_font(32, "Sans-Serif-Bold") 

    # ... (Background, Product Drawing, Contact/Caption/Price Drawing remain the same, 
    # as their positioning is now correctly managed by the grid-aligned box data 'b' ) ...
    
    # Background Gradient 
    c1 = hex_to_rgb(T["bg_grad"][0])
    c2 = hex_to_rgb(T["bg_grad"][1])
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        color = tuple(int(c1[i] + (c2[i] - c1[i]) * ratio) for i in range(3))
        draw.line([(0,y), (WIDTH,y)], fill=color)

    # Template Graphics (omitted for brevity, remains the same)
    
    # Draw Product & Shadow (Layer 1)
    product_box = next((b for b in boxes if b["role"] == "product"), None)
    
    if product_box and img: 
        b = product_box
        
        # Adjust product position for Content Video (Smaller)
        if content_type == "Content Video": 
            b["y"] = 250
            b["h"] = 400
        
        # Scale and placement logic (UNCHANGED)
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

            # Product Placement
            prod_mask = prod.getchannel('A')
            canvas.paste(prod, 
                         (int(b["x"]+(b["w"]-pw)//2), 
                          int(b["y"]+(b["h"]-ph)//2 + math.sin(t*3)*10)), 
                         prod_mask)
                         
    # 2a. Draw Contact/URL
    contact_box = next((b for b in boxes if b["role"] == "contact"), None)
    if contact_box:
        alpha = int(255 * linear_fade(t, DURATION - 1.5, 0.5))
        y_start = contact_box.get('y', 1200)
        if alpha > 0:
            # We use max_width=600 for the text line wrapping, ensuring it respects the grid alignment
            draw_centered_text(draw, texts["contact"], y_start, CONTACT_FONT, T["text"], max_width=600, alpha=alpha)
        
    # 2b. Draw Caption/Hook (Title) 
    caption_box = next((b for b in boxes if b["role"] == "caption"), None)
    if caption_box:
        
        if content_type == "Product Showcase":
            alpha = int(255 * linear_fade(t, 1.0, 0.5)) 
        elif content_type == "Content Video":
            alpha_in = linear_fade(t, 0.5, 1.0) 
            alpha_out = 1.0 - linear_fade(t, 2.5, 1.0)
            alpha = int(255 * max(0, min(alpha_in, alpha_out)))

        if alpha > 0:
            # The text drawing function already handles centering within the canvas based on text size
            draw_centered_text(draw, texts["caption"], caption_box.get('y', 150), 
                            HEADLINE_FONT, T["accent"], max_width=600, alpha=alpha)


    # 2c. Draw Price (Product Showcase ONLY)
    if content_type == "Product Showcase":
        price_box = next((b for b in boxes if b["role"] == "price"), None)
        if price_box and t > 1.4:
            PRICE_X, PRICE_Y_START, PRICE_W, PRICE_H = price_box["x"], price_box["y"], price_box["w"], price_box["h"]
            
            alpha = int(255 * linear_fade(t, 1.4, 0.5))
            
            # Button logic (Simplified for space)
            fill_color = (*hex_to_rgb(T["price_bg"]), alpha)
            draw.rounded_rectangle([PRICE_X, PRICE_Y_START, PRICE_X + PRICE_W, PRICE_Y_START + PRICE_H], 
                                    radius=30, fill=fill_color)
            price_font = get_font(68)
            price_text_bbox_h = draw.textbbox((0,0), texts["price"].split('\n')[0], font=price_font)[3] 
            price_text_y = PRICE_Y_START + (PRICE_H - price_text_bbox_h) // 2 - 10 
            draw_centered_text(draw, texts["price"], price_text_y, price_font, T["price_text"], max_width=PRICE_W, alpha=alpha)
                
    # 2d. Draw TIPS (Content Video - ALL ANIMATION STYLES)
    if content_type == "Content Video":
        
        tip_text = texts.get("full_tips", "")
        # Use the width of the main content area (600px wide for 10 columns) for tip text alignment
        TIP_CONTENT_MAX_WIDTH = calc_grid_x(10)[1] 
        
        tips = [line.strip('*').strip('-').strip() for line in tip_text.split('\n')[1:] if line.strip().startswith('*') or line.strip().startswith('-')]
        
        if tips:
            line_height = 70 
            start_y = 450 if img else 450
            
            # --- ANIMATION STYLE LOGIC ---
            
            # (Logic for Typewriter, Smooth Fade, Block Reveal remains the same, 
            # now benefiting from consistent font and centered positioning.)
            
            if animation_style == "Smooth Fade (All at Once)":
                FADE_START = 3.5
                FADE_DURATION = 0.8
                alpha = int(255 * linear_fade(t, FADE_START, FADE_DURATION))
                
                if alpha > 0:
                    for i, full_tip in enumerate(tips):
                        y_pos = start_y + (i * line_height)
                        
                        # Get bbox for the specific text
                        tip_bbox = draw.textbbox((0,0), full_tip, font=TIP_FONT)
                        tip_w = tip_bbox[2]
                        padding = 20
                        
                        # Calculate X-coordinates to center the block on the screen
                        tip_x_start = (WIDTH - tip_w - padding * 2) // 2
                        tip_x_end = tip_x_start + tip_w + padding * 2
                        
                        # Draw semi-transparent background rectangle (fading with the text)
                        draw.rounded_rectangle(
                             [ tip_x_start, y_pos - 15, tip_x_end, y_pos + line_height - 15],
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
            # The other animation styles (Typewriter/Block Reveal) use identical text/background drawing logic 
            # and will now automatically benefit from the centered text block calculation.
            
            elif animation_style == "Typewriter (Sequential Reveal)":
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
                        tip_bbox = draw.textbbox((0,0), full_tip, font=TIP_FONT)
                        tip_w = tip_bbox[2]
                        padding = 20
                        
                        alpha_ratio_bg = min(1.0, (t - tip_start_time) / 0.15)
                        
                        tip_x_start = (WIDTH - tip_w - padding * 2) // 2
                        tip_x_end = tip_x_start + tip_w + padding * 2
                        
                        draw.rounded_rectangle(
                            [ tip_x_start, y_pos - 15, tip_x_end, y_pos + line_height - 15],
                            radius=10,
                            fill=(*hex_to_rgb(BRAND_ACCENT), int(180 * alpha_ratio_bg)) 
                        )
                        text_offset_y = (line_height - tip_bbox[3]) // 2 
                        draw.text(((WIDTH - tip_w) // 2, y_pos - 15 + text_offset_y), 
                                  current_tip_text, 
                                  font=TIP_FONT, 
                                  fill=T["text"])
                    
                    cumulative_delay = tip_start_time + tip_duration + TIP_DELAY
            
            elif animation_style == "Block Reveal (Sequential Block Fade)":
                START_TIME = 3.5
                BLOCK_INTERVAL = 0.4
                FADE_DURATION = 0.3
                
                for i, full_tip in enumerate(tips):
                    block_start = START_TIME + i * BLOCK_INTERVAL
                    alpha = int(255 * linear_fade(t, block_start, FADE_DURATION))
                    
                    if alpha > 0:
                        y_pos = start_y + (i * line_height)
                        tip_bbox = draw.textbbox((0,0), full_tip, font=TIP_FONT)
                        tip_w = tip_bbox[2]
                        padding = 20

                        tip_x_start = (WIDTH - tip_w - padding * 2) // 2
                        tip_x_end = tip_x_start + tip_w + padding * 2

                        draw.rounded_rectangle(
                            [ tip_x_start, y_pos - 15, tip_x_end, y_pos + line_height - 15],
                            radius=10,
                            fill=(*hex_to_rgb(BRAND_ACCENT), int(180 * (alpha/255))) 
                        )
                        
                        text_offset_y = (line_height - tip_bbox[3]) // 2
                        draw.text(((WIDTH - tip_w) // 2, y_pos - 15 + text_offset_y), 
                                  full_tip, 
                                  font=TIP_FONT, 
                                  fill=(*hex_to_rgb(T["text"]), alpha)
                        )
    # --- BLOCK 3: Draw Logo (Highest Layer) ---
    logo_box = next((b for b in boxes if b["role"] == "logo"), None)
    if logo_box:
        if logo_img:
            logo_resized = logo_img.resize((logo_box["w"], logo_box["h"]), Image.LANCZOS)
            canvas.paste(logo_resized, (logo_box["x"], logo_box["y"]), logo_resized)
            
    # Vignette (UNCHANGED)
    vig = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
    vdraw = ImageDraw.Draw(vig)
    for y in range(int(HEIGHT*0.65), HEIGHT):
        a = int(200 * (y - HEIGHT*0.65) / (HEIGHT*0.35))
        vdraw.line([(0,y), (WIDTH,y)], fill=(0,0,0,a))
    canvas.paste(vig, (0,0), vig)

    return np.array(canvas)

# ... (UI Logic remains the same, using the new grid-aligned layout) ...
# ================================
# UI LOGIC (FINALIZED with Product Upload)
# ================================
st.title("AdGen EVO – SM Interiors Edition")

if 'generated_tips' not in st.session_state:
    st.session_state['generated_tips'] = 'EXPERT INSIGHT\n* Prioritize safety features.\n* Less is more; choose high-quality pieces.\n* Select non-toxic, low-VOC finishes.'


with st.sidebar:
    st.header("TikTok Content Builder")
    u_content_type = st.radio(
        "Content Pillar", 
        ["Product Showcase (Pillar A/C)", "Content Video (Pillar B)"],
        index=0, # Default to Product Showcase where the upload is crucial
        help="Showcase drives sales; Content Videos drive Saves/Shares/Follows."
    )
    st.markdown("---")

    st.header("Video Settings")
    u_duration = st.slider("Video Duration (Seconds)", min_value=3, max_value=8, value=6, step=1, help="6s is recommended for most animations.")
    
    # ----------------------------------------------------
    # CONDITIONALLY RENDER UI BASED ON PILLAR SELECTION
    # ----------------------------------------------------
    if u_content_type == "Product Showcase (Pillar A/C)":
        st.subheader("Product Ad Details")
        
        # --- PRODUCT IMAGE UPLOADER ---
        u_file = st.file_uploader("Product Image (REQUIRED)", type=["png","jpg","jpeg"]) 
        # --- END UPLOADER ---
        
        u_model = st.text_input("Product Name", "Walden Dresser")
        u_price = st.text_input("Price / Discount", "Ksh 49,900") 
        u_contact = st.text_input("Contact Info", "0710 895 737")
        u_style = st.selectbox("Template", list(TEMPLATES.keys()))
        u_music = st.selectbox("Music", list(MUSIC_TRACKS.keys()))
        u_animation_style = "Simple Fade" # Placeholder
        btn_ad = st.button(f"Generate {u_duration}s Product Ad", type="primary")
        
    else: # Content Video (Pillar B)
        st.subheader("Content Details")
        
        # --- BACKGROUND IMAGE UPLOADER (Optional) ---
        u_file = st.file_uploader("Background Image (Optional)", type=["png","jpg","jpeg"]) 
        # --- END UPLOADER ---
        
        u_model = st.text_input("Product/Topic for Tip", "Nursery safety")
        u_type = st.radio("Tip Category", ["DIY Tips", "Furniture Tips", "Interior Design Tips", "Maintenance Tips"])
        
        if st.button(f"Generate Tips for '{u_model}'", key="tip_gen_btn"):
            u_tips_text = generate_tips(u_type, u_model)
            st.session_state['generated_tips'] = u_tips_text
        
        u_caption_text = st.text_area("Final Caption/Tips", 
                                        value=st.session_state.get('generated_tips'),
                                        help="First line is the title/hook. Bullet points are the animated tips.")
        
        u_animation_style = st.selectbox(
            "Text Animation Style", 
            ["Smooth Fade (All at Once)", "Typewriter (Sequential Reveal)", "Block Reveal (Sequential Block Fade)"],
            index=0,
            help="Select the style for revealing the tips after the title fades out."
        )
        
        u_contact = st.text_input("Contact/URL (Small Footer)", "sm.co.ke")
        u_style = st.selectbox("Template", ["SM Classic", "Gold Diagonal"])
        u_music = st.selectbox("Music", list(MUSIC_TRACKS.keys()))
        
        u_price = "" 
        
        btn_ad = st.button(f"Generate {u_duration}s Content Video", type="primary")


# Video Ad Generation Logic
if btn_ad:
    global DURATION
    DURATION = u_duration 
    
    status = st.status(f"Creating your {u_content_type} video...", expanded=True)

    # 1. Process image (Crucial step for Product Showcase)
    product_img = None
    if u_file:
        status.update(label="Processing image...")
        raw = Image.open(u_file).convert("RGBA")
        
        if u_content_type == "Product Showcase (Pillar A/C)":
            # Only remove background for product ads
            product_img = process_image_pro(raw)
        else:
            # Use raw image as background for content videos
            product_img = raw
            
        st.image(product_img, "Processed Image", width=200)

    # 1.1 Check for Product Showcase image requirement
    if u_content_type == "Product Showcase (Pillar A/C)" and not u_file:
        st.error("Product Showcase requires a Product Image upload.")
        status.update(label="Failed", state="error")
        st.stop()


    # 2. AI hook + smart layout mapping
    status.update(label="AI determining layout...")
    
    if u_content_type == "Product Showcase (Pillar A/C)":
        hook, layout = get_data_groq(product_img, u_model)
    else: # Content Video Logic
        # For content videos, we manually set the layout to a fixed, centered version
        hook = u_caption_text.split('\n')[0].strip()
        fixed_layout = {'logo': 'LOGO_TOP', 'product': 'PRODUCT_CENTER', 'caption': 'CAPTION_HEADLINE', 'contact': 'CONTACT_FOOTER'}
        # Recalculate fixed map using grid for consistency
        CAPTION_X, CAPTION_W = calc_grid_x(10)
        PRODUCT_X, PRODUCT_W = calc_grid_x(10) 
        CONTACT_X, CONTACT_W = calc_grid_x(10)
        LOGO_X, LOGO_W = GRID_GUTTER, calc_grid_x(4)[1]

        layout_map = {
            "LOGO_TOP": {"x": LOGO_X, "y": 50, "w": LOGO_W, "h": 100}, 
            "PRODUCT_CENTER": {"x": PRODUCT_X, "y": 250, "w": PRODUCT_W, "h": 600}, 
            "CAPTION_HEADLINE": {"x": CAPTION_X, "y": 150, "w": CAPTION_W, "h": 120}, 
            "CONTACT_FOOTER": {"x": CONTACT_X, "y": 1200, "w": CONTACT_W, "h": 60}
        }
        layout = [layout_map[block_name].copy() | {'role': role} for role, block_name in fixed_layout.items() if role in ['logo', 'product', 'caption', 'contact']]

    st.write(f"**Video Hook:** {hook}")
    
    # 2.5 Load Logo
    logo_img = get_cached_logo(LOGO_URL, WIDTH, HEIGHT)

    # 3. Render frames
    status.update(label="Animating frames...")
    texts = {"caption": hook, "price": u_price, "contact": u_contact}
    
    content_pillar_key = u_content_type.split(' ')[0] # "Product" or "Content"
    if content_pillar_key == "Content":
        texts["full_tips"] = u_caption_text
    
    frames = [create_frame(i/FPS, product_img, layout, texts, u_style, logo_img, content_pillar_key, u_animation_style) for i in range(FPS*DURATION)]
    clip = ImageSequenceClip(frames, fps=FPS)

    # 4. Add music & 5. Export
    status.update(label="Adding music & exporting...")
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

    output_filename = f"SM_{content_pillar_key}_{u_model.replace(' ', '_')}_{DURATION}s.mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        final.write_videofile(tmp.name, codec="libx264", audio_codec="aac", fps=FPS, logger=None, verbose=False)
        st.video(tmp.name)
        with open(tmp.name, "rb") as f:
            st.download_button("Download Video", f, output_filename, "video/mp4")
        os.unlink(tmp.name)

    status.update(label="Done! Your ad is ready", state="complete")

st.caption("AdGen EVO by Grok × Streamlit – 2025 Edition")
