import streamlit as st
import io, requests, math, tempfile, base64, json, random, time, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeAudioClip

# --- GLOBAL CONFIG ---
st.set_page_config(page_title="S&M Canva Factory Pro", layout="wide", page_icon="🎬")

# --- ASSETS & CONSTANTS ---
WIDTH, HEIGHT = 720, 1280
FPS = 30
DURATION = 6
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

# Royalty-free background tracks (Hosted MP3 examples)
MUSIC_TRACKS = {
    "Upbeat Pop": "https://cdn.pixabay.com/audio/2024/05/24/audio_16709e7558.mp3",
    "Luxury Chill": "https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3",
    "High Energy": "https://cdn.pixabay.com/audio/2024/01/16/audio_e2b992254f.mp3"
}

if "mistral_key" not in st.secrets:
    st.error("🚨 Missing Secret: Add `mistral_key` to your .streamlit/secrets.toml")
    st.stop()

HEADERS = {"Authorization": f"Bearer {st.secrets['mistral_key']}", "Content-Type": "application/json"}

# --- ROBUST FONT LOADER ---
@st.cache_resource
def load_fonts():
    """Loads a nice Google Font dynamically to ensure it works on Cloud & Local"""
    font_url = "https://github.com/google/fonts/raw/main/ofl/oswald/Oswald-Bold.ttf"
    try:
        r = requests.get(font_url, timeout=5)
        return io.BytesIO(r.content)
    except:
        return None # Fallback to default

FONT_BYTES = load_fonts()

def get_font(size):
    if FONT_BYTES:
        return ImageFont.truetype(FONT_BYTES, size)
    else:
        return ImageFont.load_default()

# --- ADVANCED ANIMATION MATH ---
def ease_out_elastic(t):
    """Elastic bounce effect for popping elements"""
    c4 = (2 * math.pi) / 3
    if t == 0: return 0
    if t == 1: return 1
    return math.pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

def linear_fade(t, start, duration):
    """Returns 0.0 to 1.0 alpha based on time"""
    if t < start: return 0.0
    if t > start + duration: return 1.0
    return (t - start) / duration

# --- TEMPLATES (Refined) ---
TEMPLATES = {
    "Midnight Luxury": {
        "bg_grad": ["#0f0c29", "#302b63", "#24243e"],
        "accent": "#FFD700", # Gold
        "text": "#FFFFFF",
        "price_bg": "#FFD700",
        "price_text": "#000000",
        "font_scale": 1.0
    },
    "Clean Corporate": {
        "bg_grad": ["#ffffff", "#dfe9f3"],
        "accent": "#2980b9", # Blue
        "text": "#2c3e50",
        "price_bg": "#2980b9",
        "price_text": "#ffffff",
        "font_scale": 0.9
    },
    "Neon Vibrant": {
        "bg_grad": ["#434343", "#000000"],
        "accent": "#00ff99", # Neon Green
        "text": "#ffffff",
        "price_bg": "#00ff99",
        "price_text": "#000000",
        "font_scale": 1.1
    }
}

# --- AI HELPERS ---
def ask_mistral(payload):
    try:
        r = requests.post("https://api.mistral.ai/v1/chat/completions", json=payload, headers=HEADERS, timeout=30)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        st.error(f"AI Error: {e}")
        st.stop()

@st.cache_data(show_spinner=False)
def get_smart_layout(model, price):
    """Asks LLM for optimal layout coordinates"""
    prompt = f"""
    Canvas size: {WIDTH}x{HEIGHT}.
    I need a JSON layout for a vertical video ad.
    Roles: 'logo', 'product', 'price', 'contact', 'caption'.
    Product: {model}
    
    Rules:
    1. Logo: Top center or top left.
    2. Product: Large, center/upper-center.
    3. Caption: Just below product.
    4. Price: Big badge near bottom.
    5. Contact: Very bottom.
    
    Return JSON list of objects: {{ "role": "...", "x": int, "y": int, "w": int, "h": int }}
    NO MARKDOWN. ONLY JSON.
    """
    payload = {
        "model": "mistral-large-latest",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"} 
    }
    try:
        resp = ask_mistral(payload)
        data = json.loads(resp)
        # Mistral sometimes wraps it in a wrapper key
        if "layout" in data: return data["layout"]
        if isinstance(data, list): return data
        # Fallback if structure is weird
        raise ValueError("Invalid JSON")
    except:
        # Robust Fallback Layout
        return [
            {"role": "logo", "x": 40, "y": 40, "w": 200, "h": 100},
            {"role": "product", "x": 60, "y": 180, "w": 600, "h": 600},
            {"role": "caption", "x": 60, "y": 800, "w": 600, "h": 150},
            {"role": "price", "x": 160, "y": 1000, "w": 400, "h": 120},
            {"role": "contact", "x": 60, "y": 1180, "w": 600, "h": 60}
        ]

