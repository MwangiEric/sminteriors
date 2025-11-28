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
import gc
import time
from moviepy.editor import ImageSequenceClip
import groq

# =============================
# CONFIGURATION
# =============================
WIDTH, HEIGHT = 1080, 1920
FPS = 30
TEXT_MAX_Y = 1400

# Brand Colors
BG_DARK = "#2B1B10"
ACCENT_GOLD = "#D4AF37"
TEXT_WHITE = "#F8F4E9"

# Assets (FIXED: no trailing spaces!)
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"
AUDIO_URL = "https://ik.imagekit.io/ericmwangi/advertising-music-308403.mp3?updatedAt=1764101548797"
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/josefinsans/JosefinSans-Bold.ttf"

TEMPLATE_ANIMATIONS = {
    "Diagonal Stripes": "typewriter",
    "Golden Waves": "fade-in-slide",
    "Metallic Curves": "highlight",
    "Modern Grid": "highlight"
}

@st.cache_resource
def load_font():
    try:
        resp = requests.get(FONT_URL, timeout=10)
        if resp.status_code == 200:
            return io.BytesIO(resp.content)
    except:
        pass
    return None

def get_font(size):
    font_io = load_font()
    if font_io:
        try:
            return ImageFont.truetype(font_io, size)
        except:
            pass
    for name in ["Arial Bold.ttf", "arialbd.ttf", "Arial-BoldMT", "Helvetica-Bold"]:
        try:
            return ImageFont.truetype(name, size)
        except:
            continue
    return ImageFont.load_default()

@st.cache_resource
def get_groq_client():
    if 'groq_key' not in st.secrets:
        st.error("❌ Add 'groq_key' to Streamlit Secrets")
        return None
    return groq.Client(api_key=st.secrets['groq_key'])

@st.cache_resource
def load_logo():
    try:
        resp = requests.get(LOGO_URL, timeout=10)
        if resp.status_code == 200:
            logo = Image.open(io.BytesIO(resp.content)).convert("RGBA")
            ratio = min(280 / logo.width, 140 / logo.height)
            new_size = (int(logo.width * ratio), int(logo.height * ratio))
            return logo.resize(new_size, Image.LANCZOS)
    except:
        pass
    fallback = Image.new("RGBA", (280, 140), (0,0,0,0))
    draw = ImageDraw.Draw(fallback)
    font = get_font(80)
    draw.text((20, 25), "SM", fill=ACCENT_GOLD, font=font)
    return fallback

