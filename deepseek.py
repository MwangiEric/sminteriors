import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import requests
import json
import time
import tempfile
import os
from rembg import remove

# --- CONFIGURATION ---
GROQ_API_KEY = st.secrets.get('groq_key')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# Using a faster/more common model for quick response, as llama-4-scout might be fictional or slow.
# STICKING to the user's provided model for compliance, but noting the potential issue.
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct" 

# Design settings
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1350  # Better for social media
HORIZONTAL_MARGIN = 100
EFFECTIVE_WIDTH = CANVAS_WIDTH - (2 * HORIZONTAL_MARGIN)
TOP_PADDING = 200
BOTTOM_PADDING = 200
MAX_QUOTE_HEIGHT = CANVAS_HEIGHT - TOP_PADDING - BOTTOM_PADDING

# Colors and branding
GOLD = "#FFD700"
WHITE = "#FFFFFF"
DARK_BG = "#0A0A0A"
ACCENT_COLOR = "#E8B4B8" # Not currently used, but good to keep.

LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

# --- GROQ TEXT GENERATION (Smart Texts) ---

def generate_marketing_content(prompt_type, product_type="furniture", additional_context=""):
    """Generate different types of marketing content using Groq"""
    # Implementation remains largely the same, focusing on compliance and stability.
    if not GROQ_API_KEY:
        st.error("Groq API key not found. Please set 'groq_key' in secrets.")
        return None

    # Different prompts for different content types
    prompts = {
        "quote": f"""Create an elegant, inspiring 1-2 sentence quote about {product_type} and interior design. 
        Focus on: beauty, comfort, luxury, or transformation. Make it emotional and aspirational.
        Return ONLY the raw quote text, no quotes or attribution.""",
        
        "product_description": f"""Write compelling marketing copy for a {product_type} from SM Interiors Nairobi.
        Include: catchy product name, 2-3 benefits, and a call to action. Format as JSON with keys:
        product_name, description, benefits (array), call_to_action""",
        
        "urgency_text": f"""Create short, urgent marketing text for {product_type} promotions.
        Include limited time offers, scarcity, and excitement. Return 2-3 options as array."""
    }
    
    # Using the quote prompt as the default fallback
    user_prompt = prompts.get(prompt_type, prompts["quote"])

    system_prompt = "You are a professional interior design copywriter for SM Interiors Kenya. Create compelling, elegant marketing content."
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 200
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(GROQ_URL, headers=headers, data=json.dumps(payload), timeout=30)
            response.raise_for_status()
            
            data = response.json()
            generated_text = data['choices'][0]['message']['content'].strip()
            
            # Simple cleanup for quote generation
            if prompt_type == "quote":
                 if generated_text.startswith('"') and generated_text.endswith('"'):
                    generated_text = generated_text[1:-1]
            
            return generated_text
            
        except requests.exceptions.HTTPError as e:
            st.error(f"HTTP Error: {e}. Check API key and model name.")
            return None
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time) # Exponential backoff
            else:
                st.error(f"Failed to connect to Groq API after {max_retries} attempts: {e}")
                return None
        except (KeyError, json.JSONDecodeError):
            st.error("Error parsing Groq response. Check if model returned valid JSON for description requests.")
            return None
    return None


# --- DESIGN FUNCTIONS (Smart Layout) ---

