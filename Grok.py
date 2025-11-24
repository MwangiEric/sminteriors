import streamlit as st
import base64
from PIL import Image

st.set_page_config(page_title="SM Layout Editor", layout="centered")
st.title("SM Interiors — Drag & Drop Layout Editor")
st.caption("Drag elements • Slider sizes • Upload images • Real-time preview")

# Session state for positions/sizes/images
if "elements" not in st.session_state:
    st.session_state.elements = {
        "sofa": {"x": 540, "y": 900, "w": 860, "h": 860, "img_b64": ""},
        "logo": {"x": 100, "y": 100, "w": 200, "h": 100, "img_b64": ""},
        "hook": {"x": 540, "y": 300, "text": "This Sold Out in 24 Hours", "size": 100},
        "price": {"x": 540, "y": 1460, "text": "Ksh 94,900", "size": 120},
        "cta": {"x": 540, "y": 1700, "text": "DM 0710 895 737", "size": 90},
    }

el = st.session_state.elements

# Uploads
col1, col2 = st.columns(2)
with col1:
    sofa_file = st.file_uploader("Upload Sofa", type=["png","jpg","jpeg"])
    if sofa_file:
        img = Image.open(sofa_file).convert("RGBA")
        img = img.resize((el["sofa"]["w"], el["sofa"]["h"]), Image.LANCZOS)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        el["sofa"]["img_b64"] = base64.b64encode(buffered.getvalue()).decode()
with col2:
    logo_file = st.file_uploader("Upload Logo", type=["png","jpg","jpeg"])
    if logo_file:
        img = Image.open(logo_file).convert("RGBA")
        img = img.resize((el["logo"]["w"], el["logo"]["h"]), Image.LANCZOS)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        el["logo"]["img_b64"] = base64.b64encode(buffered.getvalue()).decode()

# Sliders
st.subheader("Resize with Sliders")
c1, c2, c3 = st.columns(3)
with c1:
    el["sofa"]["w"] = st.slider("Sofa Width", 400, 1000, el["sofa"]["w"])
    el["sofa"]["h"] = st.slider("Sofa Height", 400, 1400, el["sofa"]["h"])
    if el["sofa"]["img_b64"]:
        img = Image.open(io.BytesIO(base64.b64decode(el["sofa"]["img_b64"])))
        img = img.resize((el["sofa"]["w"], el["sofa"]["h"]), Image.LANCZOS)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        el["sofa"]["img_b64"] = base64.b64encode(buffered.getvalue()).decode()
with c2:
    el["logo"]["w"] = st.slider("Logo Width", 100, 400, el["logo"]["w"])
    el["logo"]["h"] = st.slider("Logo Height", 50, 300, el["logo"]["h"])
    if el["logo"]["img_b64"]:
        img = Image.open(io.BytesIO(base64.b64decode(el["logo"]["img_b64"])))
        img = img.resize((el["logo"]["w"], el["logo"]["h"]), Image.LANCZOS)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        el["logo"]["img_b64"] = base64.b64encode(buffered.getvalue()).decode()
with c3:
    el["hook"]["size"] = st.slider("Hook Size", 60, 180, el["hook"]["size"])
    el["price"]["size"] = st.slider("Price Size", 80, 200, el["price"]["size"])
    el["cta"]["size"] = st.slider("CTA Size", 60, 140, el["cta"]["size"])

# HTML5 Canvas for Drag (with JS)
html = f"""
<div style="position: relative; width: 540px; height: 960px; border: 1px solid gold; margin: auto;">
  <canvas id="preview" width="1080" height="1920" style="width: 540px; height: 960px;"></canvas>
</div>

<script>
const canvas = document.getElementById('preview');
const ctx = canvas.getContext('2d');
const scale = 0.5;  // Preview scale
let dragging = null;
const elements = {json.dumps(el)};

function drawPreview() {{
  ctx.fillStyle = '#0F0A05'; ctx.fillRect(0,0,1080,1920);
  
  // Gold rings
  ctx.strokeStyle = '#FFD700'; ctx.lineWidth = 6;
  [600,800,1000].forEach(r => {{
    ctx.beginPath();
    ctx.arc(540,960,r,0,2*Math.PI);
    ctx.stroke();
  }});

  // Sofa
  if (elements.sofa.img_b64) {{
    const sofaImg = new Image();
    sofaImg.src = "data:image/png;base64," + elements.sofa.img_b64;
    ctx.drawImage(sofaImg, elements.sofa.x - elements.sofa.w/2, elements.sofa.y - elements.sofa.h/2, elements.sofa.w, elements.sofa.h);
  }}

  // Logo
  if (elements.logo.img_b64) {{
    const logoImg = new Image();
    logoImg.src = "data:image/png;base64," + elements.logo.img_b64;
    ctx.drawImage(logoImg, elements.logo.x, elements.logo.y, elements.logo.w, elements.logo.h);
  }}

  // Text
  ['hook', 'price', 'cta'].forEach(name => {{
    ctx.font = `bold ${elements[name].size}px Arial`;
    ctx.fillStyle = '#FFFFFF';
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 6;
    ctx.textAlign = 'center';
    const text = elements[name].text;
    ctx.strokeText(text, elements[name].x, elements[name].y);
    ctx.fillText(text, elements[name].x, elements[name].y);
  }});
}}

drawPreview();

// Drag logic (mouse events on canvas)
canvas.addEventListener('mousedown', e => {{
  const rect = canvas.getBoundingClientRect();
  const x = (e.clientX - rect.left) / scale;
  const y = (e.clientY - rect.top) / scale;
  
  for (let name in elements) {{
    const el = elements[name];
    if (name === "sofa" || name === "logo") {{
      if (Math.abs(x - el.x) < el.w/2 && Math.abs(y - el.y) < el.h/2) {{
        dragging = name;
        offsetX = x - el.x;
        offsetY = y - el.y;
      }}
    }} else {{
      if (Math.abs(x - el.x) < 400 && Math.abs(y - el.y) < 100) {{
        dragging = name;
        offsetX = x - el.x;
        offsetY = y - el.y;
      }}
    }}
  }}
}});

canvas.addEventListener('mousemove', e => {{
  if (dragging) {{
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / scale;
    const y = (e.clientY - rect.top) / scale;
    elements[dragging].x = x - offsetX;
    elements[dragging].y = y - offsetY;
    drawPreview();
  }}
}});

canvas.addEventListener('mouseup', e => {{
  dragging = null;
}});
</script>
"""

st.components.v1.html(html, height=1000, scrolling=True)

if st.button("PRINT FINAL LAYOUT"):
    st.code(json.dumps(el, indent=4), language="python")
    st.success("Copy this → paste into your Reel generator")

st.caption("You now know how drag + sliders work in Streamlit — use session_state to store, canvas for drag, sliders for resize.")
