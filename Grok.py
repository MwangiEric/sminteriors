# app.py — Streamlit Pro Layout Editor (Drag + Sliders + Upload + Hotlink)
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image, ImageDraw, ImageFont
import io
import platform
import requests # Added requests for fetching URLs

st.set_page_config(page_title="SM Interiors Layout Editor", layout="centered")
st.title("SM Interiors — Pro Layout Editor")
st.caption("Drag • Resize • Upload • Real-time 1080×1920 preview")

# --- Function to get a cross-platform modern font path ---
def get_modern_font(size):
    """Attempts to find a modern system font, falls back to default."""
    try:
        # Common modern system font name (Windows, Mac, Linux)
        font_name = "Verdana.ttf" if platform.system() == "Windows" else "Verdana"
        font = ImageFont.truetype(font_name, size)
    except IOError:
        # Fallback to default PIL font if specific TTF isn't found
        font = ImageFont.load_default()
        # st.warning(f"Could not find {font_name} font file locally. Using default font.") # Optional warning
    return font

# --- Initialize session state ---
if "elements" not in st.session_state:
    st.session_state.elements = {
        "sofa":  {"x": 540, "y": 900, "w": 860, "h": 860, "img": None},
        "logo":  {"x": 100, "y": 100, "w": 200, "h": 100, "img": None},
        "hook":  {"x": 540, "y": 300, "text": "This Sold Out in 24 Hours", "size": 140},
        "price": {"x": 540, "y": 1460,"text": "Ksh 94,900", "size": 160},
        "cta":   {"x": 540, "y": 1700,"text": "DM 0710 895 737", "size": 120},
    }
# Initialize selected element for moving
if "selected_element" not in st.session_state:
    st.session_state.selected_element = "sofa"
# Initialize dynamic background session state
if "dynamic_background" not in st.session_state:
    st.session_state.dynamic_background = None # Starts with no dynamic background

el = st.session_state.elements

# --- Uploads and Hotlink Input ---
col1, col2 = st.columns(2)
with col1:
    sofa_file = st.file_uploader("Upload Sofa Photo", type=["png","jpg","jpeg"])
    if sofa_file:
        img = Image.open(sofa_file).convert("RGBA")
        img = img.resize((el["sofa"]["w"], el["sofa"]["h"]), Image.LANCZOS)
        el["sofa"]["img"] = img
with col2:
    logo_file = st.file_uploader("Upload Logo", type=["png","jpg","jpeg"])
    if logo_file:
        img = Image.open(logo_file).convert("RGBA")
        img = img.resize((el["logo"]["w"], el["logo"]["h"]), Image.LANCZOS)
        el["logo"]["img"] = img

# Hotlink input field
st.subheader("Or use a Public Image URL for Background")
image_url_input = st.text_input("Paste Public Image URL here:", help="Must be a direct link to a JPG/PNG file (e.g., https://example.com/image.jpg)")

if st.button("Load Background from URL"):
    if image_url_input:
        with st.spinner(f"Loading image from URL..."):
            try:
                response = requests.get(image_url_input)
                response.raise_for_status() # Check for bad responses
                pil_bg_image = Image.open(io.BytesIO(response.content)).convert("RGB")
                st.session_state.dynamic_background = pil_bg_image
                st.success("Background image loaded from URL successfully! The preview below has updated.")
                # st.experimental_rerun() # Not strictly necessary here as the script naturally reruns
            except requests.exceptions.RequestException as e:
                st.error(f"Error loading image from URL: {e}. Check the URL and ensure it's a direct link to an image file.")


