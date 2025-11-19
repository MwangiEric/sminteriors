import streamlit as st
import io, requests, math, tempfile, base64, json, random, time, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip
from rembg import remove 

# --- GLOBAL CONFIGURATION ---
st.set_page_config(page_title="AdGen Turbo: Groq Edition", layout="wide", page_icon="⚡")

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
    """
    1. Removes Background (Rembg)
    2. Enhances Sharpness & Contrast (Pillow)
    """
    # A. Remove Background
    # We do this BEFORE resizing to keep maximum edge quality
    with st.spinner("⚡ Removing background..."):
        img_byte_arr = io.BytesIO()
        input_image.save(img_byte_arr, format='PNG')
        input_image_bytes = img_byte_arr.getvalue()
        
        output_bytes = remove(input_image_bytes)
        clean_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")

    # B. Enhancements
    enhancer = ImageEnhance.Contrast(clean_img)
    clean_img = enhancer.enhance(1.15) # 15% more contrast pop
    
    enhancer = ImageEnhance.Sharpness(clean_img)
    clean_img = enhancer.enhance(1.5) # 50% sharper for video crispness
    
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
        except: continue
    return ImageFont.load_default()

# --- MATH & TEMPLATES ---
def ease_out_elastic(t):
    c4 = (2 * math.pi) / 3
    return math.pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1 if t > 0 and t < 1 else (0 if t<=0 else 1)

def linear_fade(t, start, duration):
    if t < start: return 0.0
    if t > start + duration: return 1.0
    return (t - start) / duration

TEMPLATES = {
    "SM Interiors Brand": {
        "bg_grad": ["#4C3B30", "#2a201b"], 
        "accent": "#D2A544", "text": "#FFFFFF", 
        "price_bg": "#D2A544", "price_text": "#000000"
    },
    "Clean White": {
        "bg_grad": ["#e0e0e0", "#ffffff"], 
        "accent": "#000000", "text": "#333333", 
        "price_bg": "#000000", "price_text": "#ffffff"
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
    # 1. Vision Task (Llama 3.2 Vision Preview)
    # Fastest vision model on the market
    p_hook = {
        "model": "llama-3.2-11b-vision-preview",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": "Write a 4-word catchy luxury ad hook for this furniture."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
        ]}],
        "temperature": 0.7,
        "max_tokens": 30
    }
    
    # 2. Logic Task (Llama 3 70B)
    # Incredible reasoning for layout JSON
    p_layout = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "You are a JSON layout engine. Output JSON only."},
            {"role": "user", "content": f"Create a JSON layout for a 720x1280 video. Objects: logo, product, price, contact, caption. Product: {model_name}. Ensure no overlap. Return JSON object."}
        ],
        "response_format": {"type": "json_object"}
    }

    # Execute in sequence (Groq is fast enough we don't need complex parallelism)
    caption = ask_groq(p_hook)
    caption = caption.replace('"', '') if caption else "Pure Luxury Design"
    
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
        # Handle if Groq nests it in a "layout" key or returns a raw list
        final_layout = j.get("layout", j) if isinstance(j, dict) else j
        return caption, final_layout
    except:
        return caption, default_layout

