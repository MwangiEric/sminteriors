import streamlit as st, io, requests, math, tempfile, base64, json, random, time
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import imageio.v3 as imageio

st.set_page_config(page_title="S&M Canva Factory", layout="wide") # Use wide layout
st.title("🎬 Canva-Quality AI Ads Factory")

# --- GLOBAL CONFIG & SECRETS (Keep these) ---
WIDTH, HEIGHT = 720, 1280
FPS = 30
DURATION = 6
N_FRAMES = FPS * DURATION
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"
# ... (Mistral Key and HEADERS setup remain the same) ...

# --- NEW: Font Loading (Pro-level requires a good font) ---
# NOTE: Ensure this font path exists in your environment or use a Google Font URL/service
try:
    FONT_BOLD = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
except IOError:
    FONT_BOLD = ImageFont.load_default() # Fallback

# --- CACHED AI and Helper Functions ---
# @st.cache_data ensures the AI call only runs when inputs (model, price) change.
@st.cache_data
def get_layout(model, price):
    # ... (function body remains the same, but now it's cached) ...
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
        if all(b["role"] in required_roles for b in boxes):
             return boxes
        else:
            st.warning("AI returned valid JSON but missing required roles. Using fallback layout.")
            raise ValueError
    except:
        return [
            {"role": "logo", "x": 40, "y": 40, "w": 240, "h": 120},
            {"role": "product", "x": 60, "y": 180, "w": 600, "h": 780},
            {"role": "price", "x": 60, "y": 1000, "w": 600, "h": 140},
            {"role": "contact", "x": 60, "y": 1160, "w": 600, "h": 80}
        ]

# ... (TEMPLATES dictionary remains the same) ...
# ... (ease_out_bounce, auto_fit_text, proportional_resize, draw_circles remain the same) ...


def draw_caption_animation(draw, text, box, t, template):
    """
    PRO-LEVEL: Animates the caption text with a staggered slide-in effect.
    """
    T = TEMPLATES[template]
    x, y, w, h = box["x"], box["y"], box["w"], box["h"]
    
    # Static text fitting logic
    size = T["caption_size"]
    font = FONT_BOLD
    
    # Word wrapping logic (re-using part of auto_fit_text for consistency)
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
    
    # Draw each line and letter
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


def draw_frame(t, img, boxes, price, contact, caption, template):
    T = TEMPLATES[template]
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # ... (1. Canva gradient background remains the same) ...

    # 2. Soft background copy (parallax) - with added dynamic opacity
    if img:
        bg = img.resize((WIDTH, int(HEIGHT * 0.55)), Image.LANCZOS).filter(ImageFilter.GaussianBlur(12))
        offset = int(T["parallax"] * WIDTH * math.sin(t * math.pi / DURATION))
        
        # PRO-LEVEL: Fade in background image opacity (0 to 100% in 1s)
        alpha_factor = np.clip(t / 1.0, 0, 1)
        bg_alpha = int(255 * 0.4 * alpha_factor)
        
        bg_rgba = bg.convert("RGBA")
        bg_data = bg_rgba.getdata()
        
        new_data = []
        for item in bg_data:
            if item[3] > 0: # Check if original pixel is not transparent
                new_data.append((item[0], item[1], item[2], bg_alpha))
            else:
                new_data.append(item)
        bg_rgba.putdata(new_data)
        
        canvas.paste(bg_rgba, (offset, int(HEIGHT * 0.22)), bg_rgba)
        
    # 3. Logo (proportional + shadow)
    # ... (remains the same) ...

    # 4. Product (Canva bounce + shadow)
    # ... (remains the same) ...

    # 5. Price (Canva badge + bounce)
    # ... (remains the same) ...

    # 6. Contact (Canva style)
    # ... (remains the same) ...
    
    # 7. Animated circles (free)
    draw_circles(draw, t, template)
    
    # 8. NEW: Animated Caption
    caption_box = next((b for b in boxes if b["role"] == "caption"), None)
    if caption_box:
        draw_caption_animation(draw, caption, caption_box, t, template)

    # --- DROP ALPHA → RGB only ---
    rgb = np.array(canvas)[:, :, :3]
    return rgb

# ---------- Streamlit UI and Generation Flow ----------
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
    
    generate_button = st.button("🚀 Generate TikTok Video Ad")

# Main content area
st.header("Upload, Generate, Go Viral.")

# Handle image display
if uploaded_file is not None:
    st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
else:
    st.info("Upload an image in the sidebar to begin.")


# Generation Block
if generate_button and uploaded_file is not None:
    
    img = Image.open(uploaded_file).convert("RGBA")
    
    # 1. AI Analysis & Layout (with progress bar)
    st.subheader("Process Status")
    progress_bar = st.progress(0, text="Starting AI Analysis...")

    with st.spinner("1. Getting AI Hook from Pixtral..."):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        caption = get_caption(b64)
    progress_bar.progress(33, text="AI Hook generated. Getting Layout from Mistral-Large...")

    with st.spinner("2. Generating AI Layout JSON..."):
        boxes = get_layout(model_input, price_input)
        # Add the fixed caption box AFTER AI layout to ensure it's included
        boxes.append({"role": "caption", "x": 60, "y": 80, "w": 600, "h": 100})
        
    progress_bar.progress(66, text="Layout complete. Rendering video frames...")
    
    st.subheader("AI Outputs")
    st.markdown(f"**🔥 AI Hook:** {caption}")
    with st.expander("View Generated AI Layout (JSON)"):
        st.json(boxes)

    # 2. Video Rendering (with progress bar)
    frames = []
    
    # Calculate frames to render
    for i in range(DURATION * FPS):
        t = i / FPS
        frame = draw_frame(t, img, boxes, price_input, contact_input, caption, template_choice)
        frames.append(frame)
        # Update progress bar every few frames to prevent excessive overhead
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

# --- Placeholder/Initial UI ---
if not generate_button and uploaded_file is None:
    st.info("Select your image and customize the settings in the sidebar to generate a 6-second, animated ad.")

# --- Link to Streamlit Guide ---
st.markdown("---")
st.caption("Need more Streamlit expertise? Learn how to deploy advanced data apps.")
