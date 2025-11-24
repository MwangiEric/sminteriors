# app.py (FIXED - Larger Text + Top-to-Bottom Animation)
import streamlit as st
import numpy as np
import imageio
import tempfile
import base64
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import os

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
        
        # Rich golden gradient
        base_r = (120 * (1 - y_norm) + 255 * y_norm).astype(np.uint8)
        base_g = (80 * (1 - y_norm) + 220 * y_norm).astype(np.uint8)
        base_b = (40 * (1 - y_norm) + 100 * y_norm).astype(np.uint8)
        
        # Multiple wave layers
        wave1 = np.sin(x_norm * 8 * math.pi + t) * 25
        wave2 = np.cos(y_norm * 6 * math.pi + t * 1.3) * 20
        wave3 = np.sin((x_norm + y_norm) * 10 * math.pi + t * 0.7) * 15
        
        r = np.clip(base_r + wave1 * 0.8 + wave3 * 0.3, 0, 255).astype(np.uint8)
        g = np.clip(base_g + wave1 * 0.6 + wave2 * 0.4, 0, 255).astype(np.uint8)
        b = np.clip(base_b + wave2 * 0.5 + wave3 * 0.2, 0, 255).astype(np.uint8)
        
        bg = np.stack([r, g, b], axis=-1)
        
        # Enhanced sparkles
        sparkle_intensity = (np.sin(x.astype(float) * y.astype(float) * 0.0002 + t * 8) > 0.99)
        bg[sparkle_intensity] = [255, 240, 160]
        
        return bg.astype(np.uint8)
    
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
        
        r = np.clip(base_r + wave1 * 0.9, 0, 255).astype(np.uint8)
        g = np.clip(base_g + wave1 * 0.7 + wave2 * 0.5, 0, 255).astype(np.uint8)
        b = np.clip(base_b + wave2 * 0.6, 0, 255).astype(np.uint8)
        
        return np.stack([r, g, b], axis=-1).astype(np.uint8)
    
    def vintage_sepia(self, width, height, time_progress):
        y, x = np.ogrid[0:height, 0:width]
        y_norm = y / height
        t = time_progress * 2 * math.pi
        
        # Sepia tones
        base_r = (120 * (1 - y_norm) + 200 * y_norm).astype(np.uint8)
        base_g = (100 * (1 - y_norm) + 170 * y_norm).astype(np.uint8)
        base_b = (80 * (1 - y_norm) + 120 * y_norm).astype(np.uint8)
        
        # Subtle noise texture
        noise = (np.random.rand(height, width) * 20 - 10).astype(np.float32)
        
        r = np.clip(base_r.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        g = np.clip(base_g.astype(np.float32) + noise * 0.8, 0, 255).astype(np.uint8)
        b = np.clip(base_b.astype(np.float32) + noise * 0.6, 0, 255).astype(np.uint8)
        
        return np.stack([r, g, b], axis=-1).astype(np.uint8)
    
    def royal_bronze(self, width, height, time_progress):
        y, x = np.ogrid[0:height, 0:width]
        y_norm, x_norm = y / height, x / width
        t = time_progress * 2.2 * math.pi
        
        # Bronze metallic tones
        base_r = (110 * (1 - y_norm) + 180 * y_norm).astype(np.uint8)
        base_g = (80 * (1 - y_norm) + 140 * y_norm).astype(np.uint8)
        base_b = (60 * (1 - y_norm) + 100 * y_norm).astype(np.uint8)
        
        # Metallic wave effects
        wave1 = np.sin(x_norm * 10 * math.pi + t) * 20
        wave2 = np.cos(y_norm * 7 * math.pi + t * 1.5) * 15
        metallic = np.sin((x_norm * 5 + y_norm * 3) * math.pi + t * 2) * 10
        
        r = np.clip(base_r.astype(np.float32) + wave1 * 0.7 + metallic * 0.5, 0, 255).astype(np.uint8)
        g = np.clip(base_g.astype(np.float32) + wave1 * 0.5 + wave2 * 0.4, 0, 255).astype(np.uint8)
        b = np.clip(base_b.astype(np.float32) + wave2 * 0.3 + metallic * 0.3, 0, 255).astype(np.uint8)
        
        bg = np.stack([r, g, b], axis=-1)
        
        # Bronze highlights
        highlights = (np.sin(x.astype(float) * 0.01 + y.astype(float) * 0.01 + t * 3) > 0.95)
        bg[highlights] = [205, 127, 50]
        
        return bg.astype(np.uint8)
    
    def sunset_gold(self, width, height, time_progress):
        y, x = np.ogrid[0:height, 0:width]
        y_norm, x_norm = y / height, x / width
        t = time_progress * 1.8 * math.pi
        
        # Sunset colors
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

# ------------- TOP-TO-BOTTOM Text Animation System -------------
class TopToBottomTextAnimator:
    def __init__(self):
        self.animation_styles = {
            "Typewriter Top-to-Bottom": self.typewriter_top_bottom,
            "Smooth Reveal Top-to-Bottom": self.smooth_top_bottom,
        }
    
    def typewriter_top_bottom(self, text, progress, line_info):
        """Typewriter effect from top to bottom"""
        lines = line_info['lines']
        total_lines = len(lines)
        
        # Calculate how many full lines to show
        lines_to_show = int(total_lines * progress)
        
        # Build revealed text
        revealed_lines = []
        for i in range(total_lines):
            if i < lines_to_show:
                # Show complete line
                revealed_lines.append(lines[i])
            elif i == lines_to_show:
                # Show partial line (character by character)
                partial_progress = (progress * total_lines) - lines_to_show
                chars_to_show = int(len(lines[i]) * partial_progress)
                revealed_lines.append(lines[i][:chars_to_show])
            else:
                # Line not yet revealed
                revealed_lines.append("")
        
        revealed_text = "\n".join(revealed_lines)
        return revealed_text, progress
    
    def smooth_top_bottom(self, text, progress, line_info):
        """Smooth reveal from top to bottom"""
        lines = line_info['lines']
        total_lines = len(lines)
        
        # Calculate lines to show with smooth transition
        exact_lines = progress * total_lines
        lines_to_show = int(exact_lines)
        partial_progress = exact_lines - lines_to_show
        
        revealed_lines = []
        for i in range(total_lines):
            if i < lines_to_show:
                # Show complete line
                revealed_lines.append(lines[i])
            elif i == lines_to_show:
                # Show line with smooth character reveal
                chars_to_show = int(len(lines[i]) * partial_progress)
                revealed_lines.append(lines[i][:chars_to_show])
            else:
                revealed_lines.append("")
        
        revealed_text = "\n".join(revealed_lines)
        return revealed_text, progress

# ------------- LARGE TEXT Layout System -------------
class LargeTextLayout:
    def __init__(self, width, height, margins=60):
        self.width = width
        self.height = height
        self.margins = margins
        self.content_width = width - 2 * margins
        self.content_height = height - 2 * margins
        
    def calculate_optimal_layout(self, text, style_config):
        """Calculate optimal font size for LARGE text"""
        # Start with larger base font size
        base_font_size = style_config.get('base_font_size', 80)
        
        # Adjust based on text length but keep it large
        text_length = len(text)
        if text_length < 50:
            font_size = min(120, base_font_size + 20)  # Very large for short text
        elif text_length < 100:
            font_size = min(100, base_font_size + 10)  # Large for medium text
        else:
            font_size = max(60, base_font_size - text_length // 30)  # Still decent size
        
        # Ensure minimum size
        font_size = max(50, font_size)
        
        # Try to load font
        try:
            font = ImageFont.truetype("Arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
                # Scale default font if possible
                try:
                    font = ImageFont.load_default()
                except:
                    pass
        
        return font, font_size
    
    def break_text_into_lines(self, text, font, max_width):
        """Break text into lines with LARGER font consideration"""
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
                # Fallback calculation
                line_width = len(test_line) * font.size // 1.8  # Adjusted for larger text
            
            if line_width > max_width:
                if len(current_line) == 1:
                    # Single word is too long, break it
                    if len(word) > 15:
                        # Break very long words
                        parts = [word[i:i+15] for i in range(0, len(word), 15)]
                        lines.extend(parts[:-1])
                        current_line = [parts[-1]]
                    else:
                        lines.append(word)
                        current_line = []
                else:
                    # Remove last word and start new line
                    current_line.pop()
                    if current_line:  # Only add if not empty
                        lines.append(' '.join(current_line))
                    current_line = [word]
        
        # Add remaining words
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def calculate_text_block_position(self, lines, font, line_height, start_from_top=True):
        """Calculate position starting from TOP"""
        total_height = len(lines) * line_height
        
        if start_from_top:
            # Start from top with some margin
            start_y = self.margins + 50
        else:
            # Center align (fallback)
            start_y = self.margins + (self.content_height - total_height) // 2
        
        return start_y

# ------------- Frame Generator with LARGE TEXT -------------
class LargeTextFrameGenerator:
    def __init__(self):
        self.bg_generator = AdvancedBackgroundGenerator()
        self.text_animator = TopToBottomTextAnimator()
    
    def create_frame_with_large_text(self, full_text, progress, frame_idx, total_frames, 
                                   width, height, style_config):
        """Create frame with LARGE text and top-to-bottom animation"""
        try:
            # Generate background
            bg_theme = self.bg_generator.get_theme(style_config['background_theme'])
            time_progress = frame_idx / total_frames
            bg = bg_theme(width, height, time_progress)
            
            if bg.dtype != np.uint8:
                bg = bg.astype(np.uint8)
                
            img = Image.fromarray(bg)
            draw = ImageDraw.Draw(img)
            
            # Initialize layout engine with LARGE text settings
            layout_engine = LargeTextLayout(width, height)
            
            # Calculate layout with LARGE font
            font, font_size = layout_engine.calculate_optimal_layout(full_text, style_config)
            
            # Break text into lines
            lines = layout_engine.break_text_into_lines(
                full_text, font, layout_engine.content_width
            )
            
            line_info = {
                'lines': lines,
                'font': font,
                'font_size': font_size
            }
            
            # Apply TOP-TO-BOTTOM text animation
            animator = self.text_animator.animation_styles[style_config['animation_style']]
            visible_text, anim_progress = animator(full_text, progress, line_info)
            
            # Calculate positioning - START FROM TOP
            try:
                bbox = draw.textbbox((0, 0), "Test", font=font)
                line_height = (bbox[3] - bbox[1]) * style_config['line_spacing']
            except:
                line_height = font_size * style_config['line_spacing'] * 1.3  # More spacing for large text
            
            visible_lines = visible_text.split('\n') if visible_text else []
            start_y = layout_engine.calculate_text_block_position(
                visible_lines, font, line_height, start_from_top=True
            )
            
            # Convert color strings to RGB tuples
            text_color = self.hex_to_rgb(style_config['text_color'])
            shadow_color = self.hex_to_rgb(style_config['shadow_color'])
            
            # Draw LARGE text with enhanced styling
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
                
                # Enhanced shadow for large text
                shadow_blur = 4
                for dx, dy in [(shadow_blur, shadow_blur), (0, shadow_blur), (shadow_blur, 0)]:
                    draw.text((x_pos + dx, y_pos + dy), line, font=font, fill=shadow_color)
                
                # Main text
                draw.text((x_pos, y_pos), line, font=font, fill=text_color)
            
            # Convert back to numpy array
            frame_array = np.array(img)
            if frame_array.dtype != np.uint8:
                frame_array = frame_array.astype(np.uint8)
                
            return frame_array
            
        except Exception as e:
            # Fallback frame
            st.warning(f"Frame issue: {e}")
            fallback_frame = np.zeros((height, width, 3), dtype=np.uint8)
            fallback_frame[:, :] = [50, 50, 50]
            return fallback_frame
    
    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# ------------- Video Generation -------------
def generate_large_text_video(sentence, duration, width, height, style_config, output_path):
    """Generate video with LARGE text and top-to-bottom animation"""
    fps = 24
    total_frames = duration * fps
    
    frame_generator = LargeTextFrameGenerator()
    
    try:
        with imageio.get_writer(
            output_path, 
            fps=fps, 
            codec="libx264",
            quality=7,
            pixelformat="yuv420p",
            macro_block_size=8
        ) as writer:
            
            for frame_idx in range(total_frames):
                progress = (frame_idx + 1) / total_frames
                
                frame = frame_generator.create_frame_with_large_text(
                    sentence, progress, frame_idx, total_frames, 
                    width, height, style_config
                )
                
                if frame.dtype != np.uint8:
                    frame = frame.astype(np.uint8)
                
                writer.append_data(frame)
                
                if frame_idx % 10 == 0:
                    yield frame_idx / total_frames
        
        yield 1.0
        
    except Exception as e:
        st.error(f"Video error: {e}")
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
    with st.container():
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center;color:#ffffff'>🎬 Large Text Typing Animations</h1>", unsafe_allow_html=True)
        
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
                    ["Typewriter Top-to-Bottom", "Smooth Reveal Top-to-Bottom"]
                )
            
            with col2:
                text_color = st.color_picker("Text Color", "#FFD700")
                shadow_color = st.color_picker("Shadow Color", "#8B4513")
                
                line_spacing = st.slider("Line Spacing", 1.3, 2.2, 1.6, 0.1)
            
            with col3:
                duration = st.slider("Duration (seconds)", 3, 8, 5)
                resolution = st.selectbox("Resolution", ["720x1280", "1080x1920"], index=1)
        
        with st.expander("📝 Text Configuration", expanded=True):
            sentence = st.text_area(
                "Your Text:",
                "WELCOME TO OUR AMAZING TEXT ANIMATION! THIS TEXT IS LARGE AND CLEAR, ANIMATING FROM TOP TO BOTTOM WITH BEAUTIFUL EFFECTS.",
                height=100,
                max_chars=300,
                help="Text will be displayed in LARGE font size and animate from top to bottom"
            )
            
            if sentence:
                chars_count = len(sentence)
                estimated_lines = max(1, chars_count // 25)  # Fewer chars per line for larger text
                st.caption(f"Characters: {chars_count}/300 • Estimated lines: {estimated_lines}")
        
        resolution_map = {"720x1280": (720, 1280), "1080x1920": (1080, 1920)}
        W, H = resolution_map[resolution]
        
        # Style configuration with LARGE text settings
        style_config = {
            'background_theme': background_theme,
            'animation_style': animation_style,
            'text_color': text_color,
            'shadow_color': shadow_color,
            'line_spacing': line_spacing,
            'base_font_size': 80,  # Larger base size
        }
        
        if st.button("🚀 Generate Large Text Animation", type="primary", use_container_width=True):
            if not sentence.strip():
                st.warning("Please enter some text.")
                return
            
            with st.spinner("Creating your LARGE TEXT animation..."):
                tmpdir = Path(tempfile.mkdtemp())
                out_mp4 = tmpdir / "large_text_animation.mp4"
                
                try:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("🎨 Setting up LARGE TEXT animation...")
                    
                    for progress in generate_large_text_video(sentence, duration, W, H, style_config, out_mp4):
                        progress_bar.progress(progress)
                        if progress < 1.0:
                            status_text.text(f"🎬 Animating top-to-bottom... {int(progress * 100)}%")
                        else:
                            status_text.text("✅ Finalizing video...")
                    
                    st.session_state.generated_video_path = out_mp4
                    st.session_state.show_video = True
                    st.session_state.video_tmpdir = tmpdir
                    
                    st.success("✨ LARGE TEXT animation created successfully!")
                    
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
                
                st.markdown("### 🎥 Your Large Text Animation")
                
                video_html = get_video_html(st.session_state.generated_video_path)
                st.markdown(video_html, unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    with open(st.session_state.generated_video_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Download MP4", 
                            data=f, 
                            file_name="large_text_animation.mp4", 
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
        st.markdown("### 🎯 Key Features")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class='feature-card'>
            <h4>📏 LARGE TEXT</h4>
            <p>Text is much larger and more readable (50-120px font sizes)</p>
            </div>
            
            <div class='feature-card'>
            <h4>⬇️ TOP-TO-BOTTOM</h4>
            <p>Text animates from the top down, line by line</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class='feature-card'>
            <h4>🎨 5 THEMES</h4>
            <p>Beautiful brown/gold animated backgrounds</p>
            </div>
            
            <div class='feature-card'>
            <h4>🌈 CUSTOM COLORS</h4>
            <p>Choose your text and shadow colors</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
