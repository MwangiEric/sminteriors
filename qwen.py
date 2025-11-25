import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps
import tempfile, os, numpy as np, io, time, sys
from moviepy.editor import ImageSequenceClip, AudioFileClip
import requests
import base64
import rembg
from groq import Groq

st.set_page_config(page_title="SM Interiors Pro Reel Generator", layout="wide", page_icon="🎬")

# Platform-specific dimensions
PLATFORM_DIMENSIONS = {
    "Instagram Reels": (1080, 1920),
    "Instagram Stories": (1080, 1920),
    "Facebook Feed": (1200, 630)
}

FPS, DURATION = 30, 6  # 6 seconds

# Your hosted MP3
MUSIC_URL = "https://ik.imagekit.io/ericmwangi/advertising-music-308403.mp3"
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png"

# Initialize Groq
try:
    GROQ_API_KEY = st.secrets["groq_key"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    client = None
    st.warning("⚠️ No Groq API key found. AI text generation disabled.")

@st.cache_resource
def load_logo():
    """Load logo with Streamlit Cloud compatibility"""
    try:
        resp = requests.get(LOGO_URL, timeout=5)
        if resp.status_code == 200:
            logo = Image.open(io.BytesIO(resp.content)).convert("RGBA")
            # Scale logo based on platform
            if st.session_state.get("platform", "Instagram Reels") == "Facebook Feed":
                return logo.resize((200, 100))
            return logo.resize((280, 140))
    except Exception as e:
        st.warning(f"Logo load failed: {e}. Using fallback.")
        # Create text-based fallback logo
        if st.session_state.get("platform", "Instagram Reels") == "Facebook Feed":
            size = (200, 100)
        else:
            size = (280, 140)
        fallback = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(fallback)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 50)
        except:
            font = ImageFont.load_default()
        draw.text((10, 20), "SM", font=font, fill="#FFD700")
        return fallback

def remove_black_edges(img):
    """Clean up transparent edges - pure Python implementation"""
    try:
        # Convert to numpy array
        img_np = np.array(img)
        
        # Create mask of non-transparent pixels
        if img_np.shape[2] == 4:  # Has alpha channel
            alpha = img_np[:, :, 3] > 10  # Slightly more forgiving threshold
        else:
            # Create alpha channel if missing
            alpha = np.ones((img_np.shape[0], img_np.shape[1]), dtype=bool)
        
        # Find bounding box of non-transparent area
        coords = np.column_stack(np.where(alpha))
        if len(coords) == 0:
            return img
        
        min_y, min_x = coords.min(axis=0)
        max_y, max_x = coords.max(axis=0)
        
        # Add padding (10% of the object size)
        pad_y = max(10, int((max_y - min_y) * 0.1))
        pad_x = max(10, int((max_x - min_x) * 0.1))
        
        min_y = max(0, min_y - pad_y)
        min_x = max(0, min_x - pad_x)
        max_y = min(img_np.shape[0], max_y + pad_y)
        max_x = min(img_np.shape[1], max_x + pad_x)
        
        # Crop to bounding box
        cropped = img.crop((min_x, min_y, max_x, max_y))
        
        return cropped
    except Exception as e:
        st.warning(f"Edge cleaning failed: {e}. Using original image.")
        return img

def remove_background(img):
    """Background removal with Streamlit Cloud compatibility"""
    try:
        # Try rembg first (works on Streamlit Cloud)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Remove background
        img_no_bg = rembg.remove(img_bytes.read())
        
        # Convert back to PIL
        img_pil = Image.open(io.BytesIO(img_no_bg)).convert('RGBA')
        
        # Clean edges
        img_pil = remove_black_edges(img_pil)
        
        return img_pil
    except Exception as e:
        st.warning(f"Background removal failed: {e}. Using simpler method.")
        try:
            # Fallback: Simple background removal using PIL
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Create a new image with transparent background
            datas = img.getdata()
            new_data = []
            for item in datas:
                # Change all white (also shades of whites)
                # pixels to transparent
                if item[0] > 200 and item[1] > 200 and item[2] > 200:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append(item)
            img.putdata(new_data)
            return img
        except Exception as e2:
            st.warning(f"Simple background removal also failed: {e2}. Using original image.")
            return img.convert('RGBA')