def create_elegant_background():
    """Create a sophisticated background with subtle elements and a radial gradient."""
    img = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT), color=DARK_BG)
    draw = ImageDraw.Draw(img)
    
    # Add subtle gradient (Vignette effect)
    center_x, center_y = CANVAS_WIDTH // 2, CANVAS_HEIGHT // 2
    max_dist = (center_x**2 + center_y**2)**0.5
    
    # Create a black overlay with a hole in the center
    overlay = Image.new('L', (CANVAS_WIDTH, CANVAS_HEIGHT), 0)
    overlay_draw = ImageDraw.Draw(overlay)
    
    # Draw a soft, large circle to simulate radial light falloff
    gradient_radius = max_dist * 0.9
    for r in range(int(gradient_radius), 0, -2):
        alpha = int(255 * (1 - (r / gradient_radius))) # Fades out from center
        if alpha > 0:
            overlay_draw.ellipse(
                [center_x - r, center_y - r, center_x + r, center_y + r], 
                fill=alpha
            )
    
    # Apply a subtle blur to the radial gradient for smoothness
    blurred_overlay = overlay.filter(ImageFilter.GaussianBlur(radius=50))
    
    # Blend the base image with the blurred light map
    # The mode 'L' is inverted here, making the center lighter.
    img_with_vignette = Image.composite(
        img.point(lambda p: int(p * 1.5) if p < 200 else 255), # Slightly brighten dark areas
        img,
        blurred_overlay.point(lambda p: 255 - p) # Use inverse (dark in center, light on edges)
    )
    img = img_with_vignette
    draw = ImageDraw.Draw(img)

    # Add geometric accents (kept from previous version)
    shapes = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    shapes_draw = ImageDraw.Draw(shapes)
    
    # Gold accent bars
    shapes_draw.rectangle([0, 0, CANVAS_WIDTH, 4], fill=GOLD)
    shapes_draw.rectangle([0, CANVAS_HEIGHT-4, CANVAS_WIDTH, CANVAS_HEIGHT], fill=GOLD)
    
    # Subtle corner accents
    corner_size = 80
    shapes_draw.rectangle([0, 0, corner_size, 4], fill=GOLD)
    shapes_draw.rectangle([0, 0, 4, corner_size], fill=GOLD)
    shapes_draw.rectangle([CANVAS_WIDTH-corner_size, 0, CANVAS_WIDTH, 4], fill=GOLD)
    shapes_draw.rectangle([CANVAS_WIDTH-4, 0, CANVAS_WIDTH, corner_size], fill=GOLD)
    shapes_draw.rectangle([0, CANVAS_HEIGHT-4, corner_size, CANVAS_HEIGHT], fill=GOLD)
    shapes_draw.rectangle([0, CANVAS_HEIGHT-corner_size, 4, CANVAS_HEIGHT], fill=GOLD)
    shapes_draw.rectangle([CANVAS_WIDTH-corner_size, CANVAS_HEIGHT-4, CANVAS_WIDTH, CANVAS_HEIGHT], fill=GOLD)
    shapes_draw.rectangle([CANVAS_WIDTH-4, CANVAS_HEIGHT-corner_size, CANVAS_WIDTH, CANVAS_HEIGHT], fill=GOLD)
    
    img.paste(shapes, (0, 0), shapes)
    return img

def get_pro_font(size, bold=False):
    """Get professional font with fallbacks"""
    try:
        # Attempt to load a specific font if available
        if bold:
            return ImageFont.truetype("arialbd.ttf", size)
        return ImageFont.truetype("arial.ttf", size)
    except:
        # Fallback to default, using a scaled size since load_default sizes are fixed
        # We rely on the font_size logic in calculate_optimal_font_size to manage this.
        return ImageFont.load_default(size)

def calculate_optimal_font_size(text, max_width, max_height, initial_size=80, min_size=30):
    """Calculate the best font size to fit text in given space"""
    temp_img = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT))
    temp_draw = ImageDraw.Draw(temp_img)
    
    font_size = initial_size
    line_spacing_factor = 1.4 # Line height ratio
    
    while font_size >= min_size:
        font = get_pro_font(font_size)
        
        # Smart Line wrapping
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            # Use textlength for better estimation
            test_width = temp_draw.textlength(test_line, font=font)
            
            if test_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Calculate total height
        # Use font_size * line_spacing_factor for vertical spacing estimation
        line_height = int(font_size * line_spacing_factor)
        total_height = len(lines) * line_height
        
        if total_height <= max_height:
            return font_size, lines
        
        font_size -= 2
    
    # If we get here, use minimum size
    # Recalculate lines for min size
    font = get_pro_font(min_size)
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        test_width = temp_draw.textlength(test_line, font=font)
        
        if test_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return min_size, lines

