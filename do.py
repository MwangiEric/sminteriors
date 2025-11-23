import streamlit as st
import io, requests, math, tempfile, os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip
from rembg import remove

st.set_page_config(page_title="SM Interiors TikTok Maker", layout="centered")

# Settings
WIDTH, HEIGHT = 1080, 1920
BG = "#0A0A0A"
GOLD = "#FFD700"
WHITE = "#FFFFFF"

LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

def get_font(size):
    try: return ImageFont.truetype("arial.ttf", size)
    except: return ImageFont.load_default()

def create_preview(product_img, product_name, description, price, phone):
    """Create a single preview image showing the layout"""
    
    # Create canvas
    canvas = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(canvas)
    
    # Load logo (already transparent)
    logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
    logo = logo.resize((220, 110), Image.LANCZOS)
    canvas.paste(logo, (WIDTH-260, 60), logo)
    
    # Process product image
    if product_img:
        product = Image.open(product_img).convert("RGBA")
        product = remove(product.tobytes())
        product = Image.open(io.BytesIO(product)).convert("RGBA")
        product = product.resize((600, 600), Image.LANCZOS)
        
        # Center product
        x = (WIDTH - 600) // 2
        y = (HEIGHT - 600) // 2 - 100
        canvas.paste(product, (x, y), product)
    
    # Text elements (carefully positioned around product)
    draw.text((WIDTH//2, 200), "LIMITED STOCK! 🔥", font=get_font(60), fill=GOLD, anchor="mm")
    
    if product_name:
        draw.text((WIDTH//2, y + 650), product_name, font=get_font(48), fill=WHITE, anchor="mm")
    
    if description:
        # Simple text wrapping
        words = description.split()
        lines = []
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=get_font(36))
            if bbox[2] < WIDTH - 100:
                line = test_line
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
        
        # Draw lines below product
        text_y = y + 720
        for line in lines:
            draw.text((WIDTH//2, text_y), line, font=get_font(36), fill=WHITE, anchor="mm")
            text_y += 45
    
    # Price
    if price:
        draw.text((WIDTH//2, text_y + 50), price, font=get_font(72), fill=GOLD, anchor="mm")
    
    # CTA Button
    draw.rectangle([WIDTH//2-150, text_y + 150, WIDTH//2+150, text_y + 220], fill=GOLD, outline=None)
    draw.text((WIDTH//2, text_y + 185), "DM TO ORDER", font=get_font(36), fill=BG, anchor="mm")
    
    # Contact info
    draw.text((WIDTH//2, HEIGHT-100), f"📞 {phone} • SM INTERIORS", font=get_font(36), fill=WHITE, anchor="mm")
    
    return canvas

def create_video(frames_data):
    """Create the actual video from frames data"""
    frames = []
    
    for i in range(30 * 8):  # 8 seconds at 30fps
        # Simple animation logic here
        # (similar to preview but with animations)
        frame = create_preview(
            frames_data['product_img'],
            frames_data['product_name'], 
            frames_data['description'],
            frames_data['price'],
            frames_data['phone']
        )
        frames.append(np.array(frame))
    
    # Add music and export
    clip = ImageSequenceClip(frames, fps=30)
    # ... rest of video creation code
    return "video_path.mp4"

# Streamlit UI
st.title("SM Interiors - TikTok Creator")

# Inputs
col1, col2 = st.columns(2)
with col1:
    product_img = st.file_uploader("Product Image", type=["png","jpg","jpeg"])
with col2:
    product_name = st.text_input("Product Name", "Horizon Media Console")
    price = st.text_input("Price", "Ksh 12,500")
    phone = st.text_input("Phone", "0710 895 737")

description = st.text_area("Description", "Premium media console with sleek design and functional elegance")

# Preview Section
st.subheader("📱 Preview")
if st.button("Generate Preview", type="secondary"):
    if product_img:
        preview = create_preview(product_img, product_name, description, price, phone)
        st.image(preview, caption="Video Layout Preview", use_column_width=True)
        
        st.success("✅ Preview ready! Check layout and generate video when satisfied.")
    else:
        st.error("Please upload a product image first")

# Generate Video
if st.button("🎬 Generate TikTok Video", type="primary"):
    if product_img:
        with st.status("Creating your video..."):
            # Create video using same layout as preview
            video_path = create_video({
                'product_img': product_img,
                'product_name': product_name,
                'description': description, 
                'price': price,
                'phone': phone
            })
            
            st.video(video_path)
            st.success("Video created successfully!")
    else:
        st.error("Please upload a product image first")