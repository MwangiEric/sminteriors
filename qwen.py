import streamlit as st
from moviepy.editor import VideoClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import math
import tempfile
import os

# ================================
# 🎨 Professional Color Palette
# ================================
GOLD_LIGHT = (245, 215, 140)   # Warm, luminous gold
GOLD_DARK  = (180, 130, 40)    # Rich, deep gold
ESPRESSO   = (50, 40, 35)      # Near-black espresso brown
ACCENT     = (255, 240, 200)   # Soft highlight

# ================================
# 🖼️ Background Animation Engine
# ================================
def create_cinematic_background(width, height, t):
    """Generate a luxurious animated background with depth and motion."""
    # Base canvas
    img = Image.new('RGB', (width, height), ESPRESSO)
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Slow vertical wave distortion for "shimmer"
    wave_freq = 0.8
    wave_amp = 8
    offset = wave_amp * math.sin(2 * math.pi * t / 12)
    
    # Draw multiple gradient layers for depth
    for i in range(5):
        alpha = max(0, 80 - i * 15)  # fade out layers
        y_offset = int(i * 30 + offset * (1 - i/5))
        
        # Alternate gold tones
        color = GOLD_LIGHT if i % 2 == 0 else GOLD_DARK
        
        for y in range(0, height, 2):
            # Create horizontal scanlines with subtle offset
            ratio = ((y + y_offset) % height) / height
            blend = 0.3 + 0.7 * (1 - abs(ratio - 0.5) * 2)  # bell curve
            
            r = int(ESPRESSO[0] * (1 - blend) + color[0] * blend)
            g = int(ESPRESSO[1] * (1 - blend) + color[1] * blend)
            b = int(ESPRESSO[2] * (1 - blend) + color[2] * blend)
            
            draw.line([(0, y), (width, y)], fill=(r, g, b, alpha))
    
    # Add subtle vignette for cinematic feel
    vignette = Image.new('L', (width, height), 0)
    v_draw = ImageDraw.Draw(vignette)
    for i in range(0, min(width, height)//2, 4):
        opacity = int(255 * (i / (min(width, height)//2)) * 0.6)
        v_draw.ellipse(
            (i, i, width - i, height - i),
            outline=opacity,
            width=4
        )
    vignette = vignette.filter(ImageFilter.GaussianBlur(30))
    img.putalpha(vignette)
    
    return img.convert('RGB')

# ================================
# 📝 Text Rendering with Motion
# ================================
def render_text_with_motion(draw, text, font, width, height, t, duration, fade_in, fade_out):
    # Center position
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (width - tw) // 2
    y = (height - th) // 2
    
    # Subtle floating motion
    float_amp = 5
    float_freq = 0.3
    y += float_amp * math.sin(2 * math.pi * t * float_freq)
    
    # Fade & glow
    if t < fade_in:
        alpha = t / fade_in
    elif t > duration - fade_out:
        alpha = (duration - t) / fade_out
    else:
        alpha = 1.0
    
    # Glow effect (draw multiple slightly offset shadows)
    glow_steps = 3
    glow_alpha = min(1.0, alpha * 0.6)
    for dx, dy in [(0,0), (1,0), (0,1), (-1,0), (0,-1)]:
        for i in range(glow_steps):
            intensity = int(255 * glow_alpha * (1 - i/glow_steps))
            if intensity > 0:
                draw.text(
                    (x + dx*i//2, y + dy*i//2),
                    text,
                    fill=(255, 240, 200, intensity),
                    font=font
                )
    
    # Main text (gold)
    text_alpha = int(255 * alpha)
    draw.text((x, y), text, fill=(GOLD_LIGHT[0], GOLD_LIGHT[1], GOLD_LIGHT[2], text_alpha), font=font)

# ================================
# 🎞️ Frame Generator
# ================================
def make_frame(t, text, width, height, font_size, duration, fade_in, fade_out):
    # Create animated background
    bg = create_cinematic_background(width, height, t)
    
    # Overlay with transparency for text
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Load modern font (fallback to default)
    try:
        font = ImageFont.truetype("Arial Bold.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default()
    
    # Render animated text
    render_text_with_motion(draw, text, font, width, height, t, duration, fade_in, fade_out)
    
    # Composite
    result = Image.alpha_composite(bg.convert('RGBA'), overlay)
    return np.array(result.convert('RGB'))

# ================================
# 🌐 Streamlit App
# ================================
st.set_page_config(
    page_title="Cinematic Text Animation",
    page_icon="🎬",
    layout="centered"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    .main { background: #0a0a0c; }
    h1 { color: #f5d78c; text-align: center; font-weight: 700; }
    .stButton>button {
        background: linear-gradient(to right, #c69a4a, #8c6d2f);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.4);
    }
    .sidebar .sidebar-content { background: #121216; }
</style>
""", unsafe_allow_html=True)

st.title("🎬 Cinematic Text Animation")
st.markdown("<div style='text-align: center; color: #aaa; margin-bottom: 30px;'>Professional • Modern • Spectacular</div>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ✨ Settings")
    text = st.text_input("Text", "ELEVATE YOUR STORY", key="text")
    duration = st.slider("Duration (seconds)", 4, 15, 8)
    fade_in = st.slider("Fade In", 0.8, 3.0, 1.4)
    fade_out = st.slider("Fade Out", 0.8, 3.0, 1.4)
    font_size = st.slider("Font Size", 40, 120, 84)
    st.markdown("<br><div style='font-size: 0.85em; color: #888;'>Background auto-animated in gold & espresso tones</div>", unsafe_allow_html=True)

# Generate button
if st.button("✨ Generate Spectacular Animation"):
    W, H = 1920, 1080  # Full HD cinematic
    
    with st.spinner("Rendering cinematic masterpiece... (30-60 sec)"):
        try:
            clip = VideoClip(
                lambda t: make_frame(t, text, W, H, font_size, duration, fade_in, fade_out),
                duration=duration
            )
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                clip.write_videofile(
                    tmp.name,
                    fps=30,
                    codec="libx264",
                    audio=False,
                    preset="slow",
                    logger=None,
                    threads=4,
                    ffmpeg_params=["-crf", "18"]  # High quality
                )
                video_path = tmp.name
            
            # Display
            st.video(video_path)
            
            # Download
            with open(video_path, "rb") as f:
                st.download_button(
                    "⬇️ Download Full HD MP4",
                    f,
                    file_name="cinematic_text_animation.mp4",
                    mime="video/mp4"
                )
            
            os.unlink(video_path)
            
        except Exception as e:
            st.error(f"Rendering failed: {str(e)}")
            st.info("Make sure requirements include: moviepy, pillow, imageio[ffmpeg], numpy")

# Footer
st.markdown("<br><hr><div style='text-align: center; color: #555; font-size: 0.9em;'>Made for creators who demand excellence</div>", unsafe_allow_html=True)
