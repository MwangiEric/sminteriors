# app.py (Pillow 10 + Pyodide compatible - PORTRAIT + ANIMATED BACKGROUND)
import streamlit as st
import numpy as np
import imageio
import tempfile
import shutil
import base64
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import os

st.set_page_config(page_title="Typing → MP4", layout="centered")

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

# ------------- Improved font handling -------------
def get_font(size=120):
    """Get a font that works across platforms including Pyodide"""
    font = None
    
    # Try different font options
    font_options = [
        "Arial.ttf", 
        "arial.ttf",
        "DejaVuSans.ttf",
        "LiberationSans-Regular.ttf",
        "FreeSans.ttf"
    ]
    
    for font_name in font_options:
        try:
            font = ImageFont.truetype(font_name, size)
            break
        except (OSError, AttributeError):
            continue
    
    # Final fallback to default font
    if font is None:
        try:
            font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
    
    return font

# ------------- Animated Brown/Gold Background -------------
def create_animated_brown_gold_background(W=1080, H=1920, frame_index=0, total_frames=180):
    """Create animated brown and gold background that changes over time"""
    # Base colors for brown and gold palette
    dark_brown = (101, 67, 33)      # Deep brown
    medium_brown = (139, 90, 43)    # Medium brown
    light_brown = (181, 136, 83)    # Light brown
    dark_gold = (205, 164, 52)      # Dark gold
    medium_gold = (218, 179, 70)    # Medium gold
    light_gold = (230, 194, 100)    # Light gold
    
    # Create gradient background with animation
    background = np.zeros((H, W, 3), dtype=np.uint8)
    
    # Animated parameters
    time_progress = frame_index / total_frames
    wave1 = math.sin(time_progress * 2 * math.pi) * 0.5 + 0.5  # 0 to 1
    wave2 = math.sin(time_progress * 4 * math.pi + 1) * 0.5 + 0.5
    wave3 = math.cos(time_progress * 3 * math.pi) * 0.5 + 0.5
    
    for y in range(H):
        # Vertical gradient mixed with waves
        vertical_progress = y / H
        
        # Create animated wave patterns
        wave_offset1 = math.sin(vertical_progress * 8 * math.pi + time_progress * 6 * math.pi) * 20
        wave_offset2 = math.cos(vertical_progress * 6 * math.pi + time_progress * 4 * math.pi) * 15
        
        # Dynamic color mixing based on animation
        if vertical_progress < 0.3:
            # Bottom section - more brown
            mix = vertical_progress / 0.3
            r = int(dark_brown[0] * (1 - mix) + medium_brown[0] * mix)
            g = int(dark_brown[1] * (1 - mix) + medium_brown[1] * mix)
            b = int(dark_brown[2] * (1 - mix) + medium_brown[2] * mix)
        elif vertical_progress < 0.7:
            # Middle section - brown to gold transition
            mix = (vertical_progress - 0.3) / 0.4
            r = int(medium_brown[0] * (1 - mix) + dark_gold[0] * mix)
            g = int(medium_brown[1] * (1 - mix) + dark_gold[1] * mix)
            b = int(medium_brown[2] * (1 - mix) + dark_gold[2] * mix)
        else:
            # Top section - more gold
            mix = (vertical_progress - 0.7) / 0.3
            r = int(dark_gold[0] * (1 - mix) + light_gold[0] * mix)
            g = int(dark_gold[1] * (1 - mix) + light_gold[1] * mix)
            b = int(dark_gold[2] * (1 - mix) + light_gold[2] * mix)
        
        # Add wave animation effects
        wave_effect = int((wave_offset1 + wave_offset2) * wave1)
        r = max(0, min(255, r + wave_effect))
        g = max(0, min(255, g + wave_effect // 2))
        b = max(0, min(255, b - wave_effect // 3))
        
        # Add sparkling gold effect
        if wave2 > 0.7 and (y + frame_index) % 20 < 2:
            sparkle_intensity = int(wave2 * 50)
            r = min(255, r + sparkle_intensity)
            g = min(255, g + sparkle_intensity)
            b = min(255, b)
        
        # Apply horizontal gradient with animation
        for x in range(W):
            horizontal_progress = x / W
            horizontal_wave = math.sin(horizontal_progress * 4 * math.pi + time_progress * 2 * math.pi) * 10
            
            final_r = max(0, min(255, r + int(horizontal_wave * wave3)))
            final_g = max(0, min(255, g + int(horizontal_wave * wave3 * 0.7)))
            final_b = max(0, min(255, b + int(horizontal_wave * wave3 * 0.3)))
            
            background[y, x] = [final_r, final_g, final_b]
    
    return background

# ------------- Frame Generation -------------
def create_frame(text, frame_index, total_frames, W=1080, H=1920):
    """Create a single frame with animated background and text overlay"""
    # Create animated background
    background = create_animated_brown_gold_background(W, H, frame_index, total_frames)
    
    # Convert background to PIL Image
    img = Image.fromarray(background)
    draw = ImageDraw.Draw(img)
    
    # Adjust font size for portrait orientation
    font_size = min(80, max(40, 80 - max(0, len(text) - 30) * 2))  # Dynamic font sizing
    font = get_font(font_size)
    
    try:
        # Modern Pillow textbbox method
        bbox = draw.textbbox((0, 0), text, font=font)
        left, top, right, bottom = bbox
        tw, th = right - left, bottom - top
        x, y = (W - tw) // 2 - left, (H - th) // 2 - top
    except AttributeError:
        # Fallback for older Pillow versions
        try:
            tw, th = draw.textsize(text, font=font)
            x, y = (W - tw) // 2, (H - th) // 2
        except:
            # Ultimate fallback
            tw, th = 100, 100
            x, y = (W - tw) // 2, (H - th) // 2
    
    # Draw text with elegant styling
    shadow_color = (60, 40, 20)  # Dark brown shadow
    text_color = (255, 215, 0)   # Gold text
    
    # Text shadow (multiple offsets for depth)
    for dx, dy in [(3, 3), (2, 2), (1, 1)]:
        draw.text((x+dx, y+dy), text, font=font, fill=shadow_color)
    
    # Main text
    draw.text((x, y), text, font=font, fill=text_color)
    
    # Add subtle glow effect
    glow_color = (255, 230, 150, 100)  # Light gold with transparency
    for glow_size in [2, 1]:
        try:
            glow_font = get_font(font_size + glow_size)
            bbox_glow = draw.textbbox((0, 0), text, font=glow_font)
            left_g, top_g, right_g, bottom_g = bbox_glow
            tw_g, th_g = right_g - left_g, bottom_g - top_g
            x_g, y_g = (W - tw_g) // 2 - left_g, (H - th_g) // 2 - top_g
            # Create a temporary image for glow effect
            glow_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow_img)
            glow_draw.text((x_g, y_g), text, font=glow_font, fill=glow_color)
            # Composite the glow
            img = Image.alpha_composite(img.convert("RGBA"), glow_img).convert("RGB")
        except:
            pass
    
    return np.array(img)

def get_video_html(video_path):
    """Convert video file to HTML video element with base64 encoding"""
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
    st.markdown("<h2 style='text-align:center;color:#ffffff'>✨ Portrait Typing Animation → MP4 ✨</h2>", unsafe_allow_html=True)

    sentence = st.text_input(
        "", 
        "Hello! This beautiful text animates with golden elegance.", 
        placeholder="Type your own sentence…",
        max_chars=150  # Slightly reduced for portrait mode
    )
    
    # Configuration options
    col1, col2 = st.columns(2)
    with col1:
        duration = st.slider("Duration (seconds)", 2, 10, 6)
    with col2:
        resolution = st.selectbox("Resolution", ["1080x1920 Portrait", "720x1280 Portrait", "540x960 Portrait"], index=0)

    resolution_map = {
        "540x960 Portrait": (540, 960),
        "720x1280 Portrait": (720, 1280), 
        "1080x1920 Portrait": (1080, 1920)
    }
    W, H = resolution_map[resolution]

    if st.button("✨ Generate MP4", type="primary"):
        if not sentence:
            st.warning("Please enter some text.")
            st.stop()

        with st.spinner("Creating your golden typing animation..."):
            fps = 30
            total_frames = duration * fps
            chars_per_frame = len(sentence) / total_frames

            # Create temporary directory
            tmpdir = Path(tempfile.mkdtemp())
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # Generate frames
                frames_dir = tmpdir / "frames"
                frames_dir.mkdir()
                
                status_text.text("Creating animated golden frames...")
                for frm in range(total_frames):
                    n = min(int(round(chars_per_frame * (frm + 1))), len(sentence))
                    
                    # Create frame with animated background
                    frame_array = create_frame(sentence[:n], frm, total_frames, W, H)
                    
                    # Save frame
                    imageio.imwrite(frames_dir / f"{frm:05d}.png", frame_array)
                    
                    # Update progress
                    if frm % 10 == 0:
                        progress_bar.progress(frm / total_frames)
                        status_text.text(f"Creating animated golden frames... {int(frm/total_frames*100)}%")

                progress_bar.progress(1.0)
                status_text.text("Creating MP4 video...")

                # Create MP4
                out_mp4 = tmpdir / "typing_portrait.mp4"
                
                # Use imageio with safe parameters
                with imageio.get_writer(
                    out_mp4, 
                    fps=fps, 
                    codec="libx264",
                    quality=8,
                    pixelformat="yuv420p"
                ) as writer:
                    for frm in range(total_frames):
                        frame_path = frames_dir / f"{frm:05d}.png"
                        frame_data = imageio.imread(frame_path)
                        writer.append_data(frame_data)
                        
                        # Clean up frame file immediately to save memory
                        if frm % 5 == 0:
                            frame_path.unlink(missing_ok=True)

                status_text.text("Finalizing...")
                
                # Store video path in session state for display
                st.session_state.generated_video_path = out_mp4
                st.session_state.show_video = True
                
                # Success message
                st.success(f"✅ Success! Created {duration}-second portrait animation with golden brown background!")

            except Exception as e:
                st.error(f"❌ Error creating animation: {str(e)}")
                st.info("💡 Tip: Try shorter text or lower resolution if you're experiencing issues.")
                st.session_state.show_video = False
            finally:
                progress_bar.empty()
                status_text.empty()

    # Display the generated video if available
    if hasattr(st.session_state, 'show_video') and st.session_state.show_video:
        if hasattr(st.session_state, 'generated_video_path') and st.session_state.generated_video_path.exists():
            st.markdown("### 🎥 Your Golden Portrait Animation")
            
            # Display video using HTML for better control
            video_html = get_video_html(st.session_state.generated_video_path)
            st.markdown(video_html, unsafe_allow_html=True)
            
            # Download button
            with open(st.session_state.generated_video_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download MP4", 
                    data=f, 
                    file_name="golden_typing_portrait.mp4", 
                    mime="video/mp4",
                    type="primary"
                )
            
            st.markdown("---")
            
            # Cleanup previous video when generating new one
            if 'previous_video_path' in st.session_state and st.session_state.previous_video_path != st.session_state.generated_video_path:
                try:
                    if st.session_state.previous_video_path.exists():
                        st.session_state.previous_video_path.unlink()
                except:
                    pass
            
            st.session_state.previous_video_path = st.session_state.generated_video_path

    # Add information about the animation
    with st.expander("ℹ️ About this Animation"):
        st.markdown("""
        **Features:**
        - 🎨 **Animated Brown & Gold Background**: Smooth color transitions with wave effects
        - 📱 **Portrait Orientation**: Perfect for mobile viewing (1080x1920)
        - ✨ **Golden Text**: Elegant typography with glow effects
        - 🌊 **Dynamic Animation**: Background evolves throughout the video
        - 🎬 **Professional Quality**: 30 FPS smooth animation
        
        **Perfect for:**
        - Social media stories
        - Mobile content
        - Professional presentations
        - Creative projects
        """)

    st.markdown("</div>", unsafe_allow_html=True)
