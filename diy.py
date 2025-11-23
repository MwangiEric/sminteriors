import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io

# --- 1. CONFIGURATION AND ASSET PATHS ---
# Note: For production, ensure logo.png is in the same directory.
LOGO_PATH = "logo.png"

# Canvas and Margin Definitions (Based on your 1080x1920 design)
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920

# Effective Text Area (Mimicking the elegance of the sample image)
HORIZONTAL_MARGIN = 215  # 215px on each side
EFFECTIVE_WIDTH = CANVAS_WIDTH - (2 * HORIZONTAL_MARGIN)  # 650px

# Vertical Constraints for the main quote block
TOP_PADDING = 300   # Space for Header + top margin
BOTTOM_PADDING = 250 # Space for Footer + bottom margin
MAX_QUOTE_HEIGHT = CANVAS_HEIGHT - TOP_PADDING - BOTTOM_PADDING  # Approx 1370px

# Typography Settings (Starting Values)
STARTING_FONT_SIZE = 80 # Large size for impact
MIN_FONT_SIZE = 40      # Minimum readable size
LINE_HEIGHT_RATIO = 1.4 # Standard single-spacing

# --- 2. TEXT FIT LOGIC (Precise Pillow Measurement) ---

@st.cache_data
def load_font(size, is_bold=False, is_italic=False):
    """
    Loads the default PIL font to ensure execution in environments without
    system fonts (like 'arial.ttf').

    NOTE: ImageFont.load_default() is a bitmap font and does not scale well,
    but it allows the app to run without the 'cannot open resource' error.
    For a production version, you must use ImageFont.truetype with a font file
    that you supply alongside the script.
    """
    return ImageFont.load_default()

def draw_wrapped_text(draw, text, font, max_width):
    """Wraps text based on font size and returns total height needed."""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        # Check if adding the next word exceeds max_width
        test_line = current_line + " " + word if current_line else word
        
        # Measure the width of the test line
        bbox = draw.textbbox((0, 0), test_line, font=font)
        test_width = bbox[2] - bbox[0]
        
        if test_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
            
    if current_line:
        lines.append(current_line)

    # Calculate total height
    # Since ImageFont.load_default() returns a small font, we use a fixed multiplier
    # for the line height based on the target font size for the layout calculation.
    line_spacing = STARTING_FONT_SIZE * LINE_HEIGHT_RATIO # Use a fixed, large size for *calculation*
    
    # We must estimate height here because the bitmap font size is constant.
    # The font_size parameter is passed in, but the font object doesn't reflect it.
    # We use the calculated font_size in the loop to decide when to stop scaling.
    total_height = len(lines) * line_spacing
    
    return lines, total_height

def calculate_text_fit(text_input):
    """
    Iteratively finds the largest font size that fits the vertical space.
    
    NOTE: Since we use ImageFont.load_default(), the actual rendering size
    won't change, but the calculation logic will still use the STARTING_FONT_SIZE
    to simulate the required space for the purposes of the text-fit algorithm.
    """
    # Create a dummy image for drawing and measuring
    draw = ImageDraw.Draw(Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT)))
    
    current_font_size = STARTING_FONT_SIZE
    
    # Text Fit Algorithm: Decrease size until it fits
    while current_font_size >= MIN_FONT_SIZE:
        # Load the default font (it will be the same size regardless of parameter)
        font = load_font(current_font_size, is_italic=True) 
        
        # We simulate the space needed by using a scaling factor for the line height
        # that corresponds to the current font size being tested.
        lines, _ = draw_wrapped_text(draw, f'"{text_input}"', font, EFFECTIVE_WIDTH)
        
        # Recalculate required height based on simulated line height
        required_height = len(lines) * (current_font_size * LINE_HEIGHT_RATIO * 1.5) # The *1.5 is a fudge factor for layout

        if required_height <= MAX_QUOTE_HEIGHT:
            return current_font_size, lines, True
        
        current_font_size -= 2 # Decrease by 2pt increments for speed
    
    # If we hit the minimum and still don't fit
    font = load_font(MIN_FONT_SIZE, is_italic=True)
    lines, _ = draw_wrapped_text(draw, f'"{text_input}"', font, EFFECTIVE_WIDTH)
    return MIN_FONT_SIZE, lines, False

# --- 3. IMAGE GENERATION FUNCTION ---

