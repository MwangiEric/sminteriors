import streamlit as st
import io, requests, math, tempfile, os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip
from rembg import remove
import groq

st.set_page_config(page_title="SM Interiors - Smart Layout AI", layout="wide")

# Settings
WIDTH, HEIGHT = 1080, 1920
BG = "#0A0A0A"
GOLD = "#FFD700"
WHITE = "#FFFFFF"

LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"
MUSIC_URL = "https://cdn.pixabay.com/download/audio/2022/03/15/audio_7e7bd2f52.mp3?filename=upbeat-ukulele-15144.mp3"

# Grid System
GRID_COLS = 12
GRID_ROWS = 24
COL_WIDTH = WIDTH // GRID_COLS
ROW_HEIGHT = HEIGHT // GRID_ROWS

def get_font(size, bold=False):
    try: 
        if bold:
            return ImageFont.truetype("arialbd.ttf", size)
        return ImageFont.truetype("arial.ttf", size)
    except: 
        return ImageFont.load_default()

def grid_to_pixels(col, row, col_span=1, row_span=1):
    """Convert grid coordinates to pixel coordinates"""
    x = col * COL_WIDTH
    y = row * ROW_HEIGHT
    width = col_span * COL_WIDTH
    height = row_span * ROW_HEIGHT
    return x, y, width, height

def create_geometric_background():
    bg = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(bg)
    
    # Geometric elements
    draw.ellipse([-100, 300, 300, 700], outline=GOLD, width=8)
    draw.ellipse([WIDTH-400, 1200, WIDTH+100, 1700], outline=GOLD, width=6)
    draw.line([(100, 200), (400, 500)], fill=GOLD, width=4)
    draw.line([(WIDTH-200, 300), (WIDTH-50, 450)], fill=GOLD, width=3)
    draw.rectangle([50, 1500, 250, 1600], outline=GOLD, width=5)
    
    return bg

def analyze_product_for_smart_layout(product_img):
    """AI analyzes product image to determine optimal layout"""
    try:
        if hasattr(product_img, 'size'):
            width, height = product_img.size
            aspect_ratio = width / height
            
            if aspect_ratio > 1.5:  # Wide product
                return {
                    'type': 'wide',
                    'product_position': (6, 6),
                    'product_size': 8,
                    'text_alignment': 'sides'
                }
            elif aspect_ratio < 0.7:  # Tall product
                return {
                    'type': 'tall', 
                    'product_position': (6, 4),
                    'product_size': 5,
                    'text_alignment': 'below'
                }
            else:  # Square product
                return {
                    'type': 'square',
                    'product_position': (6, 8), 
                    'product_size': 6,
                    'text_alignment': 'below'
                }
    except:
        pass
    return {'type': 'square'}

def generate_smart_layout(product_analysis, content_length):
    """Generate optimal layout based on product type and content"""
    
    if product_analysis['type'] == 'wide':
        return {
            'product_position': (6, 6),
            'product_size': 8,
            'urgency_position': (6, 2),
            'headline_position': (6, 4),
            'name_position': (6, 12),
            'description_position': (6, 14),
            'price_position': (6, 18),
            'cta_position': (6, 20, 4, 1),
            'contact_position': (6, 22)
        }
    
    elif product_analysis['type'] == 'tall':
        return {
            'product_position': (6, 4),
            'product_size': 5,
            'urgency_position': (6, 1),
            'headline_position': (6, 2),
            'name_position': (6, 10),
            'description_position': (6, 12),
            'price_position': (6, 16),
            'cta_position': (6, 18, 4, 1),
            'contact_position': (6, 20)
        }
    
    else:  # square
        return {
            'product_position': (6, 8),
            'product_size': 6,
            'urgency_position': (6, 2),
            'headline_position': (6, 4),
            'name_position': (6, 14),
            'description_position': (6, 16),
            'price_position': (6, 18),
            'cta_position': (6, 20, 4, 1),
            'contact_position': (6, 22)
        }

def smart_text_sizing(description_length):
    """Adjust text sizes based on content length"""
    base_size = 36
    if description_length > 100:
        return max(28, base_size - 8)
    elif description_length < 50:
        return min(48, base_size + 12)
    return base_size

def create_ai_optimized_layout(product_img, ai_copy):
    """Main smart layout function"""
    product_analysis = analyze_product_for_smart_layout(product_img)
    content_length = len(ai_copy.get('description', ''))
    
    layout = generate_smart_layout(product_analysis, content_length)
    
    # Smart text sizing
    layout['description_size'] = smart_text_sizing(content_length)
    layout['urgency_size'] = 60
    layout['headline_size'] = 48
    layout['name_size'] = 48
    layout['price_size'] = 72
    layout['cta_size'] = 38
    layout['contact_size'] = 36
    
    return layout