def create_quote_design(quote_text, product_img=None, product_name="", price=""):
    """Create elegant quote design with optional product elements, using smart left-aligned layout."""
    img = create_elegant_background()
    draw = ImageDraw.Draw(img)
    
    # Calculate optimal font size for quote
    max_text_width = EFFECTIVE_WIDTH # Use full effective width for better space management
    max_text_height = MAX_QUOTE_HEIGHT - 200
    
    font_size, quote_lines = calculate_optimal_font_size(
        quote_text, max_text_width, max_text_height
    )
    
    # Header (Centered)
    header_font = get_pro_font(36, True) # Slightly bigger header
    header_text = "SM INTERIORS"
    header_bbox = draw.textbbox((0, 0), header_text, font=header_font)
    header_width = header_bbox[2] - header_bbox[0]
    draw.text(
        ((CANVAS_WIDTH - header_width) // 2, TOP_PADDING - 100), # Higher position
        header_text, fill=GOLD, font=header_font
    )
    
    # Draw quote lines (SMART LAYOUT: Left-Aligned within margin)
    quote_font = get_pro_font(font_size)
    line_height = int(font_size * 1.4)
    total_quote_height = len(quote_lines) * line_height
    # Center the quote block vertically within the allowed space
    start_y = TOP_PADDING + (MAX_QUOTE_HEIGHT - total_quote_height) // 2
    
    for i, line in enumerate(quote_lines):
        # Left-aligned X coordinate is the HORIZONTAL_MARGIN
        x = HORIZONTAL_MARGIN 
        y = start_y + (i * line_height)
        draw.text((x, y), line, fill=WHITE, font=quote_font)

    # Draw an underline accent below the last quote line
    last_line_width = draw.textlength(quote_lines[-1], font=quote_font)
    draw.line(
        [
            HORIZONTAL_MARGIN, 
            start_y + total_quote_height + 10,
            HORIZONTAL_MARGIN + last_line_width + 50, # Extend slightly
            start_y + total_quote_height + 10
        ], 
        fill=GOLD, 
        width=5
    )
    
    # Add product image if provided (SMART LAYOUT: Bottom-Center placement)
    if product_img:
        try:
            # Process product image
            if hasattr(product_img, 'tobytes'):
                product = product_img
            else:
                product = Image.open(product_img).convert("RGBA")
            
            # Remove background
            cleaned = remove(product.tobytes())
            product_display = Image.open(io.BytesIO(cleaned)).convert("RGBA")
            product_size = 350 # Slightly larger
            product_display = product_display.resize((product_size, product_size), Image.LANCZOS)
            
            # Position product at bottom
            product_x = (CANVAS_WIDTH - product_size) // 2
            product_y = CANVAS_HEIGHT - 450 # Higher placement for prominence
            img.paste(product_display, (product_x, product_y), product_display)
            
            # Add product name and price below image
            if product_name or price:
                info_font = get_pro_font(28, True) # Larger font
                info_text = f"{product_name} • {price}" if product_name and price else product_name or price
                info_bbox = draw.textbbox((0, 0), info_text, font=info_font)
                info_width = info_bbox[2] - info_bbox[0]
                draw.text(
                    ((CANVAS_WIDTH - info_width) // 2, product_y + product_size + 20),
                    info_text, fill=GOLD, font=info_font
                )
        except Exception as e:
            st.warning(f"Could not process product image: {e}")
    
    # Footer with branding
    footer_font = get_pro_font(20)
    footer_text = "SM INTERIORS • NAIROBI • www.sminteriors.co.ke"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
    footer_width = footer_bbox[2] - footer_bbox[0]
    draw.text(
        ((CANVAS_WIDTH - footer_width) // 2, CANVAS_HEIGHT - 60),
        footer_text, fill=WHITE, font=footer_font
    )
    
    # Add logo (Top Right)
    try:
        logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
        logo = logo.resize((120, 60), Image.LANCZOS)
        img.paste(logo, (CANVAS_WIDTH - 140, 40), logo)
    except:
        pass
    
    return img, font_size, len(quote_lines)

def create_marketing_design(product_img, product_name, description, price, discount, contact_info):
    """Create product-focused marketing design with smart text alignment for description."""
    img = create_elegant_background()
    draw = ImageDraw.Draw(img)
    
    # Header with discount
    if discount:
        discount_font = get_pro_font(42, True)
        discount_bbox = draw.textbbox((0, 0), discount, font=discount_font)
        discount_width = discount_bbox[2] - discount_bbox[0]
        draw.text(
            ((CANVAS_WIDTH - discount_width) // 2, 80),
            discount, fill=GOLD, font=discount_font
        )
    
    # Product name
    name_font = get_pro_font(36, True)
    name_bbox = draw.textbbox((0, 0), product_name, font=name_font)
    name_width = name_bbox[2] - name_bbox[0]
    draw.text(
        ((CANVAS_WIDTH - name_width) // 2, 150),
        product_name, fill=WHITE, font=name_font
    )
    
    # Product image
    if product_img:
        try:
            if hasattr(product_img, 'tobytes'):
                product = product_img
            else:
                product = Image.open(product_img).convert("RGBA")
            
            cleaned = remove(product.tobytes())
            product_display = Image.open(io.BytesIO(cleaned)).convert("RGBA")
            product_size = 500
            product_display = product_display.resize((product_size, product_size), Image.LANCZOS)
            
            product_x = (CANVAS_WIDTH - product_size) // 2
            product_y = 220
            img.paste(product_display, (product_x, product_y), product_display)
            
            # Description below image (SMART LAYOUT: Left-aligned for readability)
            desc_font = get_pro_font(24) # Slightly larger font
            desc_lines = []
            words = description.split()
            current_line = []
            
            max_desc_width = EFFECTIVE_WIDTH # Ensure this matches the width used for wrapping
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=desc_font)
                test_width = bbox[2] - bbox[0]
                
                if test_width <= max_desc_width:
                    current_line.append(word)
                else:
                    if current_line:
                        desc_lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                desc_lines.append(' '.join(current_line))
            
            desc_start_y = product_y + product_size + 30
            line_spacing = 38
            for i, line in enumerate(desc_lines):
                # Draw text left-aligned from the margin
                draw.text(
                    (HORIZONTAL_MARGIN, desc_start_y + (i * line_spacing)),
                    line, fill=WHITE, font=desc_font
                )
                
            # Add a vertical gold line accent to the left of the description block
            vertical_line_x = HORIZONTAL_MARGIN - 20
            draw.line(
                [
                    vertical_line_x, 
                    desc_start_y,
                    vertical_line_x, 
                    desc_start_y + len(desc_lines) * line_spacing
                ],
                fill=GOLD,
                width=5
            )
            
        except Exception as e:
            st.warning(f"Could not process product image: {e}")
    
    # Price and contact (Centered)
    price_font = get_pro_font(32, True)
    price_text = f"Only {price}"
    price_bbox = draw.textbbox((0, 0), price_text, font=price_font)
    price_width = price_bbox[2] - price_bbox[0]
    draw.text(
        ((CANVAS_WIDTH - price_width) // 2, CANVAS_HEIGHT - 120),
        price_text, fill=GOLD, font=price_font
    )
    
    contact_font = get_pro_font(20)
    contact_bbox = draw.textbbox((0, 0), contact_info, font=contact_font)
    contact_width = contact_bbox[2] - contact_bbox[0]
    draw.text(
        ((CANVAS_WIDTH - contact_width) // 2, CANVAS_HEIGHT - 70),
        contact_info, fill=WHITE, font=contact_font
    )
    
    # Add logo (Top Left)
    try:
        logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
        logo = logo.resize((100, 50), Image.LANCZOS)
        img.paste(logo, (40, 40), logo)
    except:
        pass
    
    return img

# --- STREAMLIT APP ---

st.set_page_config(page_title="SM Interiors - AI Design Studio", layout="wide")

st.title("🎨 SM Interiors - AI Design Studio")
st.markdown("Create elegant marketing designs with AI-powered content and **smart layouts**.")

# Initialize session state
if 'generated_quote' not in st.session_state:
    st.session_state.generated_quote = None
if 'generated_design' not in st.session_state:
    st.session_state.generated_design = None

# Sidebar for design type selection
design_type = st.sidebar.selectbox(
    "Choose Design Type",
    ["Inspirational Quote", "Product Marketing", "Combined Design"]
)

# Main content based on design type
if design_type == "Inspirational Quote":
    st.subheader("✨ Create Inspirational Quote Design")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        quote_topic = st.text_input(
            "Quote Topic",
            "The beauty of modern interior design",
            help="What should the quote be about?"
        )
        
        # Optional product info for quote design
        with st.expander("Add Product Info (Optional)"):
            product_upload = st.file_uploader("Product Image", type=["png","jpg","jpeg"], key="quote_product")
            product_name_quote = st.text_input("Product Name", "Modern Luxury Sofa")
            product_price_quote = st.text_input("Price", "Ksh 25,999")
    
    with col2:
        if st.button("🎨 Generate Quote Design", use_container_width=True):
            with st.spinner("Creating elegant quote design..."):
                # Generate AI quote
                quote = generate_marketing_content("quote", quote_topic) # Use topic in generation
                if quote:
                    st.session_state.generated_quote = quote
                    
                    # Process product image if provided
                    product_img = None
                    if product_upload:
                        product_img = Image.open(product_upload)
                    
                    # Create design
                    design, font_size, line_count = create_quote_design(
                        quote, 
                        product_img, 
                        product_name_quote, 
                        product_price_quote
                    )
                    
                    st.session_state.generated_design = design
                    st.session_state.design_stats = {
                        "font_size": font_size,
                        "lines": line_count,
                        "type": "quote"
                    }
                    
                    st.success("✅ Design created successfully!")

elif design_type == "Product Marketing":
    st.subheader("📦 Create Product Marketing Design")
    
    col1, col2 = st.columns(2)
    
    with col1:
        product_upload = st.file_uploader("Product Image", type=["png","jpg","jpeg"], key="marketing_product")
        product_name = st.text_input("Product Name", "Modern Luxury Sofa")
        
        # SMART TEXT: Option to generate description
        generate_desc = st.checkbox("Generate Description with AI", value=False)
        if generate_desc:
            product_type_for_ai = st.text_input("Product Type for AI (e.g., 'velvet armchair')", product_name, key="ai_product_type")
            if st.button("Generate Marketing Text"):
                with st.spinner("Generating compelling marketing copy..."):
                    # The generate_marketing_content function is designed to return JSON for this,
                    # but since the app only uses a text area for input, we'll try to extract the main description part.
                    ai_output = generate_marketing_content("product_description", product_type_for_ai)
                    if ai_output:
                        try:
                            parsed_json = json.loads(ai_output)
                            desc = parsed_json.get('description', ai_output)
                            benefits = "\n• " + "\n• ".join(parsed_json.get('benefits', []))
                            call_to_action = parsed_json.get('call_to_action', '')
                            full_text = f"{desc}\n\nKey Features:{benefits}\n\n{call_to_action}"
                            st.session_state.product_description_ai = full_text
                        except:
                            # Fallback if Groq doesn't return clean JSON
                            st.session_state.product_description_ai = ai_output
                    st.success("Copy Generated!")
            product_description = st.text_area("Description", st.session_state.get('product_description_ai', "Premium quality sofa with elegant design and comfortable seating"), key="desc_area_ai")
        else:
            product_description = st.text_area("Description", "Premium quality sofa with elegant design and comfortable seating", key="desc_area_manual")
        
    with col2:
        product_price = st.text_input("Price", "Ksh 25,999")
        discount_offer = st.text_input("Discount Offer", "50% OFF + Free Delivery")
        contact_info = st.text_input("Contact Info", "Call: 0710 895 737 • Nairobi")
        
        if st.button("🚀 Generate Marketing Design", use_container_width=True):
            with st.spinner("Creating professional marketing design..."):
                product_img = None
                if product_upload:
                    product_img = Image.open(product_upload)
                
                design = create_marketing_design(
                    product_img,
                    product_name,
                    product_description,
                    product_price,
                    discount_offer,
                    contact_info
                )
                
                st.session_state.generated_design = design
                st.session_state.design_stats = {"type": "marketing"}
                st.success("✅ Marketing design created!")

elif design_type == "Combined Design":
    st.subheader("🌟 Create Combined Quote + Product Design")
    
    st.info("This creates a design with both an inspirational quote and product information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        quote_topic = st.text_input("Quote Topic", "Transform your living space", key="combined_quote")
        product_upload = st.file_uploader("Product Image", type=["png","jpg","jpeg"], key="combined_product")
        
    with col2:
        product_name = st.text_input("Product Name", "Designer Furniture Collection")
        product_price = st.text_input("Price", "From Ksh 15,999")
        
        if st.button("🎭 Generate Combined Design", use_container_width=True):
            with st.spinner("Creating combined design..."):
                # Generate AI quote
                quote = generate_marketing_content("quote", quote_topic)
                if quote:
                    st.session_state.generated_quote = quote
                    
                    product_img = None
                    if product_upload:
                        product_img = Image.open(product_upload)
                    
                    design, font_size, line_count = create_quote_design(
                        quote,
                        product_img,
                        product_name,
                        product_price
                    )
                    
                    st.session_state.generated_design = design
                    st.session_state.design_stats = {
                        "font_size": font_size,
                        "lines": line_count,
                        "type": "combined"
                    }
                    st.success("✅ Combined design created!")

# Display generated content and design
if st.session_state.generated_design:
    st.markdown("---")
    st.subheader("📝 Generated Content")
    if st.session_state.generated_quote:
        st.markdown(f"**Quote:** \"{st.session_state.generated_quote}\"")

    st.subheader("🎨 Your Design")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.image(st.session_state.generated_design, use_column_width=True, caption="Your Professional Design")
    
    with col2:
        if st.session_state.get('design_stats'):
            stats = st.session_state.design_stats
            if stats['type'] in ['quote', 'combined']:
                st.metric("Font Size", f"{stats['font_size']}pt")
                st.metric("Lines Used", stats['lines'])
            st.metric("Design Type", stats['type'].title())
        
        # Download button
        buf = io.BytesIO()
        st.session_state.generated_design.save(buf, format="PNG", quality=95)
        
        st.download_button(
            label="📥 Download Design",
            data=buf.getvalue(),
            file_name="sm_interiors_design.png",
            mime="image/png",
            use_container_width=True
        )

# Features section
st.markdown("---")
st.subheader("🚀 Design Features")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **🤖 AI Powered**
    - Intelligent quote generation
    - Professional copywriting
    - Context-aware content
    - Multiple content types
    """)

with col2:
    st.markdown("""
    **🎨 Professional Design**
    - Elegant gold & black theme
    - **Smart Left-Aligned Layout**
    - **Subtle Radial Background**
    - Product image processing
    """)

with col3:
    st.markdown("""
    **📱 Multi-Purpose**
    - Social media ready
    - Marketing materials
    - Inspirational content
    - Brand consistency
    """)

# Usage tips
with st.expander("💡 Pro Tips"):
    st.markdown("""
    - **For quotes**: Use emotional, aspirational topics about home and design
    - **For products**: Use high-quality images with plain backgrounds
    - **Combined designs**: Work best when product complements the quote theme
    - **Download**: All designs are high-resolution PNG suitable for printing
    - **Branding**: All designs include SM Interiors logo and contact information
    """)
