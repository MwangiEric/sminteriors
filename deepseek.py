import streamlit as st
import numpy as np
import imageio
import tempfile
import base64
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import json
from groq import Groq

# Set page config
st.set_page_config(page_title="AI Animation", layout="centered")

# Use groq_key from secrets
GROQ_API_KEY = st.secrets.get("groq_key", "")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Constants from the reference code
WIDTH, HEIGHT = 1080, 1920
FPS, DURATION = 30, 6

class GroqContentGenerator:
    def __init__(self, client):
        self.client = client
    
    def generate_diy_tips(self, topic):
        if not self.client:
            return self.get_fallback_tips(topic)
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": f"Generate 3 practical DIY tips about {topic}. Each under 120 characters. Return as JSON array."
                    }
                ],
                model="llama-3.1-8b-instant",
                temperature=0.7,
                max_tokens=300,
            )
            
            response = chat_completion.choices[0].message.content.strip()
            try:
                start_idx = response.find('[')
                end_idx = response.rfind(']') + 1
                if start_idx != -1:
                    return json.loads(response[start_idx:end_idx])
            except:
                return self.get_fallback_tips(topic)
        except:
            pass
        return self.get_fallback_tips(topic)
    
    def get_fallback_tips(self, topic):
        return [
            "Measure twice, cut once - saves time and materials.",
            "Use the right tool for the job - prevents damage and improves results.",
            "Safety first - always wear protective equipment when working."
        ]

