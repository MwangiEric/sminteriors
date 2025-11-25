import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import tempfile, os, numpy as np, io, json, random
from moviepy.editor import ImageSequenceClip, AudioFileClip
import math
import groq

st.set_page_config(page_title="SM Interiors DIY Tips Animator", layout="wide", page_icon="💡")

WIDTH, HEIGHT = 1080, 1920
FPS = 30

# LOCAL AUDIO
AUDIO_DIR = "audio"
MUSIC_FILES = {
    "Gold Luxury": "gold_luxury.mp3",
    "Viral Pulse": "viral_pulse.mp3", 
    "Elegant Flow": "elegant_flow.mp3",
}

LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png"

# DIY Categories for organized content
DIY_CATEGORIES = {
    "furniture": "🪑 Furniture Care & Restoration",
    "cleaning": "🧽 Cleaning & Maintenance", 
    "decor": "🎨 Decor & Styling",
    "organization": "📦 Organization Solutions",
    "lighting": "💡 Lighting & Ambiance",
    "woodworking": "🔨 Woodworking Basics",
    "upholstery": "🛋️ Upholstery & Fabrics",
    "paint": "🎨 Painting Techniques"
}

# Initialize Groq client
@st.cache_resource
def init_groq_client():
    """Initialize Groq client with API key"""
    if 'groq_key' in st.secrets:
        return groq.Client(api_key=st.secrets['groq_key'])
    else:
        st.error("❌ Groq API key not found. Please add 'groq_key' to Streamlit secrets.")
        return None

@st.cache_resource
def load_logo():
    """Load logo with error handling"""
    try:
        import requests
        resp = requests.get(LOGO_URL, timeout=5)
        if resp.status_code == 200:
            logo = Image.open(io.BytesIO(resp.content)).convert("RGBA").resize((280, 140))
            return logo
    except:
        fallback = Image.new("RGBA", (280, 140), (0,0,0,0))
        draw = ImageDraw.Draw(fallback)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 80)
        except:
            font = ImageFont.load_default()
        draw.text((10, 30), "SM", font=font, fill="#FFD700")
        return fallback

def calculate_duration(tip_text):
    """Calculate video duration based on word count"""
    word_count = len(tip_text.split())
    
    if word_count <= 10:
        return 5  # Quick tips
    elif word_count <= 25:
        return 8  # Standard tips
    elif word_count <= 40:
        return 12  # Detailed explanations
    else:
        return 15  # Comprehensive guides

def generate_diy_content(client, category="furniture"):
    """Generate DIY tips using Groq AI"""
    try:
        category_name = DIY_CATEGORIES[category].split(" ")[1]
        prompt = f"""
        As an interior design expert for SM Interiors, generate a DIY tip about {category_name}:
        1. A catchy DIY tip title (max 5 words)
        2. A practical DIY tip description (2-3 sentences max)
        3. A engaging social media caption
        4. Relevant hashtags (10-15 hashtags)

        Format your response as JSON:
        {{
            "title": "creative title here",
            "tip": "detailed tip description here",
            "caption": "engaging social media caption here",
            "hashtags": "#DIY #HomeDecor #InteriorDesign #Furniture #HomeImprovement #DesignTips #BudgetFriendly #HomeHacks #InteriorInspo #SMInteriors"
        }}
        """
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.8,
            max_tokens=500
        )
        
        response = chat_completion.choices[0].message.content
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            json_str = response[start:end]
            return json.loads(json_str)
        else:
            raise ValueError("Invalid JSON response from AI")
            
    except Exception as e:
        st.error(f"AI generation failed: {e}")
        # Return reliable fallback content
        return {
            "title": "PRO TIP",
            "tip": "Mix vinegar and olive oil for natural wood polish that brings out the grain beautifully.",
            "caption": "Transform your furniture with this natural polish! 🌟",
            "hashtags": "#DIY #HomeDecor #InteriorDesign #Furniture #WoodCare"
        }