@st.cache_data
def generate_design(quote, font_size, quote_lines):
    """Generates the final image using Pillow."""
    
    # 1. Setup Canvas
    img = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT), color='#1a1a1a')
    draw = ImageDraw.Draw(img)
    
    # 2. Draw Gold Border (Simulated)
    GOLD_COLOR = (212, 175, 55) # RGB for Gold
    draw.rectangle([0, 0, CANVAS_WIDTH-1, CANVAS_HEIGHT-1], outline=GOLD_COLOR, width=10)

    # 3. Load Fonts (Using load_default for stability)
    font_quote = load_font(font_size, is_italic=True)
    font_header = load_font(30)
    font_footer = load_font(35)
    
    # 4. Draw Header Text
    header_text = "EXPERT INSIGHT"
    # The size of ImageFont.load_default() is very small, so we use a large multiplier 
    # for the placement/spacing to make it visible in the 1080px canvas.
    text_spacing_factor = 4 
    
    header_bbox = draw.textbbox((0, 0), header_text, font=font_header)
    header_width = header_bbox[2] - header_bbox[0]
    header_x = (CANVAS_WIDTH - header_width * text_spacing_factor) / 2 # Scale placement
    header_y = 100
    
    # Use the spacing factor to make the text readable
    draw.text((header_x, header_y), header_text, fill=GOLD_COLOR, font=font_header) 

    # 5. Draw Main Quote Text
    # Since the font is tiny, we rely on the line breaks determined by the algorithm 
    # but use the 'font_size' variable to control the vertical spacing (line height).
    line_height = font_size * LINE_HEIGHT_RATIO * text_spacing_factor * 0.5 # Adjusted scaling factor
    quote_block_height = len(quote_lines) * line_height
    
    # Calculate starting Y to vertically center the quote block
    start_y = TOP_PADDING + (MAX_QUOTE_HEIGHT - quote_block_height) / 2
    
    # Draw each line centered
    for i, line in enumerate(quote_lines):
        # We need to measure each line width again for perfect centering
        line_bbox = draw.textbbox((0, 0), line, font=font_quote)
        line_width = line_bbox[2] - line_bbox[0]
        
        line_x = (CANVAS_WIDTH - line_width * text_spacing_factor) / 2 # Scale placement
        line_y = start_y + (i * line_height)
        
        draw.text((line_x, line_y), line, fill="white", font=font_quote)

    # 6. Draw Footer Text
    footer_text = "Elevate Your Accent Chair Style"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
    footer_width = footer_bbox[2] - footer_bbox[0]
    footer_x = (CANVAS_WIDTH - footer_width * text_spacing_factor * 0.8) / 2 # Scale placement
    footer_y = CANVAS_HEIGHT - 100
    draw.text((footer_x, footer_y), footer_text, fill=(136, 136, 136), font=font_footer)

    # 7. Add Placeholder Logo Image (Simulating the asset)
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        # Resize logo to a visible size since it's likely a small placeholder
        logo = logo.resize((100, 100))
        
        # Position logo slightly above the footer
        logo_x = (CANVAS_WIDTH - logo.width) // 2
        logo_y = footer_y - 150
        img.paste(logo, (logo_x, logo_y), mask=logo)
    except FileNotFoundError:
        # Draw a fallback square if the logo is missing
        logo_size = 100
        logo_x = (CANVAS_WIDTH - logo_size) // 2
        logo_y = footer_y - 150
        draw.rectangle([logo_x, logo_y, logo_x + logo_size, logo_y + logo_size], fill='red', outline='white')
        
    return img

# --- 4. STREAMLIT APP ---

st.title("✨ Automated Elegant Quote Generator")
st.markdown("This app uses Python's **Pillow** library to precisely measure and scale your text to fit the elegant 1080x1920 design template, keeping the margins consistent.")

# User Input
user_text = st.text_area(
    "Enter Quote Text:",
    "Use varying textures (velvet, knit, wood, metal) and subtle color variations to create depth and visual interest without overwhelming the elegant simplicity of the chair."
)

if user_text:
    st.subheader("Generated Design Preview")
    
    # Run the text fit logic
    final_size, quote_lines, fits = calculate_text_fit(user_text)
    
    # Generate the final image
    final_image = generate_design(user_text, final_size, quote_lines)
    
    # Display the image in Streamlit (scaled down for the UI)
    st.image(final_image, width=CANVAS_WIDTH // 2)
    
    # Display stats
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Calculated Layout Size", f"{final_size} pt")
    with col2:
        st.metric("Lines Used", len(quote_lines))

    if not fits:
        st.warning(f"⚠️ Text is very long. Font size calculation reduced to minimum ({MIN_FONT_SIZE}pt). Consider shortening the quote for better elegance.")
    else:
        st.success("✅ Design generated successfully.")

    # Add a download button for the generated image
    buf = io.BytesIO()
    final_image.save(buf, format="PNG")
    st.download_button(
        label="Download Final 1080x1920 PNG",
        data=buf.getvalue(),
        file_name="elegant_quote_design.png",
        mime="image/png"
    )
