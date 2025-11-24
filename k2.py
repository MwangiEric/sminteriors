# app.py (Pillow 10 + Pyodide compatible - IMPROVED)
import streamlit as st
import numpy as np
import imageio
import tempfile
import shutil
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
            # Scale default font if possible
            if hasattr(font, 'size'):
                # Create a larger default font by loading at specific size
                font = ImageFont.load_default()
        except:
            # Ultimate fallback - create a basic font
            font = ImageFont.load_default()
    
    return font

# ------------- Optimized frame generation -------------
def create_gradient_background(W=1920, H=1080):
    """Create gradient background once and reuse"""
    gradient = np.zeros((H, W, 3), dtype=np.uint8)
    for i in range(H):
        r = max(0, min(255, 30 - i // 20))
        g = max(0, min(255, 15 - i // 25))
        b = max(0, min(255, 60 - i // 30))
        gradient[i, :, 0] = r
        gradient[i, :, 1] = g
        gradient[i, :, 2] = b
    return gradient

def create_frame(text, background, W=1920, H=1080):
    """Create a single frame with text overlay"""
    # Convert background to PIL Image
    img = Image.fromarray(background.copy())
    draw = ImageDraw.Draw(img)
    
    font = get_font(120)
    
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
    
    # Draw text with shadow for better visibility
    shadow_color = (0, 100, 100)
    text_color = (0, 245, 255)
    
    # Text shadow
    draw.text((x+3, y+3), text, font=font, fill=shadow_color)
    # Main text
    draw.text((x, y), text, font=font, fill=text_color)
    
    return np.array(img)

# ------------- Main UI -------------
with st.container():
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;color:#ffffff'>✨ Typing Animation → MP4 ✨</h2>", unsafe_allow_html=True)

    sentence = st.text_input(
        "", 
        "Hello! This text will be typed in exactly six seconds.", 
        placeholder="Type your own sentence…",
        max_chars=200  # Prevent extremely long texts
    )
    
    # Configuration options
    col1, col2 = st.columns(2)
    with col1:
        duration = st.slider("Duration (seconds)", 2, 10, 6)
    with col2:
        resolution = st.selectbox("Resolution", ["720p", "1080p", "480p"], index=1)

    resolution_map = {
        "480p": (854, 480),
        "720p": (1280, 720), 
        "1080p": (1920, 1080)
    }
    W, H = resolution_map[resolution]

    if st.button("▶️ Generate MP4", type="primary"):
        if not sentence:
            st.warning("Please enter some text.")
            st.stop()

        with st.spinner("Creating your typing animation..."):
            fps = 30
            total_frames = duration * fps
            chars_per_frame = len(sentence) / total_frames

            # Create temporary directory
            tmpdir = Path(tempfile.mkdtemp())
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # Precompute gradient background
                status_text.text("Preparing background...")
                background = create_gradient_background(W, H)
                
                # Generate frames
                frames_dir = tmpdir / "frames"
                frames_dir.mkdir()
                
                status_text.text("Generating frames...")
                for frm in range(total_frames):
                    n = min(int(round(chars_per_frame * (frm + 1))), len(sentence))
                    
                    # Create frame
                    frame_array = create_frame(sentence[:n], background, W, H)
                    
                    # Save frame
                    imageio.imwrite(frames_dir / f"{frm:05d}.png", frame_array)
                    
                    # Update progress
                    if frm % 10 == 0:
                        progress_bar.progress(frm / total_frames)

                progress_bar.progress(1.0)
                status_text.text("Creating MP4 video...")

                # Create MP4
                out_mp4 = tmpdir / "typing.mp4"
                
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
                
                # Offer download
                with open(out_mp4, "rb") as f:
                    st.download_button(
                        label="⬇️ Download MP4", 
                        data=f, 
                        file_name="typing_animation.mp4", 
                        mime="video/mp4",
                        type="primary"
                    )
                
                st.success(f"✅ Success! Created {duration}-second typing animation at {resolution} resolution.")

            except Exception as e:
                st.error(f"❌ Error creating animation: {str(e)}")
                st.info("💡 Tip: Try shorter text or lower resolution if you're experiencing issues.")
            finally:
                # Cleanup
                try:
                    shutil.rmtree(tmpdir, ignore_errors=True)
                except:
                    pass
                progress_bar.empty()
                status_text.empty()

    st.markdown("</div>", unsafe_allow_html=True)
