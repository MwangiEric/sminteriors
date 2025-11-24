import streamlit as st
import io, requests, math, tempfile, base64, json, time, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, TextClip
from rembg import remove

# --- GLOBAL CONFIGURATION ---
st.set_page_config(page_title="TikTok AdGen Pro", layout="wide", page_icon="🎬")

# --- TIKTOK-OPTIMIZED CONSTANTS ---
WIDTH, HEIGHT = 1080, 1920  # TikTok optimal resolution (9:16)
FPS = 30
DURATION = 15  # TikTok sweet spot (7-15s for engagement)
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

# --- TRENDING MUSIC TRACKS (Royalty-free) ---
MUSIC_TRACKS = {
    "Energetic Viral": "https://archive.org/download/Bensound_-_Jazzy_Frenchy/Bensound_-_Jazzy_Frenchy.mp3",
    "Chill Luxury": "https://archive.org/download/bensound-adaytoremember/bensound-adaytoremember.mp3",
    "Modern Beats": "https://archive.org/download/bensound-sweet/bensound-sweet.mp3",
    "Upbeat Pop": "https://archive.org/download/bensound-epic/bensound-epic.mp3"
}

# --- TIKTOK HASHTAG GENERATOR ---
TRENDING_HASHTAGS = {
    "furniture": "#FurnitureTikTok #HomeDecor #InteriorDesign #HomeInspo #FurnitureDesign #ModernHome #LuxuryFurniture",
    "diy": "#DIYHome #HomeHacks #DIYProject #HomeImprovement #RoomMakeover #BudgetFriendly #DIYDecor",
    "tips": "#HomeTips #InteriorTips #DesignTips #HomeDesignTips #DecoratingTips #StyleGuide #DesignHacks",
    "showroom": "#FurnitureShowroom #NewCollection #ShopLocal #SupportSmallBusiness #HomeStore #FurnitureSale"
}

# --- AUTH ---
if "groq_key" not in st.secrets:
    st.error("🚨 Missing Secret: Add `groq_key` to your .streamlit/secrets.toml")
    st.stop()

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {st.secrets['groq_key']}",
    "Content-Type": "application/json"
}

# --- IMAGE PROCESSING ---
def process_image_pro(input_image):
    """Enhanced background removal with quality optimization."""
    with st.spinner("🎨 AI Processing Image..."):
        img_byte_arr = io.BytesIO()
        input_image.save(img_byte_arr, format="PNG")
        input_image_bytes = img_byte_arr.getvalue()

        output_bytes = remove(input_image_bytes)
        clean_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")

    # TikTok-optimized enhancements
    clean_img = ImageEnhance.Contrast(clean_img).enhance(1.2)
    clean_img = ImageEnhance.Sharpness(clean_img).enhance(1.8)
    clean_img = ImageEnhance.Color(clean_img).enhance(1.15)
    return clean_img

# --- FONTS ---
def get_font(size, bold=True):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "arial.ttf"
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()

# --- ANIMATION EASING ---
def ease_out_elastic(t):
    c4 = (2 * math.pi) / 3
    if t <= 0: return 0
    if t >= 1: return 1
    return math.pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

def ease_in_out_cubic(t):
    return 4 * t * t * t if t < 0.5 else 1 - math.pow(-2 * t + 2, 3) / 2

def linear_fade(t, start, duration):
    if t < start: return 0.0
    if t > start + duration: return 1.0
    return (t - start) / duration

# --- TIKTOK-OPTIMIZED TEMPLATES ---
BRAND_PRIMARY = "#4C3B30"
BRAND_ACCENT = "#D2A544"
BRAND_TEXT_LIGHT = "#FFFFFF"
BRAND_TEXT_DARK = "#000000"

TEMPLATES = {
    "Viral Zoom": {
        "bg_grad": ["#1a1a1a", "#2d2d2d"],
        "accent": "#FFD700", "text": BRAND_TEXT_LIGHT,
        "price_bg": "#FF4444", "price_text": BRAND_TEXT_LIGHT,
        "graphic_type": "zoom_pulse",
        "hook_style": "bold"
    },
    "Luxury Glam": {
        "bg_grad": [BRAND_PRIMARY, "#2a201b"],
        "accent": BRAND_ACCENT, "text": BRAND_TEXT_LIGHT,
        "price_bg": BRAND_ACCENT, "price_text": BRAND_TEXT_DARK,
        "graphic_type": "sparkle",
        "hook_style": "elegant"
    },
    "Modern Pop": {
        "bg_grad": ["#FF6B6B", "#4ECDC4"],
        "accent": "#FFFFFF", "text": BRAND_TEXT_LIGHT,
        "price_bg": "#FFE66D", "price_text": BRAND_TEXT_DARK,
        "graphic_type": "geometric",
        "hook_style": "playful"
    },
    "Minimal Clean": {
        "bg_grad": ["#F8F9FA", "#E9ECEF"],
        "accent": "#212529", "text": "#212529",
        "price_bg": "#212529", "price_text": BRAND_TEXT_LIGHT,
        "graphic_type": "minimal",
        "hook_style": "clean"
    }
}