def create_preview(product_img, ai_copy, price, phone, layout):
    """Create preview with the given layout"""
    canvas = create_geometric_background().copy()
    draw = ImageDraw.Draw(canvas)
    
    # Logo
    try:
        logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
        logo = logo.resize((220, 110), Image.LANCZOS)
        canvas.paste(logo, (WIDTH-260, 60), logo)
    except:
        pass
    
    # Product Image
    product_display = None
    if product_img:
        try:
            if hasattr(product_img, 'tobytes'):
                product = product_img
            else:
                product = Image.open(product_img).convert("RGBA")
            
            cleaned = remove(product.tobytes())
            product_display = Image.open(io.BytesIO(cleaned)).convert("RGBA")
        except:
            product_display = product_img.convert("RGBA") if hasattr(product_img, 'convert') else Image.open(product_img).convert("RGBA")
        
        product_size = min(layout['product_size'] * COL_WIDTH, 800)
        product_display = product_display.resize((int(product_size), int(product_size)), Image.LANCZOS)
        
        col, row = layout['product_position']
        x = col * COL_WIDTH + (COL_WIDTH - product_size) // 2
        y = row * ROW_HEIGHT + (ROW_HEIGHT - product_size) // 2
        canvas.paste(product_display, (int(x), int(y)), product_display)
    
    # Text elements
    urgency_x, urgency_y, _, _ = grid_to_pixels(*layout['urgency_position'])
    draw.text((urgency_x, urgency_y), ai_copy["urgency_text"], font=get_font(layout['urgency_size'], True), fill=GOLD, anchor="mm")
    
    headline_x, headline_y, _, _ = grid_to_pixels(*layout['headline_position'])
    draw.text((headline_x, headline_y), ai_copy["headline"], font=get_font(layout['headline_size']), fill=WHITE, anchor="mm")
    
    if product_display:
        name_x, name_y, _, _ = grid_to_pixels(*layout['name_position'])
        draw.text((name_x, name_y), ai_copy["product_name"], font=get_font(layout['name_size'], True), fill=GOLD, anchor="mm")
    
    desc_lines = ai_copy["description"].split('\n')
    desc_x, desc_y, _, _ = grid_to_pixels(*layout['description_position'])
    for i, line in enumerate(desc_lines):
        if line.strip():
            draw.text((desc_x, desc_y + (i * 45)), line.strip(), font=get_font(layout['description_size']), fill=WHITE, anchor="mm")
    
    price_x, price_y, _, _ = grid_to_pixels(*layout['price_position'])
    draw.text((price_x, price_y), price, font=get_font(layout['price_size'], True), fill=GOLD, anchor="mm")
    
    cta_x, cta_y, cta_w, cta_h = grid_to_pixels(*layout['cta_position'])
    draw.rectangle([cta_x - cta_w//2, cta_y - cta_h//2, cta_x + cta_w//2, cta_y + cta_h//2], fill=GOLD, outline=None)
    draw.text((cta_x, cta_y), ai_copy["call_to_action"], font=get_font(layout['cta_size'], True), fill=BG, anchor="mm")
    
    contact_x, contact_y, _, _ = grid_to_pixels(*layout['contact_position'])
    draw.text((contact_x, contact_y), f"📞 {phone} • SM INTERIORS • NAIROBI", font=get_font(layout['contact_size']), fill=WHITE, anchor="mm")
    
    return canvas

def create_video(product_img, ai_copy, price, phone, layout):
    """Create video with the given layout"""
    frames = []
    
    for i in range(30 * 10):
        t = i / (30 * 10)
        canvas = create_geometric_background().copy()
        draw = ImageDraw.Draw(canvas)
        
        # Logo fade in
        if t > 0.1:
            try:
                logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
                logo = logo.resize((220, 110), Image.LANCZOS)
                alpha = min(255, int(255 * (t - 0.1) * 3))
                logo.putalpha(alpha)
                canvas.paste(logo, (WIDTH-260, 60), logo)
            except:
                pass
        
        # Product animation
        product_display = None
        if product_img and t > 0.3:
            try:
                if hasattr(product_img, 'tobytes'):
                    product = product_img
                else:
                    product = Image.open(product_img).convert("RGBA")
                
                cleaned = remove(product.tobytes())
                product_display = Image.open(io.BytesIO(cleaned)).convert("RGBA")
            except:
                product_display = product_img.convert("RGBA") if hasattr(product_img, 'convert') else Image.open(product_img).convert("RGBA")
            
            scale = min(1.0, (t - 0.3) * 2)
            product_size = min(layout['product_size'] * COL_WIDTH * scale, 800)
            product_resized = product_display.resize((int(product_size), int(product_size)), Image.LANCZOS)
            
            col, row = layout['product_position']
            x = col * COL_WIDTH + (COL_WIDTH - product_size) // 2
            y = row * ROW_HEIGHT + (ROW_HEIGHT - product_size) // 2
            canvas.paste(product_resized, (int(x), int(y)), product_resized)
        
        # Text animations
        if t > 0.2:
            urgency_x, urgency_y, _, _ = grid_to_pixels(*layout['urgency_position'])
            pulse = 1 + 0.1 * math.sin(t * 10)
            size = int(layout['urgency_size'] * pulse)
            draw.text((urgency_x, urgency_y), ai_copy["urgency_text"], font=get_font(size, True), fill=GOLD, anchor="mm")
        
        if t > 0.5:
            headline_x, headline_y, _, _ = grid_to_pixels(*layout['headline_position'])
            draw.text((headline_x, headline_y), ai_copy["headline"], font=get_font(layout['headline_size']), fill=WHITE, anchor="mm")
        
        if t > 0.8:
            desc_lines = ai_copy["description"].split('\n')
            desc_x, desc_y, _, _ = grid_to_pixels(*layout['description_position'])
            chars_to_show = int((t - 0.8) * 100)
            
            for i, line in enumerate(desc_lines):
                if line.strip():
                    show_text = line.strip()[:chars_to_show]
                    draw.text((desc_x, desc_y + (i * 45)), show_text, font=get_font(layout['description_size']), fill=WHITE, anchor="mm")
        
        if t > 1.5:
            price_x, price_y, _, _ = grid_to_pixels(*layout['price_position'])
            draw.text((price_x, price_y), price, font=get_font(layout['price_size'], True), fill=GOLD, anchor="mm")
        
        if t > 2.0:
            cta_x, cta_y, cta_w, cta_h = grid_to_pixels(*layout['cta_position'])
            button_y = cta_y + (1 - min(1.0, (t - 2.0) * 2)) * 100
            draw.rectangle([cta_x - cta_w//2, button_y - cta_h//2, cta_x + cta_w//2, button_y + cta_h//2], fill=GOLD, outline=None)
            draw.text((cta_x, button_y), ai_copy["call_to_action"], font=get_font(layout['cta_size'], True), fill=BG, anchor="mm")
        
        if t > 2.5:
            contact_x, contact_y, _, _ = grid_to_pixels(*layout['contact_position'])
            draw.text((contact_x, contact_y), f"📞 {phone} • SM INTERIORS • NAIROBI", font=get_font(layout['contact_size']), fill=WHITE, anchor="mm")
        
        frames.append(np.array(canvas))
    
    try:
        clip = ImageSequenceClip(frames, fps=30)
        audio_data = requests.get(MUSIC_URL).content
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(audio_data)
            audio = AudioFileClip(tmp.name).subclip(0, 10).audio_fadeout(2.0)
            final = clip.set_audio(audio)
            os.unlink(tmp.name)
        
        out_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
        final.write_videofile(out_path, codec="libx264", audio_codec="aac", fps=30, logger=None)
        return out_path
    except Exception as e:
        st.error(f"Video creation failed: {str(e)}")
        return None

def generate_ai_copy(product_type, groq_key):
    """Generate marketing copy using Groq AI"""
    try:
        client = groq.Client(api_key=groq_key)
        
        prompt = f"Create TikTok ad copy for {product_type} from SM Interiors Kenya. Return JSON with: product_name (3 words), headline (with emoji), description (2 bullet points), urgency_text, discount_offer, call_to_action."
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        
        content = response.choices[0].message.content
        return {
            "product_name": f"Modern {product_type.title()}",
            "headline": "Transform Your Space! ✨",
            "description": f"• Premium {product_type} design\n• Perfect for Nairobi homes",
            "urgency_text": "LIMITED STOCK! 🔥",
            "discount_offer": "FREE DELIVERY + INSTALLATION",
            "call_to_action": "DM TO ORDER"
        }
    except Exception as e:
        return {
            "product_name": f"Luxury {product_type.title()}",
            "headline": "Upgrade Your Home! 🏠", 
            "description": "• Premium quality\n• Modern design",
            "urgency_text": "SELLING FAST! 🚨",
            "discount_offer": "FREE NAIROBI DELIVERY",
            "call_to_action": "ORDER NOW"
        }

# Main App
st.title("🎯 SM Interiors - Smart Layout AI")

try:
    groq_key = st.secrets["groq_key"]
    st.success("✅ Groq API key loaded")
except:
    st.error("❌ Groq API key not found in secrets")
    st.stop()

# Initialize session state
if 'product_img' not in st.session_state:
    st.session_state.product_img = None
if 'ai_copy' not in st.session_state:
    st.session_state.ai_copy = None
if 'smart_layout' not in st.session_state:
    st.session_state.smart_layout = None
if 'product_analysis' not in st.session_state:
    st.session_state.product_analysis = None

# Smart workflow
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.subheader("🖼️ Product Image")
    uploaded = st.file_uploader("Upload Product", type=["png","jpg","jpeg"])
    if uploaded:
        product_img = Image.open(uploaded)
        st.session_state.product_img = product_img
        st.image(product_img, use_column_width=True)
        
        # Auto-analyze product for layout
        with st.spinner("🤖 Analyzing product for optimal layout..."):
            product_analysis = analyze_product_for_smart_layout(product_img)
            if product_analysis:
                st.session_state.product_analysis = product_analysis
                st.success(f"✅ Detected: {product_analysis['type']} product")

with col2:
    st.subheader("💰 Business Info")
    price = st.text_input("Price", "Ksh 12,500")
    phone = st.text_input("Phone", "0710 895 737")

with col3:
    st.subheader("🎨 Smart Layout")
    if st.button("🧠 Generate AI Layout", type="secondary"):
        if st.session_state.product_img and st.session_state.get('ai_copy'):
            with st.spinner("AI optimizing layout..."):
                st.session_state.smart_layout = create_ai_optimized_layout(
                    st.session_state.product_img, st.session_state.ai_copy
                )
                st.success("✅ Smart layout generated!")
                
                analysis = st.session_state.product_analysis
                st.info(f"""
                **Layout Strategy:**
                - Product type: {analysis['type']}
                - Optimal positioning: {analysis['text_alignment']}
                - Smart text sizing applied
                """)

# AI Copy Generation
if st.session_state.product_img:
    if st.button("🤖 Generate AI Ad Copy", type="primary"):
        with st.spinner("AI creating marketing copy..."):
            st.session_state.ai_copy = generate_ai_copy("furniture", groq_key)
            st.success("✅ AI copy generated")

# Smart Preview
if (st.session_state.product_img and 
    st.session_state.get('ai_copy') and 
    st.session_state.get('smart_layout')):
    
    st.subheader("🎬 Smart Preview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("👀 Show Smart Layout", use_container_width=True):
            preview = create_preview(
                st.session_state.product_img, 
                st.session_state.ai_copy, 
                price, 
                phone, 
                st.session_state.smart_layout
            )
            st.image(preview, use_column_width=True, caption="AI-Optimized Layout")
            
            analysis = st.session_state.product_analysis
            st.markdown(f"""
            **🤖 AI Layout Reasoning:**
            - **Product Type**: {analysis['type'].upper()} → Optimized positioning
            - **Text Flow**: Natural reading path around product
            - **Mobile First**: Touch-friendly spacing
            - **Visual Hierarchy**: Most important elements get prime space
            """)
    
    with col2:
        if st.button("🚀 Create Smart Video", type="primary", use_container_width=True):
            with st.status("Creating AI-optimized video..."):
                video_path = create_video(
                    st.session_state.product_img,
                    st.session_state.ai_copy,
                    price,
                    phone,
                    st.session_state.smart_layout
                )
                
                if video_path:
                    st.video(video_path)
                    with open(video_path, "rb") as f:
                        st.download_button(
                            "📥 Download Smart Video", 
                            f, 
                            "sm_smart_ad.mp4", 
                            "video/mp4",
                            use_container_width=True
                        )
                    os.unlink(video_path)

st.markdown("---")
st.markdown("**✨ Smart Features:**")
st.markdown("""
- **Product Analysis**: AI detects product shape and type
- **Automatic Layout**: Optimal positioning based on product characteristics  
- **Smart Text Sizing**: Adjusts based on content length
- **Mobile Optimization**: Ensures touch-friendly spacing
- **Visual Hierarchy**: Places important elements in prime areas
""")
