import streamlit as st
import io, requests, math, tempfile, time, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip
from rembg import remove

st.set_page_config(page_title="SM Interiors TikTok Maker", layout="centered", page_icon="🎯")

# ────────────────────────────── TIKTOK OPTIMIZED SETTINGS ──────────────────────────────
WIDTH, HEIGHT = 1080, 1920  # True TikTok vertical format
FPS = 30
DURATION = 12  # Slightly longer for better storytelling

BG = "#0A0A0A"  # Pure black for better contrast
GOLD = "#FFD700"  # Brighter gold for mobile
ACCENT = "#E8B4B8"  # Rose gold accent
WHITE = "#FFFFFF"

LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"
# More energetic TikTok-style music
MUSIC_URL = "https://cdn.pixabay.com/download/audio/2022/03/15/audio_7e7cbd2f52.mp3?filename=upbeat-ukulele-15144.mp3"

# ────────────────────────────── HELPERS ──────────────────────────────
def get_font(size, bold=False):
    try: 
        if bold:
            return ImageFont.truetype("arialbd.ttf", size)
        return ImageFont.truetype("arial.ttf", size)
    except: 
        return ImageFont.load_default()

def ease_out_bounce(t):
    if t < (1 / 2.75):
        return 7.5625 * t * t
    elif t < (2 / 2.75):
        t -= (1.5 / 2.75)
        return 7.5625 * t * t + 0.75
    elif t < (2.5 / 2.75):
        t -= (2.25 / 2.75)
        return 7.5625 * t * t + 0.9375
    else:
        t -= (2.625 / 2.75)
        return 7.5625 * t * t + 0.984375

# ────────────────────────────── TIKTOK OPTIMIZED APP ──────────────────────────────
st.title("🎯 SM Interiors - TikTok Ad Creator")
st.markdown("Create scroll-stopping videos optimized for TikTok!")

col1, col2 = st.columns(2)
with col1:
    product_img = st.file_uploader("📸 Product Image", type=["png","jpg","jpeg"], help="Use high-quality product photos")
    urgency_text = st.text_input("🔥 Urgency Text", "LIMITED STOCK!", help="Creates urgency for viewers")
    
with col2:
    price = st.text_input("💵 Price", "Ksh 12,500")
    discount = st.text_input("🎁 Discount Offer", "FREE DELIVERY + INSTALLATION!")
    tip_text = st.text_area("📝 Product Story", 
                          "Transform your space with this premium media console! ✨\n\n• Modern minimalist design\n• Premium wood finish\n• Smart storage solutions\n• Easy to assemble\n\nPerfect for Nairobi apartments! 🏠", 
                          height=120)

# Add TikTok-specific elements
col3, col4 = st.columns(2)
with col3:
    call_to_action = st.selectbox("🎯 Call to Action", 
                                ["Shop Now!", "Order Today!", "DM to Order", "Call Now!", "Visit Showroom"])
with col4:
    show_countdown = st.checkbox("⏰ Add Limited Time Offer", value=True)

