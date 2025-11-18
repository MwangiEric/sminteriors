import streamlit as st, os, tempfile, uuid, requests
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile

def free_remove_bg(image_pil):
    """Pixian.AI  -  NO KEY, 50 free HD/day"""
    buf = io.BytesIO()
    image_pil.save(buf, format="PNG")
    buf.seek(0)
    r = requests.post("https://api.pixian.ai/remove", files={"image": ("in.png", buf, "image/png")})
    return Image.open(io.BytesIO(r.content))

def free_caption(image_pil):
    """BLIP caption"""
    from transformers import BlipProcessor, BlipForConditionalGeneration
    if "blip_model" not in st.session_state:
        st.session_state.blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        st.session_state.blip_proc  = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model, proc = st.session_state.blip_model, st.session_state.blip_proc
    inputs = proc(image_pil, return_tensors="pt")
    out = model.generate(**inputs)
    return proc.decode(out[0], skip_special_tokens=True)

# ---------- usage inside Streamlit ----------
uploaded = st.file_uploader("Product photo")
if uploaded:
    im = Image.open(uploaded)
    col1, col2 = st.columns(2)
    with col1:
        st.image(im, caption="Original")
    with col2:
        transparent = free_remove_bg(im)
        st.image(transparent, caption="Transparent PNG")
    caption = free_caption(im)
    st.write("AI description:", caption)
