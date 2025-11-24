# app.py (AI-POWERED DYNAMIC LAYOUT)
import streamlit as st
import numpy as np
import imageio
import tempfile
import base64
import math
import random
import requests
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

# Set page config
st.set_page_config(page_title="AI Layout Animator", layout="centered")

# Use groq_key from secrets
GROQ_API_KEY = st.secrets.get("groq_key", os.getenv("GROQ_API_KEY"))

st.markdown(
    """
    <style>
    .main { background: linear-gradient(-45deg,#0f0c29,#302b63,#24243e,#0f0c29); background-size:400% 400%; animation:gradientShift 12s ease infinite; }
    .glass { background:rgba(255,255,255,0.06); border-radius:16px; box-shadow:0 4px 30px rgba(0,0,0,.2); backdrop-filter:blur(7px); border:1px solid rgba(255,255,255,.1); padding:2rem 3rem; margin:2rem auto; max-width:800px; }
    .video-container { margin: 2rem 0; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
    .feature-card { background: rgba(255,255,255,0.05); border-radius: 10px; padding: 1rem; margin: 0.5rem 0; border-left: 4px solid #ffd700; }
    .ai-section { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; padding: 1.5rem; margin: 1rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------- AI LAYOUT ENGINE -------------
class AILayoutEngine:
    def __init__(self, groq_api_key=None):
        self.groq_api_key = groq_api_key
    
    def analyze_layout_intelligent(self, text, logo_size, screen_width, screen_height):
        """AI-powered layout analysis using Groq"""
        if self.groq_api_key:
            return self.analyze_with_groq(text, logo_size, screen_width, screen_height)
        else:
            return self.analyze_heuristic(text, logo_size, screen_width, screen_height)
    
    def analyze_with_groq(self, text, logo_size, screen_width, screen_height):
        """Use Groq AI to determine optimal layout"""
        prompt = f"""
        As a professional graphic designer, analyze this video layout:
        
        CONTEXT:
        - Text: "{text}" ({len(text)} characters)
        - Logo: {logo_size[0]}x{logo_size[1]} pixels
        - Screen: {screen_width}x{screen_height} (portrait)
        - Animation: Text appears top-to-bottom
        
        OUTPUT REQUIREMENTS:
        Provide a JSON response with:
        1. logo_position: "top_left", "top_right", "top_center", or "bottom_center"
        2. font_size: number between 50-160
        3. text_start_y: vertical starting position (number)
        4. layout_style: "balanced", "logo_dominant", "text_dominant", or "minimal"
        5. line_spacing: number between 1.2-2.0
        6. confidence_score: 0-1 how confident you are in this layout
        
        Consider:
        - Text length vs available space
        - Logo visibility without obstructing text
        - Visual hierarchy and readability
        - Professional aesthetic
        
        Return only valid JSON.
        """
        
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "model": "llama-3.1-8b-instant",
            "max_tokens": 500,
            "temperature": 0.3
        }
        
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload, 
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                # Extract JSON from response
                try:
                    # Find JSON in the response
                    start_idx = content.find('{')
                    end_idx = content.rfind('}') + 1
                    if start_idx != -1 and end_idx != -1:
                        json_str = content[start_idx:end_idx]
                        layout_data = json.loads(json_str)
                        return layout_data
                except:
                    pass
            
            # Fallback to heuristic if AI fails
            return self.analyze_heuristic(text, logo_size, screen_width, screen_height)
            
        except:
            return self.analyze_heuristic(text, logo_size, screen_width, screen_height)
    
    def analyze_heuristic(self, text, logo_size, screen_width, screen_height):
        """Intelligent rule-based layout analysis"""
        text_length = len(text)
        logo_width, logo_height = logo_size
        
        # Analyze text characteristics
        if text_length < 25:
            # Short text - can be large with prominent logo
            layout = {
                "logo_position": "top_center",
                "font_size": min(140, screen_height // 8),
                "text_start_y": logo_height + 100,
                "layout_style": "balanced",
                "line_spacing": 1.4,
                "confidence_score": 0.9
            }
        elif text_length < 60:
            # Medium text - balanced approach
            layout = {
                "logo_position": "top_left",
                "font_size": min(100, screen_height // 10),
                "text_start_y": logo_height + 80,
                "layout_style": "balanced", 
                "line_spacing": 1.5,
                "confidence_score": 0.85
            }
        elif text_length < 120:
            # Longer text - prioritize readability
            layout = {
                "logo_position": "top_right", 
                "font_size": min(80, screen_height // 12),
                "text_start_y": 100,  # Start higher to use more space
                "layout_style": "text_dominant",
                "line_spacing": 1.6,
                "confidence_score": 0.8
            }
        else:
            # Very long text - minimal logo
            layout = {
                "logo_position": "bottom_center",
                "font_size": min(65, screen_height // 14),
                "text_start_y": 80,
                "layout_style": "text_dominant",
                "line_spacing": 1.7,
                "confidence_score": 0.75
            }
        
        # Adjust based on screen size
        if screen_height < 1000:  # Smaller screens
            layout["font_size"] = max(50, layout["font_size"] - 10)
            layout["text_start_y"] = max(80, layout["text_start_y"] - 20)
        
        return layout
    
    def calculate_logo_position(self, layout, screen_width, screen_height, logo_size):
        """Calculate exact logo coordinates based on layout decision"""
        logo_width, logo_height = logo_size
        position = layout.get("logo_position", "top_left")
        
        positions = {
            "top_left": (40, 40),
            "top_right": (screen_width - logo_width - 40, 40),
            "top_center": ((screen_width - logo_width) // 2, 40),
            "bottom_center": ((screen_width - logo_width) // 2, screen_height - logo_height - 40)
        }
        
        return positions.get(position, (40, 40))

# ------------- Logo Handler -------------
def load_logo():
    """Load and prepare logo"""
    logo_url = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"
    try:
        response = requests.get(logo_url)
        logo_image = Image.open(io.BytesIO(response.content))
        if logo_image.mode != 'RGBA':
            logo_image = logo_image.convert('RGBA')
        logo_image = logo_image.resize((120, 60), Image.Resampling.LANCZOS)
        return logo_image
    except:
        return create_fallback_logo()

def create_fallback_logo():
    """Create fallback logo"""
    img = Image.new('RGBA', (120, 60), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("Arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    draw.rectangle([5, 15, 115, 45], fill=(255, 215, 0, 180))
    draw.text((15, 20), "BRAND", fill=(0, 0, 0, 255), font=font)
    return img

# ------------- AI Frame Generator -------------
class AIFrameGenerator:
    def __init__(self, groq_api_key=None):
        self.layout_engine = AILayoutEngine(groq_api_key)
        self.logo = load_logo()
    
    def create_ai_optimized_frame(self, text, progress, frame_idx, total_frames, width, height, style_config):
        """Create frame with AI-optimized layout"""
        try:
            # Get AI layout recommendation
            logo_size = self.logo.size if self.logo else (120, 60)
            layout = self.layout_engine.analyze_layout_intelligent(
                text, logo_size, width, height
            )
            
            # Generate background
            bg = self.generate_background(width, height, frame_idx, total_frames, style_config)
            img = Image.fromarray(bg)
            draw = ImageDraw.Draw(img)
            
            # Add logo at AI-determined position
            if self.logo:
                logo_pos = self.layout_engine.calculate_logo_position(layout, width, height, logo_size)
                img = self.add_logo_safely(img, self.logo, logo_pos)
            
            # Setup text with AI recommendations
            font_size = layout["font_size"]
            try:
                font = ImageFont.truetype("Arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
            # Break text into lines
            lines = self.break_text_into_lines(text, font, width - 160)  # Account for margins
            
            # Apply animation
            animated_text = self.apply_animation(text, lines, progress, layout)
            
            # Draw text at AI-determined position
            self.draw_animated_text(draw, animated_text, font, layout, width, height, style_config)
            
            return np.array(img).astype(np.uint8)
            
        except Exception as e:
            st.warning(f"AI frame generation: {e}")
            return self.create_fallback_frame(width, height)
    
    def generate_background(self, width, height, frame_idx, total_frames, style_config):
        """Generate animated background"""
        bg = np.zeros((height, width, 3), dtype=np.uint8)
        time_progress = frame_idx / total_frames
        
        for y in range(height):
            progress = y / height
            r = int(100 + progress * 155 + math.sin(time_progress * 5) * 20)
            g = int(80 + progress * 140 + math.cos(time_progress * 4) * 15)
            b = int(40 + progress * 60)
            
            for x in range(width):
                wave = math.sin(x * 0.02 + time_progress * 3) * 10
                bg[y, x] = [
                    max(0, min(255, r + wave)),
                    max(0, min(255, g + wave * 0.7)),
                    max(0, min(255, b))
                ]
        
        return bg
    
    def add_logo_safely(self, frame, logo, position):
        """Safely add logo to frame"""
        try:
            frame_rgba = frame.convert('RGBA')
            logo_rgba = logo.convert('RGBA')
            
            # Manual alpha compositing
            for x in range(logo.width):
                for y in range(logo.height):
                    logo_pixel = logo_rgba.getpixel((x, y))
                    if logo_pixel[3] > 0:  # Not fully transparent
                        frame_x = position[0] + x
                        frame_y = position[1] + y
                        if 0 <= frame_x < frame_rgba.width and 0 <= frame_y < frame_rgba.height:
                            frame_rgba.putpixel(
                                (frame_x, frame_y), 
                                self.blend_pixels(frame_rgba.getpixel((frame_x, frame_y)), logo_pixel)
                            )
            
            return frame_rgba.convert('RGB')
        except:
            return frame
    
    def blend_pixels(self, bg, fg):
        """Blend two pixels with alpha"""
        alpha = fg[3] / 255.0
        return (
            int(fg[0] * alpha + bg[0] * (1 - alpha)),
            int(fg[1] * alpha + bg[1] * (1 - alpha)),
            int(fg[2] * alpha + bg[2] * (1 - alpha))
        )
    
    def break_text_into_lines(self, text, font, max_width):
        """Break text into lines that fit"""
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
                    lines.append(word)
                    current_line = []
                else:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def apply_animation(self, full_text, lines, progress, layout):
        """Apply top-to-bottom animation"""
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
        
        return revealed_lines
    
    def draw_animated_text(self, draw, lines, font, layout, width, height, style_config):
        """Draw text with AI-optimized positioning"""
        text_color = self.hex_to_rgb(style_config['text_color'])
        shadow_color = self.hex_to_rgb(style_config['shadow_color'])
        line_spacing = layout.get('line_spacing', 1.5)
        
        start_y = layout['text_start_y']
        
        try:
            bbox = draw.textbbox((0, 0), "Test", font=font)
            line_height = (bbox[3] - bbox[1]) * line_spacing
        except:
            line_height = font.size * line_spacing * 1.4
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
                
            y_pos = start_y + i * line_height
            
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
            except:
                line_width = len(line) * font.size // 1.8
            
            x_pos = (width - line_width) // 2
            
            # Text shadow
            shadow_blur = 3
            draw.text((x_pos + shadow_blur, y_pos + shadow_blur), line, font=font, fill=shadow_color)
            
            # Main text
            draw.text((x_pos, y_pos), line, font=font, fill=text_color)
    
    def create_fallback_frame(self, width, height):
        """Create fallback frame"""
        bg = np.zeros((height, width, 3), dtype=np.uint8)
        bg[:, :] = [30, 30, 60]
        return bg
    
    def hex_to_rgb(self, hex_color):
        """Convert hex to RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# ------------- Groq Content Generator -------------
class GroqContentGenerator:
    def __init__(self, api_key):
        self.api_key = api_key
    
    def generate_diy_content(self, topic, content_type="tips"):
        prompts = {
            "tips": f"Generate 3 practical DIY tips for: {topic}. Keep each under 100 characters.",
            "hashtags": f"Generate 10 relevant hashtags for DIY projects about: {topic}.",
            "captions": f"Write 2 engaging social media captions about: {topic}. Keep under 120 characters each."
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [{"role": "user", "content": prompts[content_type]}],
            "model": "llama-3.1-8b-instant",
            "max_tokens": 300,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload, 
                headers=headers
            )
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            return f"API Error: {response.status_code}"
        except Exception as e:
            return f"Connection error: {str(e)}"

# ------------- Video Generation -------------
def generate_ai_video(text, duration, width, height, style_config, groq_key, output_path):
    fps = 24
    total_frames = duration * fps
    
    frame_generator = AIFrameGenerator(groq_key)
    
    try:
        with imageio.get_writer(output_path, fps=fps, codec="libx264", quality=7) as writer:
            for frame_idx in range(total_frames):
                progress = (frame_idx + 1) / total_frames
                frame = frame_generator.create_ai_optimized_frame(
                    text, progress, frame_idx, total_frames, width, height, style_config
                )
                writer.append_data(frame)
                
                if frame_idx % 10 == 0:
                    yield frame_idx / total_frames
        
        yield 1.0
    except Exception as e:
        st.error(f"Video error: {e}")
        yield 1.0

def get_video_html(video_path):
    try:
        with open(video_path, "rb") as f:
            video_b64 = base64.b64encode(f.read()).decode()
        return f'<div class="video-container"><video controls style="width:100%"><source src="data:video/mp4;base64,{video_b64}" type="video/mp4"></video></div>'
    except:
        return '<p style="color:red">Error loading video</p>'

# ------------- Main UI -------------
def main():
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center;color:#ffffff'>🎬 AI-Powered Layout Animator</h1>")
    
    # Groq AI Section
    if GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here":
        st.markdown('<div class="ai-section">', unsafe_allow_html=True)
        st.markdown("### 🤖 AI Content & Layout Assistant")
        
        col1, col2 = st.columns(2)
        with col1:
            topic = st.text_input("Topic:", placeholder="e.g., home organization, gardening")
            content_type = st.selectbox("Content Type:", ["tips", "hashtags", "captions"])
            
            if st.button("🛠️ Generate Content"):
                if topic:
                    with st.spinner("AI is generating content..."):
                        generator = GroqContentGenerator(GROQ_API_KEY)
                        content = generator.generate_diy_content(topic, content_type)
                        st.session_state.ai_content = content
        
        with col2:
            if 'ai_content' in st.session_state:
                st.text_area("AI Content:", st.session_state.ai_content, height=120)
                if st.button("🎬 Use for Animation"):
                    st.session_state.animation_text = st.session_state.ai_content.split('\n')[0][:150]
                    st.success("Ready for AI layout!")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Animation Settings
    with st.expander("🎨 AI Layout Settings", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            text_color = st.color_picker("Text Color", "#FFD700")
            shadow_color = st.color_picker("Shadow Color", "#8B4513")
            duration = st.slider("Duration (seconds)", 3, 8, 5)
        with col2:
            resolution = st.selectbox("Resolution", ["720x1280", "1080x1920"], index=1)
            ai_mode = st.checkbox("Enable AI Layout Optimization", True, 
                                help="AI will dynamically position logo and text")
    
    # Text Input
    default_text = "CREATE AMAZING CONTENT WITH AI-POWERED LAYOUT OPTIMIZATION!"
    if 'animation_text' in st.session_state:
        default_text = st.session_state.animation_text
    
    sentence = st.text_area("Your Text:", default_text, height=100, max_chars=200)
    
    resolution_map = {"720x1280": (720, 1280), "1080x1920": (1080, 1920)}
    W, H = resolution_map[resolution]
    
    style_config = {
        'text_color': text_color,
        'shadow_color': shadow_color,
    }
    
    if st.button("🚀 Generate AI-Optimized Animation", type="primary", use_container_width=True):
        if not sentence.strip():
            st.warning("Please enter some text.")
            return
        
        with st.spinner("AI is optimizing your layout..."):
            tmpdir = Path(tempfile.mkdtemp())
            out_mp4 = tmpdir / "ai_layout_animation.mp4"
            
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                groq_key = GROQ_API_KEY if ai_mode else None
                
                for progress in generate_ai_video(sentence, duration, W, H, style_config, groq_key, out_mp4):
                    progress_bar.progress(progress)
                    status_text.text(f"🎬 AI Layout: {int(progress * 100)}%")
                
                st.session_state.generated_video_path = out_mp4
                st.session_state.show_video = True
                st.session_state.video_tmpdir = tmpdir
                
                st.success("✨ AI-optimized animation created!")
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    # Display video
    if hasattr(st.session_state, 'show_video') and st.session_state.show_video:
        if st.session_state.generated_video_path.exists():
            st.markdown("### 🎥 Your AI-Optimized Animation")
            st.markdown(get_video_html(st.session_state.generated_video_path), unsafe_allow_html=True)
            
            with open(st.session_state.generated_video_path, "rb") as f:
                st.download_button("⬇️ Download MP4", f, "ai_layout_animation.mp4", "video/mp4", use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
