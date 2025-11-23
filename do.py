import streamlit as st
import io, requests, math, tempfile, os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip
from rembg import remove
import groq

st.set_page_config(page_title="SM Interiors - AI Ad Creator", layout="centered")

# Settings
WIDTH, HEIGHT = 1080, 1920
BG = "#0A0A0A"
GOLD = "#FFD700"
WHITE = "#FFFFFF"

LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"
MUSIC_URL = "https://cdn.pixabay.com/download/audio/2022/03/15/audio_7e7bd2f52.mp3?filename=upbeat-ukulele-15144.mp3"

# Unsplash categories for furniture
UNSPLASH_CATEGORIES = {
    "sofa": "sofa,living+room,modern",
    "chair": "armchair,modern+chair,designer+chair", 
    "table": "coffee+table,dining+table,modern+table",
    "bed": "modern+bed,bedroom,bed+frame",
    "cabinet": "cabinet,storage,wardrobe",
    "desk": "desk,office,workspace",
    "console": "media+console,TV+stand,entertainment+unit"
}

def get_font(size, bold=False):
    try: 
        if bold:
            return ImageFont.truetype("arialbd.ttf", size)
        return ImageFont.truetype("arial.ttf", size)
    except: 
        return ImageFont.load_default()

def get_unsplash_image(category="furniture"):
    """Get random furniture image from Unsplash"""
    url = f"https://source.unsplash.com/featured/800x800/?{category}"
    try:
        response = requests.get(url, timeout=10)
        return Image.open(io.BytesIO(response.content)).convert("RGBA")
    except:
        return None

def create_geometric_background():
    """Create geometric background with shapes and lines"""
    bg = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(bg)
    
    # Geometric elements (subtle, behind product)
    # Circles
    draw.ellipse([-100, 300, 300, 700], outline=GOLD, width=8)
    draw.ellipse([WIDTH-400, 1200, WIDTH+100, 1700], outline=GOLD, width=6)
    
    # Lines
    draw.line([(100, 200), (400, 500)], fill=GOLD, width=4)
    draw.line([(WIDTH-200, 300), (WIDTH-50, 450)], fill=GOLD, width=3)
    
    # Rectangles
    draw.rectangle([50, 1500, 250, 1600], outline=GOLD, width=5)
    draw.rectangle([WIDTH-300, 400, WIDTH-150, 500], outline=GOLD, width=4)
    
    return bg

def generate_ai_copy(product_type, groq_key, price_hint=""):
    """Generate marketing copy using Groq AI"""
    try:
        client = groq.Client(api_key=groq_key)
        
        prompt = f"""
        Create TikTok ad copy for {product_type} from SM Interiors in Kenya.
        
        Return JSON with:
        - product_name: Creative name (max 3 words)
        - headline: Catchy headline with emoji  
        - description: 2 bullet points with •
        - urgency_text: Short urgency phrase
        - discount_offer: Compelling offer
        - call_to_action: Action phrase
        
        Make it authentic for Kenya - mention Nairobi, modern living.
        """
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        
        # Simple response parsing
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
        st.error(f"AI copy generation failed: {str(e)}")
        return {
            "product_name": f"Luxury {product_type.title()}",
            "headline": "Upgrade Your Home! 🏠", 
            "description": "• Premium quality\n• Modern design",
            "urgency_text": "SELLING FAST! 🚨",
            "discount_offer": "FREE NAIROBI DELIVERY",
            "call_to_action": "ORDER NOW"
        }