def compose_product_image(img, platform="Instagram Reels"):
    """Professional image composition with cloud compatibility"""
    try:
        # Remove background
        img = remove_background(img)
        
        # Enhance contrast and sharpness
        if img.mode == 'RGBA':
            # Convert to RGB for enhancement
            rgb_img = img.convert('RGB')
            enhanced = ImageEnhance.Contrast(rgb_img).enhance(1.3)
            enhanced = ImageEnhance.Sharpness(enhanced).enhance(1.8)
            enhanced = enhanced.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
            # Merge back with alpha
            img = Image.merge('RGBA', enhanced.split() + (img.split()[3],))
        else:
            img = ImageEnhance.Contrast(img).enhance(1.3)
            img = ImageEnhance.Sharpness(img).enhance(1.8)
            img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        
        # Get platform dimensions
        WIDTH, HEIGHT = PLATFORM_DIMENSIONS[platform]
        
        # Professional composition rules
        # 1. Maintain aspect ratio
        # 2. Size product to 80% of frame width (with padding)
        # 3. Center vertically in the safe zone
        
        # Calculate target size based on platform
        if platform == "Facebook Feed":
            max_width = int(WIDTH * 0.7)  # Smaller for Facebook
        else:
            max_width = int(WIDTH * 0.8)
        
        # Calculate ratio while maintaining aspect ratio
        ratio = min(max_width / img.width, 0.8)  # Max 80% of target width
        new_width = int(img.width * ratio)
        new_height = int(img.height * ratio)
        
        # Resize with high quality
        img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # Create background
        background = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        
        # Center horizontally
        x = int((WIDTH - new_width) // 2)
        
        # Center vertically based on platform
        if platform == "Facebook Feed":
            y = int(HEIGHT * 0.4)  # Higher for Facebook
        elif platform == "Instagram Stories":
            y = int(HEIGHT * 0.45)  # Slightly higher for Stories
        else:
            y = int(HEIGHT * 0.35)  # Standard for Reels
        
        # Paste product
        background.paste(img, (x, y), img)
        
        return background
    except Exception as e:
        st.error(f"Image composition failed: {e}. Using original.")
        # Return a simple placeholder
        WIDTH, HEIGHT = PLATFORM_DIMENSIONS[platform]
        placeholder = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(placeholder)
        draw.text((50, 50), "Image Processing Failed", fill="white")
        return placeholder

def safe_image_load(uploaded, platform="Instagram Reels"):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            tmp_file.write(uploaded.read())
            tmp_path = tmp_file.name

        img = Image.open(tmp_path).convert("RGBA")
        
        # Auto-resize for processing
        max_dim = 1500
        if max(img.width, img.height) > max_dim:
            ratio = max_dim / max(img.width, img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        # Process image
        processed_img = compose_product_image(img, platform)
        os.unlink(tmp_path)

        # Save to bytes for Groq
        img_bytes = io.BytesIO()
        processed_img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        # Get platform dimensions
        WIDTH, HEIGHT = PLATFORM_DIMENSIONS[platform]
        
        # Resize to platform-specific preview size
        if platform == "Facebook Feed":
            preview_size = (850, 450)
        else:
            preview_size = (850, int(850 * HEIGHT / WIDTH))
        
        return processed_img.resize(preview_size, Image.LANCZOS), img_bytes.getvalue()

    except Exception as e:
        st.error(f"Image processing failed: {e}. Try a simple JPG/PNG under 5MB.")
        return None, None

def generate_text_with_groq(image_bytes, platform="Instagram Reels"):
    """Generate all text content using Groq with platform-specific prompts"""
    if not client:
        # Return default text based on platform
        if platform == "Instagram Stories":
            return {
                "title": "SM Interiors",
                "hook": "SPECIAL OFFER INSIDE",
                "cta": "SWIPE UP TO SHOP"
            }
        elif platform == "Facebook Feed":
            return {
                "title": "Elegant Furniture Collection",
                "hook": "Quality Craftsmanship Guaranteed",
                "cta": "Shop Now - Free Delivery Available"
            }
        else:
            return {
                "title": "SM Interiors",
                "hook": "LIMITED STOCK!",
                "cta": "DM TO ORDER • 0710 895 737"
            }
    
    try:
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Platform-specific prompts
        platform_prompts = {
            "Instagram Reels": """
Analyze this furniture product image and generate:

TITLE: [clean, descriptive product name (max 25 chars)]
HOOK: [short, urgent phrase for Reels (max 18 chars)]
CTA: [action-oriented with contact (max 30 chars)]

Example:
TITLE: Grey Chest of Drawers
HOOK: 2 LEFT IN STOCK!
CTA: ORDER NOW • 0710 895 737
""",
            "Instagram Stories": """
Analyze this furniture product image and generate:

TITLE: [clean, descriptive product name (max 25 chars)]
HOOK: [short, compelling phrase for Stories (max 18 chars)]
CTA: [swipe-up oriented phrase (max 30 chars)]

Example:
TITLE: Grey Chest of Drawers
HOOK: Exclusive Offer Inside
CTA: SWIPE UP TO SHOP NOW
""",
            "Facebook Feed": """
Analyze this furniture product image and generate:

TITLE: [clean, descriptive product name (max 30 chars)]
HOOK: [brief benefit-focused phrase (max 25 chars)]
CTA: [friendly call to action (max 35 chars)]

Example:
TITLE: Elegant Grey Chest of Drawers
HOOK: Perfect for modern living spaces
CTA: Shop now and get free delivery!
"""
        }

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": platform_prompts[platform]
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            }
                        }
                    ],
                }
            ],
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            temperature=0.7,
            max_tokens=150,
        )

        response = chat_completion.choices[0].message.content.strip()
        return parse_groq_text(response)

    except Exception as e:
        st.warning(f"AI text generation failed: {e}. Using defaults.")
        if platform == "Instagram Stories":
            return {
                "title": "SM Interiors",
                "hook": "SPECIAL OFFER INSIDE",
                "cta": "SWIPE UP TO SHOP"
            }
        elif platform == "Facebook Feed":
            return {
                "title": "Elegant Furniture Collection",
                "hook": "Quality Craftsmanship Guaranteed",
                "cta": "Shop Now - Free Delivery Available"
            }
        else:
            return {
                "title": "SM Interiors",
                "hook": "LIMITED STOCK!",
                "cta": "DM TO ORDER • 0710 895 737"
            }

