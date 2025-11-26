import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io
import tempfile
import os
import math
import requests
import json
import re
from moviepy.editor import ImageSequenceClip, AudioFileClip
import groq

# Configuration
WIDTH, HEIGHT = 1080, 1920
FPS = 30

# Your assets
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"
AUDIO_URL = "https://ik.imagekit.io/ericmwangi/advertising-music-308403.mp3?updatedAt=1764101548797"

# Font helper (safe & modern)
def get_font(size, bold=False):
    candidates = []
    if bold:
        candidates = [
            "Arial Bold.ttf", "Arial-Bold.ttf", "arialbd.ttf",
            "/System/Library/Fonts/Arial Bold.ttf",
            "DejaVuSans-Bold.ttf", "segoeui_bold.ttf"
        ]
    else:
        candidates = ["Arial.ttf", "arial.ttf", "DejaVuSans.ttf"]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except:
            continue
    return ImageFont.load_default()

# Groq client
@st.cache_resource
def get_groq_client():
    if 'groq_key' not in st.secrets:
        st.error("❌ Add 'groq_key' to Streamlit Secrets")
        return None
    return groq.Client(api_key=st.secrets['groq_key'])

# Load assets
@st.cache_resource
def load_logo():
    try:
        resp = requests.get(LOGO_URL, timeout=10)
        if resp.status_code == 200:
            logo = Image.open(io.BytesIO(resp.content)).convert("RGBA")
            return logo.resize((260, 130), Image.LANCZOS)
    except Exception as e:
        st.warning(f"Logo fallback: {e}")
    fallback = Image.new("RGBA", (260, 130), (0,0,0,0))
    draw = ImageDraw.Draw(fallback)
    font = get_font(70, bold=True)
    draw.text((10, 25), "SM", fill="#FFD700", font=font)
    return fallback

@st.cache_resource
def download_audio():
    try:
        resp = requests.get(AUDIO_URL, timeout=15)
        if resp.status_code == 200:
            path = os.path.join(tempfile.gettempdir(), "sm_bg_music.mp3")
            with open(path, "wb") as f:
                f.write(resp.content)
            return path
    except Exception as e:
        st.warning(f"Audio download failed: {e}")
    return None

