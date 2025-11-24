# app.py (ENHANCED - Multiple Advanced Features)
import streamlit as st
import numpy as np
import imageio
import tempfile
import base64
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
from typing import List, Tuple

st.set_page_config(page_title="Advanced Typing Animations", layout="centered")

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
        margin:3rem auto; max-width:800px;
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
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------- ENHANCED Background Systems -------------
class AdvancedBackgroundGenerator:
    def __init__(self):
        self.themes = {
            "Golden Elegance": self.golden_elegance,
            "Deep Amber": self.deep_amber,
            "Vintage Sepia": self.vintage_sepia,
           
            "Sunset Gold": self.sunset_gold,
        }
    
    def golden_elegance(self, width, height, time_progress):
        y, x = np.ogrid[0:height, 0:width]
        y_norm, x_norm = y / height, x / width
        t = time_progress * 3 * math.pi
        
        # Rich golden gradient
        base_r = (120 * (1 - y_norm) + 255 * y_norm).astype(np.uint8)
        base_g = (80 * (1 - y_norm) + 220 * y_norm).astype(np.uint8)
        base_b = (40 * (1 - y_norm) + 100 * y_norm).astype(np.uint8)
        
        # Multiple wave layers
        wave1 = np.sin(x_norm * 8 * math.pi + t) * 25
        wave2 = np.cos(y_norm * 6 * math.pi + t * 1.3) * 20
        wave3 = np.sin((x_norm + y_norm) * 10 * math.pi + t * 0.7) * 15
        
        r = np.clip(base_r + wave1 * 0.8 + wave3 * 0.3, 0, 255)
        g = np.clip(base_g + wave1 * 0.6 + wave2 * 0.4, 0, 255)
        b = np.clip(base_b + wave2 * 0.5 + wave3 * 0.2, 0, 255)
        
        bg = np.stack([r, g, b], axis=-1)
        
        # Enhanced sparkles
        sparkle_intensity = (np.sin(x * y * 0.0002 + t * 8) > 0.99)
        bg[sparkle_intensity] = [255, 240, 160]
        
        return bg
    
    def deep_amber(self, width, height, time_progress):
        y, x = np.ogrid[0:height, 0:width]
        y_norm, x_norm = y / height, x / width
        t = time_progress * 2.5 * math.pi
        
        # Amber tones
        base_r = (150 * (1 - y_norm) + 255 * y_norm).astype(np.uint8)
        base_g = (100 * (1 - y_norm) + 180 * y_norm).astype(np.uint8)
        base_b = (50 * (1 - y_norm) + 80 * y_norm).astype(np.uint8)
        
        wave1 = np.sin(x_norm * 12 * math.pi + t) * 30
        wave2 = np.cos(y_norm * 8 * math.pi + t * 1.7) * 25
        
        r = np.clip(base_r + wave1 * 0.9, 0, 255)
        g = np.clip(base_g + wave1 * 0.7 + wave2 * 0.5, 0, 255)
        b = np.clip(base_b + wave2 * 0.6, 0, 255)
        
        return np.stack([r, g, b], axis=-1)
    
    def vintage_sepia(self, width, height, time_progress):
        y, x = np.ogrid[0:height, 0:width]
        y_norm = y / height
        t = time_progress * 2 * math.pi
        
        # Sepia tones
        base_r = (120 * (1 - y_norm) + 200 * y_norm).astype(np.uint8)
        base_g = (100 * (1 - y_norm) + 170 * y_norm).astype(np.uint8)
        base_b = (80 * (1 - y_norm) + 120 * y_norm).astype(np.uint8)
        
        # Subtle noise texture
        noise = np.random.rand(height, width) * 20 - 10
        
        r = np.clip(base_r + noise, 0, 255)
        g = np.clip(base_g + noise * 0.8, 0, 255)
        b = np.clip(base_b + noise * 0.6, 0, 255)
        
        return np.stack([r, g, b], axis=-1)
    
    def get_theme(self, theme_name):
        return self.themes.get(theme_name, self.golden_elegance)