# --- RENDERING ---
def create_frame(t, img, boxes, texts, tpl_name):
    T = TEMPLATES[tpl_name]
    canvas = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(canvas)
    
    # 1. Gradient BG
    c1 = tuple(int(T["bg_grad"][0][i:i+2], 16) for i in (1, 3, 5))
    c2 = tuple(int(T["bg_grad"][1][i:i+2], 16) for i in (1, 3, 5))
    for y in range(HEIGHT):
        r = int(c1[0] + (c2[0]-c1[0]) * y/HEIGHT)
        g = int(c1[1] + (c2[1]-c1[1]) * y/HEIGHT)
        b = int(c1[2] + (c2[2]-c1[2]) * y/HEIGHT)
        draw.line([(0,y), (WIDTH,y)], fill=(r,g,b))

    # 2. Pattern (Faint Grid)
    for i in range(0, WIDTH, 50):
        draw.line([(i,0), (i,HEIGHT)], fill=(255,255,255, 5))

    # 3. Elements
    for b in boxes:
        role = b["role"]
        
        if role == "product":
            # Floating Effect (Because BG is removed, this looks 3D!)
            float_y = math.sin(t * 2) * 12
            scale = ease_out_elastic(min(t, 1.0))
            
            if scale > 0.01:
                pw, ph = int(b['w']*scale), int(b['h']*scale)
                p_rs = img.resize((pw, ph), Image.LANCZOS)
                
                # Dynamic Drop Shadow
                shadow = p_rs.copy()
                # Create black silhouette
                shadow_data = [(0,0,0, int(a*0.3)) for r,g,b,a in p_rs.getdata()]
                shadow.putdata(shadow_data)
                shadow = shadow.filter(ImageFilter.GaussianBlur(15))
                
                cx = b['x'] + (b['w']-pw)//2
                cy = b['y'] + (b['h']-ph)//2 + float_y
                
                # Paste Shadow offset
                canvas.paste(shadow, (int(cx), int(cy+30)), shadow)
                # Paste Object
                canvas.paste(p_rs, (int(cx), int(cy)), p_rs)

        elif role == "price":
            anim = linear_fade(t, 1.5, 0.5)
            if anim > 0:
                off_y = (1-ease_out_elastic(anim))*100
                draw.rounded_rectangle([b['x'], b['y']+off_y, b['x']+b['w'], b['y']+b['h']+off_y], radius=25, fill=T["price_bg"])
                f = get_font(65)
                tw = draw.textlength(texts["price"], font=f)
                tx = b['x'] + (b['w']-tw)//2
                ty = b['y'] + (b['h']-65)//2 + off_y - 5
                draw.text((tx, ty), texts["price"], font=f, fill=T["price_text"])

        elif role == "caption":
            if t > 1.0:
                f = get_font(50)
                w = draw.textlength(texts["caption"], font=f)
                x = (WIDTH - w) // 2
                draw.text((x, b['y']), texts["caption"], font=f, fill=T["accent"])

        elif role == "contact":
            if t > 2.5:
                f = get_font(30)
                w = draw.textlength(texts["contact"], font=f)
                x = (WIDTH - w) // 2
                draw.text((x, b['y']), texts["contact"], font=f, fill=T["text"])

        elif role == "logo":
             try:
                logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
                logo = logo.resize((b['w'], b['h']), Image.LANCZOS)
                canvas.paste(logo, (b['x'], b['y']), logo)
             except: pass

    # 4. Vignette (Cinematic finish)
    vignette = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
    v_draw = ImageDraw.Draw(vignette)
    # Darken bottom for text
    for y in range(int(HEIGHT*0.7), HEIGHT):
        alpha = int(180 * ((y - HEIGHT*0.7)/(HEIGHT*0.3)))
        v_draw.line([(0,y), (WIDTH,y)], fill=(0,0,0,alpha))
    canvas.paste(vignette, (0,0), vignette)

    return np.array(canvas)

# --- MAIN UI ---
with st.sidebar:
    st.header("⚡ Turbo Settings")
    u_file = st.file_uploader("Image", type=["jpg", "png"])
    u_model = st.text_input("Product", "Walden Console")
    u_price = st.text_input("Price", "Ksh 49,900")
    u_contact = st.text_input("Contact", "0710895737")
    u_style = st.selectbox("Template", list(TEMPLATES.keys()))
    u_music = st.selectbox("Music", list(MUSIC_TRACKS.keys()))
    btn = st.button("⚡ Generate with Groq", type="primary")

st.title("AdGen Turbo: Groq + Rembg")

if btn and u_file:
    status = st.status("Initializing Engine...", expanded=True)
    
    # 1. Background Removal (CPU/Onnx)
    status.write("🚿 Removing Background & Enhancing...")
    raw_img = Image.open(u_file).convert("RGBA")
    pro_img = process_image_pro(raw_img)
    st.image(pro_img, caption="Background Removed & Sharpened", width=200)
    
    # 2. Groq AI (Speed!)
    status.write("🚀 Groq AI: Analyzing Image & Layout...")
    buf = io.BytesIO(); pro_img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    
    start_time = time.time()
    caption, layout = get_data_groq(b64, u_model)
    end_time = time.time()
    
    status.write(f"✅ Groq Response Time: {round(end_time-start_time, 2)}s")
    status.write(f"Hook: {caption}")
    
    # 3. Render Video
    status.write("🎨 Rendering Parallax Animation...")
    texts = {"caption": caption, "price": u_price, "contact": u_contact}
    frames = []
    bar = status.progress(0)
    
    for i in range(FPS*DURATION):
        frames.append(create_frame(i/FPS, pro_img, layout, texts, u_style))
        bar.progress((i+1)/(FPS*DURATION))
        
    # 4. Audio & Mix
    status.write("🎵 Adding Sound...")
    clip = ImageSequenceClip(frames, fps=FPS)
    try:
        r_aud = requests.get(MUSIC_TRACKS[u_music])
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tf:
            tf.write(r_aud.content)
            tf_name = tf.name
        aclip = AudioFileClip(tf_name).subclip(0, DURATION).audio_fadeout(1)
        fclip = clip.set_audio(aclip)
    except: fclip = clip

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as vf:
        fclip.write_videofile(vf.name, codec="libx264", audio_codec="aac", logger=None)
        final_path = vf.name

    status.update(label="✨ Ready!", state="complete", expanded=False)
    st.video(final_path)
    with open(final_path, "rb") as f:
        st.download_button("Download Turbo Ad", f, "groq_ad.mp4")
