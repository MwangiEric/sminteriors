import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import tempfile, os, numpy as np, io, json, random
from moviepy.editor import ImageSequenceClip, AudioFileClip
import math
import groq

st.set_page_config(page_title="SM Interiors DIY Tips Animator", layout="wide", page_icon="💡")

WIDTH, HEIGHT = 1080, 1920
FPS, DURATION = 30, 8

# LOCAL AUDIO
AUDIO_DIR = "audio"
MUSIC_FILES = {
    "Gold Luxury": "https://ik.imagekit.io/ericmwangi/advertising-music-308403.mp3",
    "Viral Pulse": "viral_pulse.mp3",
    "Elegant Flow": "elegant_flow.mp3",
}

LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png"

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
    """Load logo with error handling - increased size"""
    try:
        import requests
        resp = requests.get(LOGO_URL, timeout=5)
        if resp.status_code == 200:
            logo = Image.open(io.BytesIO(resp.content)).convert("RGBA").resize((280, 140))  # Increased size
            return logo
    except:
        # Fallback: Create text logo if network fails
        fallback = Image.new("RGBA", (280, 140), (0,0,0,0))
        draw = ImageDraw.Draw(fallback)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 80)
        except:
            font = ImageFont.load_default()
        draw.text((10, 30), "SM", font=font, fill="#FFD700")
        return fallback

def generate_diy_content(client, category="furniture"):
    """Generate DIY tips using Groq AI"""
    prompt = f"""
    As an interior design expert for SM Interiors, generate:
    1. A catchy DIY tip title (max 5 words)
    2. A practical DIY tip description (2-3 sentences max)
    3. A engaging social media caption
    4. Relevant hashtags (10-15 hashtags)

    Category: {category}
    
    Format your response as JSON:
    {{
        "title": "creative title here",
        "tip": "detailed tip description here",
        "caption": "engaging social media caption here",
        "hashtags": "#DIY #HomeDecor #InteriorDesign #Furniture #HomeImprovement #DesignTips #BudgetFriendly #HomeHacks #InteriorInspo #SMInteriors"
    }}
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            temperature=0.8,
            max_tokens=500
        )
        
        response = chat_completion.choices[0].message.content
        # Extract JSON from response
        start = response.find('{')
        end = response.rfind('}') + 1
        json_str = response[start:end]
        
        return json.loads(json_str)
    except Exception as e:
        st.error(f"AI generation failed: {e}")
        # Return fallback content
        return {
            "title": "PRO TIP",
            "tip": "Mix vinegar and olive oil for natural wood polish that brings out the grain beautifully.",
            "caption": "Transform your furniture with this natural polish! 🌟 Perfect for maintaining that luxurious SM Interiors look.",
            "hashtags": "#DIY #HomeDecor #InteriorDesign #Furniture #WoodCare #HomeImprovement #DesignTips #BudgetFriendly #HomeHacks #InteriorInspo #SMInteriors"
        }

# DESIGNER TEMPLATES
def create_template_background(template_name):
    """Create different background styles for each template"""
    bg = Image.new("RGB", (WIDTH, HEIGHT), "#0F0A05")
    draw = ImageDraw.Draw(bg)
    
    if template_name == "Modern Minimal":
        # Clean lines and geometric shapes
        for i in range(0, WIDTH, 150):
            draw.line([(i, 0), (i, HEIGHT)], fill="#1A1208", width=2)
        # Gold accents
        draw.rectangle([100, 300, 150, 350], fill="#FFD700")
        draw.rectangle([WIDTH-150, 800, WIDTH-100, 850], fill="#FFD700")
        
    elif template_name == "Luxury Gold":
        # Elegant gold elements
        for i in range(5):
            radius = 300 + i * 100
            draw.ellipse([WIDTH//2-radius, HEIGHT//2-radius, WIDTH//2+radius, HEIGHT//2+radius], 
                        outline="#FFD700", width=2)
        # Gold gradient effect
        for y in range(0, HEIGHT, 50):
            alpha = int(50 + 50 * math.sin(y/100))
            draw.line([(0, y), (WIDTH, y)], fill=(255, 215, 0, alpha), width=1)
            
    elif template_name == "Geometric Art":
        # Dynamic geometric pattern
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

def create_text_frame(t, tip_lines, tip_title, current_step, total_steps, template_name, logo=None):
    """Create animated frame with selected template"""
    bg = create_template_background(template_name)
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
    draw = ImageDraw.Draw(canvas)
    
    try:
        title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 80)
        tip_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 64)
        step_font = ImageFont.truetype("DejaVuSans.ttf", 48)
    except:
        title_font = ImageFont.load_default().font_variant(size=80)
        tip_font = ImageFont.load_default().font_variant(size=64)
        step_font = ImageFont.load_default().font_variant(size=48)
    
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
    
    # Animated title
    title_y = 100 + int(30 * math.sin(t * 2))
    
    # Title with template-specific styling
    draw.text((60, title_y), tip_title, font=title_font, fill=title_color)
    
    # Step indicator
    step_text = f"Step {current_step} of {total_steps}"
    step_width = draw.textlength(step_text, font=step_font)
    draw.text((WIDTH - step_width - 60, title_y), step_text, font=step_font, fill="#FFFFFF")
    
    # Progress bar (template-specific colors)
    progress_width = 800
    progress_height = 12
    progress_x = (WIDTH - progress_width) // 2
    progress_y = title_y + 120
    
    draw.rounded_rectangle([progress_x, progress_y, progress_x + progress_width, progress_y + progress_height], 
                          radius=6, fill="#333333")
    
    progress_fill = (current_step - 1) / total_steps
    fill_width = int(progress_width * progress_fill)
    if fill_width > 0:
        draw.rounded_rectangle([progress_x, progress_y, progress_x + fill_width, progress_y + progress_height], 
                              radius=6, fill="#FFD700")
    
    # Tip lines with template-specific animation
    base_y = 600
    line_height = 100
    
    for i, line in enumerate(tip_lines):
        line_delay = i * 0.3
        line_time = max(0, t - line_delay)
        
        if template_name == "Modern Minimal":
            # Slide from bottom
            offset_y = int((1 - line_time) * 50) if line_time < 1.0 else 0
            alpha = int(255 * line_time)
        elif template_name == "Luxury Gold":
            # Fade in with scale
            scale = 0.8 + 0.2 * line_time if line_time < 1.0 else 1.0
            offset_y = 0
            alpha = int(255 * line_time)
        else:  # Geometric Art
            # Slide from right with bounce
            offset_x = int((1 - line_time) * 100 * math.sin(line_time * 5)) if line_time < 1.0 else 0
            offset_y = 0
            alpha = int(255 * line_time)
        
        y_pos = base_y + (i * line_height) + offset_y
        x_pos = WIDTH // 2
        
        if alpha > 0:
            # Get text dimensions
            bbox = draw.textbbox((0, 0), line, font=tip_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Background with template-specific style
            bg_padding = 25
            bg_rect = [
                x_pos - text_width//2 - bg_padding,
                y_pos - text_height//2 - bg_padding//2,
                x_pos + text_width//2 + bg_padding,
                y_pos + text_height//2 + bg_padding//2
            ]
            
            if template_name == "Modern Minimal":
                draw.rectangle(bg_rect, fill=(15, 10, 5, bg_alpha))
            else:
                draw.rounded_rectangle(bg_rect, radius=20, fill=(15, 10, 5, bg_alpha))
            
            # Draw text
            final_x = x_pos - text_width//2 + (offset_x if template_name == "Geometric Art" else 0)
            draw.text((final_x, y_pos - text_height//2), line, font=tip_font, fill=text_color)
    
    # Animated CTA
    cta_alpha = int(128 + 127 * math.sin(t * 4))
    cta_text = "👉 SWIPE UP FOR MORE DIY TIPS"
    
    try:
        cta_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 50)
    except:
        cta_font = ImageFont.load_default().font_variant(size=50)
    
    cta_width = draw.textlength(cta_text, font=cta_font)
    cta_x = (WIDTH - cta_width) // 2
    cta_y = HEIGHT - 150
    
    draw.text((cta_x, cta_y), cta_text, font=cta_font, fill=(255, 255, 255, cta_alpha))
    
    # Logo (larger size)
    if logo:
        canvas.paste(logo, (WIDTH - 300, 40), logo)  # Adjusted position for larger logo
    
    # Composite onto background
    bg.paste(canvas, (0, 0), canvas)
    
    return np.array(bg)

def split_text_into_lines(text, max_chars_per_line=25):
    """Split long text into multiple lines for better readability"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        if len(test_line) <= max_chars_per_line:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

