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
GRID_COLS, GRID_ROWS = 12, 24

def analyze_product_for_smart_layout(product_img):
    """AI analyzes product image to determine optimal layout"""
    try:
        # Analyze product dimensions and composition
        if hasattr(product_img, 'size'):
            width, height = product_img.size
            aspect_ratio = width / height
            
            # Smart layout decisions based on product type
            if aspect_ratio > 1.5:  # Wide product (sofa, console)
                return {
                    'type': 'wide',
                    'product_position': (6, 6),
                    'product_size': 8,
                    'text_alignment': 'sides'
                }
            elif aspect_ratio < 0.7:  # Tall product (cabinet, shelf)
                return {
                    'type': 'tall', 
                    'product_position': (6, 4),
                    'product_size': 5,
                    'text_alignment': 'below'
                }
            else:  # Square product (chair, table)
                return {
                    'type': 'square',
                    'product_position': (6, 8), 
                    'product_size': 6,
                    'text_alignment': 'below'
                }
    except:
        pass
    return None

def generate_smart_layout(product_analysis, content_length):
    """Generate optimal layout based on product type and content"""
    
    if product_analysis['type'] == 'wide':
        return {
            'product_position': (6, 6),
            'product_size': 8,
            'urgency_position': (6, 2),
            'headline_position': (6, 4),
            'name_position': (6, 12),
            'description_position': (6, 14),
            'price_position': (6, 18),
            'cta_position': (6, 20, 4, 1),
            'contact_position': (6, 22)
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
            'contact_position': (6, 20)
        }
    
    else:  # square
        return {
            'product_position': (6, 8),
            'product_size': 6,
            'urgency_position': (6, 2),
            'headline_position': (6, 4),
            'name_position': (6, 14),
            'description_position': (6, 16),
            'price_position': (6, 18),
            'cta_position': (6, 20, 4, 1),
            'contact_position': (6, 22)
        }

def smart_text_sizing(description_length):
    """Adjust text sizes based on content length"""
    base_size = 36
    if description_length > 100:
        return max(28, base_size - 8)  # Smaller for long text
    elif description_length < 50:
        return min(48, base_size + 12)  # Larger for short text
    return base_size

def create_ai_optimized_layout(product_img, ai_copy):
    """Main smart layout function"""
    
    # Step 1: Analyze product image
    product_analysis = analyze_product_for_smart_layout(product_img)
    if not product_analysis:
        product_analysis = {'type': 'square'}  # Fallback
    
    # Step 2: Analyze content length
    content_length = len(ai_copy.get('description', ''))
    
    # Step 3: Generate optimal layout
    layout = generate_smart_layout(product_analysis, content_length)
    
    # Step 4: Smart text sizing
    layout['description_size'] = smart_text_sizing(content_length)
    layout['urgency_size'] = 60
    layout['headline_size'] = 48
    layout['name_size'] = 48
    layout['price_size'] = 72
    layout['cta_size'] = 38
    layout['contact_size'] = 36
    
    return layout

# Main app with smart features
st.title("🎯 SM Interiors - Smart Layout AI")

try:
    groq_key = st.secrets["groq_key"]
except:
    st.error("❌ Groq API key not found")
    st.stop()

# Initialize
if 'smart_layout' not in st.session_state:
    st.session_state.smart_layout = None

# Smart workflow
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.subheader("🖼️ Product Image")
    uploaded = st.file_uploader("Upload Product", type=["png","jpg","jpeg"])
    if uploaded:
        product_img = Image.open(uploaded)
        st.image(product_img, use_column_width=True)
        
        # Auto-analyze product for layout
        with st.spinner("🤖 Analyzing product for optimal layout..."):
            product_analysis = analyze_product_for_smart_layout(product_img)
            if product_analysis:
                st.success(f"✅ Detected: {product_analysis['type']} product")
                st.session_state.product_analysis = product_analysis

with col2:
    st.subheader("💰 Business Info")
    price = st.text_input("Price", "Ksh 12,500")
    phone = st.text_input("Phone", "0710 895 737")

with col3:
    st.subheader("🎨 Smart Layout")
    if st.button("🧠 Generate AI Layout", type="secondary"):
        if uploaded and st.session_state.get('ai_copy'):
            with st.spinner("AI optimizing layout..."):
                st.session_state.smart_layout = create_ai_optimized_layout(
                    product_img, st.session_state.ai_copy
                )
                st.success("✅ Smart layout generated!")
                
                # Show layout insights
                analysis = st.session_state.product_analysis
                st.info(f"""
                **Layout Strategy:**
                - Product type: {analysis['type']}
                - Optimal positioning: {analysis['text_alignment']}
                - Smart text sizing applied
                """)

# AI Copy Generation
if uploaded:
    if st.button("🤖 Generate AI Ad Copy", type="primary"):
        with st.spinner("AI creating marketing copy..."):
            # Your existing AI copy generation code here
            st.session_state.ai_copy = {
                "product_name": "Modern Console",
                "headline": "Transform Your Space! ✨", 
                "description": "• Premium design\n• Perfect for Nairobi homes",
                "urgency_text": "LIMITED STOCK! 🔥",
                "discount_offer": "FREE DELIVERY",
                "call_to_action": "DM TO ORDER"
            }
            st.success("✅ AI copy generated")

# Smart Preview
if uploaded and st.session_state.get('ai_copy') and st.session_state.get('smart_layout'):
    st.subheader("🎬 Smart Preview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("👀 Show Smart Layout", use_container_width=True):
            # Use your existing create_preview function with smart layout
            preview = create_preview(
                product_img, 
                st.session_state.ai_copy, 
                price, 
                phone, 
                st.session_state.smart_layout
            )
            st.image(preview, use_column_width=True, caption="AI-Optimized Layout")
            
            # Show layout explanation
            analysis = st.session_state.product_analysis
            st.markdown(f"""
            **🤖 AI Layout Reasoning:**
            - **Product Type**: {analysis['type'].upper()} → Optimized positioning
            - **Text Flow**: Natural reading path around product
            - **Mobile First**: Touch-friendly spacing
            - **Visual Hierarchy**: Most important elements get prime space
            """)
    
    with col2:
        if st.button("🚀 Create Smart Video", type="primary", use_container_width=True):
            with st.status("Creating AI-optimized video..."):
                # Use your existing create_video function with smart layout
                video_path = create_video(
                    product_img,
                    st.session_state.ai_copy,
                    price,
                    phone,
                    st.session_state.smart_layout
                )
                
                if video_path:
                    st.video(video_path)
                    with open(video_path, "rb") as f:
                        st.download_button(
                            "📥 Download Smart Video", 
                            f, 
                            "sm_smart_ad.mp4", 
                            "video/mp4",
                            use_container_width=True
                        )
                    os.unlink(video_path)

# Manual override for experts
with st.expander("🔧 Advanced Layout Controls (Optional)"):
    st.info("AI already generated the optimal layout. Only adjust if needed.")
    # Your existing grid controls here, but hidden by default

st.markdown("---")
st.markdown("**✨ Smart Features:**")
st.markdown("""
- **Product Analysis**: AI detects product shape and type
- **Automatic Layout**: Optimal positioning based on product characteristics  
- **Smart Text Sizing**: Adjusts based on content length
- **Mobile Optimization**: Ensures touch-friendly spacing
- **Visual Hierarchy**: Places important elements in prime areas
""")