@st.cache_data(show_spinner=False)
def get_hook(img_b64):
    payload = {
        "model": "pixtral-12b-2409",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": "Write a 5-word explosive hook for a TikTok ad for this item."},
            {"type": "image_url", "image_url": f"data:image/png;base64,{img_b64}"}
        ]}],
        "max_tokens": 50
    }
    return ask_mistral(payload).replace('"', '')

# --- GRAPHICS ENGINE ---

def draw_gradient(draw, colors, h):
    # Simple linear interpolation between 2 or 3 colors
    # Optimisation: We compute this once per frame type if needed, but simple math is fast enough
    steps = len(colors) - 1
    for y in range(h):
        ratio = y / h
        idx = int(ratio * steps)
        idx = min(idx, steps - 1)
        local_ratio = (ratio * steps) - idx
        
        c1 = tuple(int(colors[idx][i:i+2], 16) for i in (1, 3, 5))
        c2 = tuple(int(colors[idx+1][i:i+2], 16) for i in (1, 3, 5))
        
        r = int(c1[0] + (c2[0] - c1[0]) * local_ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * local_ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * local_ratio)
        
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

def draw_wrapped_text(draw, text, box, font, color, align="center"):
    """Pro-level text wrapper"""
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
        lw = bbox[2]
        lx = box['x'] + (box['w'] - lw) // 2
        draw.text((lx, current_y), l, font=font, fill=color)
        current_y += bbox[3] + 10