# UI
st.title("💡 SM Interiors AI DIY Tips Animator")
st.caption("AI-powered DIY tutorial videos • 3 designer templates • Social media ready")

# Initialize Groq client
groq_client = init_groq_client()

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🤖 AI Content Generator")
    
    if groq_client and st.button("🎲 Generate Random DIY Tip", use_container_width=True):
        categories = ["furniture", "decor", "cleaning", "organization", "lighting"]
        category = random.choice(categories)
        
        with st.spinner("AI is creating your DIY tip..."):
            ai_content = generate_diy_content(groq_client, category)
            
            st.session_state.ai_title = ai_content["title"]
            st.session_state.ai_tip = ai_content["tip"]
            st.session_state.ai_caption = ai_content["caption"]
            st.session_state.ai_hashtags = ai_content["hashtags"]
    
    # Display AI generated content if available
    if hasattr(st.session_state, 'ai_title'):
        tip_title = st.text_input("Tip Title", st.session_state.ai_title, max_chars=25)
        tip_text = st.text_area("DIY Tip Description", st.session_state.ai_tip, height=100)
        
        st.subheader("📱 Social Media Content")
        st.text_area("AI Generated Caption", st.session_state.ai_caption, height=80)
        st.text_area("AI Generated Hashtags", st.session_state.ai_hashtags, height=80)
    else:
        tip_title = st.text_input("Tip Title", "PRO TIP", max_chars=25)
        tip_text = st.text_area("DIY Tip Description", 
                               "Mix vinegar and olive oil for natural wood polish that brings out the grain beautifully.",
                               height=100)

