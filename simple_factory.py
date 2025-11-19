# app.py — S&M TikTok AI + FREE Trending Music (no hosting)
import streamlit as st
from PIL import Image, ImageDraw
import base64, io, json, math, requests, tempfile, re, os, random
import imageio.v3 as imageio
import moviepy.editor as mp
from groq import Groq

st.set_page_config(page_title="S&M TikTok AI", layout="centered")
st.title("S&M Interiors × TikTok AI")
st.caption("Upload → Get 9s Viral Video with Trending Sound · 100% FREE Forever")

# ====================== FREE GROQ ======================
client = Groq(api_key=st.secrets["GROQ_KEY"])  # ← Add your free key in Streamlit Secrets

# ====================== CONFIG ======================
WIDTH, HEIGHT = 1080, 1920
FPS, DURATION = 30, 9
N_FRAMES = FPS * DURATION
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png"

# ====================== FREE TRENDING MUSIC (hotlink allowed) ======================
MUSIC_LINKS = [
    "https://cdn.org/audio/2025-trending-1.mp3",           # ← Replace with real links below
    "https://uppbeat.io/track/synapse-fire/link-me-up/mp3",           # Real 2025 banger
    "https://uppbeat.io/track/ikson-new/world/mp3",
    "https://uppbeat.io/track/prigida/moving-on/mp3",
    "https://uppbeat.io/track/jeff-kaale/midnight/mp3",
    "https://cdn.pixabay.com/download/audio/2024/08/15/audio_5a54d0f2f6.mp3?filename=upbeat-background-171614.mp3"
]
MUSIC_URL = random.choice(MUSIC_LINKS)  # Random trending sound every time

# ====================== AI ======================
def get_caption(b64):
    try:
        r = client.chat.completions.create(
            messages=[{"role": "user", "content": [
                {"type": "text", "text": "VIRAL TikTok hook for this furniture in 6–10 words. First 3 words must GRAB attention."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
            ]}],
            model="llama-3.2-11b-vision-preview",
            max_tokens=25
        )
        return r.choices[0].message.content.strip().strip('"')
    except:
        return "This sofa changed my life!"

def get_layout(model, price):
    try:
        r = client.chat.completions.create(
            messages=[{"role": "user", "content": f"Return ONLY valid JSON for 1080×1920 TikTok:\n[{{\"role\":\"logo\",\"x\":int,\"y\":int,\"w\":int,\"h\":int}}, ...]\nProduct: {model} | Price: {price} | Make it VIRAL"}],
            model="llama-3.2-90b-text-preview",
            max_tokens=400
        )
        return json.loads(re.search(r"\[.*\]", r.choices[0].message.content, re.DOTALL).group(0))
    except:
        return [
            {"role":"logo","x":80,"y":80,"w":360,"h":180},
            {"role":"product","x":40,"y":280,"w":1000,"h":1300},
            {"role":"price","x":100,"y":1620,"w":880,"h":200},
            {"role":"contact","x":100,"y":1850,"w":880,"h":100}
        ]

# ====================== DRAW FRAME ======================
def draw_frame(t, img, boxes, price, contact, caption):
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), "#000000")
    draw = ImageDraw.Draw(canvas)

    # Dark gradient
    for y in range(HEIGHT):
        alpha = y / HEIGHT
        draw.line([(0,y),(WIDTH,y)], fill=(int(10+20*alpha), int(5+15*alpha), int(20+30*alpha)))

    logo = Image.open(requests.get(LOGO_URL, stream=True).raw).convert("RGBA")
    for b in boxes:
        if b["role"] == "logo":
            canvas.paste(logo.resize((b["w"], b["h"])), (b["x"], b["y"]), logo)
        if b["role"] == "product":
            pulse = 1.0 + 0.05 * math.sin(t * 5)
            w2, h2 = int(b["w"]*pulse), int(b["h"]*pulse)
            prod = img.resize((w2, h2))
            canvas.paste(prod, (b["x"]+(b["w"]-w2)//2, b["y"]+(b["h"]-h2)//2), prod)
        if b["role"] == "price":
            bounce = 15 * math.sin(t * 4)
            draw.rounded_rectangle([b["x"], b["y"]+bounce, b["x"]+b["w"], b["y"]+b["h"]+bounce], radius=40, fill="#D4AF37")
            draw.text((b["x"]+b["w"]//2, b["y"]+b["h"]//2+bounce), price, fill="white", anchor="mm", font_size=120, stroke_width=6, stroke_fill="black")
        if b["role"] == "contact":
            draw.text((b["x"]+b["w"]//2, b["y"]+b["h"]//2), contact, fill="#D4AF37", anchor="mm", font_size=60)

    # BIG hook first 2 seconds
    if t < 2.0:
        draw.text((WIDTH//2, 300), caption.upper(), fill="white", anchor="mt", font_size=140, stroke_width=8, stroke_fill="black")
    else:
        draw.text((WIDTH//2, 150), caption.upper(), fill="white", anchor="mt", font_size=90, stroke_width=5, stroke_fill="black")

    return canvas

# ====================== UI ======================
col1, col2 = st.columns(2)
with col1:
    uploaded = st.file_uploader("Product Image", type=["png","jpg","jpeg"])
with col2:
    model = st.text_input("Product", "L-Shaped Luxury Sofa")
    price = st.text_input("Price", "KES 14,500")
    contact = st.text_input("Contact", "0710 338 377 • sminteriors.co.ke")

if st.button("Generate Viral TikTok Video", type="primary", use_container_width=True):
    if not uploaded:
        st.error("Upload an image first!")
    else:
        with st.spinner("Creating your viral video with trending sound..."):
            img = Image.open(uploaded).convert("RGBA")
            buf = io.BytesIO(); img.save(buf, format="PNG"); b64 = base64.b64encode(buf.getvalue()).decode()
            caption = get_caption(b64)
            boxes = get_layout(model, price)

            # Generate silent video
            frames = [draw_frame(i/FPS, img, boxes, price, contact, caption) for i in range(N_FRAMES)]
            silent_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            imageio.imwrite(silent_path, frames, fps=FPS, codec="libx264", pixelformat="yuv420p")

            # Add trending music (no hosting!)
            audio_temp = "temp_music.mp3"
            urllib.request.urlretrieve(MUSIC_URL, audio_temp)
            video = mp.VideoFileClip(silent_path)
            audio = mp.AudioFileClip(audio_temp).subclip(0, 9).volumex(0.7)
            final_video = video.set_audio(audio)
            final_path = silent_path.replace(".mp4", "_with_music.mp4")
            final_video.write_videofile(final_path, codec="libx264", audio_codec="aac", fps=FPS)

            # Cleanup
            os.unlink(silent_path); os.unlink(audio_temp)

        expander = st.expander("Your Viral Video Ready!")
        with expander:
            st.success(f"**Hook:** {caption}")
            st.video(final_path)
            with open(final_path, "rb") as f:
                st.download_button("Download TikTok Video", f, f"S&M_{model.replace(' ', '_')}.mp4", "video/mp4")
        st.balloons()
