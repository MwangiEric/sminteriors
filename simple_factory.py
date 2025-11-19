import streamlit as st
import io, requests, math, tempfile, base64, json, random, time, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip
from rembg import remove

# --- GLOBAL CONFIGURATION ---
st.set_page_config(page_title="AdGen EVO: Dynamic Templates", layout="wide", page_icon="✨")

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

# Groq API Endpoint
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {st.secrets['groq_key']}",
    "Content-Type": "application/json"
}

# --- IMAGE PROCESSING ENGINE (Rembg + Enhance) ---
def process_image_pro(input_image):
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
    c4 = (2 * math.pi) / 3
    return math.pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1 if t > 0 and t < 1 else (0 if t<=0 else 1)

def linear_fade(t, start, duration):
    if t < start: return 0.0
    if t > start + duration: return 1.0
    return (t - start) / duration

# --- TEMPLATES (NEW: Inspired by user images, using brand colors) ---
BRAND_PRIMARY = "#4C3B30" # Deep Brown
BRAND_ACCENT = "#D2A544"  # Gold
BRAND_TEXT_LIGHT = "#FFFFFF" # White
BRAND_TEXT_DARK = "#000000"  # Black

TEMPLATES = {
    "SM Interiors Basic": { # Your original clean template
        "bg_grad": [BRAND_PRIMARY, "#2a201b"], 
        "accent": BRAND_ACCENT, "text": BRAND_TEXT_LIGHT, 
        "price_bg": BRAND_ACCENT, "price_text": BRAND_TEXT_DARK,
        "graphic_type": "none"
    },
    "Brand Diagonal Slice": { # Inspired by Image 1 (yellow stripes)
        "bg_grad": [BRAND_PRIMARY, "#3e2e24"], # Slightly different brown gradient
        "accent": BRAND_ACCENT, "text": BRAND_TEXT_LIGHT, 
        "price_bg": BRAND_ACCENT, "price_text": BRAND_TEXT_DARK,
        "graphic_type": "diagonal",
        "graphic_color": BRAND_ACCENT # Gold stripes
    },
    "Brand Circular Flow": { # Inspired by Image 2 & 3 (orange circles)
        "bg_grad": [BRAND_PRIMARY, "#332A22"], 
        "accent": BRAND_ACCENT, "text": BRAND_TEXT_LIGHT, 
        "price_bg": BRAND_ACCENT, "price_text": BRAND_TEXT_DARK,
        "graphic_type": "circular",
        "graphic_color": BRAND_ACCENT # Gold circles
    },
    "Brand Split Panel": { # Inspired by Image 4 (blue & yellow split)
        "bg_grad": [BRAND_PRIMARY, BRAND_PRIMARY], # Solid background
        "accent": BRAND_TEXT_LIGHT, "text": BRAND_TEXT_LIGHT, 
        "price_bg": BRAND_ACCENT, "price_text": BRAND_TEXT_DARK,
        "graphic_type": "split",
        "graphic_color": BRAND_ACCENT # Gold bottom panel
    }
}

# --- GROQ AI LOGIC ---
def ask_groq(payload):
    try:
        r = requests.post(GROQ_URL, json=payload, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Groq Error: {e}")
        return None

def get_data_groq(img_b64, model_name):
    # 1. Vision Task (Llama 3.2 Vision Preview) for caption
    p_hook = {
        "model": "llama-3.2-11b-vision-preview",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": f"Write a 4-word catchy luxury ad hook for this furniture model '{model_name}'."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
        ]}],
        "temperature": 0.7,
        "max_tokens": 30
    }
    
    # 2. Logic Task (Llama 3 70B) for layout
    p_layout = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "You are a JSON layout engine for 720x1280 video. Output JSON only."},
            {"role": "user", "content": f"Create a JSON list of objects for layout. Each object must have 'role', 'x', 'y', 'w', 'h'. Roles needed: logo, product, price, contact, caption. Ensure all objects are visible and do not significantly overlap. Prioritize the product in the center. Product: {model_name}."}
        ],
        "response_format": {"type": "json_object"}
    }

    caption = ask_groq(p_hook)
    caption = caption.replace('"', '') if caption else "Elevate Your Space" # Better default
    
    layout_raw = ask_groq(p_layout)
    
    # Fallback Layout (if Groq fails or returns invalid JSON)
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
        
        # Simple validation: ensure it's a list and has required roles
        if isinstance(final_layout, list) and all("role" in item for item in final_layout):
            return caption, final_layout
        else:
            return caption, default_layout
    except:
        return caption, default_layout