# --- GROQ AI ---
def ask_groq(payload):
    try:
        r = requests.post(GROQ_URL, json=payload, headers=HEADERS, timeout=20)
        r.raise_for_status()
        data = r.json()
        choices = data.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            return message.get("content", "")
        return None
    except Exception as e:
        st.error(f"Groq API Error: {str(e)[:200]}")
        return None

def generate_tiktok_hook(product_name, style="viral"):
    """Generate a 3-5 word TikTok hook optimized for stopping scroll."""
    style_prompts = {
        "viral": "Create a viral, attention-grabbing hook that makes people stop scrolling",
        "luxury": "Create an elegant, luxury-focused hook that exudes sophistication",
        "playful": "Create a fun, energetic hook with personality",
        "urgent": "Create an urgent, FOMO-inducing hook"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a TikTok content expert. Generate only the hook text, nothing else. 3-5 words max."},
            {"role": "user", "content": f"{style_prompts.get(style, style_prompts['viral'])} for '{product_name}'. Output ONLY the hook text."}
        ],
        "temperature": 0.9,
        "max_tokens": 20
    }
    
    result = ask_groq(payload)
    return result.strip().strip('"').strip("'") if result else "Transform Your Space"

def generate_tiktok_caption(product_name, price, hook):
    """Generate complete TikTok caption with hashtags."""
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Create a 2-3 sentence TikTok caption that's engaging and calls to action. Do not include hashtags."},
            {"role": "user", "content": f"Product: {product_name}, Price: {price}, Hook: {hook}. Write caption only."}
        ],
        "temperature": 0.8,
        "max_tokens": 100
    }
    
    caption_text = ask_groq(payload) or f"Elevate your space with the {product_name}. Premium quality at {price}. DM to order! 💫"
    
    # Auto-add relevant hashtags
    hashtags = TRENDING_HASHTAGS["furniture"]
    return f"{caption_text.strip()}\n\n{hashtags}\n\n#SMInteriors #KenyanBusiness"

def generate_content_ideas(content_type, keyword):
    """Generate viral content ideas for TikTok."""
    prompts = {
        "DIY Tips": f"Generate 5 viral DIY home decor hacks for TikTok about '{keyword}'. Format as numbered list with emoji.",
        "Furniture Care": f"Generate 5 quick furniture care tips for '{keyword}' perfect for 15-second TikToks. Add emoji to each.",
        "Design Trends": f"Generate 5 trending interior design ideas about '{keyword}'. Make it Gen-Z friendly with emoji.",
        "Before/After": f"Generate 5 compelling before/after transformation concepts for '{keyword}'. TikTok style.",
        "Product Showcase": f"Generate 5 creative ways to showcase '{keyword}' on TikTok. Include trending sounds suggestions."
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a TikTok content strategist. Be creative, trendy, and concise."},
            {"role": "user", "content": prompts.get(content_type, prompts["DIY Tips"])}
        ],
        "temperature": 0.9,
        "max_tokens": 600
    }
    
    return ask_groq(payload) or "*No ideas generated. Try again.*"

# --- RENDERING ---
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0,2,4))

def draw_text_with_outline(draw, text, position, font, fill_color, outline_color, outline_width=3):
    x, y = position
    # Draw outline
    for adj_x in range(-outline_width, outline_width+1):
        for adj_y in range(-outline_width, outline_width+1):
            draw.text((x+adj_x, y+adj_y), text, font=font, fill=outline_color)
    # Draw main text
    draw.text((x, y), text, font=font, fill=fill_color)

