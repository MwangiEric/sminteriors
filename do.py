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
# Using a more reliable audio source
MUSIC_URL = "https://assets.mixkit.co/music/preview/mixkit-tech-house-vibes-130.mp3"

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
    
    # Subtle geometric elements that don't interfere with text
    draw.ellipse([-100, 300, 300, 700], outline=GOLD, width=4)
    draw.ellipse([WIDTH-400, 1200, WIDTH+100, 1700], outline=GOLD, width=3)
    draw.line([(100, 200), (400, 500)], fill=GOLD, width=2)
    draw.line([(WIDTH-200, 300), (WIDTH-50, 450)], fill=GOLD, width=2)
    
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

def calculate_text_visibility(text_length, available_space):
    """Calculate optimal text size and spacing for visibility"""
    # Base sizes for optimal mobile readability
    base_sizes = {
        'urgency': 70,
        'headline': 52,
        'product_name': 48,
        'description': 36,
        'price': 80,
        'cta': 42,
        'contact': 32
    }
    
    # Adjust for text length
    if text_length > 100:  # Long text
        adjustments = {'description': -8, 'headline': -4}
    elif text_length < 30:  # Short text  
        adjustments = {'description': 4, 'headline': 4}
    else:
        adjustments = {}
    
    # Apply adjustments
    for key in adjustments:
        if key in base_sizes:
            base_sizes[key] += adjustments[key]
    
    return base_sizes

def generate_smart_layout(product_analysis, text_analysis):
    """Generate optimal layout based on product type and text analysis"""
    
    if product_analysis['type'] == 'wide':
        return {
            'product_position': (6, 6),
            'product_size': 7,  # Slightly smaller for wide products
            'urgency_position': (6, 2),
            'headline_position': (6, 4),
            'name_position': (6, 12),
            'description_position': (6, 14),
            'price_position': (6, 18),
            'cta_position': (6, 20, 4, 1),
            'contact_position': (6, 22),
            'text_sizes': text_analysis
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
            'contact_position': (6, 20),
            'text_sizes': text_analysis
        }
    
    else:  # square
        return {
            'product_position': (6, 7),  # Adjusted for better text space
            'product_size': 6,
            'urgency_position': (6, 2),
            'headline_position': (6, 4),
            'name_position': (6, 14),
            'description_position': (6, 16),
            'price_position': (6, 19),  # More space above price
            'cta_position': (6, 21, 4, 1),
            'contact_position': (6, 23),
            'text_sizes': text_analysis
        }

def create_ai_optimized_layout(product_img, ai_copy):
    """Main smart layout function"""
    product_analysis = analyze_product_for_smart_layout(product_img)
    
    # Calculate text visibility requirements
    description_length = len(ai_copy.get('description', ''))
    text_analysis = calculate_text_visibility(description_length, available_space=600)
    
    layout = generate_smart_layout(product_analysis, text_analysis)
    
    return layout