# --- RENDERING ---
def draw_wrapped_text(draw, text, box, font, color, align="center"):
    """Improved text wrapping with alignment"""
    lines = []
    words = text.split()
    line = ""
    for w in words:
        test_line = line + " " + w if line else w
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] > box['w'] and line: # Check width, but only if 'line' isn't empty
            lines.append(line)
            line = w
        else:
            line = test_line
    lines.append(line)
    
    current_y = box['y'] # Start Y
    
    for l in lines:
        bbox = draw.textbbox((0,0), l, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        if align == "center":
            lx = box['x'] + (box['w'] - text_width) // 2
        elif align == "left":
            lx = box['x']
        elif align == "right":
            lx = box['x'] + box['w'] - text_width
        
        draw.text((lx, current_y), l, font=font, fill=color)
        current_y += text_height + 5 # Line spacing

def create_frame(t, img, boxes, texts, tpl_name):
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
        # Inspired by Image 1: Yellow diagonal stripes
        diag_alpha = int(255 * linear_fade(t, 0.5, 1.0)) # Fade in
        for i in range(-WIDTH, WIDTH + HEIGHT, 50): # Diagonal lines
            draw.line([(i, 0), (i + HEIGHT, HEIGHT)], fill=(graphic_color_rgb[0], graphic_color_rgb[1], graphic_color_rgb[2], diag_alpha), width=10)
        
        # Add a solid diagonal block behind text (Image 1 style)
        if t > 0.8:
            solid_alpha = int(255 * linear_fade(t, 1.0, 0.5))
            draw.polygon([
                (0, 100), (WIDTH, 0), (WIDTH, 200), (0, 300)
            ], fill=(graphic_color_rgb[0], graphic_color_rgb[1], graphic_color_rgb[2], solid_alpha))


    elif T["graphic_type"] == "circular" and graphic_color_rgb:
        # Inspired by Image 2 & 3: Orange circles
        circle_alpha = int(255 * linear_fade(t, 0.8, 0.7))
        # Large bottom-right circle
        circle_size = int(WIDTH * 1.5 * ease_out_elastic(max(0, t - 0.5)))
        cx, cy = int(WIDTH * 0.8), int(HEIGHT * 0.7)
        draw.ellipse([cx - circle_size//2, cy - circle_size//2, cx + circle_size//2, cy + circle_size//2], 
                     fill=(graphic_color_rgb[0], graphic_color_rgb[1], graphic_color_rgb[2], int(circle_alpha * 0.6)))
        
        # Smaller top-left circle
        circle_size_small = int(WIDTH * 0.7 * ease_out_elastic(max(0, t - 1.0)))
        cx_s, cy_s = int(WIDTH * 0.2), int(HEIGHT * 0.3)
        draw.ellipse([cx_s - circle_size_small//2, cy_s - circle_size_small//2, cx_s + circle_size_small//2, cy_s + circle_size_small//2], 
                     fill=(graphic_color_rgb[0], graphic_color_rgb[1], graphic_color_color[2], int(circle_alpha * 0.4)))


    elif T["graphic_type"] == "split" and graphic_color_rgb:
        # Inspired by Image 4: Blue background with yellow bottom strip
        split_height = int(HEIGHT * 0.3 * ease_out_elastic(max(0, t - 1.0))) # Animate height
        draw.rectangle([0, HEIGHT - split_height, WIDTH, HEIGHT], fill=T["graphic_color"]) # Bottom bar
        
        # Small decorative dots/pattern top-right (Image 4 style)
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
                # Ensure price text is dark if on light background, light if on dark background
                price_text_color = T["price_text"] 
                
                draw_wrapped_text(draw, texts["price"], 
                                  {'x': b['x'], 'y': b['y']+off_y, 'w': b['w'], 'h': b['h']}, 
                                  f, price_text_color)
                

        elif role == "caption":
            if t > 1.0:
                f = get_font(50)
                draw_wrapped_text(draw, texts["caption"], b, f, T["accent"])

        elif role == "contact":
            if t > 2.5:
                f = get_font(30)
                draw_wrapped_text(draw, texts["contact"], b, f, T["text"]) # Align center by default
                
        elif role == "logo":
             try:
                logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
                logo = logo.resize((b['w'], b['h']), Image.LANCZOS)
                # Apply a slight shadow to logo to make it pop on complex backgrounds
                logo_shadow = Image.new('RGBA', logo.size, (0,0,0,0))
                logo_shadow_draw = ImageDraw.Draw(logo_shadow)
                logo_shadow_draw.ellipse([5,5,logo.width-5,logo.height-5], fill=(0,0,0,100)) # Simple oval shadow
                logo_shadow = logo_shadow.filter(ImageFilter.GaussianBlur(10))

                canvas.paste(logo_shadow, (b['x']+5, b['y']+5), logo_shadow) # Offset shadow
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
with st.sidebar:
    st.header("⚡ Turbo Settings")
    u_file = st.file_uploader("Product Image", type=["jpg", "png"])
    u_model = st.text_input("Product Name", "Walden Media Console")
    u_price = st.text_input("Price", "Ksh 49,900")
    u_contact = st.text_input("Contact Info", "0710895737")
    
    # Select from NEW templates
    u_style = st.selectbox("Design Template", list(TEMPLATES.keys()), index=0) 
    u_music = st.selectbox("Background Music", list(MUSIC_TRACKS.keys()))
    btn = st.button("🚀 Generate Ad Video", type="primary")

st.title("AdGen EVO: Dynamic Brand Ads")

if btn and u_file:
    status = st.status("Initializing AI & Design Engine...", expanded=True)
    
    # 1. Background Removal & Enhancement
    status.write("🚿 Cleaning & Enhancing Product Image...")
    raw_img = Image.open(u_file).convert("RGBA")
    pro_img = process_image_pro(raw_img)
    st.image(pro_img, caption="AI Processed Product", width=200)
    
    # 2. Groq AI for Hook & Layout
    status.write("🚀 Groq AI: Crafting Ad Copy & Layout...")
    buf = io.BytesIO(); pro_img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    
    start_time = time.time()
    caption, layout = get_data_groq(b64, u_model)
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
    except Exception as e: 
        st.warning(f"Audio failed ({e}), rendering silent video. Ensure you select a valid track.")
        print(f"Audio Error: {e}")
        fclip = clip

    # 5. Finalize Video
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as vf:
        fclip.write_videofile(vf.name, codec="libx264", audio_codec="aac", logger=None)
        final_path = vf.name

    status.update(label="✨ Ad Video Ready!", state="complete", expanded=False)
    st.video(final_path)
    with open(final_path, "rb") as f:
        st.download_button("Download Ad", f, "ad_dynamic_brand.mp4")

elif btn:
    st.error("Please upload a product image to start!")