if st.button("🚀 CREATE TIKTOK VIDEO", type="primary", use_container_width=True):
    with st.status("Creating your TikTok ad...", expanded=True) as status:
        # Process product image
        status.write("🔄 Processing product image...")
        product = None
        if product_img:
            raw = Image.open(product_img).convert("RGBA")
            clean = remove(raw.tobytes())
            product = Image.open(io.BytesIO(clean)).convert("RGBA").resize((800, 800), Image.LANCZOS)
        
        logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA").resize((280, 140), Image.LANCZOS)

        status.write("🎬 Creating TikTok-optimized frames...")
        frames = []

        # Modern geometric elements for TikTok
        shapes = [
            ("arc", (-150, 200, 450, 800), 0, 180, 20),
            ("arc", (WIDTH-500, 1400, WIDTH+150, 2100), 180, 360, 18),
            ("circle", (WIDTH-150, 300, WIDTH-50, 400), 15),
            ("circle", (100, 1600, 200, 1700), 12),
        ]

        for i in range(FPS * DURATION):
            t = i / (FPS * DURATION)
            canvas = Image.new("RGB", (WIDTH, HEIGHT), BG)
            draw = ImageDraw.Draw(canvas)

            # 1. Modern background elements (appear quickly)
            for idx, shape in enumerate(shapes):
                if t > idx * 0.05:  # Faster appearance
                    progress = min((t - idx*0.05) / 0.1, 1.0)
                    if shape[0] == "arc":
                        draw.arc(shape[1], start=shape[2], end=shape[2] + (shape[3]-shape[2])*progress, fill=GOLD, width=shape[4])
                    elif shape[0] == "circle":
                        draw.ellipse(shape[1], outline=GOLD, width=shape[2])

            # 2. Logo (appears early)
            if t > 0.2:
                alpha = min((t - 0.2)/0.2, 1.0)
                logo_layer = logo.copy()
                logo_layer.putalpha(int(255 * alpha))
                canvas.paste(logo_layer, (WIDTH-320, 60), logo_layer)

            # 3. URGENCY TEXT - Big and attention-grabbing
            if t > 0.5:
                urgency_alpha = min((t - 0.5)/0.3, 1.0)
                # Pulsing effect
                pulse = 1 + 0.1 * math.sin(t * 10)
                size = int(72 * pulse)
                try:
                    font = ImageFont.truetype("arialbd.ttf", size)
                except:
                    font = get_font(size)
                
                # Red background for urgency
                bbox = draw.textbbox((0,0), urgency_text, font=font)
                w, h = bbox[2]-bbox[0], bbox[3]-bbox[1]
                x = (WIDTH - w) // 2
                draw.rectangle([x-20, 50, x+w+20, 50+h+20], fill="#FF375F")
                draw.text((x, 60), urgency_text, font=font, fill=WHITE)

            # 4. PRODUCT REVEAL - Early and prominent
            if product and t > 1.0:
                scale = ease_out_bounce(min((t - 1.0)/0.6, 1.0))
                w = int(800 * scale)
                h = int(800 * scale)
                resized = product.resize((w, h), Image.LANCZOS)
                
                # Add subtle rotation and floating effect
                angle = math.sin(t * 8) * 2
                rotated = resized.rotate(angle, expand=False)
                
                x = (WIDTH - w) // 2
                y = int(HEIGHT * 0.4 - h//2 + math.sin(t*6)*15)
                canvas.paste(rotated, (x, y), rotated)

            # 5. PRODUCT STORY - Short, punchy lines
            if t > 2.0:
                chars_visible = int((t - 2.0) * 35)
                display_text = tip_text[:chars_visible]

                lines = []
                current_line = ""
                for char in display_text:
                    test_line = current_line + char
                    bbox = draw.textbbox((0,0), test_line, font=get_font(42))
                    if bbox[2] < WIDTH - 100 or char == '\n':
                        if char == '\n':
                            lines.append(current_line)
                            current_line = ""
                        else:
                            current_line = test_line
                    else:
                        lines.append(current_line)
                        current_line = char
                if current_line:
                    lines.append(current_line)

                y = HEIGHT * 0.75
                for i, line in enumerate(lines):
                    bbox = draw.textbbox((0,0), line, font=get_font(42))
                    w = bbox[2] - bbox[0]
                    x = (WIDTH - w) // 2
                    
                    # Text shadow for readability
                    draw.text((x+3, y+3), line, font=get_font(42), fill="#000000")
                    draw.text((x, y), line, font=get_font(42), fill=WHITE)
                    y += 50

            # 6. PRICE & DISCOUNT - Big and bold
            if t > 4.0:
                price_alpha = min((t - 4.0)/0.5, 1.0)
                
                # Price with strikethrough original
                original_price = "Ksh 18,000"
                draw.text((WIDTH-400, 300), original_price, font=get_font(48), fill="#888888")
                draw.line([(WIDTH-400, 325), (WIDTH-400+200, 325)], fill="#888888", width=3)
                
                # New price in gold
                draw.text((WIDTH-400, 350), price, font=get_font(64, bold=True), fill=GOLD)
                
                # Discount badge
                if discount:
                    draw.rectangle([WIDTH-450, 430, WIDTH-50, 500], fill=ACCENT, outline=GOLD, width=3)
                    draw.text((WIDTH-430, 440), discount, font=get_font(36), fill=WHITE)

            # 7. LIMITED TIME COUNTDOWN
            if show_countdown and t > 5.0:
                time_left = max(0, 7 - (t - 5.0) * 7)  # 7 second countdown
                minutes = int(time_left // 60)
                seconds = int(time_left % 60)
                countdown_text = f"⏰ OFFER ENDS IN: {seconds} SECONDS!"
                
                draw.rectangle([50, 400, 600, 470], fill="#FF375F", outline=WHITE, width=4)
                draw.text((70, 410), countdown_text, font=get_font(38, bold=True), fill=WHITE)

            # 8. CALL TO ACTION - Big button style
            if t > 6.0:
                cta_alpha = min((t - 6.0)/0.5, 1.0)
                # Pulsing CTA button
                pulse_size = 1 + 0.05 * math.sin(t * 8)
                
                draw.rectangle([WIDTH//2-200, HEIGHT-200, WIDTH//2+200, HEIGHT-120], 
                             fill="#FF375F", outline=GOLD, width=6)
                draw.text((WIDTH//2-180, HEIGHT-190), f"✨ {call_to_action} ✨", 
                         font=get_font(48, bold=True), fill=WHITE)

            # 9. CONTACT INFO - Always visible at bottom
            if t > 7.0:
                draw.text((50, HEIGHT-150), "📱 DM US ON INSTAGRAM", font=get_font(44), fill=GOLD)
                draw.text((50, HEIGHT-100), "📞 0710 895 737 • 📍 Nairobi", font=get_font(40), fill=WHITE)
                draw.text((50, HEIGHT-60), "🚚 FREE DELIVERY IN NAIROBI", font=get_font(36), fill=ACCENT)

            frames.append(np.array(canvas))

        status.write("🎵 Adding trending audio...")
        clip = ImageSequenceClip(frames, fps=FPS)
        
        # Download and add music
        audio_data = requests.get(MUSIC_URL).content
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(audio_data)
            audio = AudioFileClip(tmp.name).subclip(0, DURATION).audio_fadeout(2.0)
            final = clip.set_audio(audio)
            os.unlink(tmp.name)

        status.write("📹 Exporting TikTok video...")
        out_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
        final.write_videofile(out_path, codec="libx264", audio_codec="aac", fps=FPS, logger=None)

        status.update(label="✅ Your TikTok ad is ready!", state="complete")
        
        # Preview and download
        st.success("🎉 Video created successfully! Perfect for TikTok!")
        st.video(out_path)
        
        with open(out_path, "rb") as f:
            st.download_button(
                "📥 DOWNLOAD TIKTOK VIDEO", 
                f, 
                "sm_interiors_tiktok.mp4", 
                "video/mp4",
                type="primary",
                use_container_width=True
            )
        
        # TikTok tips
        st.markdown("---")
        st.markdown("**🎯 TikTok Posting Tips:**")
        st.markdown("""
        - **Caption**: Use engaging questions like "Which room needs this?" 
        - **Hashtags**: #NairobiFurniture #HomeDecorKenya #SMInteriors #KenyaHome #AffordableLuxury
        - **Post Time**: 7-9 PM when people are browsing
        - **Call to Action**: Ask viewers to comment or DM
        """)
        
        os.unlink(out_path)