# AI Content Generator
def generate_diy_content(client):
    prompt = """
    You are a luxury interior design expert for "SM Interiors". Generate a high-value DIY tip for social media.

    Requirements:
    - Title: MAX 4 WORDS, catchy, uppercase-style
    - Tip: Practical, 15-30 words, actionable
    - Caption: Engaging, includes emoji, under 120 chars
    - Hashtags: 8-12 relevant hashtags starting with #

    Respond ONLY with valid JSON:
    {
        "title": "WOOD POLISH HACK",
        "tip": "Mix 1 part white vinegar with 2 parts olive oil. Apply with a soft cloth in circular motions for instant shine.",
        "caption": "Revive dull wood in seconds! ✨ #DIY",
        "hashtags": "#DIY #WoodCare #HomeDecor #InteriorDesign #SMInteriors #FurnitureHack #NaturalClean #LuxuryHome"
    }
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.85,
            max_tokens=400
        )
        response = chat_completion.choices[0].message.content
        # Extract JSON robustly
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            # Clean hashtags
            tags = re.findall(r'#\w+', data.get("hashtags", ""))
            data["hashtags"] = " ".join(tags[:12])
            return data
    except Exception as e:
        st.error(f"AI error: {e}")
    # Fallback
    return {
        "title": "WOOD POLISH HACK",
        "tip": "Mix 1 part white vinegar with 2 parts olive oil. Apply with a soft cloth in circular motions for instant shine.",
        "caption": "Revive dull wood in seconds! ✨ #DIY",
        "hashtags": "#DIY #WoodCare #HomeDecor #InteriorDesign #SMInteriors #FurnitureHack #NaturalClean #LuxuryHome"
    }

# Geometric Background
def create_geometric_background():
    bg = Image.new("RGB", (WIDTH, HEIGHT), "#0A0703")
    draw = ImageDraw.Draw(bg)
    # Gold accents
    draw.rectangle([180, 280, 420, 480], outline="#FFD700", width=3)
    draw.ellipse([650, 380, 980, 710], outline="#FFD700", width=3)
    draw.polygon([(150, 1150), (420, 1150), (285, 1400)], outline="#FFD700", width=3)
    # Subtle grid
    for x in range(0, WIDTH, 250):
        draw.line([(x, 0), (x, HEIGHT)], fill="#151008", width=1)
    return bg

# Text splitting
def split_text(text, max_len=28):
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = ' '.join(current + [word])
        if len(test) <= max_len:
            current.append(word)
        else:
            if current:
                lines.append(' '.join(current))
            current = [word]
    if current:
        lines.append(' '.join(current))
    return lines

# Frame generator
def create_frame(t, lines, title, logo=None):
    bg = create_geometric_background()
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    
    title_font = get_font(80, bold=True)
    text_font = get_font(66, bold=True)
    cta_font = get_font(50, bold=True)
    
    # Title: lower to avoid logo (logo is top-left)
    title_y = 220 + int(15 * math.sin(t * 1.5))
    draw.text((80, title_y), title, fill="#FFD700", font=title_font)
    
    # Logo: top-left, below title
    if logo:
        overlay.paste(logo, (60, 60), logo)  # LEFT-aligned
    
    # Animated tip lines
    base_y = 620
    line_height = 105
    for i, line in enumerate(lines):
        progress = max(0, min(1, (t - i * 0.35) * 2.2))
        if progress <= 0:
            continue
        offset_y = int((1 - progress) * 50)
        alpha = int(255 * progress)
        y = base_y + i * line_height - offset_y
        # Shadow + text
        draw.text((WIDTH//2 + 3, y + 3), line, fill=(0,0,0, alpha), font=text_font, anchor="mm")
        draw.text((WIDTH//2, y), line, fill=(255,255,255, alpha), font=text_font, anchor="mm")
    
    # CTA
    cta_text = "👉 SWIPE UP FOR MORE!"
    cta_alpha = int(180 + 70 * math.sin(t * 3.5))
    draw.text((WIDTH//2, HEIGHT - 150), cta_text, fill=(255,255,255, cta_alpha), font=cta_font, anchor="mm")
    
    bg.paste(overlay, (0,0), overlay)
    return np.array(bg)

# --- Streamlit UI ---
st.set_page_config(page_title="SM Interiors AI Video", layout="wide", page_icon="💡")
st.title("💡 SM Interiors AI DIY Video")
st.caption("AI-generated • Your logo on left • Geometric design • Your music")

client = get_groq_client()

if client and st.button("✨ Generate & Create Video", type="primary"):
    with st.spinner("AI is crafting your DIY tip..."):
        content = generate_diy_content(client)
        tip_lines = split_text(content["tip"])
        duration = min(12, max(6, len(content["tip"].split()) // 2 + 4))
    
    st.subheader("📱 AI-Generated Content")
    col1, col2 = st.columns(2)
    with col1:
        st.text_area("Caption", content["caption"], height=80)
    with col2:
        st.text_area("Hashtags", content["hashtags"], height=80)
    
    with st.spinner("Rendering video..."):
        logo = load_logo()
        audio_path = download_audio()
        frames = []
        for i in range(FPS * duration):
            t = i / FPS
            frame = create_frame(t, tip_lines, content["title"], logo)
            frames.append(frame)
        
        clip = ImageSequenceClip(frames, fps=FPS)
        if audio_path and os.path.exists(audio_path):
            try:
                audio = AudioFileClip(audio_path).subclip(0, min(duration, AudioFileClip(audio_path).duration))
                clip = clip.set_audio(audio)
            except Exception as e:
                st.warning(f"Audio skipped: {e}")
        
        out_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
        try:
            clip.write_videofile(out_path, fps=FPS, codec="libx264", audio_codec="aac", preset="fast", logger=None)
            st.success("✅ Video ready!")
            st.video(out_path)
            with open(out_path, "rb") as f:
                st.download_button("⬇️ Download Video", f, "SM_DIY_Geometric.mp4", "video/mp4", use_container_width=True)
        except Exception as e:
            st.error(f"Video encoding failed: {e}")
        finally:
            clip.close()
            if 'audio' in locals():
                audio.close()
            if os.path.exists(out_path):
                os.unlink(out_path)
            if audio_path and os.path.exists(audio_path):
                os.unlink(audio_path)

else:
    st.info("➡️ Click the button to generate an AI-powered DIY video with your branding.")
