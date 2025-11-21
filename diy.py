import streamlit as st
import io, requests, math, tempfile, base64, json, time, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip, TextClip, CompositeVideoClip
from rembg import remove

# ────────────────────────────── CONFIG ──────────────────────────────
st.set_page_config(page_title="DIY Tips → Creative Video", layout="wide", page_icon="✨")

WIDTH, HEIGHT = 720, 1280
FPS = 30
DURATION = 6

LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

MUSIC = {
    "Luxury Chill": "https://archive.org/download/bensound-adaytoremember/bensound-adaytoremember.mp3",
    "Modern Beats": "https://archive.org/download/bensound-sweet/bensound-sweet.mp3"
}

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {"Authorization": f"Bearer {st.secrets['groq_key']}", "Content-Type": "application/json"}

# ────────────────────────────── HELPERS ──────────────────────────────
def ask_groq(payload):
    try:
        r = requests.post(GROQ_URL, json=payload, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Groq error: {e}")
        return None

def get_font(size):
    for path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "arial.ttf"]:
        try: return ImageFont.truetype(path, size)
        except: pass
    return ImageFont.load_default()

# ────────────────────────────── TIP GENERATOR ──────────────────────────────
st.title("DIY & Interior Tips → Creative Video Maker")

tab1, tab2 = st.tabs(["Generate Tips", "Make Creative Video"])

with tab1:
    st.header("Generate 5 Viral DIY / Interior Tips")
    tip_type = st.selectbox("Tip Category", [
        "DIY Home Decor Hacks", "Furniture Restoration", 
        "Small Space Solutions", "Luxury on a Budget", "Quick Staging Tricks"
    ])
    focus = st.text_input("Focus keyword (optional)", "velvet sofa, mid-century, brass accents")

    if st.button("Generate Tips", type="primary"):
        with st.spinner("Groq is writing fire tips..."):
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are a viral short-form content expert for luxury interiors. Respond ONLY with 5 numbered bullet points, each 12–18 words max. Make them visual, actionable, and addictive."},
                    {"role": "user", "content": f"Give me 5 {tip_type.lower()} tips related to '{focus}'. Keep each tip under 18 words."}
                ],
                "temperature": 0.85,
                "max_tokens": 500
            }
            result = ask_groq(payload)
            if result:
                st.session_state.tips = result.strip()
                st.success("Tips ready!")
                st.markdown(result)
            else:
                st.error("Failed – check your Groq key")

# ────────────────────────────── VIDEO CREATOR ──────────────────────────────
with tab2:
    st.header("Turn Any Tip into a 6-Second Creative Video")
    
    default_tips = st.session_state.get("tips", "")
    tip_text = st.text_area("Paste one tip here (or write your own)", height=120, value=default_tips.split("\n")[0] if default_tips else "")
    
    col1, col2 = st.columns(2)
    with col1:
        bg_music = st.selectbox("Music", list(MUSIC.keys()), index=0)
    with col2:
        optional_img = st.file_uploader("Optional product image (adds wow factor)", type=["png","jpg","jpeg"])

    if st.button("Create Creative Video", type="primary"):
        if not tip_text.strip():
            st.error("Write or paste a tip first!")
        else:
            with st.status("Cooking your video...") as status:
                status.write("Preparing canvas...")
                
                # Optional product image (with background removal)
                product_img = None
                if optional_img:
                    raw = Image.open(optional_img).convert("RGBA")
                    clean = remove(raw.getdata())
                    product_img = Image.open(io.BytesIO(clean)).convert("RGBA")
                    # resize to fit nicely
                    product_img = product_img.resize((550, 550), Image.LANCZOS)

                # Generate frames
                frames = []
                for i in range(FPS * DURATION):
                    t = i / (FPS * DURATION)  # 0 → 1
                    
                    canvas = Image.new("RGBA", (WIDTH, HEIGHT), "#1a120f")
                    draw = ImageDraw.Draw(canvas)

                    # Subtle gold gradient bars
                    for y in range(0, HEIGHT, 200):
                        alpha = int(80 * (1 - abs(t*2 - 1)))
                        draw.rectangle([0, y, WIDTH, y+80], fill=f"#D2A544{hex(alpha)[2:].zfill(2)}")

                    # Product (if any) – elastic pop-in
                    if product_img and t > 0.2:
                        scale = ease_out_elastic(min((t-0.2)/0.8, 1.0))
                        w = int(550 * scale)
                        h = int(550 * scale)
                        resized = product_img.resize((w, h), Image.LANCZOS)
                        x = (WIDTH - w) // 2
                        y = int(HEIGHT * 0.38 - h//2 + math.sin(t*10)*8)
                        canvas.paste(resized, (x, y), resized)

                    # Logo top-left
                    try:
                        logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
                        logo = logo.resize((180, 90), Image.LANCZOS)
                        canvas.paste(logo, (40, 40), logo)
                    except: pass

                    # Main tip text – typewriter + glow
                    if t > 0.4:
                        visible_ratio = min((t - 0.4) / 0.4, 1.0)
                        visible_chars = int(len(tip_text) * visible_ratio)
                        display_text = tip_text[:visible_chars]
                        
                        font = get_font(68)
                        bbox = draw.textbbox((0,0), display_text, font=font)
                        text_w = bbox[2] - bbox[0]
                        text_x = (WIDTH - text_w) // 2
                        text_y = HEIGHT - 360

                        # Glow
                        for dx in [-4,0,4]:
                            for dy in [-4,0,4]:
                                if dx or dy:
                                    draw.text((text_x+dx, text_y+dy), display_text, font=font, fill="#D2A544")

                        # Main text
                        draw.text((text_x, text_y), display_text, font=font, fill="white")

                    # Final call-to-action
                    if t > 0.8:
                        cta = "Shop SM Interiors →"
                        f = get_font(48)
                        bbox = draw.textbbox((0,0), cta, font=f)
                        w = bbox[2]-bbox[0]
                        draw.text(((WIDTH-w)//2, HEIGHT-180), cta, font=f, fill="#D2A544")

                    frames.append(np.array(canvas))

                status.write("Adding music...")
                clip = ImageSequenceClip(frames, fps=FPS)
                
                audio_url = MUSIC[bg_music]
                audio_file = requests.get(audio_url).content
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    tmp.write(audio_file)
                    tmp_path = tmp.name
                
                audio = AudioFileClip(tmp_path).subclip(0, DURATION).audio_fadeout(0.5)
                final = clip.set_audio(audio)
                os.unlink(tmp_path)

                status.write("Exporting video...")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as out:
                    final.write_videofile(out.name, codec="libx264", audio_codec="aac", logger=None)
                    video_path = out.name

                status.update(label="Done! Your creative is ready ↓", state="complete")
                st.video(video_path)
                
                with open(video_path, "rb") as f:
                    st.download_button("Download Creative Video", f, f"sm_diy_creative.mp4", "video/mp4")
                os.unlink(video_path)

# Simple elastic easing
def ease_out_elastic(t):
    if t <= 0: return 0
    if t >= 1: return 1
    return 2**(-10*t) * math.sin((t*10 - 0.75) * (2*math.pi)/3) + 1