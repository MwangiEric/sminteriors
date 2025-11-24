# app.py (OPTIMIZED - Smart Typing Layout + Animated BG)
import streamlit as st
import numpy as np
import imageio
import tempfile
import base64
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import os

st.set_page_config(page_title="Smart Typing → MP4", layout="centered")

st.markdown(
    """
    <style>
    @keyframes gradientShift{
      0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%}
    }
    .main {
        background: linear-gradient(-45deg,#0f0c29,#302b63,#24243e,#0f0c29);
        background-size:400% 400%; animation:gradientShift 12s ease infinite;
    }
    .glass {
        background:rgba(255,255,255,0.06); border-radius:16px;
        box-shadow:0 4px 30px rgba(0,0,0,.2); backdrop-filter:blur(7px);
        border:1px solid rgba(255,255,255,.1); padding:2rem 3rem;
        margin:3rem auto; max-width:700px;
    }
    .video-container {
        margin: 2rem 0;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------- Smart Text Layout System -------------
class SmartTextLayout:
    def __init__(self, width, height, margins=100):
        self.width = width
        self.height = height
        self.margins = margins
        self.content_width = width - 2 * margins
        self.content_height = height - 2 * margins
        
    def calculate_font_size(self, text, max_font=80, min_font=24):
        """Calculate optimal font size based on text length and available space"""
        avg_chars_per_line = max(10, self.content_width // 30)  # Estimate based on width
        estimated_lines = max(1, len(text) // avg_chars_per_line)
        
        # Calculate max font size that fits vertically
        max_possible_font = min(max_font, self.content_height // max(estimated_lines, 1))
        font_size = max(min_font, max_possible_font - len(text) // 20)
        
        return font_size
    
    def break_text_into_lines(self, text, font):
        """Break text into lines that fit within content width"""
        words = text.split(' ')
        lines = []
        current_line = []
        
        draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
        
        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            
            try:
                bbox = draw.textbbox((0, 0), test_line, font=font)
                line_width = bbox[2] - bbox[0]
            except:
                line_width = len(test_line) * font.size // 2
            
            if line_width > self.content_width:
                # Remove the last word and start new line
                current_line.pop()
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Single word is too long, force break
                    lines.append(word[:20] + '...')
                    current_line = []
        
        if current_line:
            lines.append(' '.join(current_line))
            
        return lines
    
    def calculate_start_position(self, lines, font, line_height):
        """Calculate starting Y position to center text block vertically"""
        total_text_height = len(lines) * line_height
        start_y = self.margins + (self.content_height - total_text_height) // 2
        return max(self.margins, start_y)

# ------------- Optimized Background Animation -------------
def create_animated_gold_brown_bg(width, height, time_progress):
    """Create animated brown/gold background using vectorized operations"""
    # Create coordinate grids
    y, x = np.ogrid[0:height, 0:width]
    
    # Normalize coordinates
    y_norm = y / height
    x_norm = x / width
    
    # Time-based animation parameters
    t = time_progress * 2 * math.pi
    
    # Brown to gold gradient (vectorized)
    # Base gradient from dark brown to light gold
    base_r = (101 * (1 - y_norm) + 218 * y_norm).astype(np.uint8)
    base_g = (67 * (1 - y_norm) + 165 * y_norm).astype(np.uint8)
    base_b = (33 * (1 - y_norm) + 32 * y_norm).astype(np.uint8)
    
    # Animated wave patterns
    wave1 = np.sin(x_norm * 6 * math.pi + t) * 20
    wave2 = np.cos(y_norm * 4 * math.pi + t * 1.5) * 15
    wave3 = np.sin(x_norm * 3 * math.pi + y_norm * 5 * math.pi + t * 0.7) * 10
    
    # Combine waves
    combined_wave = wave1 + wave2 + wave3
    
    # Apply waves to create animated texture
    r = np.clip(base_r + combined_wave * 0.8, 0, 255)
    g = np.clip(base_g + combined_wave * 0.6, 0, 255)
    b = np.clip(base_b + combined_wave * 0.3, 0, 255)
    
    # Create final background
    background = np.stack([r, g, b], axis=-1)
    
    # Add occasional gold sparkles
    sparkle_mask = (np.sin(x * y * 0.0001 + t * 5) > 0.98) & (y_norm > 0.2) & (y_norm < 0.8)
    background[sparkle_mask] = [255, 223, 0]
    
    return background

# ------------- Smart Frame Generation -------------
def create_smart_typing_frame(full_text, chars_visible, frame_index, total_frames, width=1080, height=1920):
    """Create frame with smart text layout and animated background"""
    # Calculate time progress for background animation
    time_progress = frame_index / total_frames
    
    # Create animated background
    bg = create_animated_gold_brown_bg(width, height, time_progress)
    img = Image.fromarray(bg)
    draw = ImageDraw.Draw(img)
    
    # Initialize layout system
    layout = SmartTextLayout(width, height)
    
    # Calculate optimal font size
    font_size = layout.calculate_font_size(full_text)
    try:
        font = ImageFont.truetype("Arial.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
    
    # Get visible portion of text
    visible_text = full_text[:chars_visible]
    
    # Break text into lines
    lines = layout.break_text_into_lines(visible_text, font)
    
    # Calculate line height
    try:
        bbox = draw.textbbox((0, 0), "Test", font=font)
        line_height = (bbox[3] - bbox[1]) * 1.4
    except:
        line_height = font_size * 1.4
    
    # Calculate starting position
    start_y = layout.calculate_start_position(lines, font, line_height)
    
    # Draw each line with animation effects
    shadow_color = (70, 45, 20)  # Dark brown shadow
    text_color = (255, 215, 0)   # Gold text
    
    for i, line in enumerate(lines):
        y_pos = start_y + i * line_height
        
        # Calculate line width for centering
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
        except:
            line_width = len(line) * font_size // 2
        
        x_pos = (width - line_width) // 2
        
        # Draw text shadow for depth
        draw.text((x_pos + 2, y_pos + 2), line, font=font, fill=shadow_color)
        
        # Draw main text
        draw.text((x_pos, y_pos), line, font=font, fill=text_color)
    
    return np.array(img)

# ------------- Fast Video Generation -------------
def generate_smart_typing_video(sentence, duration, width, height, output_path):
    """Generate video with smart typing layout"""
    fps = 30
    total_frames = duration * fps
    total_chars = len(sentence)
    chars_per_frame = total_chars / total_frames
    
    # Pre-calculate layout once
    layout = SmartTextLayout(width, height)
    font_size = layout.calculate_font_size(sentence)
    
    with imageio.get_writer(
        output_path, 
        fps=fps, 
        codec="libx264",
        quality=8,
        pixelformat="yuv420p"
    ) as writer:
        
        for frame_idx in range(total_frames):
            # Calculate characters to show
            chars_to_show = min(int(chars_per_frame * (frame_idx + 1)), total_chars)
            
            # Create frame
            frame = create_smart_typing_frame(
                sentence, chars_to_show, frame_idx, total_frames, width, height
            )
            
            writer.append_data(frame)
            
            # Yield progress
            if frame_idx % 10 == 0:
                yield frame_idx / total_frames
    
    yield 1.0  # Complete

def get_video_html(video_path):
    """Convert video file to HTML video element"""
    try:
        with open(video_path, "rb") as video_file:
            video_bytes = video_file.read()
        video_b64 = base64.b64encode(video_bytes).decode()
        video_html = f'''
        <div class="video-container">
            <video controls style="width:100%; border-radius:8px;">
                <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        </div>
        '''
        return video_html
    except Exception as e:
        return f"<p style='color:red;'>Error loading video: {str(e)}</p>"

# ------------- Main UI -------------
with st.container():
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;color:#ffffff'>✨ Smart Typing Animation ✨</h2>", unsafe_allow_html=True)

    # Configuration
    col1, col2 = st.columns(2)
    with col1:
        duration = st.slider("Duration (seconds)", 2, 6, 4)
    with col2:
        resolution = st.selectbox("Resolution", ["720x1280", "1080x1920"], index=1)

    resolution_map = {
        "720x1280": (720, 1280), 
        "1080x1920": (1080, 1920)
    }
    W, H = resolution_map[resolution]

    sentence = st.text_area(
        "Text to animate:", 
        "Welcome to this beautiful typing animation with smart text layout and golden brown background effects!",
        height=80,
        max_chars=300,
        placeholder="Enter your text here... (up to 300 characters)"
    )

    if st.button("🚀 Generate Smart Animation", type="primary"):
        if not sentence.strip():
            st.warning("Please enter some text.")
            st.stop()

        if len(sentence) > 300:
            st.warning("Text too long! Please limit to 300 characters.")
            st.stop()

        with st.spinner("Creating smart typing animation..."):
            import tempfile
            tmpdir = Path(tempfile.mkdtemp())
            out_mp4 = tmpdir / "smart_typing.mp4"
            
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Generate video
                status_text.text("🔄 Calculating optimal text layout...")
                
                for progress in generate_smart_typing_video(sentence, duration, W, H, out_mp4):
                    progress_bar.progress(progress)
                    if progress < 1.0:
                        status_text.text(f"🎬 Generating frames... {int(progress * 100)}%")
                    else:
                        status_text.text("✅ Finalizing video...")
                
                # Store results
                st.session_state.generated_video_path = out_mp4
                st.session_state.show_video = True
                st.session_state.video_tmpdir = tmpdir
                
                st.success(f"✨ Done! Generated {duration}-second smart typing animation")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import shutil
                try:
                    shutil.rmtree(tmpdir, ignore_errors=True)
                except:
                    pass

    # Display video if available
    if hasattr(st.session_state, 'show_video') and st.session_state.show_video:
        if (hasattr(st.session_state, 'generated_video_path') and 
            st.session_state.generated_video_path.exists()):
            
            st.markdown("### 🎥 Your Smart Typing Animation")
            
            # Display video
            video_html = get_video_html(st.session_state.generated_video_path)
            st.markdown(video_html, unsafe_allow_html=True)
            
            # Download button
            with open(st.session_state.generated_video_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download MP4", 
                    data=f, 
                    file_name="smart_typing_animation.mp4", 
                    mime="video/mp4",
                    type="primary"
                )

    # Features explanation
    with st.expander("🧠 Smart Features"):
        st.markdown("""
        **Intelligent Text Layout:**
        - 📐 **Automatic Font Sizing**: Font size adjusts based on text length
        - 📝 **Smart Line Breaking**: Text automatically wraps to fit screen width
        - 🎯 **Vertical Centering**: Text block is perfectly centered vertically
        - 📏 **Dynamic Margins**: Optimal spacing calculated automatically
        
        **Beautiful Animations:**
        - 🎨 **Animated Brown/Gold Background**: Smooth color transitions with wave effects
        - ✨ **Gold Sparkles**: Subtle sparkling effects throughout
        - 🌊 **Multi-layer Waves**: Complex wave patterns for rich texture
        - 💫 **Time-based Evolution**: Background changes throughout animation
        
        **Performance Optimized:**
        - ⚡ **Vectorized Operations**: Fast NumPy-based background generation
        - 🎞️ **Direct Frame Streaming**: No intermediate file storage
        - 🔄 **Progressive Rendering**: Real-time progress updates
        """)

    st.markdown("</div>", unsafe_allow_html=True)

# Cleanup
if hasattr(st.session_state, 'video_tmpdir') and not hasattr(st.session_state, 'show_video'):
    import shutil
    try:
        shutil.rmtree(st.session_state.video_tmpdir, ignore_errors=True)
    except:
        pass
