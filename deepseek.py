import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import tempfile, os, numpy as np, io
from moviepy.editor import ImageSequenceClip, AudioFileClip, TextClip, CompositeVideoClip
import math

st.set_page_config(page_title="SM Interiors DIY Tips Animator", layout="wide", page_icon="💡")

WIDTH, HEIGHT = 1080, 1920
FPS, DURATION = 30, 8  # 8 seconds for tips

# LOCAL AUDIO (same as reel tool)
AUDIO_DIR = "audio"
MUSIC_FILES = {
    "Gold Luxury": "gold_luxury.mp3",
    "Viral Pulse": "viral_pulse.mp3",
    "Elegant Flow": "elegant_flow.mp3",
}

LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png"

@st.cache_resource
def load_logo():
    """Load logo with error handling"""
    try:
        import requests
        resp = requests.get(LOGO_URL, timeout=5)
        if resp.status_code == 200:
            logo = Image.open(io.BytesIO(resp.content)).convert("RGBA").resize((200, 100))
            return logo
    except:
        # Fallback: Create text logo if network fails
        fallback = Image.new("RGBA", (200, 100), (0,0,0,0))
        draw = ImageDraw.Draw(fallback)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 60)
        except:
            font = ImageFont.load_default()
        draw.text((10, 20), "SM", font=font, fill="#FFD700")
        return fallback

def create_diy_background():
    """Create branded background for DIY tips"""
    bg = Image.new("RGB", (WIDTH, HEIGHT), "#0F0A05")
    draw = ImageDraw.Draw(bg)
    
    # Subtle geometric patterns
    for i in range(0, WIDTH, 100):
        draw.line([(i, 0), (i, HEIGHT)], fill="#1A1208", width=1)
    for i in range(0, HEIGHT, 100):
        draw.line([(0, i), (WIDTH, i)], fill="#1A1208", width=1)
    
    # Gold accent circles
    for cx, cy, r in [(200, 400, 80), (880, 1200, 120), (900, 600, 60)]:
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline="#FFD700", width=3)
    
    return bg