# --- Sliders (Moved to sidebar for cleaner main layout) ---
st.sidebar.subheader("Adjust Element Sizes")
with st.sidebar:
    st.markdown("### Image Dimensions (px)")
    el["sofa"]["w"] = st.slider("Sofa Width", 400, 1000, el["sofa"]["w"], 10)
    el["sofa"]["h"] = st.slider("Sofa Height", 400, 1400, el["sofa"]["h"], 10)
    if el["sofa"]["img"]:
        el["sofa"]["img"] = el["sofa"]["img"].resize((el["sofa"]["w"], el["sofa"]["h"]), Image.LANCZOS)
    
    el["logo"]["w"] = st.slider("Logo Width", 100, 400, el["logo"]["w"], 10)
    el["logo"]["h"] = st.slider("Logo Height", 50, 300, el["logo"]["h"], 10)
    if el["logo"]["img"]:
        el["logo"]["img"] = el["logo"]["img"].resize((el["logo"]["w"], el["logo"]["h"]), Image.LANCZOS)
    
    st.markdown("### Font Sizes (pt)")
    el["hook"]["size"] = st.slider("Hook Size", 80, 250, el["hook"]["size"])
    el["price"]["size"] = st.slider("Price Size", 100, 300, el["price"]["size"])
    el["cta"]["size"] = st.slider("CTA Size", 80, 200, el["cta"]["size"])


# --- Canvas with drag functionality and element selection ---
st.subheader("Drag and Move Elements")
selected_name = st.radio("Select an element to move:", 
                         ["sofa", "logo", "hook", "price", "cta"], 
                         key="selected_element_radio", 
                         horizontal=True)

canvas_result = st_canvas(
    fill_color="rgba(255, 215, 0, 0.3)", 
    stroke_width=0,
    background_color="#0F0A05",
    background_image=None, # The background is rendered with PIL below, not in the canvas component
    update_streamlit=True,
    height=960, # Display size for user interaction
    width=540,  # Display size for user interaction
    drawing_mode="transform", 
    key="canvas",
)

# --- Draw everything onto a high-res background (1080x1920) ---

# Use the dynamic background if available, otherwise use default color
if "dynamic_background" in st.session_state and st.session_state.dynamic_background is not None:
    # Resize the dynamic image to fit your canvas resolution
    bg = st.session_state.dynamic_background.resize((1080, 1920), Image.LANCZOS)
else:
    # Fallback to the default color background if none is selected/loaded
    bg = Image.new("RGB", (1080, 1920), (15,10,5))

draw = ImageDraw.Draw(bg)

# Gold rings (These are drawing over the background image)
for r in [500, 750, 1000]:
    draw.ellipse([540-r, 960-r, 540+r, 960+r], outline=(255,215,0), width=6)

# Sofa
if el["sofa"]["img"]:
    x = el["sofa"]["x"] - el["sofa"]["w"]//2
    y = el["sofa"]["y"] - el["sofa"]["h"]//2
    bg.paste(el["sofa"]["img"], (x, y), el["sofa"]["img"])

# Logo
if el["logo"]["img"]:
    bg.paste(el["logo"]["img"], (el["logo"]["x"], el["logo"]["y"]), el["logo"]["img"])

# Text (Using the modern Verdana font)
for name in ["hook", "price", "cta"]:
    text = el[name]["text"]
    size = el[name]["size"]
    font = get_modern_font(size)
    
    # Calculate text position (centered X, centered Y)
    # Use textbbox for accurate measurement
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = el[name]["x"] - w//2
    y = el[name]["y"] - h//2 
    
    draw.text((x, y), text, fill=(255,255,255), font=font,
              stroke_width=4, stroke_fill=(0,0,0))


# --- Display the Final Image Preview ---
st.image(bg.resize((540,960)), caption="Live 1080x1920 Output (Preview Scaled to 540x960)", use_column_width=True)


# --- Drag logic (from canvas clicks/transforms) ---
if canvas_result.json_data:
    objects = canvas_result.json_data["objects"]
    if objects:
        obj = objects[-1] 
        
        # Scale coordinates up by 2x to match the internal 1080x1920 resolution
        scale_factor = 2
        
        # Update the position of the currently selected element from the radio buttons
        el[st.session_state.selected_element]["x"] = int(obj["left"] * scale_factor + obj["width"] * scale_factor // 2)
        el[st.session_state.selected_element]["y"] = int(obj["top"] * scale_factor + obj["height"] * scale_factor // 2)
        
        # Rerun the script to apply the new positions
        st.experimental_rerun()

# Final output button
if st.button("PRINT FINAL LAYOUT CODE"):
    st.code(f"elements = {st.session_state.elements}", language="python")
    st.success("Copy this into your Reel generator → perfect every time")

st.caption("You now control pixels like a pro. Charge Ksh 80,000 per Reel.")
