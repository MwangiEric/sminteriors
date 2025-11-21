import streamlit as st
import io, requests, math, tempfile, time, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip
from rembg import remove

st.set_page_config(page_title="SM Interiors – Viral Tips Video Maker", layout="centered", page_icon="gold_circle")

# ────────────────────────────── DESIGN CONSTANTS ──────────────────────────────
WIDTH, HEIGHT = 720, 1280
FPS = 30
DURATION = 7  # slightly longer for better typing feel

BG_COLOR = "#1E0F0B"
GOLD = "#D4AF37"
WHITE = "#FFFFFF"

LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"
MUSIC_URL = "https://archive.org/download/bensound-adaytoremember/bensound-adaytoremember.mp3"

# ────────────────────────────── HELPERS ──────────────────────────────
def get_font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        return ImageFont.load_default()

def ease_out_quart(t): 
    return 1 - (1 - t) ** 4

def draw_curved_shapes(draw):
    # Big gold circles & curves like your design
    draw.ellipse([50, 100, 400, 450], outline=GOLD, width=18)
    draw.ellipse([WIDTH-450, 700, WIDTH-50, 1100], outline=GOLD, width=20)
    draw.arc([200, -200, WIDTH+200, 600], start=0, end=90, fill=GOLD, width=25)
    draw.arc([-100, 800, 500, 1400], start=270, end=360, fill=GOLD, width=22)

# ────────────────────────────── MAIN APP ──────────────────────────────
st.markdown("<h1 style='text-align:center; color:#D4AF37;'>SM Interiors – Viral Tips Video Maker</h1>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Generate 5 Tips", "Create Video from Tip"])

# ============================= TAB 1: Generate Tips =============================
with tab1:
    st.markdown("### Generate 5 Viral DIY / Interior Tips")
    focus = st.text_input("Focus keyword (e.g., 'media console', 'velvet sofa')", "Horizon Media Console")

    if st.button("Generate 5 Tips", type="primary"):
        with st.spinner("Creating viral tips..."):
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are a luxury interiors content creator for SM Interiors. Write exactly 5 short, punchy, visual tips (12–20 words each). Number them 1–5. No intro text."},
                    {"role": "user", "content": f"Create 5 TikTok/Reels tips about the {focus} or how to style it."}
                ],
                "temperature": 0.9,
                "max_tokens": 400
            }
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                                json=payload,
                                headers={"Authorization": f"Bearer {st.secrets.groq_key}"})
                tips = r.json()["choices"][0]["message"]["content"]
                st.session_state.tips = tips
                st.success("Tips ready!")
                st.markdown(f"**{tips}**")
            except:
                st.error("Check your Groq key in secrets")