def create_template_background(template_name):
    """Create different background styles for each template"""
    bg = Image.new("RGB", (WIDTH, HEIGHT), "#0F0A05")
    draw = ImageDraw.Draw(bg)
    
    if template_name == "Modern Minimal":
        for i in range(0, WIDTH, 150):
            draw.line([(i, 0), (i, HEIGHT)], fill="#1A1208", width=2)
        draw.rectangle([100, 300, 150, 350], fill="#FFD700")
        draw.rectangle([WIDTH-150, 800, WIDTH-100, 850], fill="#FFD700")
        
    elif template_name == "Luxury Gold":
        for i in range(5):
            radius = 300 + i * 100
            draw.ellipse([WIDTH//2-radius, HEIGHT//2-radius, WIDTH//2+radius, HEIGHT//2+radius], 
                        outline="#FFD700", width=2)
        for y in range(0, HEIGHT, 50):
            alpha = int(50 + 50 * math.sin(y/100))
            draw.line([(0, y), (WIDTH, y)], fill=(255, 215, 0, alpha), width=1)
            
    elif template_name == "Geometric Art":
        shapes = [
            ("rectangle", [200, 400, 400, 600]),
            ("circle", [800, 600, 950]),
            ("triangle", [(100, 1200), (300, 1200), (200, 1400)])
        ]
        
        for shape_type, coords in shapes:
            if shape_type == "rectangle":
                draw.rectangle(coords, outline="#FFD700", width=3)
            elif shape_type == "circle":
                draw.ellipse([coords[0]-coords[2], coords[1]-coords[2], coords[0]+coords[2], coords[1]+coords[2]], 
                           outline="#FFD700", width=3)
            elif shape_type == "triangle":
                draw.polygon(coords, outline="#FFD700", width=3)
    
    return bg

def get_text_dimensions(draw, text, font):
    """Safe text dimension calculation"""
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except:
        # Fallback: estimate dimensions
        return len(text) * 30, 60

def create_text_frame(t, tip_text, tip_title, current_step, total_steps, template_name, logo=None):
    """Create animated frame with safe text rendering"""
    bg = create_template_background(template_name)
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
    draw = ImageDraw.Draw(canvas)
    
    # Safe font loading with fallbacks
    try:
        title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 70)  # Reduced from 80
        tip_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 54)    # Reduced from 64
        step_font = ImageFont.truetype("DejaVuSans.ttf", 42)        # Reduced from 48
        cta_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 42)    # Reduced from 50
    except:
        # Fallback to default fonts
        title_font = ImageFont.load_default()
        tip_font = ImageFont.load_default()
        step_font = ImageFont.load_default()
        cta_font = ImageFont.load_default()
    
    # Template-specific styling
    if template_name == "Modern Minimal":
        title_color = "#FFFFFF"
        text_color = "#FFD700"
        bg_alpha = 180
    elif template_name == "Luxury Gold":
        title_color = "#FFD700"
        text_color = "#FFFFFF"
        bg_alpha = 220
    else:  # Geometric Art
        title_color = "#FFD700"
        text_color = "#FFFFFF"
        bg_alpha = 200
    
    # SAFE TITLE RENDERING
    title_y = 100 + int(30 * math.sin(t * 2))
    
    # Ensure title fits within screen width
    title_width, title_height = get_text_dimensions(draw, tip_title, title_font)
    if title_width > WIDTH - 120:  # 60px margins on both sides
        # Scale down font if title is too long
        try:
            title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 60)
            title_width, title_height = get_text_dimensions(draw, tip_title, title_font)
        except:
            pass
    
    title_x = 60
    draw.text((title_x, title_y), tip_title, font=title_font, fill=title_color)
    
    # Step indicator
    step_text = f"Step {current_step} of {total_steps}"
    step_width, step_height = get_text_dimensions(draw, step_text, step_font)
    draw.text((WIDTH - step_width - 60, title_y), step_text, font=step_font, fill="#FFFFFF")
    
    # Progress bar
    progress_width = 800
    progress_height = 12
    progress_x = (WIDTH - progress_width) // 2
    progress_y = title_y + title_height + 40
    
    draw.rounded_rectangle([progress_x, progress_y, progress_x + progress_width, progress_y + progress_height], 
                          radius=6, fill="#333333")
    
    progress_fill = (current_step - 1) / total_steps
    fill_width = int(progress_width * progress_fill)
    if fill_width > 0:
        draw.rounded_rectangle([progress_x, progress_y, progress_x + fill_width, progress_y + progress_height], 
                              radius=6, fill="#FFD700")
    
    # SAFE TIP TEXT RENDERING
    tip_lines = split_text_smart(tip_text, draw, tip_font, max_width=WIDTH - 120)
    
    base_y = 600
    line_height = 90  # Reduced from 100
    
    for i, line in enumerate(tip_lines):
        if i >= 4:  # Max 4 lines to prevent overflow
            break
            
        line_delay = i * 0.3
        line_time = max(0, t - line_delay)
        
        if template_name == "Modern Minimal":
            offset_y = int((1 - line_time) * 50) if line_time < 1.0 else 0
            alpha = int(255 * line_time)
        elif template_name == "Luxury Gold":
            offset_y = 0
            alpha = int(255 * line_time)
        else:
            offset_x = int((1 - line_time) * 100 * math.sin(line_time * 5)) if line_time < 1.0 else 0
            offset_y = 0
            alpha = int(255 * line_time)
        
        y_pos = base_y + (i * line_height) + offset_y
        x_pos = WIDTH // 2
        
        if alpha > 0 and y_pos < HEIGHT - 200:  # Don't render below safe area
            line_width, line_height_px = get_text_dimensions(draw, line, tip_font)
            
            # Ensure line fits within screen
            if line_width > WIDTH - 120:
                # Scale down font for this line
                try:
                    smaller_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 46)
                    line_width, line_height_px = get_text_dimensions(draw, line, smaller_font)
                    current_font = smaller_font
                except:
                    current_font = tip_font
            else:
                current_font = tip_font
            
            bg_padding = 20
            bg_rect = [
                x_pos - line_width//2 - bg_padding,
                y_pos - line_height_px//2 - bg_padding//2,
                x_pos + line_width//2 + bg_padding,
                y_pos + line_height_px//2 + bg_padding//2
            ]
            
            # Ensure background doesn't go off screen
            bg_rect[0] = max(10, bg_rect[0])
            bg_rect[2] = min(WIDTH - 10, bg_rect[2])
            
            if template_name == "Modern Minimal":
                draw.rectangle(bg_rect, fill=(15, 10, 5, bg_alpha))
            else:
                draw.rounded_rectangle(bg_rect, radius=15, fill=(15, 10, 5, bg_alpha))
            
            final_x = x_pos - line_width//2
            draw.text((final_x, y_pos - line_height_px//2), line, font=current_font, fill=text_color)
    
    # CTA - Safe rendering
    cta_alpha = int(128 + 127 * math.sin(t * 4))
    cta_text = "👉 SWIPE FOR MORE TIPS"
    
    cta_width, cta_height = get_text_dimensions(draw, cta_text, cta_font)
    if cta_width > WIDTH - 120:
        cta_text = "👉 MORE TIPS"
        cta_width, cta_height = get_text_dimensions(draw, cta_text, cta_font)
    
    cta_x = (WIDTH - cta_width) // 2
    cta_y = HEIGHT - 120  # Moved up for safety
    
    draw.text((cta_x, cta_y), cta_text, font=cta_font, fill=(255, 255, 255, cta_alpha))
    
    # Logo
    if logo:
        canvas.paste(logo, (WIDTH - 300, 40), logo)
    
    bg.paste(canvas, (0, 0), canvas)
    return np.array(bg)

def split_text_smart(text, draw, font, max_width=900):
    """Smart text splitting that respects actual text width"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        test_width, _ = get_text_dimensions(draw, test_line, font)
        
        if test_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # If still too wide, split long words
    final_lines = []
    for line in lines:
        line_width, _ = get_text_dimensions(draw, line, font)
        if line_width <= max_width:
            final_lines.append(line)
        else:
            # Split into chunks
            words = line.split()
            temp_line = []
            for word in words:
                if get_text_dimensions(draw, word, font)[0] > max_width:
                    # Split long word
                    mid = len(word) // 2
                    temp_line.append(word[:mid])
                    final_lines.append(' '.join(temp_line))
                    temp_line = [word[mid:]]
                else:
                    temp_line.append(word)
                    test_line = ' '.join(temp_line)
                    if get_text_dimensions(draw, test_line, font)[0] > max_width:
                        temp_line.pop()
                        final_lines.append(' '.join(temp_line))
                        temp_line = [word]
            if temp_line:
                final_lines.append(' '.join(temp_line))
    
    return final_lines[:6]  # Max 6 lines total

def generate_multiple_tips(client, category, count=3):
    """Generate multiple tips for batch processing"""
    tips = []
    for i in range(count):
        try:
            tip_content = generate_diy_content(client, category)
            tips.append({
                "title": tip_content["title"],
                "tip": tip_content["tip"],
                "caption": tip_content["caption"],
                "hashtags": tip_content["hashtags"],
                "duration": calculate_duration(tip_content["tip"])
            })
        except Exception as e:
            st.error(f"Failed to generate tip {i+1}: {e}")
            # Add fallback tip
            tips.append({
                "title": f"Tip {i+1}",
                "tip": "Keep your furniture looking new with regular dusting and proper cleaning techniques.",
                "caption": "Simple maintenance goes a long way! ✨",
                "hashtags": "#DIY #HomeCare #Furniture",
                "duration": 8
            })
    return tips

# UI
st.title("💡 SM Interiors DIY Tips Animator")
st.caption("Stable text rendering • Smart duration calculator • Batch processing")

# Initialize Groq client
groq_client = init_groq_client()

# Mode selection
mode = st.radio("Choose Mode", ["Single Tip", "Multiple Tips"], horizontal=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🤖 Content Generator")
    
    # Category selection
    selected_category = st.selectbox(
        "DIY Category",
        list(DIY_CATEGORIES.keys()),
        format_func=lambda x: DIY_CATEGORIES[x]
    )
    
    if mode == "Single Tip":
        if groq_client and st.button("🎲 Generate Random DIY Tip", use_container_width=True):
            with st.spinner("AI is creating your DIY tip..."):
                try:
                    ai_content = generate_diy_content(groq_client, selected_category)
                    st.session_state.ai_title = ai_content["title"]
                    st.session_state.ai_tip = ai_content["tip"]
                    st.session_state.ai_caption = ai_content["caption"]
                    st.session_state.ai_hashtags = ai_content["hashtags"]
                    st.session_state.ai_duration = calculate_duration(ai_content["tip"])
                except Exception as e:
                    st.error(f"AI generation failed: {e}")
        
        # Display content
        if hasattr(st.session_state, 'ai_title'):
            tip_title = st.text_input("Tip Title", st.session_state.ai_title, max_chars=25)
            tip_text = st.text_area("DIY Tip Description", st.session_state.ai_tip, height=100)
        else:
            tip_title = st.text_input("Tip Title", "PRO TIP", max_chars=25)
            tip_text = st.text_area("DIY Tip Description", 
                                   "Mix vinegar and olive oil for natural wood polish.", 
                                   height=100)
        
        if tip_text:
            duration = calculate_duration(tip_text)
            st.info(f"🎬 Auto Duration: **{duration} seconds** ({len(tip_text.split())} words)")
    
    else:  # Multiple Tips mode
        st.subheader("🔄 Batch Generation")
        num_tips = st.slider("Number of Tips", 2, 5, 3)  # Reduced max for stability
        
        if groq_client and st.button("🚀 Generate Multiple Tips", use_container_width=True):
            with st.spinner(f"Generating {num_tips} tips..."):
                try:
                    multiple_tips = generate_multiple_tips(groq_client, selected_category, num_tips)
                    st.session_state.multiple_tips = multiple_tips
                    st.success(f"✅ Generated {len(multiple_tips)} tips!")
                except Exception as e:
                    st.error(f"Batch generation failed: {e}")

with col2:
    st.subheader("🎨 Design Settings")
    
    template = st.selectbox("Template", ["Modern Minimal", "Luxury Gold", "Geometric Art"])
    
    template_descriptions = {
        'Modern Minimal': 'Clean lines, minimalist design',
        'Luxury Gold': 'Elegant gold accents', 
        'Geometric Art': 'Dynamic shapes, artistic layout'
    }
    st.info(f"**{template}** - {template_descriptions[template]}")
    
    if mode == "Single Tip":
        total_steps = st.slider("Total Steps in Series", 1, 5, 3)  # Reduced max
        current_step = st.slider("Current Step", 1, total_steps, 1)
    else:
        total_steps = st.slider("Total Steps (for all)", 1, 5, 3)
        current_step = 1
    
    music_key = st.selectbox("Background Music", list(MUSIC_FILES.keys()), index=0)

# Preview for Single Tip mode
if mode == "Single Tip" and 'tip_text' in locals() and tip_text.strip():
    st.markdown("---")
    st.subheader("📱 Preview")
    
    logo_img = load_logo()
    preview_time = st.slider("Preview Time", 0.0, 2.0, 1.0, 0.1)

    try:
        preview_frame = create_text_frame(
            t=preview_time,
            tip_text=tip_text,
            tip_title=tip_title,
            current_step=current_step,
            total_steps=total_steps,
            template_name=template,
            logo=logo_img
        )
        st.image(Image.fromarray(preview_frame), use_column_width=True)
        st.caption(f"Preview - {calculate_duration(tip_text)} seconds")
    except Exception as e:
        st.error(f"Preview failed: {e}")

# GENERATE VIDEO - Single Tip
if mode == "Single Tip" and st.button("🚀 GENERATE VIDEO", type="primary", use_container_width=True):
    if not tip_text.strip():
        st.error("Please enter a DIY tip!")
    else:
        with st.spinner("Creating video..."):
            try:
                frames = []
                logo_img = load_logo()
                duration = calculate_duration(tip_text)
                
                for i in range(FPS * duration):
                    t = i / FPS
                    frame = create_text_frame(t, tip_text, tip_title, current_step, total_steps, template, logo_img)
                    frames.append(frame)
                
                clip = ImageSequenceClip(frames, fps=FPS)
                
                # Audio handling
                audio_path = os.path.join(AUDIO_DIR, MUSIC_FILES[music_key])
                if os.path.exists(audio_path):
                    try:
                        audio = AudioFileClip(audio_path).subclip(0, min(duration, 15))  # Max 15 seconds
                        clip = clip.set_audio(audio)
                    except Exception as e:
                        st.warning(f"Audio skipped: {e}")
                
                video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
                clip.write_videofile(
                    video_path,
                    fps=FPS,
                    codec="libx264",
                    audio_codec="aac" if os.path.exists(audio_path) else None,
                    threads=2,  # Reduced for stability
                    preset="medium",  # More reliable than "fast"
                    verbose=False,
                    logger=None
                )
                
                st.success("✅ VIDEO READY!")
                st.video(video_path)
                
                with open(video_path, "rb") as f:
                    st.download_button(
                        "⬇️ DOWNLOAD VIDEO", 
                        f, 
                        f"SM_DIY_{template.replace(' ', '_')}.mp4", 
                        "video/mp4", 
                        use_container_width=True
                    )
                
                # Cleanup
                os.unlink(video_path)
                clip.close()
                
            except Exception as e:
                st.error(f"Video generation failed: {e}")
                st.info("💡 Try shortening your text or using a simpler template.")

# Multiple Tips Batch Generation
elif mode == "Multiple Tips" and hasattr(st.session_state, 'multiple_tips'):
    if st.button("🎬 GENERATE ALL VIDEOS", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        logo_img = load_logo()
        
        for i, tip in enumerate(st.session_state.multiple_tips):
            progress_bar.progress((i) / len(st.session_state.multiple_tips))
            
            with st.expander(f"🎥 Generating: {tip['title']}"):
                try:
                    frames = []
                    duration = tip['duration']
                    
                    for frame_num in range(FPS * duration):
                        t = frame_num / FPS
                        frame = create_text_frame(t, tip['tip'], tip['title'], 1, total_steps, template, logo_img)
                        frames.append(frame)
                    
                    clip = ImageSequenceClip(frames, fps=FPS)
                    
                    video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
                    clip.write_videofile(
                        video_path,
                        fps=FPS,
                        codec="libx264",
                        audio_codec=None,  # Skip audio for batch for speed
                        threads=2,
                        preset="medium",
                        verbose=False,
                        logger=None
                    )
                    
                    with open(video_path, "rb") as f:
                        st.download_button(
                            f"⬇️ Download: {tip['title']}",
                            f,
                            f"SM_Tip_{i+1}_{template.replace(' ', '_')}.mp4",
                            "video/mp4"
                        )
                    
                    os.unlink(video_path)
                    clip.close()
                    
                except Exception as e:
                    st.error(f"Failed to generate video {i+1}: {e}")
        
        progress_bar.progress(1.0)
        st.success("✅ Batch generation complete!")

st.markdown("---")
st.caption("✅ STABLE TEXT RENDERING • SMART DURATION • BATCH PROCESSING • MOBILE OPTIMIZED")