def create_frame(t, img, boxes, data, template_name):
    T = TEMPLATES[template_name]
    
    # 1. Base Canvas
    canvas = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(canvas)
    draw_gradient(draw, T["bg_grad"], HEIGHT)
    
    # 2. Parallax Background (Blurred)
    if img:
        bg_scale = 1.1
        bg_w, bg_h = int(WIDTH * bg_scale), int(HEIGHT * 0.6 * bg_scale)
        bg_img = img.resize((bg_w, bg_h)).filter(ImageFilter.GaussianBlur(15))
        
        # Parallax Math
        offset_x = int((WIDTH - bg_w) // 2 + (math.sin(t) * 20))
        offset_y = 200
        
        # Fade in background
        bg_alpha = int(255 * 0.4 * linear_fade(t, 0, 1))
        bg_img.putalpha(bg_alpha)
        canvas.paste(bg_img, (offset_x, offset_y), bg_img)

    # 3. Process Elements from JSON Layout
    for b in boxes:
        role = b["role"]
        
        if role == "logo":
            # Download logo once in main loop ideally, but cached by OS here usually fine
            try:
                logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
                aspect = logo.width / logo.height
                nh = b['h']
                nw = int(nh * aspect)
                logo = logo.resize((nw, nh), Image.LANCZOS)
                canvas.paste(logo, (b['x'], b['y']), logo)
            except: pass

        elif role == "product":
            # Scale animation (Elastic pop at 0.5s)
            scale = ease_out_elastic(max(0, t - 0.5)) 
            scale = min(scale, 1.0) # Clamp
            
            if scale > 0.01:
                pw, ph = int(b['w'] * scale), int(b['h'] * scale)
                p_img = img.resize((pw, ph), Image.LANCZOS)
                
                # Shadow
                shadow = p_img.copy()
                # Make shadow black
                shadow_data = shadow.getdata()
                new_data = [(0,0,0, int(a*0.3)) for r,g,b,a in shadow_data]
                shadow.putdata(new_data)
                shadow = shadow.filter(ImageFilter.GaussianBlur(10))
                
                # Center logic
                cx = b['x'] + (b['w'] - pw) // 2
                cy = b['y'] + (b['h'] - ph) // 2
                
                canvas.paste(shadow, (cx+15, cy+15), shadow)
                canvas.paste(p_img, (cx, cy), p_img)

        elif role == "caption":
            # Typewriter effect
            if t > 1.5:
                font = get_font(50)
                draw_wrapped_text(draw, data["caption"], b, font, T["accent"])

        elif role == "price":
            # Slide up from bottom at 2.0s
            slide_prog = linear_fade(t, 2.0, 0.5)
            if slide_prog > 0:
                y_off = (1 - ease_out_elastic(slide_prog)) * 200
                
                # Draw Badge
                draw.rounded_rectangle(
                    [b['x'], b['y'] + y_off, b['x']+b['w'], b['y']+b['h'] + y_off], 
                    radius=20, fill=T["price_bg"]
                )
                # Draw Text
                font = get_font(70)
                text_w = draw.textlength(data["price"], font=font)
                tx = b['x'] + (b['w'] - text_w) // 2
                ty = b['y'] + (b['h'] - 70) // 2 + y_off - 5
                draw.text((tx, ty), data["price"], fill=T["price_text"], font=font)

        elif role == "contact":
            if t > 3.0:
                font = get_font(30)
                draw_wrapped_text(draw, data["contact"], b, font, T["text"])

    # 4. Cinematic Vignette (Top Tier Polish)
    # Creates a subtle darkening at the edges
    # (Simulated with a radial gradient logic simply by drawing dark corners)
    # For performance, we just darken the bottom heavily for text readability
    
    # Gradient overlay at bottom
    overlay = Image.new('RGBA', (WIDTH, int(HEIGHT*0.3)), (0,0,0,0))
    o_draw = ImageDraw.Draw(overlay)
    for y in range(overlay.height):
        alpha = int(200 * (y / overlay.height))
        o_draw.line([(0, y), (WIDTH, y)], fill=(0,0,0, alpha))
    canvas.paste(overlay, (0, HEIGHT - overlay.height), overlay)

    return np.array(canvas)

# --- UI & MAIN LOGIC ---

st.title("✨ Top-Tier Ads Factory")
st.caption("Powered by Mistral AI, Pillow & MoviePy")

with st.sidebar:
    st.header("🛠️ Setup")
    u_file = st.file_uploader("Product Image", type=["png", "jpg"])
    u_model = st.text_input("Product Name", "Aurum SmartWatch")
    u_price = st.text_input("Price", "$299")
    u_contact = st.text_input("CTA / Site", "Shop Now @ Aurum.com")
    
    st.divider()
    u_template = st.selectbox("Visual Style", list(TEMPLATES.keys()))
    u_music = st.selectbox("Background Music", list(MUSIC_TRACKS.keys()))
    
    btn_gen = st.button("🎬 Render Video", type="primary")

if btn_gen and u_file:
    # PREPARATION
    status = st.status("🚀 Starting Engine...", expanded=True)
    
    img = Image.open(u_file).convert("RGBA")
    
    # 1. AI GEN
    status.write("🧠 Dreaming up captions (Pixtral)...")
    buf = io.BytesIO(); img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    caption = get_hook(b64)
    status.write(f"✅ Hook: {caption}")
    
    status.write("📐 Calculating pixel-perfect layout (Mistral)...")
    layout_boxes = get_smart_layout(u_model, u_price)
    
    # Data Packet
    render_data = {
        "caption": caption,
        "price": u_price,
        "contact": u_contact
    }

    # 2. FRAME RENDERING
    status.write("🎨 Painting frames...")
    frames = []
    prog_bar = status.progress(0)
    
    total_frames = FPS * DURATION
    for i in range(total_frames):
        t = i / FPS
        frame_pixels = create_frame(t, img, layout_boxes, render_data, u_template)
        frames.append(frame_pixels)
        prog_bar.progress((i+1) / total_frames)
        
    # 3. VIDEO ASSEMBLY (MoviePy)
    status.write("🎼 Mixing audio & encoding (MoviePy)...")
    
    # Create video clip
    clip = ImageSequenceClip(frames, fps=FPS)
    
    # Add Audio
    try:
        # Download audio to temp file
        audio_url = MUSIC_TRACKS[u_music]
        audio_resp = requests.get(audio_url)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f_aud:
            f_aud.write(audio_resp.content)
            audio_path = f_aud.name
            
        audio_clip = AudioFileClip(audio_path).subclip(0, DURATION)
        # Fade out audio at end
        audio_clip = audio_clip.audio_fadeout(1)
        
        final_clip = clip.set_audio(audio_clip)
    except Exception as e:
        st.warning(f"Audio failed ({e}), rendering silent video.")
        final_clip = clip

    # Write File
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f_out:
        final_clip.write_videofile(f_out.name, codec="libx264", audio_codec="aac", logger=None)
        video_path = f_out.name

    status.update(label="✨ Done!", state="complete", expanded=False)

    # 4. RESULT
    c1, c2 = st.columns([2, 1])
    with c1:
        st.video(video_path)
    with c2:
        st.success("Your ad is ready!")
        st.info(f"**Hook Used:** {caption}")
        with open(video_path, "rb") as v_file:
            st.download_button("⬇️ Download MP4", v_file, "ad_toptier.mp4")

elif btn_gen and not u_file:
    st.error("Please upload an image first.")