def generate_diy_content_with_retry(client, topic, max_retries=3):
    for attempt in range(max_retries):
        try:
            prompt = f"""
            You are a luxury interior design expert for "SM Interiors". Generate a DIY tip about {topic}.

            Requirements:
            - Title: MAX 4 WORDS, uppercase
            - Tip: Practical, 20-35 words
            - Caption: <100 chars, with emoji
            - Hashtags: 6-10 relevant

            Respond ONLY with valid JSON:
            {{
                "title": "WOOD POLISH HACK",
                "tip": "Mix 2 tbsp olive oil with 1 tbsp lemon juice. Apply with cloth, wait 2 minutes, buff to shine.",
                "caption": "Natural wood revival! 🌿✨",
                "hashtags": "#DIY #WoodCare #SMInteriors"
            }}
            """
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.8,
                max_tokens=300
            )
            resp_text = chat_completion.choices[0].message.content
            json_match = re.search(r'\{.*\}', resp_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                tags = re.findall(r'#\w+', data.get("hashtags", ""))
                data["hashtags"] = " ".join(tags[:10])
                return data
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(0.5 * (2 ** attempt))
    return None

@st.cache_data
def get_ai_content(topic: str, seed: int):
    client = get_groq_client()
    if not client:
        return None
    return generate_diy_content_with_retry(client, topic)

# =============================
# ANIMATED BACKGROUNDS (NEW!)
# =============================
def create_background(template_name, t=0.0):
    base = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(base, "RGBA")
    
    if template_name == "Diagonal Stripes":
        angle = math.radians(45)
        stripe_width = 80
        offset = (t * 0.5) % stripe_width
        for i in range(-20, 20):
            y_start = i * stripe_width - offset
            y_end = y_start + stripe_width
            points = [
                (0, y_start),
                (WIDTH, y_start + WIDTH * math.tan(angle)),
                (WIDTH, y_end + WIDTH * math.tan(angle)),
                (0, y_end)
            ]
            alpha = int(60 + 40 * math.sin(t * 1.5 + i))
            color = ACCENT_GOLD + f"{alpha:02x}"
            draw.polygon(points, fill=color)
        draw.rectangle([20, 20, WIDTH-20, HEIGHT-20], outline=ACCENT_GOLD, width=2)
    
    elif template_name == "Golden Waves":
        for y in range(0, HEIGHT, 15):
            wave_y = y + 10 * math.sin((y / 150) + t * 0.8)
            alpha = int(80 + 30 * math.sin(t * 1.2 + y / 50))
            color = ACCENT_GOLD + f"{alpha:02x}"
            draw.line([(0, wave_y), (WIDTH, wave_y)], fill=color, width=10)
        for i in range(3):
            x_offset = int(50 * math.sin(t * 0.5 + i))
            y_offset = int(30 * math.cos(t * 0.7 + i))
            draw.ellipse(
                [WIDTH//2 - 300 + x_offset, HEIGHT//2 - 150 + y_offset,
                 WIDTH//2 + 300 + x_offset, HEIGHT//2 + 150 + y_offset],
                outline=ACCENT_GOLD + "20", width=3
            )
    
    elif template_name == "Metallic Curves":
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        for i in range(5):
            radius = 400 + 50 * math.sin(t * 0.6 + i)
            start_angle = 0
            end_angle = 180 + 30 * math.sin(t * 0.4 + i)
            alpha = int(100 + 50 * math.sin(t * 0.8 + i))
            color = ACCENT_GOLD + f"{alpha:02x}"
            draw.arc(
                [center_x - radius, center_y - radius,
                 center_x + radius, center_y + radius],
                start_angle, end_angle, fill=color, width=20
            )
        for i in range(15):
            x = int(WIDTH * (0.3 + 0.4 * math.sin(t * 0.3 + i)))
            y = int(HEIGHT * (0.2 + 0.6 * math.cos(t * 0.2 + i)))
            size = 8 + 4 * math.sin(t * 0.5 + i)
            alpha = int(120 + 80 * math.sin(t * 0.7 + i))
            color = ACCENT_GOLD + f"{alpha:02x}"
            draw.ellipse(
                [x - size, y - size, x + size, y + size],
                fill=color
            )
    
    elif template_name == "Modern Grid":
        for x in range(0, WIDTH, 150):
            draw.line([(x, 0), (x, HEIGHT)], fill=ACCENT_GOLD + "08", width=1)
        for y in range(0, HEIGHT, 150):
            draw.line([(0, y), (WIDTH, y)], fill=ACCENT_GOLD + "08", width=1)
    
    return np.array(base)

# =============================
# TEXT UTILS
# =============================
def split_text_dynamic(text, font, max_width):
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = ' '.join(current + [word])
        bbox = font.getbbox(test)
        if bbox[2] - bbox[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(' '.join(current))
            current = [word]
    if current:
        lines.append(' '.join(current))
    return lines

def adjust_title_font(title, max_width, max_font_size=90):
    font_size = max_font_size
    while font_size >= 45:
        font = get_font(font_size)
        bbox = font.getbbox(title)
        if bbox[2] - bbox[0] <= max_width:
            return font
        font_size -= 2
    return get_font(45)

# =============================
# FRAME RENDERER (ANIMATED BG + TEXT)
# =============================
def create_tiktok_frame(t, lines, title, logo, font_title, font_text, template_name):
    # Generate animated background using current time
    bg_array = create_background(template_name, t)
    
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Logo (larger)
    if logo:
        overlay.paste(logo, (70, 60), logo)
    
    # Title (lowered + animated)
    title_y = 340
    title_animation = TEMPLATE_ANIMATIONS.get(template_name, "highlight")
    
    if title_animation == "typewriter":
        letters_per_sec = 6
        visible_chars = int(t * letters_per_sec)
        displayed_title = title[:visible_chars]
        draw.text((WIDTH // 2, title_y), displayed_title, fill=ACCENT_GOLD, font=font_title, anchor="mm")
        if visible_chars >= len(title) and t > 1.0 and int(t * 4) % 2 == 0:
            cursor_w = font_title.getbbox(displayed_title or " ")[2]
            cursor_x = WIDTH // 2 + cursor_w // 2 + 5
            draw.line([(cursor_x, title_y - 40), (cursor_x, title_y + 40)], fill=ACCENT_GOLD, width=2)

    elif title_animation == "fade-in-slide":
        if t < 0.1:
            pass
        elif t < 1.2:
            progress = min(1.0, (t - 0.1) / 1.1)
            offset_y = 20 * (1 - progress)
            draw.text((WIDTH // 2, title_y - offset_y), title, fill=ACCENT_GOLD, font=font_title, anchor="mm")
        else:
            draw.text((WIDTH // 2, title_y), title, fill=ACCENT_GOLD, font=font_title, anchor="mm")

    else:  # "highlight"
        title_bbox = font_title.getbbox(title)
        title_w = title_bbox[2] - title_bbox[0]
        if title_w > WIDTH - 200:
            title_lines = split_text_dynamic(title, font_title, WIDTH - 200)
            for i, t_line in enumerate(title_lines):
                y = 320 + i * 100
                if y < TEXT_MAX_Y:
                    draw.text((WIDTH // 2, y), t_line, fill=ACCENT_GOLD, font=font_title, anchor="mm")
        else:
            draw.text((WIDTH // 2, title_y), title, fill=ACCENT_GOLD, font=font_title, anchor="mm")
    
    # Animated tip text
    base_y = 620
    line_height = 95
    for line_idx, line in enumerate(lines):
        y = base_y + line_idx * line_height
        if y + line_height > TEXT_MAX_Y:
            break
        
        words = line.split()
        if not words:
            continue
        
        word_start_time = line_idx * 0.8
        highlighted = False
        for word_idx, word in enumerate(words):
            word_time_start = word_start_time + word_idx * 0.25
            if word_time_start <= t < word_time_start + 0.25:
                test_prefix = ' '.join(words[:word_idx])
                prefix_w = font_text.getbbox(test_prefix + " ")[2] if test_prefix else 0
                word_w = font_text.getbbox(word)[2]
                line_w = font_text.getbbox(line)[2]
                x_start = WIDTH // 2 - line_w // 2 + prefix_w
                word_bbox = font_text.getbbox(word)
                draw.rectangle(
                    [x_start - 4, y + word_bbox[1] - 4, x_start + word_w + 4, y + word_bbox[3] + 4],
                    fill=ACCENT_GOLD + "30"
                )
                draw.text((WIDTH // 2, y), line, fill=TEXT_WHITE, font=font_text, anchor="mm")
                highlighted = True
                break
        
        if not highlighted:
            draw.text((WIDTH // 2, y), line, fill=TEXT_WHITE, font=font_text, anchor="mm")
    
    # CTA
    cta_text = "Follow @SMInteriors"
    draw.text((WIDTH // 2, HEIGHT - 180), cta_text, fill=ACCENT_GOLD, font=get_font(50), anchor="mm")
    
    # Composite overlay onto background
    fg = np.array(overlay)[:,:,:3]
    alpha = np.array(overlay)[:,:,3:] / 255.0
    frame = (bg_array * (1 - alpha) + fg * alpha).astype(np.uint8)
    return frame

# =============================
# STREAMLIT APP
# =============================
st.set_page_config(page_title="SM Interiors Reels", layout="wide", page_icon="📱")
st.title("📱 SM Interiors — Luxury Animated Reels")
st.caption("Diagonal, Waves, Metallic • Gold & Brown • TikTok/Reels Ready")

col1, col2 = st.columns(2)
with col1:
    topic = st.text_input("DIY Topic", "marble countertop polish")
with col2:
    template = st.selectbox(
        "🎨 Animated Template",
        ["Diagonal Stripes", "Golden Waves", "Metallic Curves", "Modern Grid"]
    )

duration = st.slider("Duration (seconds)", 4, 8, 6)

if st.button("✨ Generate AI Tip", use_container_width=True):
    with st.spinner("Creating your luxury DIY tip..."):
        try:
            content = get_ai_content(topic, hash(topic) % 100000)
            if content:
                st.session_state.ai_content = content
                st.session_state.duration = duration
                st.session_state.template = template
            else:
                st.error("❌ AI failed. Try again.")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Edit & Preview
if 'ai_content' in st.session_state:
    content = st.session_state.ai_content
    duration = st.session_state.duration
    template = st.session_state.template
    
    st.subheader("✏️ Edit Content")
    edited_title = st.text_input("Title (max 4 words)", content["title"], max_chars=30)
    edited_tip = st.text_area("DIY Tip (20-35 words)", content["tip"], height=100, max_chars=180)
    st.text_area("Hashtags", content["hashtags"], height=60, disabled=True)
    
    # Preview at t=1.5s
    st.markdown("---")
    st.subheader("📱 Animated Preview")
    logo = load_logo()
    font_title = adjust_title_font(edited_title, WIDTH - 200)
    font_text = get_font(64)
    lines = split_text_dynamic(edited_tip, font_text, WIDTH - 220)
    preview_frame = create_tiktok_frame(1.5, lines, edited_title, logo, font_title, font_text, template)
    st.image(preview_frame, width=320)
    
    # Render Video
    if st.button("🚀 Export Reels Video", type="primary", use_container_width=True):
        if len(edited_tip.split()) > 40:
            st.warning("⚠️ Keep tip under 40 words for best results.")
        else:
            with st.spinner("Rendering... (30-60 sec)"):
                progress = st.progress(0)
                frames = []
                total_frames = FPS * duration
                
                for i in range(total_frames):
                    t = i / FPS
                    frame = create_tiktok_frame(t, lines, edited_title, logo, font_title, font_text, template)
                    frames.append(frame)
                    if i % max(1, total_frames // 30) == 0:
                        progress.progress(min(1.0, (i + 1) / total_frames))
                
                out_path = os.path.join(tempfile.gettempdir(), f"sm_reels_{int(time.time())}.mp4")
                try:
                    clip = ImageSequenceClip(frames, fps=FPS)
                    clip.write_videofile(
                        out_path, fps=FPS, codec="libx264",
                        audio_codec="aac", preset="medium",
                        logger=None, threads=4, ffmpeg_params=["-crf", "23"]
                    )
                    st.success("✅ Reels video ready!")
                    st.video(out_path)
                    with open(out_path, "rb") as f:
                        st.download_button(
                            "⬇️ Download for TikTok/Reels",
                            f, "SM_Interiors_Reels.mp4",
                            "video/mp4",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"Render failed: {e}")
                finally:
                    clip.close()
                    del frames
                    gc.collect()
