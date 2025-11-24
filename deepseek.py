# app.py (FIXED - Data Type Issues Resolved)
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

# ------------- FIXED Background Systems -------------
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
        
        # Rich golden gradient - ensure uint8
        base_r = (120 * (1 - y_norm) + 255 * y_norm).astype(np.uint8)
        base_g = (80 * (1 - y_norm) + 220 * y_norm).astype(np.uint8)
        base_b = (40 * (1 - y_norm) + 100 * y_norm).astype(np.uint8)
        
        # Multiple wave layers - ensure calculations stay in bounds
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
        bg[highlights] = [205, 127, 50]  # Bronze color
        
        return bg.astype(np.uint8)
    
    def sunset_gold(self, width, height, time_progress):
        y, x = np.ogrid[0:height, 0:width]
        y_norm, x_norm = y / height, x / width
        t = time_progress * 1.8 * math.pi
        
        # Sunset colors - dark to bright gold
        base_r = (130 * (1 - y_norm) + 255 * y_norm).astype(np.uint8)
        base_g = (70 * (1 - y_norm) + 200 * y_norm).astype(np.uint8)
        base_b = (30 * (1 - y_norm) + 100 * y_norm).astype(np.uint8)
        
        # Sunset wave patterns
        wave1 = np.sin(x_norm * 6 * math.pi + t) * 25
        wave2 = np.cos(y_norm * 4 * math.pi + t * 0.8) * 20
        wave3 = np.sin((x_norm - y_norm) * 8 * math.pi + t * 1.2) * 15
        
        r = np.clip(base_r.astype(np.float32) + wave1 * 0.8 + wave3 * 0.4, 0, 255).astype(np.uint8)
        g = np.clip(base_g.astype(np.float32) + wave1 * 0.6 + wave2 * 0.5, 0, 255).astype(np.uint8)
        b = np.clip(base_b.astype(np.float32) + wave2 * 0.4, 0, 255).astype(np.uint8)
        
        bg = np.stack([r, g, b], axis=-1)
        
        # Sunset glow effect
        glow_mask = (y_norm > 0.7) & (np.sin(x_norm * 4 * math.pi + t) > 0.5)
        glow_addition = np.array([30, 30, 10], dtype=np.uint8)
        bg[glow_mask] = np.clip(bg[glow_mask].astype(np.int32) + glow_addition, 0, 255).astype(np.uint8)
        
        return bg.astype(np.uint8)
    
    def get_theme(self, theme_name):
        return self.themes.get(theme_name, self.golden_elegance)

# ------------- SIMPLIFIED Text Animation Systems -------------
class AdvancedTextAnimator:
    def __init__(self):
        self.animation_styles = {
            "Typewriter": self.typewriter_effect,
            "Smooth Reveal": self.smooth_reveal,
        }
    
    def typewriter_effect(self, text, progress, line_info):
        """Classic typewriter effect"""
        total_chars = sum(len(line) for line in line_info['lines'])
        chars_to_show = int(total_chars * progress)
        return self.reveal_by_character(text, chars_to_show, line_info)
    
    def smooth_reveal(self, text, progress, line_info):
        """Smooth character-by-character reveal"""
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

