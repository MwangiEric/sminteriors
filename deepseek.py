import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import tempfile, os, numpy as np, io, random
from moviepy.editor import ImageSequenceClip, AudioFileClip
import math

st.set_page_config(page_title="SM Interiors DIY Tips Animator", layout="wide", page_icon="💡")

WIDTH, HEIGHT = 1080, 1920
FPS = 30

# SIMPLIFIED CONFIG
DIY_CATEGORIES = {
    "furniture": "🪑 Furniture",
    "cleaning": "🧽 Cleaning", 
    "decor": "🎨 Decor",
}

def calculate_duration(text):
    """Simple duration calculator"""
    words = len(text.split())
    if words <= 15: return 5
    elif words <= 25: return 6  
    elif words <= 35: return 7
    else: return 8

def create_safe_frame(tip_text, tip_title, template_name):
    """Create a single safe frame without complex animations"""
    # Simple background
    bg = Image.new("RGB", (WIDTH, HEIGHT), "#0F0A05")
    draw = ImageDraw.Draw(bg)
    
    # Add simple gold elements
    draw.rectangle([100, 100, 200, 150], fill="#FFD700")
    draw.rectangle([WIDTH-200, HEIGHT-200, WIDTH-100, HEIGHT-150], fill="#FFD700")
    
    # Safe font loading
    try:
        title_font = ImageFont.truetype("Arial", 80)
        text_font = ImageFont.truetype("Arial", 60)
    except:
        # Use default font if Arial not available
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
    
    # Safe title - centered and truncated if too long
    safe_title = tip_title[:20]  # Max 20 chars
    title_bbox = draw.textbbox((0, 0), safe_title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (WIDTH - title_width) // 2
    draw.text((title_x, 200), safe_title, font=title_font, fill="#FFD700")
    
    # Safe text wrapping
    words = tip_text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=text_font)
        test_width = bbox[2] - bbox[0]
        
        if test_width < WIDTH - 100:  # 50px margins
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
        if len(lines) >= 4:  # Max 4 lines
            break
    
    if current_line and len(lines) < 4:
        lines.append(' '.join(current_line))
    
    # Render text lines
    line_height = 80
    start_y = 600
    
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=text_font)
        line_width = bbox[2] - bbox[0]
        x = (WIDTH - line_width) // 2
        y = start_y + (i * line_height)
        
        # Text background for readability
        padding = 20
        draw.rectangle([
            x - padding, y - padding,
            x + line_width + padding, y + line_height
        ], fill="#1A1208")
        
        draw.text((x, y), line, font=text_font, fill="#FFFFFF")
    
    # Simple CTA at bottom
    cta = "👉 SWIPE FOR MORE TIPS"
    cta_bbox = draw.textbbox((0, 0), cta, font=text_font)
    cta_width = cta_bbox[2] - cta_bbox[0]
    cta_x = (WIDTH - cta_width) // 2
    draw.text((cta_x, HEIGHT - 150), cta, font=text_font, fill="#FFD700")
    
    return np.array(bg)

def generate_simple_video(tip_text, tip_title, template, music_key, output_path):
    """Generate video with minimal complexity"""
    duration = calculate_duration(tip_text)
    frames = []
    
    # Generate simple frames (no complex animations)
    for i in range(FPS * duration):
        frame = create_safe_frame(tip_text, tip_title, template)
        frames.append(frame)
    
    # Create clip
    clip = ImageSequenceClip(frames, fps=FPS)
    
    # Try to add audio if available
    try:
        audio_path = f"audio/{music_key.lower().replace(' ', '_')}.mp3"
        if os.path.exists(audio_path):
            audio = AudioFileClip(audio_path).subclip(0, duration)
            clip = clip.set_audio(audio)
    except:
        pass  # Continue without audio
    
    # Export with safe settings
    clip.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac" if clip.audio else None,
        verbose=False,
        logger=None
    )
    
    clip.close()
    return True