def create_preview(product_img, ai_copy, price, phone):
    """Create preview with geometric background"""
    # Start with geometric background
    canvas = create_geometric_background().copy()
    draw = ImageDraw.Draw(canvas)
    
    # Load logo
    try:
        logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
        logo = logo.resize((220, 110), Image.LANCZOS)
        canvas.paste(logo, (WIDTH-260, 60), logo)
    except:
        pass
    
    # Process product image (remove background)
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
        
        product_display = product_display.resize((600, 600), Image.LANCZOS)
        
        # Center product on geometric background
        x = (WIDTH - 600) // 2
        y = (HEIGHT - 600) // 2 - 100
        canvas.paste(product_display, (x, y), product_display)
    
    # AI-generated text
    draw.text((WIDTH//2, 200), ai_copy["urgency_text"], font=get_font(60, True), fill=GOLD, anchor="mm")
    draw.text((WIDTH//2, 280), ai_copy["headline"], font=get_font(48), fill=WHITE, anchor="mm")
    
    if product_display:
        draw.text((WIDTH//2, y + 650), ai_copy["product_name"], font=get_font(48, True), fill=GOLD, anchor="mm")
    
    # Description
    desc_lines = ai_copy["description"].split('\n')
    text_y = y + 720 if product_display else 500
    for line in desc_lines:
        if line.strip():
            draw.text((WIDTH//2, text_y), line.strip(), font=get_font(36), fill=WHITE, anchor="mm")
            text_y += 45
    
    # Price & CTA
    draw.text((WIDTH//2, text_y + 50), price, font=get_font(72, True), fill=GOLD, anchor="mm")
    draw.text((WIDTH//2, text_y + 120), ai_copy["discount_offer"], font=get_font(36), fill=WHITE, anchor="mm")
    
    draw.rectangle([WIDTH//2-180, text_y + 180, WIDTH//2+180, text_y + 250], fill=GOLD, outline=None)
    draw.text((WIDTH//2, text_y + 215), ai_copy["call_to_action"], font=get_font(38, True), fill=BG, anchor="mm")
    
    # Contact
    draw.text((WIDTH//2, HEIGHT-80), f"📞 {phone} • SM INTERIORS • NAIROBI", font=get_font(36), fill=WHITE, anchor="mm")
    
    return canvas

def create_video(product_img, ai_copy, price, phone):
    """Create video with same geometric background"""
    frames = []
    
    for i in range(30 * 10):  # 10 seconds
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
            size = int(600 * scale)
            product_resized = product_display.resize((size, size), Image.LANCZOS)
            
            x = (WIDTH - size) // 2
            y = (HEIGHT - size) // 2 - 100
            canvas.paste(product_resized, (x, y), product_resized)
            product_display = product_resized
        
        # Text animations
        if t > 0.2:
            pulse = 1 + 0.1 * math.sin(t * 10)
            size = int(60 * pulse)
            draw.text((WIDTH//2, 200), ai_copy["urgency_text"], font=get_font(size, True), fill=GOLD, anchor="mm")
        
        if t > 0.5:
            draw.text((WIDTH//2, 280), ai_copy["headline"], font=get_font(48), fill=WHITE, anchor="mm")
        
        if product_display and t > 0.7:
            draw.text((WIDTH//2, y + 650), ai_copy["product_name"], font=get_font(48, True), fill=GOLD, anchor="mm")
        
        if t > 0.8:
            desc_lines = ai_copy["description"].split('\n')
            chars_to_show = int((t - 0.8) * 100)
            text_y = y + 720 if product_display else 500
            
            for line in desc_lines:
                if line.strip():
                    show_text = line.strip()[:chars_to_show]
                    draw.text((WIDTH//2, text_y), show_text, font=get_font(36), fill=WHITE, anchor="mm")
                    text_y += 45
        
        if t > 1.5:
            draw.text((WIDTH//2, text_y + 50), price, font=get_font(72, True), fill=GOLD, anchor="mm")
        
        if t > 2.0:
            button_y = text_y + 180 + (1 - min(1.0, (t - 2.0) * 2)) * 100
            draw.rectangle([WIDTH//2-180, button_y, WIDTH//2+180, button_y + 70], fill=GOLD, outline=None)
            draw.text((WIDTH//2, button_y + 35), ai_copy["call_to_action"], font=get_font(38, True), fill=BG, anchor="mm")
        
        if t > 2.5:
            draw.text((WIDTH//2, HEIGHT-80), f"📞 {phone} • SM INTERIORS • NAIROBI", font=get_font(36), fill=WHITE, anchor="mm")
        
        frames.append(np.array(canvas))
    
    # Add music and export
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

# Streamlit UI
st.title("🎯 SM Interiors - AI Ad Creator")
st.markdown("Create scroll-stopping TikTok ads with AI")

# API Key
groq_key = st.text_input("🔑 Groq API Key", type="password", help="Get free API key from https://console.groq.com")

# Initialize session state
if 'product_img' not in st.session_state:
    st.session_state.product_img = None
if 'ai_copy' not in st.session_state:
    st.session_state.ai_copy = None
if 'unsplash_image' not in st.session_state:
    st.session_state.unsplash_image = None

# Product Selection
st.subheader("🖼️ Choose Product Image")
product_option = st.radio("Image Source:", ["Use Unsplash Furniture", "Upload My Own Image"], horizontal=True)

if product_option == "Use Unsplash Furniture":
    col1, col2 = st.columns([2, 1])
    with col1:
        product_type = st.selectbox("Select Furniture Type", list(UNSPLASH_CATEGORIES.keys()))
    with col2:
        if st.button("🔄 Get Random Image", use_container_width=True):
            with st.spinner("Fetching from Unsplash..."):
                unsplash_img = get_unsplash_image(UNSPLASH_CATEGORIES[product_type])
                if unsplash_img:
                    st.session_state.unsplash_image = unsplash_img
                    st.session_state.product_img = unsplash_img
                    st.success("✅ Image loaded!")
                else:
                    st.error("❌ Failed to load image")
    
    if st.session_state.unsplash_image:
        st.image(st.session_state.unsplash_image, caption="Unsplash Product Image", use_column_width=True)

else:
    uploaded_file = st.file_uploader("Upload Product Image", type=["png","jpg","jpeg"])
    if uploaded_file:
        st.session_state.product_img = uploaded_file
        st.image(uploaded_file, caption="Your Product Image", use_column_width=True)

# Pricing & Contact
st.subheader("💰 Pricing & Contact Info")
col1, col2 = st.columns(2)
with col1:
    price = st.text_input("Price", "Ksh 12,500")
    phone = st.text_input("Phone Number", "0710 895 737")
with col2:
    price_range = st.selectbox("Price Range", ["Budget", "Medium", "Premium", "Luxury"])

# AI Copy Generation
st.subheader("🤖 AI Ad Copy Generation")
if st.session_state.product_img and groq_key:
    if st.button("✨ Generate AI Marketing Copy", type="secondary", use_container_width=True):
        with st.spinner("AI is creating compelling ad copy..."):
            product_type_name = product_type if product_option == "Use Unsplash Furniture" else "furniture"
            st.session_state.ai_copy = generate_ai_copy(product_type_name, groq_key, price_range)
            
            if st.session_state.ai_copy:
                st.success("✅ AI ad copy generated!")
                
                # Show the generated copy
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("Product Name", st.session_state.ai_copy["product_name"])
                    st.text_input("Headline", st.session_state.ai_copy["headline"])
                with col2:
                    st.text_input("Urgency Text", st.session_state.ai_copy["urgency_text"])
                    st.text_input("Discount Offer", st.session_state.ai_copy["discount_offer"])
                st.text_area("Description", st.session_state.ai_copy["description"], height=100)
                st.text_input("Call to Action", st.session_state.ai_copy["call_to_action"])
elif not groq_key:
    st.warning("⚠️ Please enter your Groq API key to generate AI copy")
elif not st.session_state.product_img:
    st.warning("⚠️ Please select or upload a product image first")

# Preview Section
if st.session_state.product_img and st.session_state.ai_copy:
    st.subheader("📱 Preview")
    
    if st.button("👀 Generate Preview", type="secondary", use_container_width=True):
        with st.spinner("Creating preview..."):
            preview = create_preview(st.session_state.product_img, st.session_state.ai_copy, price, phone)
            st.image(preview, caption="Ad Preview with Geometric Background", use_column_width=True)
            st.success("✅ Preview ready! Check the layout below.")

# Video Generation
if st.session_state.product_img and st.session_state.ai_copy:
    st.subheader("🎬 Video Generation")
    
    if st.button("🚀 CREATE TIKTOK VIDEO", type="primary", use_container_width=True):
        with st.status("Creating your TikTok video...", expanded=True) as status:
            status.write("📦 Processing product image...")
            status.write("🎨 Applying geometric background...")
            status.write("✍️ Adding AI-generated text...")
            status.write("🎵 Adding background music...")
            status.write("📹 Exporting video...")
            
            video_path = create_video(st.session_state.product_img, st.session_state.ai_copy, price, phone)
            
            if video_path:
                status.update(label="✅ Video created successfully!", state="complete")
                st.video(video_path)
                
                with open(video_path, "rb") as f:
                    st.download_button(
                        "📥 Download TikTok Video", 
                        f, 
                        "sm_interiors_tiktok_ad.mp4",
                        "video/mp4",
                        type="primary",
                        use_container_width=True
                    )
                # Clean up
                try:
                    os.unlink(video_path)
                except:
                    pass
            else:
                st.error("❌ Failed to create video")

# Instructions
with st.expander("📚 How to use this tool"):
    st.markdown("""
    1. **Get Groq API Key**: Visit [Groq Console](https://console.groq.com) for free API key
    2. **Choose Image Source**: Use Unsplash or upload your own product photo
    3. **Enter Pricing**: Set your price and contact information  
    4. **Generate AI Copy**: Let AI create compelling marketing text
    5. **Create Preview**: See how your ad will look
    6. **Generate Video**: Get ready-to-post TikTok ad

    **🎯 Tips for Best Results:**
    - Use clear, well-lit product photos
    - Unsplash provides professional furniture images
    - Geometric backgrounds keep focus on your products
    - AI creates Kenya-specific marketing copy
    """)

st.markdown("---")
st.markdown("**✨ SM INTERIORS - Professional Furniture Marketing**")