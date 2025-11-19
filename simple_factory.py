import streamlit as st, io, requests, math, tempfile, base64, json, random, time
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import imageio.v3 as imageio

# --- GLOBAL CONFIG & SECRETS ---
st.set_page_config(page_title="S&M Canva Factory", layout="wide")
st.title("🎬 Canva-Quality AI Ads Factory")

WIDTH, HEIGHT = 720, 1280
FPS = 30
DURATION = 6
N_FRAMES = FPS * DURATION
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

if "mistral_key" not in st.secrets:
    st.error("Add `mistral_key` in Secrets (free at console.mistral.ai)")
    st.stop()
HEADERS = {"Authorization": f"Bearer {st.secrets['mistral_key']}", "Content-Type": "application/json"}

# --- FONT LOADING ---
try:
    # Attempt to load a common bold font (Adjust path if needed)
    FONT_BOLD = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
except IOError:
    # Fallback if the path is invalid
    FONT_BOLD = ImageFont.load_default() 

# --- ANIMATION HELPERS (Define first, as they are used by TEMPLATES-dependent functions) ---

def ease_out_bounce(t):
    n1, d1 = 7.5625, 2.75
    if t < 1 / d1: return n1 * t * t
    elif t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375

def proportional_resize(im, max_h):
    aspect = im.width / im.height
    new_h = max_h
    new_w = int(aspect * new_h)
    return im.resize((new_w, new_h), Image.LANCZOS)

# --- TEMPLATES (Defined second, as they are referenced by drawing functions) ---
TEMPLATES = {
    "Canva Pop": {
        "bg_grad": ["#071025", "#1e3fae"],
        "accent": "#00e6ff",
        "text": "#ffffff",
        "price_bg": "#001225",
        "price_text": "#00e6ff",
        "caption_size": 56,
        "price_size": 68,
        "contact_size": 36,
        "shadow": True,
        "parallax": 0.06
    },
    "Canva Luxury": {
        "bg_grad": ["#04080f", "#091426"],
        "accent": "#d4af37",
        "text": "#ffffff",
        "price_bg": "#d4af37",
        "price_text": "#000000",
        "caption_size": 52,
        "price_size": 72,
        "contact_size": 34,
        "shadow": True,
        "parallax": 0.04
    },
    "Canva Minimal": {
        "bg_grad": ["#f6f7f9", "#e9eef6"],
        "accent": "#1e3fae",
        "text": "#1e3fae",
        "price_bg": "#1e3fae",
        "price_text": "#ffffff",
        "caption_size": 50,
        "price_size": 66,
        "contact_size": 32,
        "shadow": False,
        "parallax": 0.02
    }
}

# --- AI API CALLS ---
def ask_mistral(payload):
    for attempt in range(1, 6):
        try:
            r = requests.post("https://api.mistral.ai/v1/chat/completions", json=payload, headers=HEADERS, timeout=60)
            if r.status_code == 429:
                time.sleep(2 ** attempt + random.uniform(0, 1))
                continue
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt == 5:
                st.error(f"Mistral API failed after 5 retries: {e}")
                st.stop()
            time.sleep(2 ** attempt)
    st.stop()

def get_caption(img_b64):
    payload = {
        "model": "pixtral-12b-2409",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": "Describe this furniture in one short, catchy TikTok hook (max 12 words)."},
            {"type": "image_url", "image_url": f"data:image/png;base64,{img_b64}"}
        ]}],
        "max_tokens": 30
    }
    return ask_mistral(payload)

# --- CACHED AI Layout Function ---
@st.cache_data
def get_layout(model, price):
    payload = {
        "model": "mistral-large-latest",
        "messages": [{"role": "user", "content": f"""
720×1280 canvas. Return ONLY this JSON (no overlap):
[{{"role":"logo","x":0,"y":0,"w":0,"h":0}},
 {{"role":"product","x":0,"y":0,"w":0,"h":0}},
 {{"role":"price","x":0,"y":0,"w":0,"h":0}},
 {{"role":"contact","x":0,"y":0,"w":0,"h":0}}]
Product: {model} | Price: {price}
Ensure **no overlap** between boxes. Keep 50 px margin.
"""}],
        "max_tokens": 400
    }
    text = ask_mistral(payload)
    try:
        # PRO-LEVEL: Explicit validation of the JSON structure
        boxes = json.loads(text)
        required_roles = {"logo", "product", "price", "contact"}
        if all(b["role"] in required_roles for b in boxes) and len(boxes) >= 4:
             return boxes
        else:
            raise ValueError
    except:
        # Fallback Layout
        return [
            {"role": "logo", "x": 40, "y": 40, "w": 240, "h": 120},
            {"role": "product", "x": 60, "y": 180, "w": 600, "h": 780},
            {"role": "price", "x": 60, "y": 1000, "w": 600, "h": 140},
            {"role": "contact", "x": 60, "y": 1160, "w": 600, "h": 80}
        ]