# UI
st.title("💡 SM Interiors DIY Tips Animator")
st.caption("Simple & Stable Version")

# Mode selection
mode = st.radio("Mode", ["Single Tip", "Multiple Tips"], horizontal=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Content")
    
    if mode == "Single Tip":
        tip_title = st.text_input("Tip Title", "DIY PRO TIP", max_chars=20)
        tip_text = st.text_area(
            "Tip Description", 
            "Mix equal parts vinegar and water for natural wood cleaning. Apply with soft cloth and buff dry.",
            height=100
        )
        
        if tip_text:
            duration = calculate_duration(tip_text)
            st.info(f"Duration: {duration} seconds ({len(tip_text.split())} words)")
    
    else:  # Multiple Tips
        st.subheader("Batch Tips")
        num_tips = st.slider("Number of Tips", 2, 4, 2)
        
        tips = []
        for i in range(num_tips):
            with st.expander(f"Tip {i+1}"):
                title = st.text_input(f"Title {i+1}", f"Tip {i+1}", key=f"title_{i}")
                text = st.text_area(f"Description {i+1}", f"Simple DIY tip number {i+1}", key=f"text_{i}")
                tips.append({"title": title, "text": text})

with col2:
    st.subheader("Settings")
    
    template = st.selectbox("Template", ["Simple Gold", "Modern Brown"])
    music_key = st.selectbox("Music", ["Elegant Flow", "Gold Luxury", "Viral Pulse"])
    
    if mode == "Single Tip":
        st.write("**Preview**")
        if st.button("Update Preview"):
            preview_frame = create_safe_frame(tip_text, tip_title, template)
            st.image(Image.fromarray(preview_frame), use_column_width=True)

# GENERATION
if mode == "Single Tip":
    if st.button("🎬 GENERATE SINGLE VIDEO", type="primary", use_container_width=True):
        if not tip_text.strip():
            st.error("Please enter tip text")
        else:
            with st.spinner("Creating video..."):
                try:
                    output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
                    
                    if generate_simple_video(tip_text, tip_title, template, music_key, output_path):
                        st.success("✅ VIDEO READY!")
                        st.video(output_path)
                        
                        with open(output_path, "rb") as f:
                            st.download_button(
                                "⬇️ DOWNLOAD VIDEO",
                                f,
                                "SM_DIY_Tip.mp4",
                                "video/mp4",
                                use_container_width=True
                            )
                    
                    # Cleanup
                    if os.path.exists(output_path):
                        os.unlink(output_path)
                        
                except Exception as e:
                    st.error(f"Generation failed: {str(e)}")
                    st.info("💡 Try using shorter text or different content.")

else:  # Multiple Tips
    if st.button("🎬 GENERATE ALL VIDEOS", type="primary", use_container_width=True):
        if not tips or not any(tip['text'].strip() for tip in tips):
            st.error("Please enter tip content")
        else:
            progress_bar = st.progress(0)
            
            for i, tip in enumerate(tips):
                if tip['text'].strip():
                    progress_bar.progress((i) / len(tips))
                    
                    with st.expander(f"Generating: {tip['title']}"):
                        try:
                            output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
                            
                            if generate_simple_video(tip['text'], tip['title'], template, music_key, output_path):
                                with open(output_path, "rb") as f:
                                    st.download_button(
                                        f"⬇️ Download: {tip['title']}",
                                        f,
                                        f"SM_Tip_{i+1}.mp4",
                                        "video/mp4"
                                    )
                            
                            if os.path.exists(output_path):
                                os.unlink(output_path)
                                
                        except Exception as e:
                            st.error(f"Failed tip {i+1}: {str(e)}")
            
            progress_bar.progress(1.0)
            st.success("✅ Batch complete!")

st.markdown("---")
st.caption("✅ SIMPLE & STABLE • AUTO DURATION • BATCH PROCESSING")
