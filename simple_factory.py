import streamlit as st
import io, requests, math, tempfile, base64, json, random, time, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip

# --- GLOBAL CONFIGURATION ---
st.set_page_config(page_title="AdGen Pro: Brand Edition", layout="wide", page_icon="🎬")

# --- CONSTANTS ---
WIDTH, HEIGHT = 720, 1280
FPS = 30
DURATION = 6
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

# More reliable royalty-free music tracks (using archive.org for better stability)
MUSIC_TRACKS = {
    "Upbeat Pop (Stable)": "https://archive.org/download/Bensound_-_Jazzy_Frenchy/Bensound_-_Jazzy_Frenchy.mp3",
    "Luxury Chill (Stable)": "https://archive.org/download/bensound-adaytoremember/bensound-adaytoremember.mp3",
    "High Energy (Stable)": "https://archive.org/download/bensound-sweet/bensound-sweet.mp3",
    "Acoustic Breeze (Stable)": "https://archive.org/download/bensound-acousticbreeze/bensound-acousticbreeze.mp3"
}

# --- API SETUP ---
if "mistral_key" not in st.secrets:
    st.error("🚨 Missing Secret: Add `mistral_key` to your .streamlit/secrets.toml")
    st.stop()

HEADERS = {"Authorization": f"Bearer {st.secrets['mistral_key']}", "Content-Type": "application/json"}

# --- STABLE LOCAL FONT LOADER ---
# Use system fonts (most reliable on Streamlit Cloud's Linux environment)
def get_font(size):
    """
    Tries to load standard system fonts available in Streamlit Cloud (Linux).
    Falls back to default if nothing is found.
    """
    possible_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "arial.ttf", # For local Windows testing
        "Arial.ttf", # For local Mac testing
    ]
    
    for path in possible_fonts:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
            
    # Absolute fallback to Pillow's built-in default font
    try:
        return ImageFont.load_default(size=size) # For Pillow >= 10.0.0
    except:
        return ImageFont.load_default() # For older Pillow versions

# --- MATH & ANIMATION ---
def ease_out_elastic(t):
    """Bouncy animation effect."""
    c4 = (2 * math.pi) / 3
    if t == 0: return 0
    if t == 1: return 1
    return math.pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

def linear_fade(t, start, duration):
    """Helper for fading elements in."""
    if t < start: return 0.0
    if t > start + duration: return 1.0
    return (t - start) / duration

# --- TEMPLATES (Updated with SM Interiors Brand Colors) ---
TEMPLATES = {
    "SM Interiors Brand": { # NEW BRAND TEMPLATE
        "bg_grad": ["#4C3B30", "#332A22"], # Deep brown, slightly lighter brown
        "accent": "#D2A544", # Brand Gold
        "text": "#FFFFFF",   # White text
        "price_bg": "#D2A544", # Gold Price background
        "price_text": "#000000" # Black text on gold
    },
    "Midnight Luxury": {
        "bg_grad": ["#0f0c29", "#302b63", "#24243e"],
        "accent": "#FFD700", "text": "#FFFFFF", 
        "price_bg": "#FFD700", "price_text": "#000000"
    },
    "Clean Corporate": {
        "bg_grad": ["#ffffff", "#dfe9f3"],
        "accent": "#2980b9", "text": "#2c3e50", 
        "price_bg": "#2980b9", "price_text": "#ffffff"
    },
    "Neon Vibrant": {
        "bg_grad": ["#434343", "#000000"],
        "accent": "#00ff99", "text": "#ffffff", 
        "price_bg": "#00ff99", "price_text": "#000000"
    }
}

# --- AI LOGIC (WITH RETRY & FALLBACK) ---
def ask_mistral_safe(payload, retries=3):
    """Robust API caller that handles 429 errors automatically."""
    base_delay = 2
    for attempt in range(retries):
        try:
            r = requests.post("https://api.mistral.ai/v1/chat/completions", json=payload, headers=HEADERS, timeout=20)
            
            if r.status_code == 429:
                wait = base_delay * (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait)
                continue
                
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt == retries - 1:
                return None
    return None