# ------------- SIMPLIFIED Layout System -------------
class AdvancedTextLayout:
    def __init__(self, width, height, margins=80):
        self.width = width
        self.height = height
        self.margins = margins
        self.content_width = width - 2 * margins
        self.content_height = height - 2 * margins
        
    def calculate_optimal_layout(self, text, style_config):
        """Calculate optimal font, spacing, and positioning"""
        # Simple font size calculation
        avg_chars = len(text) / max(1, (self.content_width // 30))
        font_size = max(24, min(80, 70 - int(avg_chars * 0.5)))
        
        # Try to load font
        try:
            font = ImageFont.truetype("Arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        return font, font_size
    
    def break_text_into_lines(self, text, font, max_width):
        """Simple line breaking with word wrapping"""
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
                    # Single word is too long, break it
                    lines.append(word)
                    current_line = []
                else:
                    # Remove last word and start new line
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
        
        # Add remaining words
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def calculate_text_block_position(self, lines, font, line_height):
        """Calculate position for text block"""
        total_height = len(lines) * line_height
        
        if total_height > self.content_height:
            start_y = self.margins  # Top align if too tall
        else:
            # Center align
            start_y = self.margins + (self.content_height - total_height) // 2
        
        return start_y

# ------------- FIXED Frame Generator -------------
class AdvancedFrameGenerator:
    def __init__(self):
        self.bg_generator = AdvancedBackgroundGenerator()
        self.text_animator = AdvancedTextAnimator()
    
    def create_enhanced_frame(self, full_text, progress, frame_idx, total_frames, 
                            width, height, style_config):
        """Create a frame with all enhanced features"""
        try:
            # Generate background
            bg_theme = self.bg_generator.get_theme(style_config['background_theme'])
            time_progress = frame_idx / total_frames
            bg = bg_theme(width, height, time_progress)
            
            # Ensure background is uint8
            if bg.dtype != np.uint8:
                bg = bg.astype(np.uint8)
                
            img = Image.fromarray(bg)
            draw = ImageDraw.Draw(img)
            
            # Initialize layout engine
            layout_engine = AdvancedTextLayout(width, height)
            
            # Calculate layout
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
            start_y = layout_engine.calculate_text_block_position(
                visible_lines, font, line_height
            )
            
            # Convert color strings to RGB tuples
            text_color = self.hex_to_rgb(style_config['text_color'])
            shadow_color = self.hex_to_rgb(style_config['shadow_color'])
            
            # Draw text with enhanced styling
            for i, line in enumerate(visible_lines):
                if not line.strip():  # Skip empty lines
                    continue
                    
                y_pos = start_y + i * line_height
                
                try:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    line_width = bbox[2] - bbox[0]
                except:
                    line_width = len(line) * font_size // 2
                
                x_pos = (width - line_width) // 2
                
                # Text shadow
                shadow_blur = 2
                draw.text((x_pos + shadow_blur, y_pos + shadow_blur), line, font=font, fill=shadow_color)
                
                # Main text
                draw.text((x_pos, y_pos), line, font=font, fill=text_color)
            
            # Convert back to numpy array and ensure uint8
            frame_array = np.array(img)
            if frame_array.dtype != np.uint8:
                frame_array = frame_array.astype(np.uint8)
                
            return frame_array
            
        except Exception as e:
            # Fallback: create a simple frame if something goes wrong
            st.warning(f"Frame generation issue: {e}. Using fallback.")
            fallback_frame = np.zeros((height, width, 3), dtype=np.uint8)
            fallback_frame[:, :] = [50, 50, 50]  # Gray background
            return fallback_frame
    
    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# ------------- FIXED Video Generation -------------
def generate_enhanced_video(sentence, duration, width, height, style_config, output_path):
    """Generate video with all enhanced features"""
    fps = 24  # Reduced for better performance
    total_frames = duration * fps
    
    frame_generator = AdvancedFrameGenerator()
    
    try:
        with imageio.get_writer(
            output_path, 
            fps=fps, 
            codec="libx264",
            quality=7,  # Slightly lower quality for stability
            pixelformat="yuv420p",
            macro_block_size=8  # Ensure compatible dimensions
        ) as writer:
            
            for frame_idx in range(total_frames):
                progress = (frame_idx + 1) / total_frames
                
                frame = frame_generator.create_enhanced_frame(
                    sentence, progress, frame_idx, total_frames, 
                    width, height, style_config
                )
                
                # Ensure frame is uint8 before writing
                if frame.dtype != np.uint8:
                    frame = frame.astype(np.uint8)
                
                writer.append_data(frame)
                
                if frame_idx % 10 == 0:  # Reduced frequency for better performance
                    yield frame_idx / total_frames
        
        yield 1.0
        
    except Exception as e:
        st.error(f"Video generation error: {e}")
        yield 1.0  # Still yield completion to avoid hanging

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
        st.markdown("<h1 style='text-align:center;color:#ffffff'>🎬 Advanced Typing Animations</h1>", unsafe_allow_html=True)
        
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
                    ["Typewriter", "Smooth Reveal"]
                )
            
            with col2:
                text_color = st.color_picker("Text Color", "#FFD700")
                shadow_color = st.color_picker("Shadow Color", "#8B4513")
                
                line_spacing = st.slider("Line Spacing", 1.2, 2.0, 1.4, 0.1)
            
            with col3:
                duration = st.slider("Duration (seconds)", 2, 6, 4)
                resolution = st.selectbox("Resolution", ["720x1280", "1080x1920"], index=0)  # Default to smaller for performance
        
        with st.expander("📝 Text Configuration", expanded=True):
            sentence = st.text_area(
                "Your Text:",
                "Create beautiful animated text videos with multiple themes and effects!",
                height=80,
                max_chars=200,  # Reduced for stability
                help="Enter up to 200 characters for best performance."
            )
            
            # Text preview
            if sentence:
                chars_count = len(sentence)
                st.caption(f"Characters: {chars_count}/200 • Estimated lines: {max(1, chars_count // 40)}")
        
        resolution_map = {"720x1280": (720, 1280), "1080x1920": (1080, 1920)}
        W, H = resolution_map[resolution]
        
        # Style configuration
        style_config = {
            'background_theme': background_theme,
            'animation_style': animation_style,
            'text_color': text_color,
            'shadow_color': shadow_color,
            'line_spacing': line_spacing,
        }
        
        if st.button("🚀 Generate Animation", type="primary", use_container_width=True):
            if not sentence.strip():
                st.warning("Please enter some text.")
                return
            
            if len(sentence) > 200:
                st.warning("Text too long! Please limit to 200 characters for stability.")
                return
            
            with st.spinner("Creating your animation..."):
                tmpdir = Path(tempfile.mkdtemp())
                out_mp4 = tmpdir / "typing_animation.mp4"
                
                try:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("🎨 Setting up animation...")
                    
                    for progress in generate_enhanced_video(sentence, duration, W, H, style_config, out_mp4):
                        progress_bar.progress(progress)
                        if progress < 1.0:
                            status_text.text(f"🎬 Generating {animation_style}... {int(progress * 100)}%")
                        else:
                            status_text.text("✅ Finalizing video...")
                    
                    # Store results
                    st.session_state.generated_video_path = out_mp4
                    st.session_state.show_video = True
                    st.session_state.video_tmpdir = tmpdir
                    
                    st.success(f"✨ Animation created successfully!")
                    
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
                
                st.markdown("### 🎥 Your Animation")
                
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
                            file_name="typing_animation.mp4", 
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
        
        st.markdown("</div>", unsafe_allow_html=True)

# Run the app
if __name__ == "__main__":
    main()