with col2:
    st.subheader("🎨 Designer Template")
    
    template = st.selectbox("Choose Template", 
                           ["Modern Minimal", "Luxury Gold", "Geometric Art"],
                           help="Select from 3 professionally designed templates")
    
    total_steps = st.slider("Total Steps in Series", 1, 10, 3)
    current_step = st.slider("Current Step Number", 1, total_steps, 1)
    music_key = st.selectbox("Background Music", list(MUSIC_FILES.keys()), index=0)
    
    # Template preview
template_descriptions = {
    'Modern Minimal': 'Clean lines, minimalist design',
    'Luxury Gold': 'Elegant gold accents, premium feel', 
    'Geometric Art': 'Dynamic shapes, artistic layout'
}
st.info(f"**{template}** - {template_descriptions[template]}")

# Auto-split text preview
if 'tip_text' in locals():
    tip_lines = split_text_into_lines(tip_text)
    st.write("**Text Preview:**")
    for i, line in enumerate(tip_lines):
        st.write(f"Line {i+1}: `{line}`")
    
    if len(tip_lines) > 4:
        st.warning("⚠️ Consider shortening your tip - too many lines may look crowded")

# LIVE PREVIEW
st.markdown("---")
st.subheader("📱 LIVE PREVIEW")

logo_img = load_logo()
preview_time = st.slider("Preview Animation Time", 0.0, 3.0, 1.0, 0.1)

if 'tip_text' in locals() and 'template' in locals():
    preview_frame = create_text_frame(
        t=preview_time,
        tip_lines=tip_lines,
        tip_title=tip_title,
        current_step=current_step,
        total_steps=total_steps,
        template_name=template,
        logo=logo_img
    )

    st.image(Image.fromarray(preview_frame), use_column_width=True)
    st.caption(f"Preview of {template} template")

# GENERATE VIDEO
if st.button("🚀 GENERATE DIY TIP VIDEO", type="primary", use_container_width=True):
    if not tip_text.strip():
        st.error("Please enter a DIY tip!")
    else:
        with st.spinner("Creating your professional DIY tip video... (takes ~30 seconds)"):
            frames = []
            logo_img = load_logo()
            tip_lines = split_text_into_lines(tip_text)
            
            # Generate frames for full duration
            for i in range(FPS * DURATION):
                t = i / FPS
                frame = create_text_frame(t, tip_lines, tip_title, current_step, total_steps, template, logo_img)
                frames.append(frame)
            
            # Create video clip
            clip = ImageSequenceClip(frames, fps=FPS)
            
            # Add audio
            audio_path = os.path.join(AUDIO_DIR, MUSIC_FILES[music_key])
            if os.path.exists(audio_path):
                try:
                    audio = AudioFileClip(audio_path).subclip(0, min(DURATION, AudioFileClip(audio_path).duration))
                    clip = clip.set_audio(audio)
                except Exception as e:
                    st.warning(f"Audio skipped: {e}. Using video only.")
            
            # Export
            video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            clip.write_videofile(
                video_path,
                fps=FPS,
                codec="libx264",
                audio_codec="aac" if os.path.exists(audio_path) else None,
                threads=4,
                preset="fast",
                logger=None
            )
            
            st.success("✅ PROFESSIONAL DIY TIP VIDEO READY!")
            st.video(video_path)
            
            # Download section with AI content
            with open(video_path, "rb") as f:
                st.download_button(
                    "⬇️ DOWNLOAD DIY TIP VIDEO", 
                    f, 
                    f"SM_DIY_{template.replace(' ', '_')}_{current_step}_of_{total_steps}.mp4", 
                    "video/mp4", 
                    use_container_width=True
                )
            
            # Show AI generated social media content
            if hasattr(st.session_state, 'ai_caption'):
                st.subheader("📱 Social Media Ready Content")
                col1, col2 = st.columns(2)
                with col1:
                    st.text_area("💬 Copy this caption:", st.session_state.ai_caption, height=100)
                with col2:
                    st.text_area("🏷️ Copy these hashtags:", st.session_state.ai_hashtags, height=100)
            
            # Cleanup
            os.unlink(video_path)
            clip.close()
            if 'audio' in locals():
                audio.close()

# FEATURES SHOWCASE
st.markdown("---")
st.subheader("✨ What's New")

features = st.columns(3)
with features[0]:
    st.markdown("**🤖 AI Powered**")
    st.caption("Groq AI generates creative DIY tips, captions, and hashtags automatically")
with features[1]:
    st.markdown("**🎨 3 Templates**")
    st.caption("Modern Minimal, Luxury Gold, and Geometric Art designs")
with features[2]:
    st.markdown("**📱 Social Ready**")
    st.caption("Complete social media package with captions and hashtags")

st.caption("✅ AI-POWERED • 3 DESIGNER TEMPLATES • SOCIAL MEDIA OPTIMIZED • BRAND CONSISTENT")