def get_layout_safe(model):
    prompt = f"""
    Canvas: {WIDTH}x{HEIGHT}.
    Roles: 'logo', 'product', 'price', 'contact', 'caption'.
    Product: {model}
    Return JSON list: {{ "role": "...", "x": int, "y": int, "w": int, "h": int }}
    NO MARKDOWN.
    """
    payload = {
        "model": "mistral-large-latest",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"} 
    }
    
    # Hardcoded Fallback Layout (Used if AI fails)
    fallback = [
        {"role": "logo", "x": 50, "y": 50, "w": 200, "h": 100},
        {"role": "product", "x": 60, "y": 200, "w": 600, "h": 600},
        {"role": "caption", "x": 60, "y": 850, "w": 600, "h": 100},
        {"role": "price", "x": 160, "y": 1000, "w": 400, "h": 120},
        {"role": "contact", "x": 60, "y": 1180, "w": 600, "h": 60}
    ]
    
    resp = ask_mistral_safe(payload)
    if not resp: return fallback
    
    try:
        data = json.loads(resp)
        if "layout" in data: return data["layout"]
        if isinstance(data, list): return data
        return fallback
    except:
        return fallback

def get_hook_safe(img_b64):
    payload = {
        "model": "pixtral-12b-2409",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": "Write a 5-word explosive hook for a TikTok ad for this item."},
            {"type": "image_url", "image_url": f"data:image/png;base64,{img_b64}"}
        ]}],
        "max_tokens": 50
    }
    resp = ask_mistral_safe(payload)
    return resp.replace('"', '') if resp else "Don't Miss This Deal! 🔥"

# --- RENDERING ENGINE ---
def draw_wrapped_text(draw, text, box, font, color):
    """Fits text inside a box automatically."""
    lines = []
    words = text.split()
    line = ""
    for w in words:
        test_line = line + " " + w if line else w
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] > box['w']:
            lines.append(line)
            line = w
        else:
            line = test_line
    lines.append(line)
    
    total_h = sum([draw.textbbox((0,0), l, font=font)[3] for l in lines])
    current_y = box['y'] + (box['h'] - total_h) // 2
    
    for l in lines:
        bbox = draw.textbbox((0,0), l, font=font)
        lx = box['x'] + (box['w'] - bbox[2]) // 2
        draw.text((lx, current_y), l, font=font, fill=color)
        current_y += bbox[3] + 10