def create_text_frame(t, tip_lines, tip_title, current_step, total_steps, logo=None):
    """Create animated frame for DIY tips"""
    bg = create_diy_background()
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
    draw = ImageDraw.Draw(canvas)
    
    try:
        title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 80)
        tip_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 64)
        step_font = ImageFont.truetype("DejaVuSans.ttf", 48)
    except:
        title_font = ImageFont.load_default().font_variant(size=80)
        tip_font = ImageFont.load_default().font_variant(size=64)
        step_font = ImageFont.load_default().font_variant(size=48)
    
    # Animated title (slide in from top)
    title_y = 100 + int(50 * math.sin(t * 2))  # Subtle bounce effect
    
    # Title with shadow
    draw.text((61, title_y+1), tip_title, font=title_font, fill="#000000")
    draw.text((60, title_y), tip_title, font=title_font, fill="#FFD700")
    
    # Step indicator
    step_text = f"Step {current_step} of {total_steps}"
    draw.text((WIDTH-400, title_y), step_text, font=step_font, fill="#FFFFFF")
    
    # Progress bar
    progress_width = 800
    progress_height = 15
    progress_x = (WIDTH - progress_width) // 2
    progress_y = title_y + 120
    
    # Progress bar background
    draw.rounded_rectangle([progress_x, progress_y, progress_x + progress_width, progress_y + progress_height], 
                          radius=7, fill="#333333")
    
    # Progress fill (animated)
    progress_fill = (current_step - 1) / total_steps
    fill_width = int(progress_width * progress_fill)
    if fill_width > 0:
        draw.rounded_rectangle([progress_x, progress_y, progress_x + fill_width, progress_y + progress_height], 
                              radius=7, fill="#FFD700")
    
    # Tip lines with staggered animation
    base_y = 600
    line_height = 100
    
    for i, line in enumerate(tip_lines):
        # Each line enters with a slight delay
        line_delay = i * 0.3
        line_time = max(0, t - line_delay)
        
        if line_time < 1.0:  # Entrance animation
            # Slide from right with fade
            offset_x = int((1 - line_time) * 100)
            alpha = int(255 * line_time)
        else:
            offset_x = 0
            alpha = 255
        
        # Text position with subtle hover
        y_pos = base_y + (i * line_height) + int(5 * math.sin(t * 3 + i))
        x_pos = (WIDTH // 2) + offset_x
        
        # Text with semi-transparent background for readability
        if alpha > 0:
            # Get text bounding box
            bbox = draw.textbbox((0, 0), line, font=tip_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Background for text
            bg_padding = 20
            bg_rect = [
                x_pos - text_width//2 - bg_padding,
                y_pos - text_height//2 - bg_padding//2,
                x_pos + text_width//2 + bg_padding,
                y_pos + text_height//2 + bg_padding//2
            ]
            draw.rounded_rectangle(bg_rect, radius=15, fill=(15, 10, 5, 200))
            
            # Draw text with gold color and shadow
            text_color = (255, 215, 0, alpha)
            shadow_color = (0, 0, 0, alpha)
            
            draw.text((x_pos - text_width//2 + 2, y_pos - text_height//2 + 2), 
                     line, font=tip_font, fill=shadow_color)
            draw.text((x_pos - text_width//2, y_pos - text_height//2), 
                     line, font=tip_font, fill=text_color)
    
    # CTA at bottom (pulsing effect)
    cta_alpha = int(128 + 127 * math.sin(t * 4))
    cta_text = "👉 SWIPE UP FOR MORE DIY TIPS"
    cta_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 50) if hasattr(ImageFont, 'truetype') else ImageFont.load_default().font_variant(size=50)
    
    cta_bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    cta_width = cta_bbox[2] - cta_bbox[0]
    cta_x = (WIDTH - cta_width) // 2
    cta_y = HEIGHT - 150
    
    draw.text((cta_x, cta_y), cta_text, font=cta_font, fill=(255, 255, 255, cta_alpha))
    
    # Logo
    if logo:
        canvas.paste(logo, (WIDTH - 220, 50), logo)
    
    # Composite onto background
    bg.paste(canvas, (0, 0), canvas)
    
    return np.array(bg)

def split_text_into_lines(text, max_chars_per_line=25):
    """Split long text into multiple lines for better readability"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        if len(test_line) <= max_chars_per_line:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

# UI
st.title("💡 SM Interiors DIY Tips Animator")
st.caption("Create engaging DIY tutorial videos for social media • 8 seconds per tip")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 DIY Tip Content")
    
    tip_title = st.text_input("Tip Title (max 25 chars)", "PRO TIP", max_chars=25)
    
    tip_text = st.text_area(
        "DIY Tip Description", 
        "Use vinegar and baking soda to clean stubborn stains on furniture",
        height=100,
        help="Describe the DIY tip step by step"
    )
    
    total_steps = st.slider("Total Steps in Series", 1, 10, 3, 
                           help="This helps show progress (Step X of Y)")
    
    current_step = st.slider("Current Step Number", 1, total_steps, 1,
                            help="Which step is this in the series?")
    
    music_key = st.selectbox("Background Music", list(MUSIC_FILES.keys()), index=0)

with col2:
    st.subheader("🎬 Preview Settings")
    
    # Auto-split text preview
    tip_lines = split_text_into_lines(tip_text)
    st.write("**Text will appear as:**")
    for i, line in enumerate(tip_lines):
        st.write(f"Line {i+1}: `{line}`")
    
    if len(tip_lines) > 4:
        st.warning("⚠️ Consider shortening your tip - too many lines may look crowded")
    
    st.info("💡 **Pro Tip:** Keep each line under 25 characters for best mobile readability")

# LIVE PREVIEW
st.markdown("---")
st.subheader("📱 LIVE PREVIEW")

logo_img = load_logo()
preview_time = st.slider("Preview Animation Time", 0.0, 3.0, 1.0, 0.1,
                        help="Drag to see different animation states")

preview_frame = create_text_frame(
    t=preview_time,
    tip_lines=tip_lines,
    tip_title=tip_title,
    current_step=current_step,
    total_steps=total_steps,
    logo=logo_img
)

st.image(Image.fromarray(preview_frame), use_column_width=True)
st.caption("This shows how your tip will look at this moment in the animation")

# GENERATE VIDEO
if st.button("🚀 GENERATE DIY TIP VIDEO", type="primary", use_container_width=True):
    if not tip_text.strip():
        st.error("Please enter a DIY tip!")
    else:
        with st.spinner("Creating your DIY tip video... (takes ~30 seconds)"):
            frames = []
            logo_img = load_logo()
            
            # Generate frames for full duration
            for i in range(FPS * DURATION):
                t = i / FPS  # Time in seconds
                frame = create_text_frame(t, tip_lines, tip_title, current_step, total_steps, logo_img)
                frames.append(frame)
            
            # Create video clip
            clip = ImageSequenceClip(frames, fps=FPS)
            
            # Add audio
            audio_path = os.path.join(AUDIO_DIR, MUSIC_FILES[music_key])
            if os.path.exists(audio_path):
                try:
                    audio = AudioFileClip(audio_path).subclip(0, min(DURATION, AudioFileClip(audio_path).duration))
                    clip = clip.set_audio(audio)
                except Exception as e:
                    st.warning(f"Audio skipped: {e}. Using video only.")
            
            # Export
            video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            clip.write_videofile(
                video_path,
                fps=FPS,
                codec="libx264",
                audio_codec="aac" if os.path.exists(audio_path) else None,
                threads=4,
                preset="fast",
                logger=None
            )
            
            st.success("✅ DIY TIP VIDEO READY!")
            st.video(video_path)
            
            with open(video_path, "rb") as f:
                st.download_button(
                    "⬇️ DOWNLOAD DIY TIP VIDEO", 
                    f, 
                    f"SM_DIY_Tip_{current_step}_of_{total_steps}.mp4", 
                    "video/mp4", 
                    use_container_width=True
                )
            
            # Cleanup
            os.unlink(video_path)
            clip.close()
            if 'audio' in locals():
                audio.close()

# BATCH TIP GENERATOR
st.markdown("---")
st.subheader("🔄 Multiple Tips Generator")

st.info("**Coming Soon:** Generate a series of DIY tip videos automatically!")

st.markdown("""
### 💡 Best Practices for DIY Tip Videos:
1. **Keep it short** - One clear tip per video
2. **Use simple language** - Easy to understand
3. **Show progress** - Use step numbers for series
4. **Brand consistency** - Gold and brown colors
5. **Mobile first** - Vertical format, large text
""")

st.caption("✅ OPTIMIZED FOR INSTAGRAM REELS & TIKTOK • BRAND-CONSISTENT • EASY TO USE")
