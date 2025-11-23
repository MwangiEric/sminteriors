import streamlit as st
import io, requests, math, tempfile, time, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip
from rembg import remove

st.set_page_config(page_title="SM Interiors – Animated Creative", layout="centered", page_icon="circle")

# ────────────────────────────── SETTINGS ──────────────────────────────
WIDTH, HEIGHT = 720, 1280
FPS = 30
DURATION = 8

BG = "#1E0F0B"
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

def ease_out_elastic(t):
    if t >= 1: 
        return 1
    c4 = (2 * math.pi) / 3
    return 2**(-10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

# ────────────────────────────── MAIN APP ──────────────────────────────
st.title("SM Interiors – Animated Gold Creative Maker")

col1, col2 = st.columns(2)
with col1:
    product_img = st.file_uploader("Product Image (optional)", type=["png","jpg","jpeg"])
with col2:
    price = st.text_input("Price", "Ksh 12,500")
    tip_text = st.text_area("Text / Caption", "Unveiling the Horizon Media Console, a symphony of sleek design and functional elegance, ready to transform your living space.", height=120)

if st.button("Generate Animated Video", type="primary"):
    with st.status("Drawing your luxury creative…", expanded=True) as status:
        status.write("Processing product image…")
        product = None
        if product_img:
            raw = Image.open(product_img).convert("RGBA")
            clean = remove(raw.tobytes())
            product = Image.open(io.BytesIO(clean)).convert("RGBA").resize((600, 600), Image.LANCZOS)

        logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA").resize((220, 110), Image.LANCZOS)

        status.write("Creating hand-drawn animation frames…")
        frames = []

        # Predefine gold shape paths (circles, arcs, arrows)
        shapes = [
            ("arc", (-100, -100, 400, 400), 0, 90, 25),
            ("arc", (WIDTH-400, 600, WIDTH+100, 1200), 270, 360, 22),
            ("ellipse", (50, 100, 350, 400), 20),
            ("ellipse", (WIDTH-380, 800, WIDTH-80, 1100), 18),
            ("line", (WIDTH-200, 100, WIDTH-50, 100), 30),
            ("line", (WIDTH-200, 100, WIDTH-150, 150), 25),
            ("line", (WIDTH-150, 150, WIDTH-50, 150), 25),
        ]

        for i in range(FPS * DURATION):
            t = i / (FPS * DURATION)
            canvas = Image.new("RGB", (WIDTH, HEIGHT), BG)
            draw = ImageDraw.Draw(canvas)

            # 1. Draw gold shapes progressively
            for idx, shape in enumerate(shapes):
                if t > idx * 0.08:
                    progress = min((t - idx*0.08) / 0.15, 1.0)
                    if shape[0] == "arc":
                        draw.arc(shape[1], start=shape[2], end=shape[2] + (shape[3]-shape[2])*progress, fill=GOLD, width=shape[4])
                    elif shape[0] == "ellipse":
                        draw.ellipse(shape[1], outline=GOLD, width=shape[2])
                    elif shape[0] == "line":
                        x1, y1, x2, y2 = shape[1]
                        draw.line([(x1, y1), (x1 + (x2-x1)*progress, y1 + (y2-y1)*progress)], fill=GOLD, width=shape[2])

            # 2. Logo fade in
            if t > 0.3:
                alpha = min((t - 0.3)/0.3, 1.0)
                logo_layer = logo.copy()
                logo_layer.putalpha(int(255 * alpha))
                canvas.paste(logo_layer, (40, 40), logo_layer)

            # 3. Product elastic reveal
            if product and t > 1.2:
                scale = ease_out_elastic(min((t - 1.2)/0.8, 1.0))
                w = int(600 * scale)
                h = int(600 * scale)
                resized = product.resize((w, h), Image.LANCZOS)
                x = (WIDTH - w) // 2
                y = int(HEIGHT * 0.45 - h//2 + math.sin(t*12)*12)
                canvas.paste(resized, (x, y), resized)

            # 4. Typing text effect (top to bottom)
            if t > 2.0:
                chars_visible = int((t - 2.0) * 45)  # speed
                display = tip_text[:chars_visible]

                lines = []
                words = display.split()
                line = ""
                for word in words:
                    test = line + (" " + word if line else word)
                    if draw.textbbox((0,0), test, font=get_font(48))[2] < WIDTH - 120:
                        line = test
                    else:
                        lines.append(line)
                        line = word
                if line: lines.append(line)

                y = 180
                for line in lines:
                    bbox = draw.textbbox((0,0), line, font=get_font(48))
                    w = bbox[2] - bbox[0]
                    x = (WIDTH - w) // 2
                    # Gold stroke
                    for dx, dy in [(2,2), (-2,-2), (3,3), (-3,-3)]:
                        draw.text((x+dx, y+dy), line, font=get_font(48), fill=GOLD)
                    draw.text((x, y), line, font=get_font(48), fill=WHITE)
                    y += 68

            # 5. Price tag draw-in animation
            if t > 4.5:
                prog = min((t - 4.5)/0.8, 1.0)
                # Box
                draw.rectangle([WIDTH-300, 70, WIDTH-300 + 260*prog, 170], outline=GOLD, width=6)
                draw.rectangle([WIDTH-300, 70, WIDTH-40, 170], fill=GOLD if prog > 0.8 else None)
                # Text
                if prog > 0.6:
                    draw.text((WIDTH-280, 92), price, font=get_font(52), fill=BG if prog > 0.8 else GOLD)

            # 6. Bottom branding
            if t > 5.5:
                draw.text((50, HEIGHT-110), "SM INTERIORS", font=get_font(44), fill=GOLD)
                draw.text((50, HEIGHT-70), "0710 895 737", font=get_font(40), fill=WHITE)

            frames.append(np.array(canvas))

        status.write("Adding music…")
        clip = ImageSequenceClip(frames, fps=FPS)
        audio_data = requests.get(MUSIC_URL).content
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(audio_data)
            audio = AudioFileClip(tmp.name).subclip(0, DURATION).audio_fadeout(1.0)
            final = clip.set_audio(audio)
            os.unlink(tmp.name)

        status.write("Exporting video…")
        out_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
        
        # FIXED: Corrected the video writing line
        final.write_videofile(out_path, codec="libx264", audio_codec="aac", fps=FPS, logger=None)

        status.update(label="Your animated creative is ready!", state="complete")
        st.video(out_path)
        with open(out_path, "rb") as f:
            st.download_button("Download Video", f, "sm_animated_creative.mp4", "video/mp4")
        os.unlink(out_path)