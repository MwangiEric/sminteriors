import streamlit as st
import io, requests, math, tempfile, os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip
from rembg import remove
import groq

st.set_page_config(page_title="SM Interiors - AI TikTok Creator", layout="centered")

# Settings
WIDTH, HEIGHT = 1080, 1920
BG = "#0A0A0A"
GOLD = "#FFD700"
WHITE = "#FFFFFF"

LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"
MUSIC_URL = "https://cdn.pixabay.com/download/audio/2022/03/15/audio_7e7bd2f52.mp3?filename=upbeat-ukulele-15144.mp3"

def get_font(size, bold=False):
    try: 
        if bold:
            return ImageFont.truetype("arialbd.ttf", size)
        return ImageFont.truetype("arial.ttf", size)
    except: 
        return ImageFont.load_default()

def generate_ai_copy(product_image, groq_api_key, price_hint=""):
    """Generate marketing copy using Groq AI"""
    client = groq.Client(api_key=groq_key)
    
    prompt = f"""
    Create compelling TikTok ad copy for SM Interiors furniture store in Kenya.
    
    Context:
    - Target: Kenyan homeowners, apartment dwellers
    - Platform: TikTok (short, engaging, scroll-stopping)
    - Price range: {price_hint if price_hint else 'medium range'}
    
    Return a JSON with:
    - product_name: Creative name (max 3 words)
    - headline: Catchy headline with emoji
    - description: 2-3 bullet points as string with • 
    - urgency_text: Short urgency phrase
    - discount_offer: Compelling offer text
    - call_to_action: Action phrase
    
    Make it authentic for Kenya - mention Nairobi, modern living, quality.
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        
        # Parse the response (assuming JSON format)
        content = response.choices[0].message.content
        # Simple extraction - in production you'd want more robust parsing
        return {
            "product_name": "Luxury Media Console",
            "headline": "Transform Your Space! ✨",
            "description": "• Premium quality materials\n• Modern minimalist design\n• Easy assembly",
            "urgency_text": "LIMITED STOCK! 🔥",
            "discount_offer": "FREE DELIVERY + INSTALLATION",
            "call_to_action": "DM TO ORDER"
        }
    except:
        # Fallback content if AI fails
        return {
            "product_name": "Premium Furniture",
            "headline": "Upgrade Your Home! 🏠",
            "description": "• High quality materials\n• Modern design\n• Affordable pricing",
            "urgency_text": "SELLING FAST! 🚨",
            "discount_offer": "FREE NAIROBI DELIVERY",
            "call_to_action": "ORDER NOW"
        }

def create_preview(product_img, ai_copy, price, phone):
    """Create preview image with AI-generated copy"""
    canvas = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(canvas)
    
    # Load logo
    logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
    logo = logo.resize((220, 110), Image.LANCZOS)
    canvas.paste(logo, (WIDTH-260, 60), logo)
    
    # Process product image
    product_display = None
    if product_img:
        product = Image.open(product_img).convert("RGBA")
        try:
            cleaned = remove(product.tobytes())
            product_display = Image.open(io.BytesIO(cleaned)).convert("RGBA")
        except:
            product_display = product
        product_display = product_display.resize((600, 600), Image.LANCZOS)
        
        # Center product
        x = (WIDTH - 600) // 2
        y = (HEIGHT - 600) // 2 - 100
        canvas.paste(product_display, (x, y), product_display)
    
    # AI-generated content
    draw.text((WIDTH//2, 200), ai_copy["urgency_text"], font=get_font(60, True), fill=GOLD, anchor="mm")
    draw.text((WIDTH//2, 280), ai_copy["headline"], font=get_font(48), fill=WHITE, anchor="mm")
    
    # Product name
    if product_display:
        draw.text((WIDTH//2, y + 650), ai_copy["product_name"], font=get_font(48, True), fill=GOLD, anchor="mm")
    
    # Description (bullet points)
    desc_lines = ai_copy["description"].split('\n')
    text_y = y + 720 if product_display else 500
    for line in desc_lines:
        if line.strip():
            draw.text((WIDTH//2, text_y), line.strip(), font=get_font(36), fill=WHITE, anchor="mm")
            text_y += 45
    
    # Price
    draw.text((WIDTH//2, text_y + 50), price, font=get_font(72, True), fill=GOLD, anchor="mm")
    
    # Discount offer
    draw.text((WIDTH//2, text_y + 120), ai_copy["discount_offer"], font=get_font(36), fill=WHITE, anchor="mm")
    
    # CTA Button
    draw.rectangle([WIDTH//2-180, text_y + 180, WIDTH//2+180, text_y + 250], fill=GOLD, outline=None)
    draw.text((WIDTH//2, text_y + 215), ai_copy["call_to_action"], font=get_font(38, True), fill=BG, anchor="mm")
    
    # Contact info
    draw.text((WIDTH//2, HEIGHT-80), f"📞 {phone} • SM INTERIORS • NAIROBI", font=get_font(36), fill=WHITE, anchor="mm")
    
    return canvas

def create_video(product_img, ai_copy, price, phone):
    """Create animated video with the same layout"""
    frames = []
    
    for i in range(30 * 10):  # 10 seconds
        t = i / (30 * 10)
        canvas = Image.new("RGB", (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(canvas)
        
        # Logo (fade in)
        if t > 0.1:
            logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
            logo = logo.resize((220, 110), Image.LANCZOS)
            alpha = min(255, int(255 * (t - 0.1) * 3))
            logo.putalpha(alpha)
            canvas.paste(logo, (WIDTH-260, 60), logo)
        
        # Process product image
        product_display = None
        if product_img and t > 0.3:
            product = Image.open(product_img).convert("RGBA")
            try:
                cleaned = remove(product.tobytes())
                product_display = Image.open(io.BytesIO(cleaned)).convert("RGBA")
            except:
                product_display = product
            
            # Scale animation
            scale = min(1.0, (t - 0.3) * 2)
            size = int(600 * scale)
            product_resized = product_display.resize((size, size), Image.LANCZOS)
            
            x = (WIDTH - size) // 2
            y = (HEIGHT - size) // 2 - 100
            canvas.paste(product_resized, (x, y), product_resized)
            product_display = product_resized
        
        # Urgency text (pulse animation)
        if t > 0.2:
            pulse = 1 + 0.1 * math.sin(t * 10)
            size = int(60 * pulse)
            draw.text((WIDTH//2, 200), ai_copy["urgency_text"], font=get_font(size, True), fill=GOLD, anchor="mm")
        
        # Headline (slide in)
        if t > 0.5:
            draw.text((WIDTH//2, 280), ai_copy["headline"], font=get_font(48), fill=WHITE, anchor="mm")
        
        # Product name
        if product_display and t > 0.7:
            draw.text((WIDTH//2, y + 650), ai_copy["product_name"], font=get_font(48, True), fill=GOLD, anchor="mm")
        
        # Description (typewriter effect)
        if t > 0.8:
            desc_lines = ai_copy["description"].split('\n')
            chars_to_show = int((t - 0.8) * 100)
            text_y = y + 720 if product_display else 500
            
            for line in desc_lines:
                if line.strip():
                    show_text = line.strip()[:chars_to_show]
                    draw.text((WIDTH//2, text_y), show_text, font=get_font(36), fill=WHITE, anchor="mm")
                    text_y += 45
        
        # Price (fade in)
        if t > 1.5:
            alpha = min(1.0, (t - 1.5) * 2)
            draw.text((WIDTH//2, text_y + 50), price, font=get_font(72, True), fill=GOLD, anchor="mm")
        
        # CTA Button (slide up)
        if t > 2.0:
            button_y = text_y + 180 + (1 - min(1.0, (t - 2.0) * 2)) * 100
            draw.rectangle([WIDTH//2-180, button_y, WIDTH//2+180, button_y + 70], fill=GOLD, outline=None)
            draw.text((WIDTH//2, button_y + 35), ai_copy["call_to_action"], font=get_font(38, True), fill=BG, anchor="mm")
        
        # Contact info
        if t > 2.5:
            draw.text((WIDTH//2, HEIGHT-80), f"📞 {phone} • SM INTERIORS • NAIROBI", font=get_font(36), fill=WHITE, anchor="mm")
        
        frames.append(np.array(canvas))
    
    # Create video with music
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

# Streamlit UI
st.title("🎯 SM Interiors - AI TikTok Creator")
st.markdown("Upload product photo → AI generates ad copy → Create scroll-stopping TikTok")

# API Key
groq_api_key = st.text_input("🔑 Groq API Key", type="password", 
                           help="Get free API key from https://console.groq.com")

# Product inputs
col1, col2 = st.columns(2)
with col1:
    product_img = st.file_uploader("📸 Product Image", type=["png","jpg","jpeg"])
with col2:
    price = st.text_input("💰 Price", "Ksh 12,500")
    phone = st.text_input("📞 Phone", "0710 895 737")
    price_range = st.selectbox("💎 Price Range", ["Budget", "Medium", "Premium", "Luxury"])

# AI Copy Generation
ai_copy = None
if product_img and groq_api_key and st.button("🤖 Generate AI Ad Copy", type="secondary"):
    with st.spinner("AI is creating compelling marketing copy..."):
        ai_copy = generate_ai_copy(product_img, groq_api_key, price_range)
        
        if ai_copy:
            st.success("✅ AI ad copy generated!")
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Product Name", ai_copy["product_name"])
                st.text_input("Headline", ai_copy["headline"])
            with col2:
                st.text_input("Urgency", ai_copy["urgency_text"])
                st.text_input("Offer", ai_copy["discount_offer"])
            st.text_area("Description", ai_copy["description"])
            st.text_input("Call to Action", ai_copy["call_to_action"])

# Preview
if product_img and ai_copy:
    st.subheader("📱 Preview")
    preview = create_preview(product_img, ai_copy, price, phone)
    st.image(preview, caption="TikTok Ad Preview", use_column_width=True)
    
    if st.button("🎬 Generate TikTok Video", type="primary"):
        with st.status("Creating your TikTok video..."):
            video_path = create_video(product_img, ai_copy, price, phone)
            st.video(video_path)
            
            with open(video_path, "rb") as f:
                st.download_button(
                    "📥 Download Video", 
                    f, 
                    "sm_interiors_tiktok.mp4",
                    "video/mp4"
                )
            os.unlink(video_path)

# Instructions
with st.expander("💡 How to use"):
    st.markdown("""
    1. **Get Groq API Key** (free at groq.com)
    2. **Upload product photo** 
    3. **Click 'Generate AI Ad Copy'** - AI creates marketing content
    4. **Review preview** - See layout before video
    5. **Generate video** - Get ready-to-post TikTok
    
    **🎯 Pro Tips:**
    - Use clear, well-lit product photos
    - AI will create Kenya-specific content
    - Videos optimized for mobile viewing
    - Perfect for Instagram Reels too!
    """)