class ProfessionalAnimationGenerator:
    def __init__(self):
        self.logo = self.load_logo()
    
    def load_logo(self):
        try:
            response = requests.get("https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037")
            logo = Image.open(io.BytesIO(response.content))
            if logo.mode != 'RGBA': 
                logo = logo.convert('RGBA')
            return logo.resize((300, 150), Image.Resampling.LANCZOS)
        except:
            img = Image.new('RGBA', (300, 150), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.rectangle([10, 30, 290, 120], fill=(245, 215, 140, 180))
            return img

    def create_frame(self, t, text, template):
        """Create professional frame with vertical text animation"""
        # Create background with dynamic elements
        canvas = Image.new("RGB", (WIDTH, HEIGHT), template["bg_color"])
        draw = ImageDraw.Draw(canvas)
        
        # Add animated background elements (like the rings in reference)
        for cx, cy, r in [(540, 960, 600), (660, 840, 800)]:
            pulse = 1 + 0.1 * math.sin(t * 3)
            draw.ellipse(
                [cx-r*pulse, cy-r*pulse, cx+r*pulse, cy+r*pulse], 
                outline=template["ring_color"], 
                width=4
            )
        
        # Load fonts with proper sizing
        try:
            title_font = ImageFont.truetype("arial.ttf", 80)
            text_font = ImageFont.truetype("arial.ttf", 60)
        except:
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
        
        # Break text into lines for vertical animation
        lines = self.break_text_to_lines(text, text_font, WIDTH - 200)
        
        # Apply vertical animation
        animated_lines = self.apply_vertical_animation(lines, t, DURATION)
        
        # Calculate starting position (top of screen)
        start_y = 300
        
        # Draw animated text from top to bottom
        for i, line_data in enumerate(animated_lines):
            line, alpha = line_data
            if not line:
                continue
                
            # Calculate line position with smooth animation
            line_y = start_y + (i * 120)
            
            # Apply entrance animation
            if alpha < 1.0:
                line_y += (1 - alpha) * 50  # Slide in from bottom
                
            # Calculate text width for centering
            try:
                bbox = draw.textbbox((0, 0), line, font=text_font)
                text_width = bbox[2] - bbox[0]
            except:
                text_width = len(line) * 30
                
            x = (WIDTH - text_width) // 2
            
            # Draw text with professional effects
            text_color = self.apply_alpha(template["text_color"], alpha)
            shadow_color = self.apply_alpha("#000000", alpha * 0.5)
            
            # Text shadow for readability
            draw.text((x + 3, line_y + 3), line, font=text_font, fill=shadow_color)
            # Main text
            draw.text((x, line_y), line, font=text_font, fill=text_color)
        
        # Add logo
        if self.logo:
            canvas.paste(self.logo, (WIDTH - 330, 30), self.logo)
        
        return np.array(canvas)

    def break_text_to_lines(self, text, font, max_width):
        """Professional text wrapping with pixel-perfect measurements"""
        words = text.split()
        lines = []
        current_line = []
        
        temp_img = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        
        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            
            try:
                bbox = temp_draw.textbbox((0, 0), test_line, font=font)
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

    def apply_vertical_animation(self, lines, t, duration):
        """Professional vertical animation with smooth transitions"""
        total_lines = len(lines)
        lines_per_second = total_lines / (duration * 0.8)  # 80% for text reveal
        
        current_line_index = t * lines_per_second
        animated_lines = []
        
        for i, line in enumerate(lines):
            line_progress = (current_line_index - i)
            
            if line_progress < 0:
                # Line hasn't started yet
                animated_lines.append(("", 0.0))
            elif line_progress < 1.0:
                # Line is animating in
                alpha = line_progress
                # Optional: character-by-character reveal within line
                chars_to_show = int(len(line) * alpha)
                animated_line = line[:chars_to_show]
                animated_lines.append((animated_line, alpha))
            else:
                # Line is fully visible
                animated_lines.append((line, 1.0))
        
        return animated_lines

    def apply_alpha(self, color, alpha):
        """Apply alpha to hex color"""
        if isinstance(color, str) and color.startswith('#'):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            return (r, g, b)
        return color

# Professional templates like in reference code
TEMPLATES = {
    "Professional": {
        "bg_color": "#0F0A05",
        "ring_color": "#FFD700", 
        "text_color": "#FFFFFF",
    },
    "Modern": {
        "bg_color": "#1A1A2E",
        "ring_color": "#00D4FF",
        "text_color": "#E6E6E6",
    },
    "Minimal": {
        "bg_color": "#FFFFFF",
        "ring_color": "#333333",
        "text_color": "#000000",
    }
}

def generate_video(text, template, output_path):
    """Professional video generation like reference code"""
    generator = ProfessionalAnimationGenerator()
    
    total_frames = FPS * DURATION
    
    try:
        with imageio.get_writer(
            output_path, 
            fps=FPS, 
            codec="libx264", 
            quality=8,
            pixelformat="yuv420p"
        ) as writer:
            for frame_idx in range(total_frames):
                t = frame_idx / FPS
                frame = generator.create_frame(t, text, template)
                writer.append_data(frame)
                
                if frame_idx % 10 == 0:
                    yield frame_idx / total_frames
        
        yield 1.0
    except Exception as e:
        st.error(f"Video generation error: {e}")
        yield 1.0

def main():
    # Initialize AI
    ai_generator = GroqContentGenerator(client)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if client:
            topic = st.text_input("DIY Topic", placeholder="e.g., woodworking, home repair")
            if st.button("Generate Tips") and topic:
                with st.spinner("Generating professional tips..."):
                    tips = ai_generator.generate_diy_tips(topic)
                    if tips:
                        st.session_state.ai_tips = tips
                        st.session_state.selected_tip = tips[0]
        
        if 'ai_tips' in st.session_state:
            selected = st.selectbox("Select tip", st.session_state.ai_tips)
            st.session_state.animation_text = selected
    
    with col2:
        template_choice = st.selectbox("Style", list(TEMPLATES.keys()))
        text_color = st.color_picker("Text Color", "#FAF5E6")
    
    # Text input
    default_text = st.session_state.get('animation_text', "Create professional content with optimized vertical animations.")
    text_input = st.text_area("Text Content", default_text, height=100)
    
    # Preview
    if st.button("Preview Frame"):
        generator = ProfessionalAnimationGenerator()
        template = TEMPLATES[template_choice]
        preview_frame = generator.create_frame(0, text_input, template)
        st.image(Image.fromarray(preview_frame), caption="Preview", use_column_width=True)
    
    # Generate video
    if st.button("Generate Professional Animation"):
        if not text_input.strip():
            st.warning("Enter text content")
            return
            
        template = TEMPLATES[template_choice]
        
        with st.spinner("Rendering professional animation..."):
            tmp_path = Path(tempfile.mkdtemp()) / "professional_animation.mp4"
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for progress in generate_video(text_input, template, tmp_path):
                progress_bar.progress(progress)
                status_text.text(f"Rendering: {int(progress * 100)}%")
            
            # Display result
            with open(tmp_path, "rb") as f:
                video_bytes = f.read()
                st.video(video_bytes)
                
                st.download_button(
                    "Download MP4",
                    video_bytes,
                    "professional_animation.mp4",
                    "video/mp4",
                    use_container_width=True
                )

if __name__ == "__main__":
    main()