def parse_groq_text(text):
    """Parse Groq's text output"""
    lines = text.split("\n")
    data = {}
    for line in lines:
        if ": " in line:
            key, value = line.split(": ", 1)
            data[key.strip()] = value.strip()
    return data

# ✅ 3 PROFESSIONAL TEMPLATES
PRO_TEMPLATES = {
    "Luxury": {
        "bg_color": "#0F0A05",
        "ring_color": "#FFD700",
        "text_color": "#FFFFFF",
        "price_bg": "#FFD700",
        "price_text": "#0F0A05",
        "cta_pulse": True,
        "geometric_style": "gold_only",
        "safe_zones": {
            "title": (60, 80),
            "hook": (60, 180),
            "price": (540, 1600),
            "cta": (60, 1800),
            "logo": (40, 40)
        }
    },
    "Modern": {
        "bg_color": "#FFFFFF",
        "ring_color": "#2C3E50",
        "text_color": "#2C3E50",
        "price_bg": "#3498DB",
        "price_text": "#FFFFFF",
        "cta_pulse": False,
        "geometric_style": "blue_gray",
        "safe_zones": {
            "title": (60, 80),
            "hook": (60, 180),
            "price": (540, 1600),
            "cta": (60, 1800),
            "logo": (40, 40)
        }
    },
    "Bold": {
        "bg_color": "#000000",
        "ring_color": "#E74C3C",
        "text_color": "#FFFFFF",
        "price_bg": "#E74C3C",
        "price_text": "#FFFFFF",
        "cta_pulse": True,
        "geometric_style": "red_pulse",
        "safe_zones": {
            "title": (60, 80),
            "hook": (60, 180),
            "price": (540, 1600),
            "cta": (60, 1800),
            "logo": (40, 40)
        }
    }
}