# ------------- ENHANCED Text Animation Systems -------------
class AdvancedTextAnimator:
    def __init__(self):
        self.animation_styles = {
            "Typewriter": self.typewriter_effect,
            "Smooth Reveal": self.smooth_reveal,
            "Character Pop": self.character_pop,
            "Wave Typing": self.wave_typing,
        }
    
    def typewriter_effect(self, text, progress, line_info):
        """Classic typewriter effect"""
        total_chars = sum(len(line) for line in line_info['lines'])
        chars_to_show = int(total_chars * progress)
        return self.reveal_by_character(text, chars_to_show, line_info)
    
    def smooth_reveal(self, text, progress, line_info):
        """Smooth opacity-based reveal"""
        chars_to_show = int(len(text) * progress)
        revealed_text = text[:chars_to_show]
        
        # For smooth reveal, we'll handle this in the drawing phase
        return revealed_text, progress
    
    def character_pop(self, text, progress, line_info):
        """Characters pop in with slight animation"""
        chars_to_show = int(len(text) * progress)
        return self.reveal_by_character(text, chars_to_show, line_info)
    
    def wave_typing(self, text, progress, line_info):
        """Wave-like typing from left to right"""
        chars_to_show = int(len(text) * progress)
        return self.reveal_by_character(text, chars_to_show, line_info)
    
    def reveal_by_character(self, text, chars_to_show, line_info):
        """Reveal text character by character"""
        current_pos = 0
        revealed_lines = []
        
        for line in line_info['lines']:
            line_chars = len(line)
            if current_pos + line_chars <= chars_to_show:
                revealed_lines.append(line)
            elif current_pos < chars_to_show:
                reveal_count = chars_to_show - current_pos
                revealed_lines.append(line[:reveal_count])
            else:
                revealed_lines.append("")
            current_pos += line_chars
        
        revealed_text = "\n".join(revealed_lines)
        return revealed_text, chars_to_show / len(text)