def create_tiktok_frame(t, product_img, template_name, texts):
    """Create a single frame optimized for TikTok with trending animations."""
    T = TEMPLATES[template_name]
    canvas = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(canvas)
    
    # Gradient background
    c1 = hex_to_rgb(T["bg_grad"][0])
    c2 = hex_to_rgb(T["bg_grad"][1])
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(c1[0] + (c2[0] - c1[0]) * ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    
    # Animated graphics based on template
    if T.get("graphic_type") == "sparkle":
        # Animated sparkles
        for i in range(8):
            sparkle_t = (t + i * 0.3) % 2.0
            if sparkle_t < 1.0:
                alpha = int(255 * math.sin(sparkle_t * math.pi))
                size = int(30 * ease_out_elastic(sparkle_t))
                x = int(WIDTH * (0.1 + 0.8 * (i / 8)))
                y = int(HEIGHT * (0.2 + 0.6 * ((i * 37) % 100) / 100))
                draw.ellipse([x-size, y-size, x+size, y+size], 
                           fill=(255, 215, 0, alpha))
    
    # Product showcase with zoom animation
    product_scale = 1.0
    if t < 2.0:
        product_scale = 0.5 + 0.5 * ease_out_elastic(t / 2.0)
    elif t > 12.0:
        product_scale = 1.0 + 0.2 * ease_in_out_cubic((t - 12.0) / 3.0)
    
    # Floating animation
    float_offset = math.sin(t * 1.5) * 20
    
    product_h = int(HEIGHT * 0.5 * product_scale)
    product_w = int(product_img.width * (product_h / product_img.height))
    
    if product_w > 0 and product_h > 0:
        p_resized = product_img.resize((product_w, product_h), Image.LANCZOS)
        
        # Shadow
        shadow = Image.new("RGBA", (product_w + 40, product_h + 40), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.ellipse([10, 10, product_w + 30, product_h + 30], fill=(0, 0, 0, 100))
        shadow = shadow.filter(ImageFilter.GaussianBlur(25))
        
        prod_x = (WIDTH - product_w) // 2
        prod_y = int(HEIGHT * 0.35) + int(float_offset)
        
        canvas.paste(shadow, (prod_x - 20, prod_y + 40), shadow)
        canvas.paste(p_resized, (prod_x, prod_y), p_resized)
    
    # Hook text (top) - TikTok style
    if t > 0.5:
        hook_alpha = min(1.0, (t - 0.5) / 0.5)
        hook_y_offset = int(50 * (1 - ease_out_elastic(hook_alpha)))
        
        hook_font = get_font(90)
        hook_text = texts.get("hook", "Amazing Deal!")
        
        # Get text size for centering
        bbox = draw.textbbox((0, 0), hook_text, font=hook_font)
        text_width = bbox[2] - bbox[0]
        hook_x = (WIDTH - text_width) // 2
        hook_y = 150 - hook_y_offset
        
        draw_text_with_outline(draw, hook_text, (hook_x, hook_y), 
                              hook_font, T["accent"], (0, 0, 0), 4)
    
    # Price badge - TikTok viral style
    if t > 3.0:
        price_scale = ease_out_elastic(min(1.0, (t - 3.0) / 0.8))
        if price_scale > 0:
            badge_w = int(500 * price_scale)
            badge_h = int(140 * price_scale)
            badge_x = (WIDTH - badge_w) // 2
            badge_y = int(HEIGHT * 0.75)
            
            # Glowing effect
            glow = Image.new("RGBA", (badge_w + 40, badge_h + 40), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow)
            glow_color = hex_to_rgb(T["price_bg"]) + (150,)
            glow_draw.rounded_rectangle([10, 10, badge_w + 30, badge_h + 30], 
                                       radius=35, fill=glow_color)
            glow = glow.filter(ImageFilter.GaussianBlur(20))
            canvas.paste(glow, (badge_x - 20, badge_y - 20), glow)
            
            # Main badge
            badge_color = hex_to_rgb(T["price_bg"]) + (255,)
            draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
                                  radius=30, fill=badge_color)
            
            # Price text
            price_font = get_font(70)
            price_text = texts.get("price", "Ksh 49,900")
            p_bbox = draw.textbbox((0, 0), price_text, font=price_font)
            p_width = p_bbox[2] - p_bbox[0]
            p_x = badge_x + (badge_w - p_width) // 2
            p_y = badge_y + 30
            
            draw.text((p_x, p_y), price_text, font=price_font, fill=T["price_text"])
    
    # CTA (Call to Action)
    if t > 10.0:
        cta_alpha = min(1.0, (t - 10.0) / 1.0)
        cta_font = get_font(50)
        cta_text = f"📱 {texts.get('contact', '0710895737')}"
        
        c_bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
        c_width = c_bbox[2] - c_bbox[0]
        cta_x = (WIDTH - c_width) // 2
        cta_y = int(HEIGHT * 0.88)
        
        # Pulsing effect
        pulse = 1.0 + 0.1 * math.sin(t * 3)
        draw_text_with_outline(draw, cta_text, (int(cta_x), cta_y),
                              cta_font, T["text"], (0, 0, 0), 3)
    
    # Logo (top corner)
    try:
        logo = Image.open(requests.get(LOGO_URL, stream=True, timeout=10).raw).convert("RGBA")
        logo = logo.resize((180, 100), Image.LANCZOS)
        canvas.paste(logo, (50, 50), logo)
    except:
        pass
    
    return np.array(canvas.convert("RGB"))

# --- STREAMLIT UI ---
st.title("🎬 TikTok AdGen Pro")
st.caption("Create viral furniture ads optimized for TikTok & Instagram Reels")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📸 Product Setup")
    uploaded_file = st.file_uploader("Upload Product Image", type=["jpg", "png", "jpeg"])
    product_name = st.text_input("Product Name", "Walden Media Console")
    price = st.text_input("Price (e.g., Ksh 49,900)", "Ksh 49,900")
    contact = st.text_input("Contact (Phone/WhatsApp)", "0710895737")
    
    st.subheader("🎨 Style & Music")
    template = st.selectbox("Template Style", list(TEMPLATES.keys()))
    music = st.selectbox("Background Track", list(MUSIC_TRACKS.keys()))
    
    generate_btn = st.button("🚀 Generate TikTok Ad", type="primary", use_container_width=True)

with col2:
    st.subheader("💡 Content Idea Generator")
    content_type = st.selectbox("Content Type", 
                                ["DIY Tips", "Furniture Care", "Design Trends", 
                                 "Before/After", "Product Showcase"])
    keyword = st.text_input("Focus Keyword", "Mid-Century Console")
    
    if st.button("✨ Generate Ideas", use_container_width=True):
        with st.spinner("Generating viral content ideas..."):
            ideas = generate_content_ideas(content_type, keyword)
            st.markdown("### 🎯 Content Ideas")
            st.markdown(ideas)
            st.success("💾 Copy these ideas for your content calendar!")

# --- VIDEO GENERATION ---
if generate_btn:
    if not uploaded_file:
        st.error("⚠️ Please upload a product image first!")
    else:
        progress_container = st.container()
        
        with progress_container:
            # Step 1: Process image
            st.info("🎨 Step 1/4: AI Processing Image...")
            raw_img = Image.open(uploaded_file).convert("RGBA")
            processed_img = process_image_pro(raw_img)
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.image(raw_img, caption="Original", use_container_width=True)
            with col_b:
                st.image(processed_img, caption="AI Processed", use_container_width=True)
            
            # Step 2: Generate hook
            st.info("🧠 Step 2/4: Generating Viral Hook...")
            hook = generate_tiktok_hook(product_name, "viral")
            st.success(f"**Hook:** {hook}")
            
            # Step 3: Generate caption
            full_caption = generate_tiktok_caption(product_name, price, hook)
            with st.expander("📝 View Complete TikTok Caption"):
                st.text_area("Copy this caption:", full_caption, height=150)
            
            # Step 4: Render video
            st.info("🎬 Step 3/4: Rendering Video...")
            
            texts = {
                "hook": hook,
                "price": price,
                "contact": contact
            }
            
            frames = []
            total_frames = FPS * DURATION
            progress_bar = st.progress(0)
            
            for i in range(total_frames):
                frame = create_tiktok_frame(i / FPS, processed_img, template, texts)
                frames.append(frame)
                if i % 10 == 0:
                    progress_bar.progress((i + 1) / total_frames)
            
            progress_bar.progress(1.0)
            
            # Step 5: Add audio
            st.info("🎵 Step 4/4: Adding Music...")
            clip = ImageSequenceClip(frames, fps=FPS)
            
            audio_path = None
            try:
                audio_response = requests.get(MUSIC_TRACKS[music], timeout=20)
                audio_response.raise_for_status()
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tf:
                    tf.write(audio_response.content)
                    audio_path = tf.name
                
                audio_clip = AudioFileClip(audio_path)
                audio_clip = audio_clip.subclip(0, min(DURATION, audio_clip.duration))
                audio_clip = audio_clip.audio_fadeout(1.5)
                clip = clip.set_audio(audio_clip)
            except Exception as e:
                st.warning(f"⚠️ Audio failed, creating silent video: {e}")
            
            # Render final video
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as vf:
                output_path = vf.name
            
            try:
                clip.write_videofile(
                    output_path,
                    codec="libx264",
                    audio_codec="aac",
                    bitrate="5000k",  # Higher quality for TikTok
                    fps=FPS,
                    preset="medium",
                    logger=None
                )
                
                st.success("✅ Video Ready!")
                st.video(output_path)
                
                with open(output_path, "rb") as f:
                    st.download_button(
                        "⬇️ Download TikTok Video (1080x1920)",
                        f,
                        file_name=f"{product_name.replace(' ', '_')}_tiktok.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )
                
                st.info("📱 **TikTok Upload Tips:**\n"
                       "- Upload during peak hours (6-9 PM)\n"
                       "- Use the generated caption with hashtags\n"
                       "- Pin the top comment with a CTA\n"
                       "- Respond to comments within first hour")
                
            finally:
                # Cleanup
                try:
                    if os.path.exists(output_path):
                        os.unlink(output_path)
                    if audio_path and os.path.exists(audio_path):
                        os.unlink(audio_path)
                except:
                    pass

# Footer
st.markdown("---")
st.caption("Made with ❤️ by SM Interiors | Optimized for TikTok & Reels")
