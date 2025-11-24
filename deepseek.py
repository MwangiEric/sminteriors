# app.py (FIXED - Logo in Videos + Groq Integration + Proper Text Sizing)
import streamlit as st
import numpy as np
import imageio
import tempfile
import base64
import math
import random
import requests
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

# Set page config first
st.set_page_config(page_title="DIY Animation Creator", layout="centered")

# Use groq_key from secrets
GROQ_API_KEY = st.secrets.get("groq_key", os.getenv("GROQ_API_KEY"))

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
        margin:2rem auto; max-width:800px;
    }
    .video-container {
        margin: 2rem 0;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .feature-card {
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #ffd700;
    }
    .logo-container {
        text-align: center;
        margin-bottom: 1rem;
    }
    .logo {
        max-width: 200px;
        height: auto;
    }
    .diy-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------- Logo Integration -------------
def load_logo():
    """Load and resize logo for video frames"""
    logo_url = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"
    try:
        response = requests.get(logo_url)
        logo_image = Image.open(io.BytesIO(response.content))
        # Resize logo to appropriate size for videos
        logo_size = (120, 60)  # Width, Height - good size for video overlay
        logo_image = logo_image.resize(logo_size, Image.Resampling.LANCZOS)
        return logo_image
    except Exception as e:
        st.warning(f"Could not load logo: {e}")
        # Create a simple text logo as fallback
        img = Image.new('RGBA', (120, 60), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("Arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        draw.text((10, 20), "LOGO", fill=(255, 215, 0), font=font)
        return img

# ------------- FIXED Background Systems -------------
class StableBackgroundGenerator:
    def __init__(self):
        self.themes = {
            "Golden Elegance": self.golden_elegance,
            "Deep Amber": self.deep_amber,
            "Vintage Sepia": self.vintage_sepia,
        }
    
    def golden_elegance(self, width, height, time_progress):
        """Fixed background generation with consistent dimensions"""
        # Create consistent array shape
        bg = np.zeros((height, width, 3), dtype=np.uint8)
        
        for y in range(height):
            for x in range(width):
                # Simple gradient that's guaranteed to work
                r = int(100 + (155 * y / height) + math.sin(x * 0.01 + time_progress * 10) * 20)
                g = int(80 + (140 * y / height) + math.cos(y * 0.01 + time_progress * 8) * 15)
                b = int(40 + (60 * y / height) + math.sin((x + y) * 0.005 + time_progress * 12) * 10)
                
                bg[y, x] = [
                    max(0, min(255, r)),
                    max(0, min(255, g)),
                    max(0, min(255, b))
                ]
        
        return bg
    
    def deep_amber(self, width, height, time_progress):
        bg = np.zeros((height, width, 3), dtype=np.uint8)
        
        for y in range(height):
            for x in range(width):
                r = int(150 + (105 * y / height) + math.sin(x * 0.02 + time_progress * 6) * 25)
                g = int(100 + (80 * y / height) + math.cos(y * 0.015 + time_progress * 7) * 20)
                b = int(50 + (30 * y / height) + math.sin((x - y) * 0.01 + time_progress * 5) * 15)
                
                bg[y, x] = [
                    max(0, min(255, r)),
                    max(0, min(255, g)),
                    max(0, min(255, b))
                ]
        
        return bg
    
    def vintage_sepia(self, width, height, time_progress):
        bg = np.zeros((height, width, 3), dtype=np.uint8)
        
        for y in range(height):
            for x in range(width):
                r = int(120 + (80 * y / height) + (random.random() * 10 - 5))
                g = int(100 + (70 * y / height) + (random.random() * 10 - 5))
                b = int(80 + (40 * y / height) + (random.random() * 10 - 5))
                
                bg[y, x] = [r, g, b]
        
        return bg
    
    def get_theme(self, theme_name):
        return self.themes.get(theme_name, self.golden_elegance)

# ------------- RESPONSIVE Text Layout System -------------
class ResponsiveTextLayout:
    def __init__(self, width, height, margins=80):
        self.width = width
        self.height = height
        self.margins = margins
        self.content_width = width - 2 * margins
        self.content_height = height - 2 * margins
        
    def calculate_responsive_font_size(self, text):
        """Calculate font size based on BOTH screen dimensions AND text length"""
        text_length = len(text)
        
        # Base size from screen dimensions (responsive)
        base_size_from_screen = min(
            self.height / 12,  # 1080px / 12 = 90px
            self.width / 8     # 720px / 8 = 90px
        )
        
        # Adjust for text length
        if text_length < 20:
            font_size = base_size_from_screen * 1.6   # ~144px for short text
        elif text_length < 40:
            font_size = base_size_from_screen * 1.3   # ~117px
        elif text_length < 80:
            font_size = base_size_from_screen * 1.0   # ~90px
        elif text_length < 120:
            font_size = base_size_from_screen * 0.8   # ~72px
        else:
            font_size = base_size_from_screen * 0.7   # ~63px
        
        # Ensure reasonable bounds
        font_size = max(50, min(160, font_size))
        
        return int(font_size)
    
    def break_text_into_lines(self, text, font, max_width):
        """Break text into lines that fit the width"""
        words = text.split()
        lines = []
        current_line = []
        
        temp_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(temp_img)
        
        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            
            try:
                bbox = draw.textbbox((0, 0), test_line, font=font)
                line_width = bbox[2] - bbox[0]
            except:
                line_width = len(test_line) * font.size // 1.8
            
            if line_width > max_width:
                if len(current_line) == 1:
                    # Single word too long - break it
                    if len(word) > 15:
                        parts = [word[i:i+12] for i in range(0, len(word), 12)]
                        lines.extend(parts[:-1])
                        current_line = [parts[-1]]
                    else:
                        lines.append(word)
                        current_line = []
                else:
                    current_line.pop()
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines

# ------------- Top-to-Bottom Animation System -------------
class TopToBottomAnimator:
    def __init__(self):
        self.styles = {
            "Typewriter Top-to-Bottom": self.typewriter_effect,
            "Smooth Line-by-Line": self.smooth_line_effect,
        }
    
    def typewriter_effect(self, text, progress, line_info):
        """Text appears from top to bottom, line by line"""
        lines = line_info['lines']
        total_lines = len(lines)
        
        lines_to_show = int(total_lines * progress)
        partial_progress = (progress * total_lines) - lines_to_show
        
        revealed_lines = []
        for i in range(total_lines):
            if i < lines_to_show:
                revealed_lines.append(lines[i])
            elif i == lines_to_show:
                chars_to_show = int(len(lines[i]) * partial_progress)
                revealed_lines.append(lines[i][:chars_to_show])
            else:
                revealed_lines.append("")
        
        return "\n".join(revealed_lines), progress
    
    def smooth_line_effect(self, text, progress, line_info):
        """Each line appears completely in sequence"""
        lines = line_info['lines']
        total_lines = len(lines)
        
        # More distinct line appearances
        line_progress = progress * total_lines
        current_line = int(line_progress)
        
        revealed_lines = []
        for i in range(total_lines):
            if i < current_line:
                revealed_lines.append(lines[i])
            elif i == current_line:
                # Current line appears gradually
                line_portion = line_progress - current_line
                chars_to_show = int(len(lines[i]) * line_portion)
                revealed_lines.append(lines[i][:chars_to_show])
            else:
                revealed_lines.append("")
        
        return "\n".join(revealed_lines), progress

# ------------- FIXED Frame Generator -------------
class StableFrameGenerator:
    def __init__(self):
        self.bg_generator = StableBackgroundGenerator()
        self.text_animator = TopToBottomAnimator()
        self.logo = load_logo()
    
    def create_stable_frame(self, full_text, progress, frame_idx, total_frames, 
                          width, height, style_config):
        """Create frame with guaranteed consistent dimensions"""
        try:
            # Generate background with exact dimensions
            bg_theme = self.bg_generator.get_theme(style_config['background_theme'])
            time_progress = frame_idx / total_frames
            bg = bg_theme(width, height, time_progress)
            
            # Convert to PIL Image
            img = Image.fromarray(bg)
            draw = ImageDraw.Draw(img)
            
            # Add logo to top left
            if self.logo:
                logo_position = (30, 30)  # Top left with some margin
                img.paste(self.logo, logo_position, self.logo)
            
            # Calculate responsive layout
            layout = ResponsiveTextLayout(width, height)
            font_size = layout.calculate_responsive_font_size(full_text)
            
            try:
                font = ImageFont.truetype("Arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
            # Break text into lines
            lines = layout.break_text_into_lines(full_text, font, layout.content_width)
            
            line_info = {
                'lines': lines,
                'font': font,
                'font_size': font_size
            }
            
            # Apply animation
            animator = self.text_animator.styles[style_config['animation_style']]
            visible_text, anim_progress = animator(full_text, progress, line_info)
            
            # Calculate line height and start position
            try:
                bbox = draw.textbbox((0, 0), "Test", font=font)
                line_height = (bbox[3] - bbox[1]) * style_config['line_spacing']
            except:
                line_height = font_size * style_config['line_spacing'] * 1.4
            
            # Start from top (below logo)
            start_y = 120  # Below logo area
            
            visible_lines = visible_text.split('\n') if visible_text else []
            
            # Draw text
            text_color = self.hex_to_rgb(style_config['text_color'])
            shadow_color = self.hex_to_rgb(style_config['shadow_color'])
            
            for i, line in enumerate(visible_lines):
                if not line.strip():
                    continue
                    
                y_pos = start_y + i * line_height
                
                try:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    line_width = bbox[2] - bbox[0]
                except:
                    line_width = len(line) * font_size // 1.8
                
                x_pos = (width - line_width) // 2
                
                # Text shadow
                shadow_blur = 3
                draw.text((x_pos + shadow_blur, y_pos + shadow_blur), line, font=font, fill=shadow_color)
                
                # Main text
                draw.text((x_pos, y_pos), line, font=font, fill=text_color)
            
            # Convert back to numpy with guaranteed dimensions
            frame_array = np.array(img)
            if frame_array.shape != (height, width, 3):
                # Force correct dimensions if needed
                frame_array = np.zeros((height, width, 3), dtype=np.uint8)
                frame_array[:] = [50, 50, 50]  # Fallback color
            
            return frame_array.astype(np.uint8)
            
        except Exception as e:
            # Guaranteed fallback frame
            st.warning(f"Frame generation issue: {e}")
            fallback_frame = np.zeros((height, width, 3), dtype=np.uint8)
            fallback_frame[:, :] = [30, 30, 60]  # Dark blue fallback
            return fallback_frame
    
    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# ------------- Groq DIY Content Generator -------------
class GroqDIYGenerator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def generate_diy_content(self, topic, content_type="tips"):
        """Generate DIY tips, hashtags, or captions"""
        prompts = {
            "tips": f"Generate 3 practical DIY tips for: {topic}. Make them actionable and easy to follow. Keep each tip under 100 characters.",
            "hashtags": f"Generate 10 relevant hashtags for DIY projects about: {topic}. Include both popular and niche hashtags.",
            "captions": f"Write 2 engaging social media captions for DIY content about: {topic}. Make them inspiring and under 120 characters each."
        }
        
        prompt = prompts.get(content_type, prompts["tips"])
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "model": "llama-3.1-8b-instant",
            "max_tokens": 300,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(self.base_url, json=payload, headers=headers)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                return f"API Error: {response.status_code}"
        except Exception as e:
            return f"Connection error: {str(e)}"
    
    def generate_complete_diy_kit(self, topic):
        """Generate complete DIY content package"""
        results = {}
        for content_type in ["tips", "hashtags", "captions"]:
            results[content_type] = self.generate_diy_content(topic, content_type)
        return results

# ------------- Video Generation -------------
def generate_stable_video(sentence, duration, width, height, style_config, output_path):
    """Generate video with guaranteed stability"""
    fps = 24
    total_frames = duration * fps
    
    frame_generator = StableFrameGenerator()
    
    try:
        with imageio.get_writer(
            output_path, 
            fps=fps, 
            codec="libx264",
            quality=7,
            pixelformat="yuv420p"
        ) as writer:
            
            for frame_idx in range(total_frames):
                progress = (frame_idx + 1) / total_frames
                
                frame = frame_generator.create_stable_frame(
                    sentence, progress, frame_idx, total_frames, 
                    width, height, style_config
                )
                
                # Ensure frame is correct type and dimensions
                if frame.dtype != np.uint8:
                    frame = frame.astype(np.uint8)
                if frame.shape != (height, width, 3):
                    frame = np.zeros((height, width, 3), dtype=np.uint8)
                
                writer.append_data(frame)
                
                if frame_idx % 10 == 0:
                    yield frame_idx / total_frames
        
        yield 1.0
        
    except Exception as e:
        st.error(f"Video writing error: {e}")
        yield 1.0

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
def main():
    # Display logo
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    logo_image = load_logo()
    if logo_image and hasattr(logo_image, 'size'):
        # Resize for display
        display_logo = logo_image.resize((200, 100), Image.Resampling.LANCZOS)
        st.image(display_logo, width=200)
    st.markdown('</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center;color:#ffffff'>🎬 DIY Content Creator</h1>", unsafe_allow_html=True)
        
        # Groq DIY Assistant Section
        if GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here":
            st.markdown('<div class="diy-section">', unsafe_allow_html=True)
            st.markdown("### 🤖 DIY Content Assistant")
            
            col1, col2 = st.columns(2)
            
            with col1:
                diy_topic = st.text_input(
                    "DIY Topic:",
                    placeholder="e.g., home organization, woodworking, gardening",
                    key="diy_topic"
                )
                
                content_type = st.selectbox(
                    "Content Type:",
                    ["tips", "hashtags", "captions", "complete kit"],
                    key="content_type"
                )
                
                if st.button("🛠️ Generate DIY Content", key="generate_diy"):
                    if diy_topic:
                        with st.spinner("Creating your DIY content..."):
                            diy_generator = GroqDIYGenerator(GROQ_API_KEY)
                            
                            if content_type == "complete kit":
                                results = diy_generator.generate_complete_diy_kit(diy_topic)
                                st.session_state.diy_results = results
                            else:
                                result = diy_generator.generate_diy_content(diy_topic, content_type)
                                st.session_state.diy_results = {content_type: result}
            
            with col2:
                if 'diy_results' in st.session_state:
                    st.markdown("### 📋 Generated Content")
                    
                    if 'tips' in st.session_state.diy_results:
                        st.text_area("DIY Tips:", st.session_state.diy_results['tips'], height=100)
                    
                    if 'hashtags' in st.session_state.diy_results:
                        st.text_area("Hashtags:", st.session_state.diy_results['hashtags'], height=80)
                    
                    if 'captions' in st.session_state.diy_results:
                        st.text_area("Social Captions:", st.session_state.diy_results['captions'], height=100)
                    
                    if st.button("🎬 Use for Animation"):
                        # Use the first available content for animation
                        for content_type, content in st.session_state.diy_results.items():
                            if content and "Error" not in content:
                                # Take first line or first 150 chars
                                lines = content.split('\n')
                                usable_text = lines[0] if lines else content[:150]
                                st.session_state.diy_animation_text = usable_text
                                st.success("Content ready for animation!")
                                break
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Animation Configuration
        with st.expander("🎨 Animation Settings", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                background_theme = st.selectbox(
                    "Background Theme",
                    ["Golden Elegance", "Deep Amber", "Vintage Sepia"]
                )
                
                animation_style = st.selectbox(
                    "Animation Style",
                    ["Typewriter Top-to-Bottom", "Smooth Line-by-Line"]
                )
            
            with col2:
                text_color = st.color_picker("Text Color", "#FFD700")
                shadow_color = st.color_picker("Shadow Color", "#8B4513")
                
                line_spacing = st.slider("Line Spacing", 1.3, 2.2, 1.6, 0.1)
            
            with col3:
                duration = st.slider("Duration (seconds)", 3, 8, 5)
                resolution = st.selectbox("Resolution", ["720x1280", "1080x1920"], index=1)
        
        # Text Input
        with st.expander("📝 Animation Text", expanded=True):
            # Use DIY content if available
            default_text = "CREATE AMAZING DIY PROJECTS! SHARE YOUR CREATIONS WITH THE WORLD USING THESE SIMPLE TIPS AND TRICKS."
            
            if 'diy_animation_text' in st.session_state:
                default_text = st.session_state.diy_animation_text
                # Clear after use
                del st.session_state.diy_animation_text
            
            sentence = st.text_area(
                "Your Text:",
                default_text,
                height=100,
                max_chars=200,
                help="Text will animate from top to bottom with your logo"
            )
            
            if sentence:
                chars_count = len(sentence)
                st.caption(f"Characters: {chars_count}/200 • Font size: 50px-160px (responsive)")
        
        resolution_map = {"720x1280": (720, 1280), "1080x1920": (1080, 1920)}
        W, H = resolution_map[resolution]
        
        style_config = {
            'background_theme': background_theme,
            'animation_style': animation_style,
            'text_color': text_color,
            'shadow_color': shadow_color,
            'line_spacing': line_spacing,
        }
        
        if st.button("🎬 Create Animation", type="primary", use_container_width=True):
            if not sentence.strip():
                st.warning("Please enter some text.")
                return
            
            with st.spinner("Creating your branded animation..."):
                tmpdir = Path(tempfile.mkdtemp())
                out_mp4 = tmpdir / "diy_animation.mp4"
                
                try:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("🔄 Setting up animation...")
                    
                    for progress in generate_stable_video(sentence, duration, W, H, style_config, out_mp4):
                        progress_bar.progress(progress)
                        if progress < 1.0:
                            status_text.text(f"🎬 Animating top-to-bottom... {int(progress * 100)}%")
                        else:
                            status_text.text("✅ Finalizing video...")
                    
                    st.session_state.generated_video_path = out_mp4
                    st.session_state.show_video = True
                    st.session_state.video_tmpdir = tmpdir
                    
                    st.success("✨ Branded animation created successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import shutil
                    try:
                        shutil.rmtree(tmpdir, ignore_errors=True)
                    except:
                        pass
        
        # Display video
        if hasattr(st.session_state, 'show_video') and st.session_state.show_video:
            if (hasattr(st.session_state, 'generated_video_path') and 
                st.session_state.generated_video_path.exists()):
                
                st.markdown("### 🎥 Your Branded Animation")
                
                video_html = get_video_html(st.session_state.generated_video_path)
                st.markdown(video_html, unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    with open(st.session_state.generated_video_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Download MP4", 
                            data=f, 
                            file_name="diy_content_animation.mp4", 
                            mime="video/mp4",
                            type="primary",
                            use_container_width=True
                        )
                with col2:
                    if st.button("🗑️ Clear", use_container_width=True):
                        import shutil
                        if hasattr(st.session_state, 'video_tmpdir'):
                            try:
                                shutil.rmtree(st.session_state.video_tmpdir, ignore_errors=True)
                            except:
                                pass
                        st.session_state.show_video = False
                        st.rerun()
        
        # Features
        st.markdown("---")
        st.markdown("### 🎯 What's Included")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class='feature-card'>
            <h4>🏷️ Branded Logo</h4>
            <p>Your logo appears in every video frame</p>
            </div>
            
            <div class='feature-card'>
            <h4>⬇️ Top-to-Bottom Animation</h4>
            <p>Text flows smoothly from top to bottom</p>
            </div>
            
            <div class='feature-card'>
            <h4>📏 Responsive Text Sizing</h4>
            <p>Font size adjusts to screen size and text length</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class='feature-card'>
            <h4>🤖 AI DIY Assistant</h4>
            <p>Generate tips, hashtags, and captions with Groq</p>
            </div>
            
            <div class='feature-card'>
            <h4>🎨 Custom Themes</h4>
            <p>Choose from multiple background themes</p>
            </div>
            
            <div class='feature-card'>
            <h4>⚡ Stable Generation</h4>
            <p>Reliable video creation every time</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