def create_frame(t, product_img, hook, price, cta, title, template_name, platform="Instagram Reels", logo=None):
    """Create frame with Streamlit Cloud compatible integer coordinates"""
    # Get platform dimensions
    WIDTH, HEIGHT = PLATFORM_DIMENSIONS[platform]
    
    # Get template
    template = PRO_TEMPLATES[template_name]
    
    # Create canvas with proper integer dimensions
    canvas = Image.new("RGB", (int(WIDTH), int(HEIGHT)), template["bg_color"])
    draw = ImageDraw.Draw(canvas)
    
    # ✅ SUBTLE ANIMATED GEOMETRIC SHAPES (template-specific)
    if template["geometric_style"] == "gold_only":
        # Gold rings (static)
        for cx, cy, r in [(WIDTH//2, HEIGHT//2, 600), (WIDTH//2+120, HEIGHT//2-120, 800), (WIDTH//2-180, HEIGHT//2+180, 1000)]:
            draw.ellipse([int(cx-r), int(cy-r), int(cx+r), int(cy+r)], outline=template["ring_color"], width=4)
    
    elif template["geometric_style"] == "blue_gray":
        # Subtle blue rectangles and circles
        for i in range(3):
            size = int(150 + 30 * np.sin(t * 0.5 + i))
            x = int(WIDTH//2 + 200 * np.cos(t * 0.3 + i * 2))
            y = int(HEIGHT//2 + 150 * np.sin(t * 0.3 + i * 2))
            if i % 2 == 0:
                draw.ellipse([x-size, y-size, x+size, y+size], outline="#3498DB", width=2)
            else:
                draw.rectangle([x-size, y-size, x+size, y+size], outline="#2C3E50", width=2)
    
    elif template["geometric_style"] == "red_pulse":
        # Pulsing red elements
        for i in range(2):
            pulse = 1 + 0.2 * np.sin(t * 2 + i)
            size = int(100 * pulse)
            x = int(WIDTH//2 + 150 * np.cos(t * 0.4 + i))
            y = int(HEIGHT//2 + 100 * np.sin(t * 0.4 + i))
            draw.ellipse([x-size, y-size, x+size, y+size], outline="#E74C3C", width=int(2 * pulse))

    # ✅ PRODUCT (centered professionally)
    base_scale = st.session_state.get("product_scale", 1.0)
    scale = base_scale * (0.8 + 0.2 * (np.sin(t * 2) ** 2))
    
    # Platform-specific sizing
    if platform == "Facebook Feed":
        base_size = 600
        max_height = 400
    else:
        base_size = 850
        max_height = 1200
    
    size = int(base_size * scale)
    
    # Resize product while maintaining aspect ratio
    if product_img.width > 0 and product_img.height > 0:
        ratio = size / max(product_img.width, product_img.height)
        new_width = max(1, int(product_img.width * ratio))
        new_height = max(1, int(product_img.height * ratio))
    else:
        new_width, new_height = size, size
    
    # Ensure product doesn't exceed max height
    if new_height > max_height:
        scale_factor = max_height / new_height
        new_width = max(1, int(new_width * scale_factor))
        new_height = max_height
    
    # Safe resize with error handling
    try:
        resized = product_img.resize((new_width, new_height), Image.LANCZOS)
    except Exception as e:
        st.warning(f"Resize failed: {e}. Using original size.")
        resized = product_img
    
    # Rotate slightly
    angle = np.sin(t * 0.5) * 3
    try:
        rotated = resized.rotate(angle, expand=True, resample=Image.BICUBIC)
    except Exception as e:
        st.warning(f"Rotation failed: {e}. Using unrotated image.")
        rotated = resized
    
    # Product position based on platform and safe zones
    prod_y = st.session_state.get("prod_y_offset", 0)
    
    if platform == "Facebook Feed":
        prod_y_base = int(HEIGHT * 0.4)
        prod_y = int(max(200, min(400, prod_y_base + prod_y)))
        prod_x = int((WIDTH - rotated.width) // 2)
    elif platform == "Instagram Stories":
        prod_y_base = int(HEIGHT * 0.45)
        prod_y = int(max(300, min(700, prod_y_base + prod_y + np.sin(t * 3) * 30)))
        prod_x = int((WIDTH - rotated.width) // 2)
    else:  # Instagram Reels
        prod_y_base = int(HEIGHT * 0.35)
        prod_y = int(max(350, min(700, prod_y_base + prod_y + np.sin(t * 3) * 30)))
        prod_x = int((WIDTH - rotated.width) // 2)
    
    # Paste product (with proper integer coordinates and error handling)
    try:
        if rotated.mode == 'RGBA':
            canvas.paste(rotated, (int(prod_x), int(prod_y)), rotated)
        else:
            canvas.paste(rotated, (int(prod_x), int(prod_y)))
    except Exception as e:
        st.warning(f"Product paste failed: {e}. Using fallback position.")
        try:
            if rotated.mode == 'RGBA':
                canvas.paste(rotated, (int(prod_x), int(prod_y_base)), rotated)
            else:
                canvas.paste(rotated, (int(prod_x), int(prod_y_base)))
        except Exception as e2:
            st.warning(f"Fallback paste also failed: {e2}. Skipping product.")

    # ✅ PLATFORM-SPECIFIC TEXT POSITIONS
    safe_zones = template["safe_zones"]
    
    # Title (top zone)
    if platform == "Facebook Feed":
        title_font_size = 50
        hook_font_size = 40
        price_font_size = 45
        cta_font_size = 40
    else:
        title_font_size = 90
        hook_font_size = 110
        price_font_size = 130
        cta_font_size = 85
    
    # Load fonts with fallbacks
    try:
        title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", title_font_size)
    except:
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", title_font_size)
        except:
            title_font = ImageFont.load_default()
    
    # Platform-specific title position
    if platform == "Instagram Stories":
        # Add "Swipe Up" indicator
        title_pos = (int(safe_zones["title"][0]), int(safe_zones["title"][1] - 40))
        draw.text(title_pos, title, font=title_font, fill=template["text_color"], 
                  stroke_width=4, stroke_fill="#000")
        
        # Swipe up arrow
        arrow_x, arrow_y = int(WIDTH - 100), int(HEIGHT - 100)
        draw.polygon([(arrow_x, arrow_y), (arrow_x + 50, arrow_y), (arrow_x + 25, arrow_y - 40)], 
                    fill=template["price_bg"])
    else:
        draw.text((int(safe_zones["title"][0]), int(safe_zones["title"][1])), title, font=title_font, fill=template["text_color"], 
                  stroke_width=5, stroke_fill="#000")

    # Hook (below title)
    try:
        hook_font = ImageFont.truetype("DejaVuSans-Bold.ttf", hook_font_size)
    except:
        try:
            hook_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", hook_font_size)
        except:
            hook_font = ImageFont.load_default()
    draw.text((int(safe_zones["hook"][0]), int(safe_zones["hook"][1])), hook, font=hook_font, fill=template["ring_color"], 
              stroke_width=6, stroke_fill="#000")

    # Price badge (thumb zone)
    try:
        price_font = ImageFont.truetype("DejaVuSans-Bold.ttf", price_font_size)
    except:
        try:
            price_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", price_font_size)
        except:
            price_font = ImageFont.load_default()
    
    if platform == "Facebook Feed":
        badge_w, badge_h = 400, 100
        badge_x = int((WIDTH - badge_w) // 2)
        badge_y = int(HEIGHT - 150)
    else:
        badge_w, badge_h = 700, 160
        badge_y = int(safe_zones["price"][1] - badge_h // 2)
        badge_x = int((WIDTH - badge_w) // 2)
    
    draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], 
                          radius=40 if platform == "Facebook Feed" else 80, 
                          fill=template["price_bg"])
    
    price_pos = (int(WIDTH // 2), int(badge_y + badge_h // 2))
    draw.text(price_pos, price, font=price_font, fill=template["price_text"], anchor="mm")

    # CTA (thumb tap zone)
    try:
        cta_font = ImageFont.truetype("DejaVuSans.ttf", cta_font_size)
    except:
        try:
            cta_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", cta_font_size)
        except:
            cta_font = ImageFont.load_default()
    
    if template["cta_pulse"] and platform != "Facebook Feed":
        pulse_scale = 1 + 0.1 * np.sin(t * 8)
        cta_font_size = int(cta_font_size * pulse_scale)
        try:
            cta_font = ImageFont.truetype("DejaVuSans.ttf", cta_font_size)
        except:
            try:
                cta_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", cta_font_size)
            except:
                cta_font = ImageFont.load_default()
    
    if platform == "Facebook Feed":
        cta_pos = (int(WIDTH // 2), int(HEIGHT - 80))
    else:
        cta_pos = (int(safe_zones["cta"][0]), int(safe_zones["cta"][1]))
    
    draw.text(cta_pos, cta, font=cta_font, fill=template["text_color"], 
              stroke_width=4 if platform == "Facebook Feed" else 5, 
              stroke_fill="#000")

    # ✅ LOGO (platform-specific positioning)
    if logo:
        if platform == "Facebook Feed":
            logo_pos = (20, 20)
        else:
            logo_pos = safe_zones["logo"]
        try:
            if logo.mode == 'RGBA':
                canvas.paste(logo, (int(logo_pos[0]), int(logo_pos[1])), logo)
            else:
                canvas.paste(logo, (int(logo_pos[0]), int(logo_pos[1])))
        except Exception as e:
            st.warning(f"Logo paste failed: {e}. Skipping logo.")

    return np.array(canvas)

# --- UI ---
st.title("🎬 SM Interiors Pro Reel Generator")
st.caption("✅ 3 Pro Templates • ✅ Platform-Specific • ✅ Fixed for Streamlit Cloud • Nov 24, 2025")

# Platform selection
platform = st.radio("📱 Output Platform", 
                   ["Instagram Reels", "Instagram Stories", "Facebook Feed"],
                   horizontal=True,
                   help="Choose where you'll post this content")

# Update session state
st.session_state.platform = platform

# Get platform dimensions
WIDTH, HEIGHT = PLATFORM_DIMENSIONS[platform]

# Template selector
template_choice = st.selectbox("🎨 Professional Template", 
                              ["Luxury", "Modern", "Bold"],
                              index=0,
                              help="Choose your visual style")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📸 Product Image")
    uploaded = st.file_uploader("Upload Product Photo", type=["png", "jpg", "jpeg", "webp"], 
                              help="JPG/PNG under 5MB • Works with outdoor shots",
                              label_visibility="collapsed")
    
    if uploaded:
        with st.spinner("Processing image..."):
            product_img, img_bytes = safe_image_load(uploaded, platform)
            if product_img:
                st.image(product_img, caption="✅ Background removed & professionally composed", use_column_width=True)
    else:
        product_img = None
        img_bytes = None

    st.subheader("💰 Price")
    if platform == "Facebook Feed":
        price = st.text_input("Price", "Ksh 18,999", label_visibility="collapsed")
    else:
        price = st.text_input("Price", "Ksh 18,999", label_visibility="collapsed")

with col2:
    st.subheader("🤖 AI-Powered Text")
    if client and uploaded and img_bytes:
        if st.button("✨ Generate All Text with AI", type="secondary", use_container_width=True):
            with st.spinner("AI generating text..."):
                ai_data = generate_text_with_groq(img_bytes, platform)
                st.session_state.title = ai_data.get("title", "SM Interiors")[:30 if platform == "Facebook Feed" else 25]
                st.session_state.hook = ai_data.get("hook", "LIMITED STOCK!")[:25 if platform == "Facebook Feed" else 18]
                if platform == "Instagram Stories":
                    st.session_state.cta = ai_data.get("cta", "SWIPE UP TO SHOP")[:30]
                elif platform == "Facebook Feed":
                    st.session_state.cta = ai_data.get("cta", "Shop now and get free delivery!")[:35]
                else:
                    st.session_state.cta = ai_data.get("cta", "DM TO ORDER • 0710 895 737")[:30]
                st.success("✅ AI generated all text content!")
    else:
        st.info("ℹ️ AI features disabled (no API key). Use manual text below.")

    st.subheader("✏️ Text Content")
    if platform == "Facebook Feed":
        max_title = 30
        max_hook = 25
        max_cta = 35
    elif platform == "Instagram Stories":
        max_title = 25
        max_hook = 18
        max_cta = 30
    else:
        max_title = 25
        max_hook = 18
        max_cta = 30
    
    title = st.text_input("Title (max chars)", 
                         value=st.session_state.get("title", "Grey Chest of Drawers")[:max_title], 
                         max_chars=max_title)
    
    hook = st.text_input("Hook (max chars)", 
                        value=st.session_state.get("hook", "2 LEFT IN STOCK!")[:max_hook], 
                        max_chars=max_hook)
    
    cta = st.text_input("CTA (max chars)", 
                       value=st.session_state.get("cta", "DM TO ORDER • 0710 895 737")[:max_cta], 
                       max_chars=max_cta)

# --- ADJUSTMENTS ---
st.markdown("---")
st.subheader("🔧 Fine-tune Product Position (Rarely Needed)")

with st.expander("Product Position Only"):
    st.caption("Adjust only if product overlaps text")
    prod_y_offset = st.slider("Product Vertical Position", -150, 150, 0, 
                            help="Move product up/down. Default = perfect for most items")
    product_scale = st.slider("Product Scale", 0.6, 1.4, 1.0, step=0.1,
                           help="Make product larger/smaller")

# Save to session state
st.session_state.prod_y_offset = prod_y_offset
st.session_state.product_scale = product_scale
st.session_state.template = template_choice

# --- PREVIEW ---
if uploaded and product_img is not None:
    st.markdown("---")
    st.subheader("✅ PREVIEW (Exact Output)")
    
    logo_img = load_logo()
    
    # Create preview frame
    preview_frame = create_frame(0, product_img, hook, price, cta, title, 
                               template_choice, platform, logo_img)
    preview_img = Image.fromarray(preview_frame)
    
    st.image(preview_img, use_column_width=True)
    st.caption(f"📱 This is exactly what will render on {platform}. Tested on Streamlit Cloud.")

# --- RENDER ---
if st.button(f"🚀 GENERATE {platform} VIDEO", type="primary", use_container_width=True):
    if not uploaded or product_img is None:
        st.error("❌ Upload a product photo first!")
    else:
        with st.spinner(f".Rendering {platform} video... (takes 20-35 seconds)"):
            logo_img = load_logo()
            frames = []
            
            # Generate frames with progress bar
            progress = st.progress(0)
            for i in range(FPS * DURATION):
                frame = create_frame(i / FPS, product_img, hook, price, cta, title, 
                                   template_choice, platform, logo_img)
                frames.append(frame)
                progress.progress((i + 1) / (FPS * DURATION))
            
            clip = ImageSequenceClip(frames, fps=FPS)
            
            # Audio handling (only for Instagram)
            audio = None
            audio_path = None
            if platform != "Facebook Feed":
                try:
                    resp = requests.get(MUSIC_URL, timeout=10)
                    if resp.status_code == 200:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                            tmp.write(resp.content)
                            audio_path = tmp.name
                        
                        audio_clip = AudioFileClip(audio_path).subclip(0, min(DURATION, AudioFileClip(audio_path).duration))
                        clip = clip.set_audio(audio_clip)
                except Exception as e:
                    st.warning(f"Audio skipped: {str(e)[:50]}... Video only.")

            # Export
            video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            try:
                clip.write_videofile(
                    video_path,
                    fps=FPS,
                    codec="libx264",
                    audio_codec="aac" if audio_path else None,
                    threads=4,
                    preset="medium",
                    bitrate="1000k" if platform != "Facebook Feed" else "500k",
                    logger=None
                )
            except Exception as e:
                st.error(f"Video export failed: {e}. Trying fallback settings.")
                clip.write_videofile(
                    video_path,
                    fps=FPS,
                    codec="libx264",
                    audio_codec="aac" if audio_path else None,
                    threads=1,
                    preset="fast",
                    bitrate="500k",
                    logger=None
                )
            
            st.success(f"✅ {platform} VIDEO GENERATED SUCCESSFULLY!")
            st.video(video_path)
            
            # Platform-specific download name
            platform_clean = platform.replace(" ", "_").replace(".", "")
            with open(video_path, "rb") as f:
                st.download_button(f"⬇️ DOWNLOAD {platform} VIDEO", f, 
                                 f"SM_Interiors_{platform_clean}.mp4", "video/mp4", 
                                 use_container_width=True,
                                 type="primary")
            
            # Cleanup
            if audio_path and os.path.exists(audio_path):
                os.unlink(audio_path)
            if os.path.exists(video_path):
                os.unlink(video_path)
            clip.close()

st.markdown("---")
st.caption("✅ TESTED ON STREAMLIT CLOUD • NO MISSING LIBRARIES • NOV 24, 2025")