# ------------- ENHANCED Layout System -------------
class AdvancedTextLayout:
    def __init__(self, width, height, margins=80):
        self.width = width
        self.height = height
        self.margins = margins
        self.content_width = width - 2 * margins
        self.content_height = height - 2 * margins
        
    def calculate_optimal_layout(self, text, style_config):
        """Calculate optimal font, spacing, and positioning"""
        # Estimate lines and font size
        avg_chars_per_line = max(15, self.content_width // (style_config['base_font_size'] // 2))
        estimated_lines = max(1, len(text) // avg_chars_per_line)
        
        # Dynamic font sizing
        max_font = style_config.get('max_font_size', 80)
        min_font = style_config.get('min_font_size', 24)
        font_size = max(min_font, min(max_font, 
            max_font - len(text) // style_config['font_reduction_factor']))
        
        # Try to load font
        try:
            font = ImageFont.truetype(style_config['font_family'], font_size)
        except:
            try:
                font = ImageFont.truetype("Arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        return font, font_size
    
    def break_text_into_lines(self, text, font, max_width):
        """Intelligent line breaking with word wrapping"""
        words = text.split()
        lines = []
        current_line = []
        
        # Create temporary drawing context for measurements
        temp_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(temp_img)
        
        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            
            try:
                bbox = draw.textbbox((0, 0), test_line, font=font)
                line_width = bbox[2] - bbox[0]
            except:
                line_width = len(test_line) * font.size // 2
            
            if line_width > max_width:
                if len(current_line) == 1:
                    # Single word is too long, force break
                    if len(word) > 20:
                        lines.append(word[:20] + '-')
                        current_line = [word[20:]]
                    else:
                        lines.append(word)
                        current_line = []
                else:
                    # Remove last word and start new line
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
            elif word == words[-1]:
                # Last word
                lines.append(' '.join(current_line))
        
        return lines
    
    def calculate_text_block_position(self, lines, font, line_height):
        """Calculate position for text block with various alignments"""
        total_height = len(lines) * line_height
        
        # Vertical alignment
        if total_height > self.content_height:
            start_y = self.margins  # Top align if too tall
        else:
            # Center align
            start_y = self.margins + (self.content_height - total_height) // 2
        
        return start_y

# ------------- ENHANCED Frame Generator -------------
class AdvancedFrameGenerator:
    def __init__(self):
        self.bg_generator = AdvancedBackgroundGenerator()
        self.text_animator = AdvancedTextAnimator()
        self.layout_engine = AdvancedTextLayout(1080, 1920)
    
    def create_enhanced_frame(self, full_text, progress, frame_idx, total_frames, 
                            width, height, style_config):
        """Create a frame with all enhanced features"""
        # Generate background
        bg_theme = self.bg_generator.get_theme(style_config['background_theme'])
        time_progress = frame_idx / total_frames
        bg = bg_theme(width, height, time_progress)
        img = Image.fromarray(bg)
        draw = ImageDraw.Draw(img)
        
        # Calculate layout
        font, font_size = self.layout_engine.calculate_optimal_layout(full_text, style_config)
        
        # Break text into lines
        lines = self.layout_engine.break_text_into_lines(
            full_text, font, self.layout_engine.content_width
        )
        
        line_info = {
            'lines': lines,
            'font': font,
            'font_size': font_size
        }
        
        # Apply text animation
        animator = self.text_animator.animation_styles[style_config['animation_style']]
        visible_text, anim_progress = animator(full_text, progress, line_info)
        
        # Calculate positioning
        try:
            bbox = draw.textbbox((0, 0), "Test", font=font)
            line_height = (bbox[3] - bbox[1]) * style_config['line_spacing']
        except:
            line_height = font_size * style_config['line_spacing']
        
        visible_lines = visible_text.split('\n') if visible_text else []
        start_y = self.layout_engine.calculate_text_block_position(
            visible_lines, font, line_height
        )
        
        # Draw text with enhanced styling
        for i, line in enumerate(visible_lines):
            y_pos = start_y + i * line_height
            
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
            except:
                line_width = len(line) * font_size // 2
            
            x_pos = (width - line_width) // 2
            
            # Enhanced text effects
            shadow_blur = 3
            shadow_color = style_config['shadow_color']
            text_color = style_config['text_color']
            
            # Text shadow
            for dx, dy in [(shadow_blur, shadow_blur), (0, shadow_blur), (shadow_blur, 0)]:
                draw.text((x_pos + dx, y_pos + dy), line, font=font, fill=shadow_color)
            
            # Main text
            draw.text((x_pos, y_pos), line, font=font, fill=text_color)
            
            # Add subtle glow for certain styles
            if style_config.get('glow_effect', False):
                for glow_size in [1]:
                    try:
                        glow_font = ImageFont.truetype(style_config['font_family'], font_size + glow_size)
                        draw.text((x_pos, y_pos), line, font=glow_font, 
                                fill=text_color + (100,))  # Semi-transparent
                    except:
                        pass
        
        return np.array(img)

# ------------- Video Generation -------------
def generate_enhanced_video(sentence, duration, width, height, style_config, output_path):
    """Generate video with all enhanced features"""
    fps = 30
    total_frames = duration * fps
    
    frame_generator = AdvancedFrameGenerator()
    
    with imageio.get_writer(
        output_path, 
        fps=fps, 
        codec="libx264",
        quality=8,
        pixelformat="yuv420p"
    ) as writer:
        
        for frame_idx in range(total_frames):
            progress = (frame_idx + 1) / total_frames
            
            frame = frame_generator.create_enhanced_frame(
                sentence, progress, frame_idx, total_frames, 
                width, height, style_config
            )
            
            writer.append_data(frame)
            
            if frame_idx % 15 == 0:
                yield frame_idx / total_frames
    
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

# ------------- Main UI with Enhanced Features -------------
with st.container():
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center;color:#ffffff'>🎬 Advanced Typing Animations</h1>", unsafe_allow_html=True)
    
    # Feature showcase
    st.markdown("""
    <div style='text-align:center; margin-bottom:2rem;'>
        <span style='background:linear-gradient(45deg, #FFD700, #FFA500); -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-weight:bold;'>
            Multiple Themes • Advanced Animations • Custom Styles
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Configuration in expandable sections
    with st.expander("🎨 Style Configuration", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            background_theme = st.selectbox(
                "Background Theme",
                ["Golden Elegance", "Deep Amber", "Vintage Sepia", "Royal Bronze", "Sunset Gold"]
            )
            
            animation_style = st.selectbox(
                "Animation Style",
                ["Typewriter", "Smooth Reveal", "Character Pop", "Wave Typing"]
            )
        
        with col2:
            text_color = st.color_picker("Text Color", "#FFD700")
            shadow_color = st.color_picker("Shadow Color", "#8B4513")
            
            line_spacing = st.slider("Line Spacing", 1.2, 2.0, 1.4, 0.1)
        
        with col3:
            duration = st.slider("Duration (seconds)", 2, 8, 4)
            resolution = st.selectbox("Resolution", ["720x1280", "1080x1920"], index=1)
    
    with st.expander("📝 Text Configuration", expanded=True):
        sentence = st.text_area(
            "Your Text:",
            "Create stunning animated text videos with multiple themes and advanced typography effects. Perfect for social media!",
            height=100,
            max_chars=400,
            help="Enter up to 400 characters. The system will automatically adjust layout and font size."
        )
        
        # Text preview
        if sentence:
            chars_count = len(sentence)
            st.caption(f"Characters: {chars_count}/400 • Estimated lines: {max(1, chars_count // 40)}")
    
    # Advanced settings
    with st.expander("⚙️ Advanced Settings"):
        col1, col2 = st.columns(2)
        with col1:
            base_font_size = st.slider("Base Font Size", 20, 100, 60)
            font_reduction = st.slider("Font Reduction", 10, 30, 15)
        with col2:
            glow_effect = st.checkbox("Enable Glow Effect", True)
            fast_mode = st.checkbox("Fast Generation Mode", True)
    
    resolution_map = {"720x1280": (720, 1280), "1080x1920": (1080, 1920)}
    W, H = resolution_map[resolution]
    
    # Style configuration
    style_config = {
        'background_theme': background_theme,
        'animation_style': animation_style,
        'text_color': text_color,
        'shadow_color': shadow_color,
        'line_spacing': line_spacing,
        'base_font_size': base_font_size,
        'font_reduction_factor': font_reduction,
        'glow_effect': glow_effect,
        'font_family': "Arial.ttf",
        'max_font_size': 80,
        'min_font_size': 24
    }
    
    if st.button("🚀 Generate Advanced Animation", type="primary", use_container_width=True):
        if not sentence.strip():
            st.warning("Please enter some text.")
            st.stop()
        
        if len(sentence) > 400:
            st.warning("Text too long! Please limit to 400 characters.")
            st.stop()
        
        with st.spinner("Creating your advanced animation..."):
            tmpdir = Path(tempfile.mkdtemp())
            out_mp4 = tmpdir / "advanced_typing.mp4"
            
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Show generation details
                status_text.text("🎨 Setting up advanced animation system...")
                
                for progress in generate_enhanced_video(sentence, duration, W, H, style_config, out_mp4):
                    progress_bar.progress(progress)
                    if progress < 1.0:
                        status_text.text(f"🎬 Generating {animation_style} animation... {int(progress * 100)}%")
                    else:
                        status_text.text("✅ Finalizing video...")
                
                # Store results
                st.session_state.generated_video_path = out_mp4
                st.session_state.show_video = True
                st.session_state.video_tmpdir = tmpdir
                
                st.success(f"✨ Advanced animation created successfully!")
                
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
            
            st.markdown("### 🎥 Your Advanced Animation")
            
            # Display video
            video_html = get_video_html(st.session_state.generated_video_path)
            st.markdown(video_html, unsafe_allow_html=True)
            
            # Download section
            col1, col2 = st.columns([3, 1])
            with col1:
                with open(st.session_state.generated_video_path, "rb") as f:
                    st.download_button(
                        label="⬇️ Download MP4", 
                        data=f, 
                        file_name="advanced_animation.mp4", 
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
    
    # Features showcase
    st.markdown("---")
    st.markdown("### 🎯 Advanced Features")
    
    features_col1, features_col2 = st.columns(2)
    
    with features_col1:
        st.markdown("""
        <div class='feature-card'>
        <h4>🎨 Multiple Themes</h4>
        <p>Choose from 5 professionally designed brown/gold color schemes</p>
        </div>
        
        <div class='feature-card'>
        <h4>✨ Advanced Animations</h4>
        <p>4 different typing effects including smooth reveals and pop animations</p>
        </div>
        
        <div class='feature-card'>
        <h4>🎯 Smart Layout</h4>
        <p>Automatic text sizing, line breaking, and perfect centering</p>
        </div>
        """, unsafe_allow_html=True)
    
    with features_col2:
        st.markdown("""
        <div class='feature-card'>
        <h4>🌈 Custom Colors</h4>
        <p>Full control over text and shadow colors with color picker</p>
        </div>
        
        <div class='feature-card'>
        <h4>📐 Fine Tuning</h4>
        <p>Adjust line spacing, font sizes, and animation parameters</p>
        </div>
        
        <div class='feature-card'>
        <h4>⚡ Optimized Performance</h4>
        <p>Fast generation with real-time progress tracking</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# Cleanup
if hasattr(st.session_state, 'video_tmpdir') and not hasattr(st.session_state, 'show_video'):
    import shutil
    try:
        shutil.rmtree(st.session_state.video_tmpdir, ignore_errors=True)
    except:
        pass