# ============================= TAB 2: Make Video =============================
with tab2:
    st.markdown("### Create Video from Any Tip")

    if "tips" not in st.session_state:
        st.info("First generate tips in the left tab →")
        st.stop()

    tips_list = [line.strip() for line in st.session_state.tips.split("\n") if line.strip() and line[0].isdigit()]
    selected_tip = st.radio("Choose which tip to turn into video", tips_list, index=0)

    col1, col2 = st.columns(2)
    with col1:
        price = st.text_input("Price (optional)", "Ksh 12,500")
    with col2:
        product_img_upload = st.file_uploader("Product image (optional – will auto-remove background)", type=["png","jpg"])

    if st.button("Create Video – SM Interiors Style", type="primary"):
        with st.status("Rendering your luxury creative…", expanded=True) as status:
            status.write("Loading assets…")

            # Load & process product image
            product = None
            if product_img_upload:
                raw = Image.open(product_img_upload).convert("RGBA")
                removed = remove(raw.tobytes())
                product = Image.open(io.BytesIO(removed)).convert("RGBA").resize((580, 580), Image.LANCZOS)

            # Load logo
            try:
                logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA").resize((200, 100), Image.LANCZOS)
            except:
                logo = None

            frames = []
            tip_text = selected_tip[2:].strip()  # remove "1. "

            for i in range(FPS * DURATION):
                t = i / (FPS * DURATION)
                canvas = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
                draw = ImageDraw.Draw(canvas)

                # Gold curved shapes
                alpha_img = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
                alpha_draw = ImageDraw.Draw(alpha_img)
                draw_curved_shapes(alpha_draw)
                canvas = Image.composite(canvas, Image.new("RGB", canvas.size, GOLD), alpha_img.convert("L"))

                # Logo top left
                if logo and t > 0.2:
                    opacity = min((t - 0.2)/0.3, 1.0)
                    logo_layer = logo.copy()
                    logo_layer.putalpha(int(255 * opacity))
                    canvas.paste(logo_layer, (40, 40), logo_layer)

                # Product reveal (elastic bounce)
                if product and t > 0.4:
                    scale = ease_out_quart(min((t - 0.4)/0.6, 1.0))
                    w = int(580 * scale)
                    h = int(580 * scale)
                    resized = product.resize((w, h), Image.LANCZOS)
                    x = (WIDTH - w) // 2
                    y = int(HEIGHT * 0.45 - h//2 + math.sin(t*15)*10)
                    canvas.paste(resized, (x, y), resized)

                # Typing text effect – from top to bottom
                if t > 1.0:
                    chars_to_show = int((t - 1.0) * 2.5 * len(tip_text))  # speed control
                    display_text = tip_text[:chars_to_show]

                    font = get_font(62)
                    lines = []
                    words = display_text.split()
                    line = ""
                    for word in words:
                        if draw.textbbox((0,0), line + word, font=font)[2] < WIDTH - 100:
                            line += (" " + word if line else word)
                        else:
                            lines.append(line)
                            line = word
                    if line: lines.append(line)

                    y_start = 180
                    for line in lines:
                        bbox = draw.textbbox((0,0), line, font=font)
                        w = bbox[2] - bbox[0]
                        x = (WIDTH - w) // 2
                        # Gold glow
                        for dx, dy in [(0,0), (2,2), (-2,-2), (3,3), (-3,-3)]:
                            draw.text((x+dx, y_start+dy), line, font=font, fill=GOLD)
                        draw.text((x, y_start), line, font=font, fill=WHITE)
                        y_start += 82

                # Price tag animation
                if price and t > 4.5:
                    alpha = min((t - 4.5)/0.8, 1.0)
                    draw.rectangle([WIDTH-280, 80, WIDTH-40, 160], fill=GOLD)
                    draw.text((WIDTH-260, 95), price, font=get_font(52), fill=BG_COLOR)

                # Bottom branding
                draw.text((50, HEIGHT-100), "SM INTERIORS", font=get_font(42), fill=GOLD)
                draw.text((50, HEIGHT-60), "0710 895 737", font=get_font(38), fill=WHITE)

                frames.append(np.array(canvas))

            status.write("Adding music & exporting…")
            clip = ImageSequenceClip(frames, fps=FPS)

            # Download music
            audio_data = requests.get(MUSIC_URL).content
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                tmp.write(audio_data)
                audio_path = tmp.name

            audio = AudioFileClip(audio_path).subclip(0, DURATION).audio_fadeout(0.8)
            final_clip = clip.set_audio(audio)
            os.unlink(audio_path)

            out_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            final_clip.write_videofile(out_path, codec="libx264", audio_codec="aac", fps=FPS, logger=None)

            status.update(label="Your SM Interiors Creative is Ready!", state="complete")

            st.video(out_path)
            with open(out_path, "rb") as f:
                st.download_button(
                    label="Download Video",
                    data=f,
                    file_name="sm_interiors_tip_video.mp4",
                    mime="video/mp4"
                )
            os.unlink(out_path)

st.markdown("<p style='text-align:center; color:#D4AF37; margin-top:50px;'>Made with love for SM Interiors – Dubai & Nairobi</p>", unsafe_allow_html=True)