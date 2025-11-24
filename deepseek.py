# app.py (ENHANCED - Logo + Larger Text + Groq Integration)
import streamlit as st
import numpy as np
import imageio
import tempfile
import base64
import math
import random
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import os
import io

# Set page config first
st.set_page_config(page_title="Premium Typing Animations", layout="centered")

# Add your Groq API key (you can set this in Streamlit secrets)
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "your_groq_api_key_here")

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
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------- Logo Integration -------------
def load_logo():
    """Load and display the logo"""
    logo_url = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"
    try:
        response = requests.get(logo_url)
        logo_image = Image.open(io.BytesIO(response.content))
        return logo_image
    except Exception as e:
        st.warning(f"Could not load logo: {e}")
        return None

# ------------- Background Systems -------------
class AdvancedBackgroundGenerator:
    def __init__(self):
        self.themes = {
            "Golden Elegance": self.golden_elegance,
            "Deep Amber": self.deep_amber,
            "Vintage Sepia": self.vintage_sepia,
            "Royal Bronze": self.royal_bronze,
            "Sunset Gold": self.sunset_gold,
        }
    
    def golden_elegance(self, width, height, time_progress):
        y, x = np.ogrid[0:height, 0:width]
        y_norm, x_norm = y / height, x / width
        t = time_progress * 3 * math.pi
        
        base_r = (120 * (1 - y_norm) + 255 * y_norm).astype(np.uint8)
        base_g = (80 * (1 - y_norm) + 220 * y_norm).astype(np.uint8)
        base_b = (40 * (1 - y_norm) + 100 * y_norm).astype(np.uint8)
        
        wave1 = np.sin(x_norm * 8 * math.pi + t) * 25
        wave2 = np.cos(y_norm * 6 * math.pi + t * 1.3) * 20
        wave3 = np.sin((x_norm + y_norm) * 10 * math.pi + t * 0.7) * 15
        
        r = np.clip(base_r + wave1 * 0.8 + wave3 * 0.3, 0, 255).astype(np.uint8)
        g = np.clip(base_g + wave1 * 0.6 + wave2 * 0.4, 0, 255).astype(np.uint8)
        b = np.clip(base_b + wave2 * 0.5 + wave3 * 0.2, 0, 255).astype(np.uint8)
        
        bg = np.stack([r, g, b], axis=-1)
        
        sparkle_intensity = (np.sin(x.astype(float) * y.astype(float) * 0.0002 + t * 8) > 0.99)
        bg[sparkle_intensity] = [255, 240, 160]
        
        return bg.astype(np.uint8)
    
    def deep_amber(self, width, height, time_progress):
        y, x = np.ogrid[0:height, 0:width]
        y_norm, x_norm = y / height, x / width
        t = time_progress * 2.5 * math.pi
        
        base_r = (150 * (1 - y_norm) + 255 * y_norm).astype(np.uint8)
        base_g = (100 * (1 - y_norm) + 180 * y_norm).astype(np.uint8)
        base_b = (50 * (1 - y_norm) + 80 * y_norm).astype(np.uint8)
        
        wave1 = np.sin(x_norm * 12 * math.pi + t) * 30
        wave2 = np.cos(y_norm * 8 * math.pi + t * 1.7) * 25
        
        r = np.clip(base_r + wave1 * 0.9, 0, 255).astype(np.uint8)
        g = np.clip(base_g + wave1 * 0.7 + wave2 * 0.5, 0, 255).astype(np.uint8)
        b = np.clip(base_b + wave2 * 0.6, 0, 255).astype(np.uint8)
        
        return np.stack([r, g, b], axis=-1).astype(np.uint8)
    
    def vintage_sepia(self, width, height, time_progress):
        y, x = np.ogrid[0:height, 0:width]
        y_norm = y / height
        t = time_progress * 2 * math.pi
        
        base_r = (120 * (1 - y_norm) + 200 * y_norm).astype(np.uint8)
        base_g = (100 * (1 - y_norm) + 170 * y_norm).astype(np.uint8)
        base_b = (80 * (1 - y_norm) + 120 * y_norm).astype(np.uint8)
        
        noise = (np.random.rand(height, width) * 20 - 10).astype(np.float32)
        
        r = np.clip(base_r.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        g = np.clip(base_g.astype(np.float32) + noise * 0.8, 0, 255).astype(np.uint8)
        b = np.clip(base_b.astype(np.float32) + noise * 0.6, 0, 255).ast(np.uint8)
        
        return np.stack([r, g, b], axis=-1).astype(np.uint8)
    
    def royal_bronze(self, width, height, time_progress):
        y, x = np.ogrid[0:height, 0:width]
        y_norm, x_norm = y / height, x / width
        t = time_progress * 2.2 * math.pi
        
        base_r = (110 * (1 - y_norm) + 180 * y_norm).astype(np.uint8)
        base_g = (80 * (1 - y_norm) + 140 * y_norm).astype(np.uint8)
        base_b = (60 * (1 - y_norm) + 100 * y_norm).astype(np.uint8)
        
        wave1 = np.sin(x_norm * 10 * math.pi + t) * 20
        wave2 = np.cos(y_norm * 7 * math.pi + t * 1.5) * 15
        metallic = np.sin((x_norm * 5 + y_norm * 3) * math.pi + t * 2) * 10
        
        r = np.clip(base_r.astype(np.float32) + wave1 * 0.7 + metallic * 0.5, 0, 255).astype(np.uint8)
        g = np.clip(base_g.astype(np.float32) + wave1 * 0.5 + wave2 * 0.4, 0, 255).astype(np.uint8)
        b = np.clip(base_b.astype(np.float32) + wave2 * 0.3 + metallic * 0.3, 0, 255).astype(np.uint8)
        
        bg = np.stack([r, g, b], axis=-1)
        
        highlights = (np.sin(x.astype(float) * 0.01 + y.astype(float) * 0.01 + t * 3) > 0.95)
        bg[highlights] = [205, 127, 50]
        
        return bg.astype(np.uint8)
    
    def sunset_gold(self, width, height, time_progress):
        y, x = np.ogrid[0:height, 0:width]
        y_norm, x_norm = y / height, x / width
        t = time_progress * 1.8 * math.pi
        
        base_r = (130 * (1 - y_norm) + 255 * y_norm).astype(np.uint8)
        base_g = (70 * (1 - y_norm) + 200 * y_norm).astype(np.uint8)
        base_b = (30 * (1 - y_norm) + 100 * y_norm).astype(np.uint8)
        
        wave1 = np.sin(x_norm * 6 * math.pi + t) * 25
        wave2 = np.cos(y_norm * 4 * math.pi + t * 0.8) * 20
        wave3 = np.sin((x_norm - y_norm) * 8 * math.pi + t * 1.2) * 15
        
        r = np.clip(base_r.astype(np.float32) + wave1 * 0.8 + wave3 * 0.4, 0, 255).astype(np.uint8)
        g = np.clip(base_g.astype(np.float32) + wave1 * 0.6 + wave2 * 0.5, 0, 255).astype(np.uint8)
        b = np.clip(base_b.astype(np.float32) + wave2 * 0.4, 0, 255).astype(np.uint8)
        
        bg = np.stack([r, g, b], axis=-1)
        
        glow_mask = (y_norm > 0.7) & (np.sin(x_norm * 4 * math.pi + t) > 0.5)
        glow_addition = np.array([30, 30, 10], dtype=np.uint8)
        bg[glow_mask] = np.clip(bg[glow_mask].astype(np.int32) + glow_addition, 0, 255).astype(np.uint8)
        
        return bg.astype(np.uint8)
    
    def get_theme(self, theme_name):
        return self.themes.get(theme_name, self.golden_elegance)

# ------------- EXTRA LARGE Text Animation System -------------
class ExtraLargeTextAnimator:
    def __init__(self):
        self.animation_styles = {
            "Typewriter Top-to-Bottom": self.typewriter_top_bottom,
            "Smooth Reveal Top-to-Bottom": self.smooth_top_bottom,
            "Line by Line": self.line_by_line,
        }
    
    def typewriter_top_bottom(self, text, progress, line_info):
        """Typewriter effect from top to bottom with EXTRA LARGE text"""
        lines = line_info['lines']
        total_lines = len(lines)
        
        lines_to_show = int(total_lines * progress)
        
        revealed_lines = []
        for i in range(total_lines):
            if i < lines_to_show:
                revealed_lines.append(lines[i])
            elif i == lines_to_show:
                partial_progress = (progress * total_lines) - lines_to_show
                chars_to_show = int(len(lines[i]) * partial_progress)
                revealed_lines.append(lines[i][:chars_to_show])
            else:
                revealed_lines.append("")
        
        revealed_text = "\n".join(revealed_lines)
        return revealed_text, progress
    
    def smooth_top_bottom(self, text, progress, line_info):
        """Smooth reveal from top to bottom with EXTRA LARGE text"""
        lines = line_info['lines']
        total_lines = len(lines)
        
        exact_lines = progress * total_lines
        lines_to_show = int(exact_lines)
        partial_progress = exact_lines - lines_to_show
        
        revealed_lines = []
        for i in range(total_lines):
            if i < lines_to_show:
                revealed_lines.append(lines[i])
            elif i == lines_to_show:
                chars_to_show = int(len(lines[i]) * partial_progress)
                revealed_lines.append(lines[i][:chars_to_show])
            else:
                revealed_lines.append("")
        
        revealed_text = "\n".join(revealed_lines)
        return revealed_text, progress
    
    def line_by_line(self, text, progress, line_info):
        """Each line appears completely one after another"""
        lines = line_info['lines']
        total_lines = len(lines)
        
        # More dramatic line-by-line appearance
        lines_to_show = int(total_lines * progress)
        
        revealed_lines = []
        for i in range(total_lines):
            if i <= lines_to_show:
                revealed_lines.append(lines[i])
            else:
                revealed_lines.append("")
        
        revealed_text = "\n".join(revealed_lines)
        return revealed_text, progress

# ------------- EXTRA LARGE Text Layout System -------------
class ExtraLargeTextLayout:
    def __init__(self, width, height, margins=50):
        self.width = width
        self.height = height
        self.margins = margins
        self.content_width = width - 2 * margins
        self.content_height = height - 2 * margins
        
    def calculate_optimal_layout(self, text, style_config):
        """Calculate EXTRA LARGE font sizes"""
        text_length = len(text)
        
        # EXTRA LARGE font sizing
        if text_length < 30:
            font_size = 140  # Very large for short text
        elif text_length < 60:
            font_size = 120  # Large for medium text
        elif text_length < 100:
            font_size = 100  # Still very large
        else:
            font_size = max(70, 90 - text_length // 25)  # Minimum 70px
        
        # Try to load font
        try:
            font = ImageFont.truetype("Arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("Arial", font_size)
                except:
                    font = ImageFont.load_default()
        
        return font, font_size
    
    def break_text_into_lines(self, text, font, max_width):
        """Break text into lines for EXTRA LARGE text"""
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
                line_width = len(test_line) * font.size // 1.5  # Adjusted for extra large text
            
            if line_width > max_width:
                if len(current_line) == 1:
                    # Single word is too long, break it
                    if len(word) > 12:
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
    
    def calculate_text_block_position(self, lines, font, line_height, start_from_top=True):
        """Calculate position starting from TOP with extra space"""
        total_height = len(lines) * line_height
        
        if start_from_top:
            # Start from top with generous spacing
            start_y = self.margins + 80
        else:
            start_y = self.margins + (self.content_height - total_height) // 2
        
        return start_y

# ------------- Frame Generator with EXTRA LARGE TEXT -------------
class ExtraLargeTextFrameGenerator:
    def __init__(self):
        self.bg_generator = AdvancedBackgroundGenerator()
        self.text_animator = ExtraLargeTextAnimator()
    
    def create_frame_with_extra_large_text(self, full_text, progress, frame_idx, total_frames, 
                                         width, height, style_config):
        """Create frame with EXTRA LARGE text and top-to-bottom animation"""
        try:
            bg_theme = self.bg_generator.get_theme(style_config['background_theme'])
            time_progress = frame_idx / total_frames
            bg = bg_theme(width, height, time_progress)
            
            if bg.dtype != np.uint8:
                bg = bg.astype(np.uint8)
                
            img = Image.fromarray(bg)
            draw = ImageDraw.Draw(img)
            
            layout_engine = ExtraLargeTextLayout(width, height)
            font, font_size = layout_engine.calculate_optimal_layout(full_text, style_config)
            
            lines = layout_engine.break_text_into_lines(
                full_text, font, layout_engine.content_width
            )
            
            line_info = {
                'lines': lines,
                'font': font,
                'font_size': font_size
            }
            
            animator = self.text_animator.animation_styles[style_config['animation_style']]
            visible_text, anim_progress = animator(full_text, progress, line_info)
            
            # Calculate positioning with extra spacing for large text
            try:
                bbox = draw.textbbox((0, 0), "Test", font=font)
                line_height = (bbox[3] - bbox[1]) * style_config['line_spacing']
            except:
                line_height = font_size * style_config['line_spacing'] * 1.5  # Extra spacing
            
            visible_lines = visible_text.split('\n') if visible_text else []
            start_y = layout_engine.calculate_text_block_position(
                visible_lines, font, line_height, start_from_top=True
            )
            
            text_color = self.hex_to_rgb(style_config['text_color'])
            shadow_color = self.hex_to_rgb(style_config['shadow_color'])
            
            # Draw EXTRA LARGE text with enhanced effects
            for i, line in enumerate(visible_lines):
                if not line.strip():
                    continue
                    
                y_pos = start_y + i * line_height
                
                try:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    line_width = bbox[2] - bbox[0]
                except:
                    line_width = len(line) * font_size // 1.5
                
                x_pos = (width - line_width) // 2
                
                # Enhanced shadow for extra large text
                shadow_blur = 5
                for dx, dy in [(shadow_blur, shadow_blur), (0, shadow_blur), (shadow_blur, 0), (-shadow_blur, 0)]:
                    draw.text((x_pos + dx, y_pos + dy), line, font=font, fill=shadow_color)
                
                # Main text
                draw.text((x_pos, y_pos), line, font=font, fill=text_color)
            
            frame_array = np.array(img)
            if frame_array.dtype != np.uint8:
                frame_array = frame_array.astype(np.uint8)
                
            return frame_array
            
        except Exception as e:
            st.warning(f"Frame generation: {e}")
            fallback_frame = np.zeros((height, width, 3), dtype=np.uint8)
            fallback_frame[:, :] = [50, 50, 50]
            return fallback_frame
    
    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# ------------- Groq AI Integration -------------
class GroqAIHelper:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def generate_text_suggestions(self, prompt, max_tokens=100):
        """Generate text suggestions using Groq AI"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": f"Generate a short, impactful text for a video animation (max 150 characters) about: {prompt}"
                }
            ],
            "model": "llama-3.1-8b-instant",  # You can change this model
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(self.base_url, json=payload, headers=headers)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                return f"Error: {response.status_code}"
        except Exception as e:
            return f"AI service error: {str(e)}"
    
    def enhance_text(self, text):
        """Enhance existing text using AI"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": f"Make this text more impactful and engaging for a video (keep under 200 characters): '{text}'"
                }
            ],
            "model": "llama-3.1-8b-instant",
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(self.base_url, json=payload, headers=headers)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                return text  # Return original if error
        except:
            return text  # Return original if error

# ------------- Video Generation -------------
def generate_extra_large_text_video(sentence, duration, width, height, style_config, output_path):
    """Generate video with EXTRA LARGE text"""
    fps = 24
    total_frames = duration * fps
    
    frame_generator = ExtraLargeTextFrameGenerator()
    
    try:
        with imageio.get_writer(
            output_path, 
            fps=fps, 
            codec="libx264",
            quality=8,
            pixelformat="yuv420p",
            macro_block_size=8
        ) as writer:
            
            for frame_idx in range(total_frames):
                progress = (frame_idx + 1) / total_frames
                
                frame = frame_generator.create_frame_with_extra_large_text(
                    sentence, progress, frame_idx, total_frames, 
                    width, height, style_config
                )
                
                if frame.dtype != np.uint8:
                    frame = frame.astype(np.uint8)
                
                writer.append_data(frame)
                
                if frame_idx % 8 == 0:
                    yield frame_idx / total_frames
        
        yield 1.0
        
    except Exception as e:
        st.error(f"Video generation error: {e}")
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
    if logo_image:
        st.image(logo_image, width=200)
    st.markdown('</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center;color:#ffffff'>🎬 Premium Text Animations</h1>", unsafe_allow_html=True)
        
        # Groq AI Section
        if GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here":
            with st.expander("🤖 AI Text Assistant (Powered by Groq)", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    ai_prompt = st.text_input("Describe what you want to say:", placeholder="e.g., motivational quote about success")
                    if st.button("✨ Generate Text", key="ai_generate"):
                        if ai_prompt:
                            with st.spinner("AI is generating your text..."):
                                groq_helper = GroqAIHelper(GROQ_API_KEY)
                                generated_text = groq_helper.generate_text_suggestions(ai_prompt)
                                st.session_state.generated_text = generated_text
                
                with col2:
                    if 'generated_text' in st.session_state:
                        st.text_area("AI Generated Text:", st.session_state.generated_text, height=100)
                        if st.button("🚀 Use This Text"):
                            st.session_state.use_ai_text = True
        
        # Configuration
        with st.expander("🎨 Style Configuration", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                background_theme = st.selectbox(
                    "Background Theme",
                    ["Golden Elegance", "Deep Amber", "Vintage Sepia", "Royal Bronze", "Sunset Gold"]
                )
                
                animation_style = st.selectbox(
                    "Animation Style",
                    ["Typewriter Top-to-Bottom", "Smooth Reveal Top-to-Bottom", "Line by Line"]
                )
            
            with col2:
                text_color = st.color_picker("Text Color", "#FFD700")
                shadow_color = st.color_picker("Shadow Color", "#8B4513")
                
                line_spacing = st.slider("Line Spacing", 1.4, 2.5, 1.8, 0.1)
            
            with col3:
                duration = st.slider("Duration (seconds)", 3, 10, 6)
                resolution = st.selectbox("Resolution", ["720x1280", "1080x1920"], index=1)
        
        with st.expander("📝 Text Configuration", expanded=True):
            # Use AI generated text if available
            default_text = "WELCOME TO PREMIUM TEXT ANIMATIONS! THIS TEXT IS EXTRA LARGE AND CLEAR, ANIMATING SMOOTHLY FROM TOP TO BOTTOM WITH STUNNING VISUAL EFFECTS."
            
            if 'use_ai_text' in st.session_state and st.session_state.use_ai_text:
                default_text = st.session_state.generated_text
                st.session_state.use_ai_text = False  # Reset after use
            
            sentence = st.text_area(
                "Your Text:",
                default_text,
                height=120,
                max_chars=250,
                help="Text will be displayed in EXTRA LARGE font size (70px-140px) and animate from top to bottom"
            )
            
            if GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here":
                if st.button("🪄 Enhance with AI", key="enhance"):
                    if sentence:
                        with st.spinner("AI is enhancing your text..."):
                            groq_helper = GroqAIHelper(GROQ_API_KEY)
                            enhanced_text = groq_helper.enhance_text(sentence)
                            st.session_state.enhanced_text = enhanced_text
                            st.rerun()
                
                if 'enhanced_text' in st.session_state:
                    st.text_area("AI Enhanced Text:", st.session_state.enhanced_text, height=100)
                    if st.button("✅ Use Enhanced Text"):
                        sentence = st.session_state.enhanced_text
                        del st.session_state.enhanced_text
            
            if sentence:
                chars_count = len(sentence)
                estimated_lines = max(1, chars_count // 20)  # Fewer chars per line for extra large text
                st.caption(f"Characters: {chars_count}/250 • Estimated lines: {estimated_lines} • Font size: 70px-140px")
        
        resolution_map = {"720x1280": (720, 1280), "1080x1920": (1080, 1920)}
        W, H = resolution_map[resolution]
        
        style_config = {
            'background_theme': background_theme,
            'animation_style': animation_style,
            'text_color': text_color,
            'shadow_color': shadow_color,
            'line_spacing': line_spacing,
        }
        
        if st.button("🎬 Generate Premium Animation", type="primary", use_container_width=True):
            if not sentence.strip():
                st.warning("Please enter some text.")
                return
            
            with st.spinner("Creating your PREMIUM animation..."):
                tmpdir = Path(tempfile.mkdtemp())
                out_mp4 = tmpdir / "premium_animation.mp4"
                
                try:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("🎨 Setting up premium animation...")
                    
                    for progress in generate_extra_large_text_video(sentence, duration, W, H, style_config, out_mp4):
                        progress_bar.progress(progress)
                        if progress < 1.0:
                            status_text.text(f"🎬 Creating EXTRA LARGE text... {int(progress * 100)}%")
                        else:
                            status_text.text("✅ Finalizing premium video...")
                    
                    st.session_state.generated_video_path = out_mp4
                    st.session_state.show_video = True
                    st.session_state.video_tmpdir = tmpdir
                    
                    st.success("✨ PREMIUM animation created successfully!")
                    
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
                
                st.markdown("### 🎥 Your Premium Animation")
                
                video_html = get_video_html(st.session_state.generated_video_path)
                st.markdown(video_html, unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    with open(st.session_state.generated_video_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Download MP4", 
                            data=f, 
                            file_name="premium_animation.mp4", 
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
        st.markdown("### 🎯 Premium Features")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class='feature-card'>
            <h4>📏 EXTRA LARGE TEXT</h4>
            <p>Massive text sizes (70px-140px) for maximum impact</p>
            </div>
            
            <div class='feature-card'>
            <h4>⬇️ TOP-TO-BOTTOM ANIMATION</h4>
            <p>Text flows smoothly from top to bottom</p>
            </div>
            
            <div class='feature-card'>
            <h4>🤖 AI POWERED</h4>
            <p>Groq AI integration for text generation and enhancement</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class='feature-card'>
            <h4>🎨 5 PREMIUM THEMES</h4>
            <p>Professional brown/gold animated backgrounds</p>
            </div>
            
            <div class='feature-card'>
            <h4>🌈 CUSTOM COLORS</h4>
            <p>Full control over text and shadow colors</p>
            </div>
            
            <div class='feature-card'>
            <h4>⚡ HIGH PERFORMANCE</h4>
            <p>Optimized for fast generation and smooth playback</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