def create_frame(t, img, boxes, data, template_name):
    T = TEMPLATES[template_name]
    
    # 1. Background Gradient
    canvas = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(canvas)
    
    # Draw gradient manually
    colors = T["bg_grad"]
    steps = len(colors) - 1
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        idx = min(int(ratio * steps), steps - 1)
        local_ratio = (ratio * steps) - idx
        c1 = tuple(int(colors[idx][i:i+2], 16) for i in (1, 3, 5))
        c2 = tuple(int(colors[idx+1][i:i+2], 16) for i in (1, 3, 5))
        r = int(c1[0] + (c2[0] - c1[0]) * local_ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * local_ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * local_ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    
    # 2. Parallax Blur Background
    if img:
        bg_w = int(WIDTH * 1.1)
        bg_h = int(HEIGHT * 0.6)
        bg_img = img.resize((bg_w, bg_h)).filter(ImageFilter.GaussianBlur(15))
        off_x = int((WIDTH - bg_w) // 2 + math.sin(t) * 15)
        
        bg_alpha = int(255 * 0.3 * linear_fade(t, 0, 1))
        bg_img.putalpha(bg_alpha)
        canvas.paste(bg_img, (off_x, 200), bg_img)

    # 3. Render Elements
    for b in boxes:
        role = b["role"]
        
        if role == "logo":
            try:
                logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
                aspect = logo.width / logo.height
                nw = int(b['h'] * aspect)
                logo = logo.resize((nw, b['h']), Image.LANCZOS)
                canvas.paste(logo, (b['x'], b['y']), logo)
            except: pass # Skip logo if fetch fails

        elif role == "product":
            # Elastic Pop
            scale = ease_out_elastic(max(0, t - 0.5))
            scale = min(max(scale, 0), 1.0) # Clamp
            
            if scale > 0.01:
                pw, ph = int(b['w'] * scale), int(b['h'] * scale)
                p_img = img.resize((pw, ph), Image.LANCZOS)
                
                # Shadow
                shadow = p_img.copy()
                shadow_data = [(0,0,0, int(a*0.3)) for r,g,b,a in p_img.getdata()]
                shadow.putdata(shadow_data)
                shadow = shadow.filter(ImageFilter.GaussianBlur(10))
                
                cx = b['x'] + (b['w'] - pw) // 2
                cy = b['y'] + (b['h'] - ph) // 2
                canvas.paste(shadow, (cx+10, cy+10), shadow)
                canvas.paste(p_img, (cx, cy), p_img)

        elif role == "price":
            # Slide Up
            prog = linear_fade(t, 2.0, 0.5)
            if prog > 0:
                y_off = (1 - ease_out_elastic(prog)) * 150
                draw.rounded_rectangle(
                    [b['x'], b['y'] + y_off, b['x']+b['w'], b['y']+b['h'] + y_off], 
                    radius=20, fill=T["price_bg"]
                )
                font = get_font(60)
                text_w = draw.textlength(data["price"], font=font)
                tx = b['x'] + (b['w'] - text_w) // 2
                ty = b['y'] + (b['h'] - 60) // 2 + y_off - 5
                draw.text((tx, ty), data["price"], fill=T["price_text"], font=font)

        elif role == "caption":
            if t > 1.5:
                font = get_font(45)
                draw_wrapped_text(draw, data["caption"], b, font, T["accent"])

        elif role == "contact":
            if t > 3.0:
                font = get_font(28)
                draw_wrapped_text(draw, data["contact"], b, font, T["text"])

    # 4. Vignette Overlay (Cinematic Touch)
    overlay = Image.new('RGBA', (WIDTH, int(HEIGHT*0.3)), (0,0,0,0))
    odraw = ImageDraw.Draw(overlay)
    for y in range(overlay.height):
        alpha = int(180 * (y / overlay.height))
        odraw.line([(0, y), (WIDTH, y)], fill=(0,0,0, alpha))
    canvas.paste(overlay, (0, HEIGHT - overlay.height), overlay)

    return np.array(canvas)

# --- MAIN APP UI ---
with st.sidebar:
    st.title("🛠️ Config")
    u_file = st.file_uploader("Product Image", type=["png", "jpg", "jpeg"])
    u_model = st.text_input("Product Name", "Walden Media Console") # Pre-filled
    u_price = st.text_input("Price", "Ksh 49,900") # Pre-filled
    u_contact = st.text_input("CTA", "0710895737") # Pre-filled
    u_template = st.selectbox("Style", list(TEMPLATES.keys()), index=0) # Default to brand
    u_music = st.selectbox("Music", list(MUSIC_TRACKS.keys()))
    btn_run = st.button("🚀 Generate Video", type="primary")

st.title("🎬 AdGen Pro: Brand-Ready Video Factory")

if btn_run and u_file:
    status = st.status("Processing...", expanded=True)
    
    # 1. Load Image
    img = Image.open(u_file).convert("RGBA")
    
    # 2. AI Operations (With Safety Nets)
    status.write("🧠 Generating Hook & Layout...")
    buf = io.BytesIO(); img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    
    # Parallel-ish fetching (Sequence in Streamlit)
    caption = get_hook_safe(b64)
    layout = get_layout_safe(u_model)
    
    status.write(f"✅ Hook: {caption}")
    
    # 3. Render Frames
    status.write("🎨 Rendering frames...")
    frames = []
    data = {"caption": caption, "price": u_price, "contact": u_contact}
    
    bar = status.progress(0)
    total = FPS * DURATION
    for i in range(total):
        frames.append(create_frame(i/FPS, img, layout, data, u_template))
        bar.progress((i+1)/total)
        
    # 4. Encode Video
    status.write("🎼 Mixing Audio & Encoding...")
    clip = ImageSequenceClip(frames, fps=FPS)
    
    try:
        # Audio Handling
        aud_url = MUSIC_TRACKS[u_music]
        r_aud = requests.get(aud_url)
        # Ensure the temp file has the correct extension for MoviePy
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tf: 
            tf.write(r_aud.content)
            tf_path = tf.name
        
        audioclip = AudioFileClip(tf_path).subclip(0, DURATION).audio_fadeout(1)
        final_clip = clip.set_audio(audioclip)
    except Exception as e:
        st.warning(f"Audio failed ({e}), rendering silent video.")
        print(f"MoviePy Audio Error Details: {e}") # Print full error for debugging
        final_clip = clip
        
    # Save output
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as vf:
        final_clip.write_videofile(vf.name, codec="libx264", audio_codec="aac", logger=None)
        out_path = vf.name
        
    status.update(label="✨ Done!", state="complete", expanded=False)
    
    # 5. Display
    col1, col2 = st.columns([2, 1])
    with col1:
        st.video(out_path)
    with col2:
        st.success("Ad Generated!")
        st.info(f"Hook: {caption}")
        with open(out_path, "rb") as f:
            st.download_button("⬇️ Download MP4", f, "ad_brand_ready.mp4")

elif btn_run:
    st.error("Upload an image first!")