def add_text_background(draw, x, y, text, font, padding=10, bg_color=(0, 0, 0, 180)):
    """Add semi-transparent background behind text for better visibility"""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Draw rounded rectangle background
    draw.rectangle(
        [x - text_width//2 - padding, y - text_height//2 - padding,
         x + text_width//2 + padding, y + text_height//2 + padding],
        fill=bg_color
    )
    return text_width, text_height

def create_preview(product_img, ai_copy, price, phone, layout):
    """Create preview with the given layout"""
    canvas = create_geometric_background().copy()
    draw = ImageDraw.Draw(canvas, 'RGBA')  # RGBA for transparency
    
    # Logo
    try:
        logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
        logo = logo.resize((200, 100), Image.LANCZOS)  # Slightly smaller
        canvas.paste(logo, (WIDTH-240, 40), logo)
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
        
        product_size = min(layout['product_size'] * COL_WIDTH, 700)  # Smaller for text space
        product_display = product_display.resize((int(product_size), int(product_size)), Image.LANCZOS)
        
        col, row = layout['product_position']
        x = col * COL_WIDTH + (COL_WIDTH - product_size) // 2
        y = row * ROW_HEIGHT + (ROW_HEIGHT - product_size) // 2
        canvas.paste(product_display, (int(x), int(y)), product_display)
    
    text_sizes = layout['text_sizes']
    
    # Urgency Text - with background for visibility
    urgency_x, urgency_y, _, _ = grid_to_pixels(*layout['urgency_position'])
    urgency_font = get_font(text_sizes['urgency'], True)
    add_text_background(draw, urgency_x, urgency_y, ai_copy["urgency_text"], urgency_font, padding=15)
    draw.text((urgency_x, urgency_y), ai_copy["urgency_text"], font=urgency_font, fill=GOLD, anchor="mm")
    
    # Headline - with background
    headline_x, headline_y, _, _ = grid_to_pixels(*layout['headline_position'])
    headline_font = get_font(text_sizes['headline'])
    add_text_background(draw, headline_x, headline_y, ai_copy["headline"], headline_font, padding=12)
    draw.text((headline_x, headline_y), ai_copy["headline"], font=headline_font, fill=WHITE, anchor="mm")
    
    # Product Name
    if product_display:
        name_x, name_y, _, _ = grid_to_pixels(*layout['name_position'])
        name_font = get_font(text_sizes['product_name'], True)
        add_text_background(draw, name_x, name_y, ai_copy["product_name"], name_font, padding=10)
        draw.text((name_x, name_y), ai_copy["product_name"], font=name_font, fill=GOLD, anchor="mm")
    
    # Description - with proper line spacing and backgrounds
    desc_lines = ai_copy["description"].split('\n')
    desc_x, desc_y, _, _ = grid_to_pixels(*layout['description_position'])
    desc_font = get_font(text_sizes['description'])
    
    for i, line in enumerate(desc_lines):
        if line.strip():
            line_y = desc_y + (i * 55)  # Increased line spacing
            add_text_background(draw, desc_x, line_y, line.strip(), desc_font, padding=8)
            draw.text((desc_x, line_y), line.strip(), font=desc_font, fill=WHITE, anchor="mm")
    
    # Price - prominent with background
    price_x, price_y, _, _ = grid_to_pixels(*layout['price_position'])
    price_font = get_font(text_sizes['price'], True)
    add_text_background(draw, price_x, price_y, price, price_font, padding=15, bg_color=(0, 0, 0, 200))
    draw.text((price_x, price_y), price, font=price_font, fill=GOLD, anchor="mm")
    
    # CTA Button - more prominent
    cta_x, cta_y, cta_w, cta_h = grid_to_pixels(*layout['cta_position'])
    # Larger button
    button_width = cta_w + 100
    button_height = cta_h + 20
    draw.rounded_rectangle(
        [cta_x - button_width//2, cta_y - button_height//2, 
         cta_x + button_width//2, cta_y + button_height//2],
        radius=15, fill=GOLD
    )
    cta_font = get_font(text_sizes['cta'], True)
    draw.text((cta_x, cta_y), ai_copy["call_to_action"], font=cta_font, fill=BG, anchor="mm")
    
    # Contact Info - with background
    contact_text = f"📞 {phone} • SM INTERIORS • NAIROBI"
    contact_x, contact_y, _, _ = grid_to_pixels(*layout['contact_position'])
    contact_font = get_font(text_sizes['contact'])
    add_text_background(draw, contact_x, contact_y, contact_text, contact_font, padding=8)
    draw.text((contact_x, contact_y), contact_text, font=contact_font, fill=WHITE, anchor="mm")
    
    return canvas

def create_video(product_img, ai_copy, price, phone, layout):
    """Create video with the given layout"""
    frames = []
    
    for i in range(30 * 8):  # Reduced to 8 seconds for faster processing
        t = i / (30 * 8)
        canvas = create_geometric_background().copy()
        draw = ImageDraw.Draw(canvas, 'RGBA')
        
        # Logo fade in
        if t > 0.1:
            try:
                logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
                logo = logo.resize((200, 100), Image.LANCZOS)
                alpha = min(255, int(255 * (t - 0.1) * 3))
                logo.putalpha(alpha)
                canvas.paste(logo, (WIDTH-240, 40), logo)
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
            product_size = min(layout['product_size'] * COL_WIDTH * scale, 700)
            product_resized = product_display.resize((int(product_size), int(product_size)), Image.LANCZOS)
            
            col, row = layout['product_position']
            x = col * COL_WIDTH + (COL_WIDTH - product_size) // 2
            y = row * ROW_HEIGHT + (ROW_HEIGHT - product_size) // 2
            canvas.paste(product_resized, (int(x), int(y)), product_resized)
        
        text_sizes = layout['text_sizes']
        
        # Text animations with backgrounds
        if t > 0.2:
            urgency_x, urgency_y, _, _ = grid_to_pixels(*layout['urgency_position'])
            urgency_font = get_font(text_sizes['urgency'], True)
            add_text_background(draw, urgency_x, urgency_y, ai_copy["urgency_text"], urgency_font, padding=15)
            draw.text((urgency_x, urgency_y), ai_copy["urgency_text"], font=urgency_font, fill=GOLD, anchor="mm")
        
        if t > 0.5:
            headline_x, headline_y, _, _ = grid_to_pixels(*layout['headline_position'])
            headline_font = get_font(text_sizes['headline'])
            add_text_background(draw, headline_x, headline_y, ai_copy["headline"], headline_font, padding=12)
            draw.text((headline_x, headline_y), ai_copy["headline"], font=headline_font, fill=WHITE, anchor="mm")
        
        if t > 0.8:
            desc_lines = ai_copy["description"].split('\n')
            desc_x, desc_y, _, _ = grid_to_pixels(*layout['description_position'])
            desc_font = get_font(text_sizes['description'])
            chars_to_show = int((t - 0.8) * 80)  # Slower typewriter effect
            
            for i, line in enumerate(desc_lines):
                if line.strip():
                    show_text = line.strip()[:chars_to_show]
                    line_y = desc_y + (i * 55)
                    add_text_background(draw, desc_x, line_y, show_text, desc_font, padding=8)
                    draw.text((desc_x, line_y), show_text, font=desc_font, fill=WHITE, anchor="mm")
        
        if t > 1.5:
            price_x, price_y, _, _ = grid_to_pixels(*layout['price_position'])
            price_font = get_font(text_sizes['price'], True)
            add_text_background(draw, price_x, price_y, price, price_font, padding=15, bg_color=(0, 0, 0, 200))
            draw.text((price_x, price_y), price, font=price_font, fill=GOLD, anchor="mm")
        
        if t > 2.0:
            cta_x, cta_y, cta_w, cta_h = grid_to_pixels(*layout['cta_position'])
            button_width = cta_w + 100
            button_height = cta_h + 20
            draw.rounded_rectangle(
                [cta_x - button_width//2, cta_y - button_height//2, 
                 cta_x + button_width//2, cta_y + button_height//2],
                radius=15, fill=GOLD
            )
            cta_font = get_font(text_sizes['cta'], True)
            draw.text((cta_x, cta_y), ai_copy["call_to_action"], font=cta_font, fill=BG, anchor="mm")
        
        if t > 2.5:
            contact_text = f"📞 {phone} • SM INTERIORS • NAIROBI"
            contact_x, contact_y, _, _ = grid_to_pixels(*layout['contact_position'])
            contact_font = get_font(text_sizes['contact'])
            add_text_background(draw, contact_x, contact_y, contact_text, contact_font, padding=8)
            draw.text((contact_x, contact_y), contact_text, font=contact_font, fill=WHITE, anchor="mm")
        
        frames.append(np.array(canvas))
    
    try:
        clip = ImageSequenceClip(frames, fps=30)
        
        # Better audio handling with error fallback
        try:
            audio_data = requests.get(MUSIC_URL, timeout=10).content
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name
            
            # Verify file is not empty
            if os.path.getsize(tmp_path) > 0:
                audio = AudioFileClip(tmp_path)
                audio = audio.subclip(0, 8).audio_fadeout(1.0)
                final = clip.set_audio(audio)
                os.unlink(tmp_path)
            else:
                final = clip  # Use video without audio
                st.warning("Audio file was empty, creating video without audio")
        except Exception as audio_error:
            st.warning(f"Audio loading failed: {audio_error}. Creating video without audio.")
            final = clip
        
        out_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
        final.write_videofile(out_path, codec="libx264", audio_codec="aac" if final.audio else None, fps=30, logger=None)
        
        # Close the clip to free resources
        if final.audio:
            final.audio.close()
        final.close()
        clip.close()
        
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
                - Text visibility: Optimized for mobile
                - Smart spacing: No overlap guaranteed
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
            - **Text Visibility**: Backgrounds for readability
            - **Mobile First**: Touch-friendly spacing
            - **No Overlap**: Guaranteed clean layout
            """)
    
    with col2:
        if st.button("🚀 Create Smart Video", type="primary", use_container_width=True):
            with st.status("Creating AI-optimized video...") as status:
                status.write("📦 Processing product image...")
                status.write("🎨 Applying smart layout...")
                status.write("👁️ Ensuring text visibility...")
                status.write("🎵 Adding background music...")
                status.write("📹 Exporting video...")
                
                video_path = create_video(
                    st.session_state.product_img,
                    st.session_state.ai_copy,
                    price,
                    phone,
                    st.session_state.smart_layout
                )
                
                if video_path:
                    status.update(label="✅ Video created successfully!", state="complete")
                    st.video(video_path)
                    
                    with open(video_path, "rb") as f:
                        st.download_button(
                            "📥 Download Smart Video", 
                            f, 
                            "sm_interiors_tiktok.mp4", 
                            "video/mp4",
                            use_container_width=True,
                            type="primary"
                        )
                    # Clean up
                    try:
                        os.unlink(video_path)
                    except:
                        pass
                else:
                    st.error("❌ Video creation failed")

st.markdown("---")
st.markdown("**✨ Smart Text Visibility Features:**")
st.markdown("""
- **Background Overlays**: Semi-transparent backgrounds behind text
- **Optimal Sizing**: Text sizes calculated for mobile readability  
- **Smart Spacing**: Increased line height and element spacing
- **No Overlap**: Guaranteed separation between elements
- **Contrast Optimization**: Gold text on dark with background
- **Touch-Friendly**: Larger buttons and touch targets
""")