# --- DRAWING FUNCTIONS (Can safely reference TEMPLATES now) ---

def draw_circles(draw, t, template):
    T = TEMPLATES[template]
    n = 8
    for i in range(n):
        angle = t * 0.3 + i * 0.8
        x = int(WIDTH // 2 + math.cos(angle) * 400)
        y = int(HEIGHT * 0.5 + math.sin(angle) * 300)
        r = 20 + i * 6
        alpha = int(255 * (0.15 - i * 0.01))
        color = T["accent"] + f"{alpha:02x}"
        draw.ellipse([(x - r, y - r), (x + r, y + r)], fill=color)

def draw_caption_animation(draw, text, box, t, template):
    """
    PRO-LEVEL: Animates the caption text with a staggered slide-in effect.
    """
    T = TEMPLATES[template]
    x, y, w, h = box["x"], box["y"], box["w"], box["h"]
    
    # Static text fitting logic
    size = T["caption_size"]
    font = FONT_BOLD.font_variant(size=size) if hasattr(FONT_BOLD, 'font_variant') else FONT_BOLD
    
    # Word wrapping logic
    lines = []
    words = text.split()
    line = ""
    for wrd in words:
        test = line + " " + wrd if line else wrd
        if draw.textlength(test, font=font) <= w - 20:
            line = test
        else:
            lines.append(line)
            line = wrd
    if line:
        lines.append(line)
    
    line_h = size + 4
    total_h = len(lines) * line_h
    y_off_base = y + (h - total_h) // 2
    
    # Animation parameters
    MAX_SLIDE = 150 # Max pixels to slide from
    TIME_START = 0.5 # Animation starts at 0.5s
    TIME_DURATION = 1.0 # Animation lasts 1.0s
    
    # Draw each line and word
    current_word_index = 0
    for i, ln in enumerate(lines):
        y_off = y_off_base + i * line_h
        
        # Center the line
        line_w = draw.textlength(ln, font=font)
        lx_base = x + (w - line_w) // 2
        
        word_x_offset = lx_base
        
        # Iterate over words in the line for individual animation
        for word_index, wrd in enumerate(ln.split()):
            # Calculate the global delay based on the index of the word in the entire caption
            # Staggered delay: 0.1s per word
            global_delay = TIME_START + current_word_index * 0.1
            current_word_index += 1
            
            # The current time in the word's local animation cycle
            local_t = (t - global_delay) / TIME_DURATION
            local_t = np.clip(local_t, 0, 1)
            
            # Apply an ease-out function for smooth motion
            eased_pos = ease_out_bounce(local_t) if local_t < 1 else 1
            
            # Calculate the animated X offset
            # Slides from left (MAX_SLIDE) to its final position (0)
            slide_x = MAX_SLIDE * (1 - eased_pos)
            
            # Draw the word
            word_color = T["accent"] if current_word_index % 2 == 0 else T["text"] # Alternate color
            draw.text(
                (word_x_offset - slide_x, y_off), # Apply slide_x
                wrd.upper(), 
                fill=word_color, 
                font=font, 
                stroke_width=2, 
                stroke_fill="#00000080" # Soft shadow
            )
            
            # Update X offset for the next word
            word_x_offset += draw.textlength(wrd + " ", font=font)

# --- MAIN DRAW FUNCTION ---
def draw_frame(t, img, boxes, price, contact, caption, template):
    T = TEMPLATES[template]
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # 1. Canva gradient background
    for y in range(HEIGHT):
        blend = y / HEIGHT
        r = int((int(T["bg_grad"][0][1:3], 16)) * (1 - blend) + int(T["bg_grad"][1][1:3], 16) * blend)
        g = int((int(T["bg_grad"][0][3:5], 16)) * (1 - blend) + int(T["bg_grad"][1][3:5], 16) * blend)
        b = int((int(T["bg_grad"][0][5:7], 16)) * (1 - blend) + int(T["bg_grad"][1][5:7], 16) * blend)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    # 2. Soft background copy (parallax) - with dynamic opacity
    if img:
        bg = img.resize((WIDTH, int(HEIGHT * 0.55)), Image.LANCZOS).filter(ImageFilter.GaussianBlur(12))
        offset = int(T["parallax"] * WIDTH * math.sin(t * math.pi / DURATION))
        
        # PRO-LEVEL: Fade in background image opacity (0 to 100% in 1s)
        alpha_factor = np.clip(t / 1.0, 0, 1)
        bg_alpha = int(255 * 0.4 * alpha_factor)
        
        # Create a new image with controlled alpha for pasting
        bg_rgba = bg.convert("RGBA")
        bg_rgba_faded = Image.new("RGBA", bg.size)
        
        # Apply the calculated alpha to the whole image
        alpha_mask = Image.new('L', bg.size, bg_alpha)
        bg_rgba_faded.paste(bg_rgba, (0, 0), alpha_mask)
        
        canvas.paste(bg_rgba_faded, (offset, int(HEIGHT * 0.22)), bg_rgba_faded)

    # 3. Logo (proportional + shadow)
    logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
    for b in boxes:
        if b["role"] == "logo":
            logo = proportional_resize(logo, b["h"])
            if T["shadow"]:
                shadow = logo.copy().filter(ImageFilter.GaussianBlur(6))
                canvas.paste(shadow, (b["x"] + 4, b["y"] + 4), shadow)
            canvas.paste(logo, (b["x"], b["y"]), logo)

    # 4. Product (Canva bounce + shadow)
    for b in boxes:
        if b["role"] == "product":
            scale = 0.94 + 0.06 * ease_out_bounce(t / DURATION)
            w2, h2 = int(b["w"] * scale), int(b["h"] * scale)
            prod = img.resize((w2, h2), Image.LANCZOS)
            x = b["x"] + (b["w"] - w2) // 2
            y = b["y"] + (b["h"] - h2) // 2
            if T["shadow"]:
                shadow = prod.copy().filter(ImageFilter.GaussianBlur(8))
                canvas.paste(shadow, (x + 8, y + 8), shadow)
            canvas.paste(prod, (x, y), prod.convert("RGBA"))

    # 5. Price (Canva badge + bounce)
    for b in boxes:
        if b["role"] == "price":
            # Bounce effect on the vertical position (1s cycle)
            bounce = int(10 * ease_out_bounce((t % 1) / 1))
            
            # Apply fade-in for the price badge (appears after 2 seconds)
            price_alpha_factor = np.clip((t - 2.0) / 1.0, 0, 1) # Fade in from 2.0s to 3.0s
            badge_color = T["price_bg"]
            text_color = T["price_text"]
            
            # Create a separate layer for the price badge to apply opacity
            badge_layer = Image.new("RGBA", canvas.size)
            badge_draw = ImageDraw.Draw(badge_layer)
            
            badge_draw.rounded_rectangle([(b["x"], b["y"] + bounce), (b["x"] + b["w"], b["y"] + b["h"] + bounce)], radius=20, fill=badge_color)
            
            # Apply opacity to the badge layer
            alpha_mask = Image.new('L', canvas.size, int(255 * price_alpha_factor))
            canvas.paste(badge_layer, (0, 0), alpha_mask)

            # Draw text on top (simple, no per-frame opacity needed after 3.0s)
            if price_alpha_factor > 0.1: # Only draw text when visible
                font_price = FONT_BOLD.font_variant(size=T["price_size"]) if hasattr(FONT_BOLD, 'font_variant') else FONT_BOLD
                draw.text((b["x"] + b["w"] // 2, b["y"] + b["h"] // 2 + bounce), price, fill=text_color, anchor="mm", font=font_price)

    # 6. Contact (Canva style)
    for b in boxes:
        if b["role"] == "contact":
            font_contact = FONT_BOLD.font_variant(size=T["contact_size"]) if hasattr(FONT_BOLD, 'font_variant') else FONT_BOLD
            draw.text((b["x"] + b["w"] // 2, b["y"] + b["h"] // 2), contact, fill=T["text"], anchor="mm", font=font_contact)

    # 7. Animated circles (free)
    draw_circles(draw, t, template)

    # 8. NEW: Animated Caption
    caption_box = next((b for b in boxes if b["role"] == "caption"), None)
    if caption_box:
        draw_caption_animation(draw, caption, caption_box, t, template)

    # --- DROP ALPHA → RGB only ---
    rgb = np.array(canvas)[:, :, :3]
    return rgb

# ---------- Streamlit UI and Generation Flow (Pro-Level Layout) ----------

# PRO-LEVEL: Use sidebar for inputs
with st.sidebar:
    st.header("⚙️ Ad Configuration")
    uploaded_file = st.file_uploader("1. Upload Product Image (PNG/JPG)", type=["png", "jpg", "jpeg"])
    
    # Text Inputs
    model_input = st.text_input("Product Name/Model", "Luxury Modern Sofa")
    price_input = st.text_input("Price Tag Text", "ONLY $1,999")
    contact_input = st.text_input("Contact Info/URL", "YourStore.com | @TikTokHandle")
    
    # Template Selection
    template_choice = st.radio("2. Choose Ad Style", list(TEMPLATES.keys()))
    
    generate_button = st.button("🚀 Generate TikTok Video Ad", use_container_width=True)

# Main content area
st.subheader("Upload, Configure, Generate. Go Viral.")

# Handle image display
if uploaded_file is not None:
    st.image(uploaded_file, caption="Uploaded Image", width=360) # Smaller preview
else:
    st.info("Upload an image in the sidebar to begin.")


# Generation Block
if generate_button and uploaded_file is not None:
    
    img = Image.open(uploaded_file).convert("RGBA")
    
    # Placeholder for status messages and video output
    status_placeholder = st.empty()
    
    # 1. AI Analysis & Layout (with progress bar)
    status_placeholder.subheader("Process Status")
    progress_bar = status_placeholder.progress(0, text="Starting AI Analysis...")

    with st.spinner("1. Getting AI Hook from Pixtral..."):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        caption = get_caption(b64)
    progress_bar.progress(33, text="AI Hook generated. Getting Layout from Mistral-Large...")

    with st.spinner("2. Generating AI Layout JSON..."):
        boxes = get_layout(model_input, price_input)
        # Add the fixed caption box
        boxes.append({"role": "caption", "x": 60, "y": 80, "w": 600, "h": 100})
        
    progress_bar.progress(66, text="Layout complete. Rendering video frames...")
    
    status_placeholder.subheader("AI Outputs")
    status_placeholder.markdown(f"**🔥 AI Hook:** {caption}")
    
    with st.expander("View Generated AI Layout (JSON)"):
        st.json(boxes)

    # 2. Video Rendering (with progress bar)
    frames = []
    
    # Calculate frames to render
    for i in range(DURATION * FPS):
        t = i / FPS
        frame = draw_frame(t, img, boxes, price_input, contact_input, caption, template_choice)
        frames.append(frame)
        # Update progress bar every few frames
        if i % 10 == 0:
            progress_bar.progress(66 + int((i / N_FRAMES) * 34), text=f"Rendering frame {i}/{N_FRAMES}...")

    progress_bar.progress(100, text="Rendering complete! Finalizing file...")
    
    # 3. File Finalization
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        imageio.imwrite(tmp.name, frames, fps=FPS, codec="libx264", pixelformat="yuv420p")
        video_path = tmp.name

    st.subheader("Generated TikTok Ad")
    st.video(video_path)
    with open(video_path, "rb") as f:
        st.download_button("⬇️ Download High-Quality MP4", f, f"{model_input.replace(' ', '_')}_canva.mp4", "video/mp4")

    st.balloons()
    
# --- Concluding Section ---
st.markdown("---")
st.caption("Need more Streamlit expertise? Learn how to deploy advanced data apps.")
st.markdown("The video on [Building a Streamlit App with Images, Videos, Audio & Interactive Messages!](https://www.youtube.com/watch?v=t7YQCQ-gkY4) is relevant because it shows the fundamental Streamlit principles needed to build the UI for a video factory application.")
