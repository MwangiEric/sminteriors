import streamlit as st
from moviepy.editor import *
from PIL import Image
import os
import io
import requests
from io import BytesIO
import numpy as np
from tempfile import NamedTemporaryFile

# Your assets
LOGO_URL = "https://ik.imagekit.io/ericmwangi/c&h.png?updatedAt=1761860288449"
WHATSAPP_ICON_URL = "https://ik.imagekit.io/ericmwangi/whatsapp.png?updatedAt=1765797099945"
TIKTOK_ICON_URL = "https://ik.imagekit.io/ericmwangi/tiktok.png?updatedAt=1765799624640"
MUSIC_URL = "https://ik.imagekit.io/ericmwangi/advertising-music-308403.mp3?updatedAt=1764101548797"  # Your track!

@st.cache_data
def download_image(url):
    response = requests.get(url)
    return Image.open(BytesIO(response.content))

@st.cache_data
def download_music(url):
    response = requests.get(url)
    temp_file = NamedTemporaryFile(delete=False, suffix=".mp3")
    temp_file.write(response.content)
    temp_file.close()
    return temp_file.name

logo_img = download_image(LOGO_URL)
whatsapp_img = download_image(WHATSAPP_ICON_URL)
tiktok_img = download_image(TIKTOK_ICON_URL)

# App UI
st.set_page_config(page_title="Car & Homes Hub Ads", layout="centered")
st.title("🚗 Car & Homes Hub - Video Ad Generator")
st.markdown("**Upload photos → Instant 10s ad with upbeat music & strong CTA**")

# Inputs
col1, col2 = st.columns(2)
with col1:
    model = st.text_input("Car Model", "Subaru XV")
    price = st.text_input("Price", "KSh 3,800,000")
    location = st.text_input("Location", "Westlands, Nairobi")
with col2:
    phone = st.text_input("Phone / WhatsApp", "+254 700 000 000")
    cta_text = st.text_input("Call to Action", "Visit Us Today!")

specs = st.text_area("Key Specs (one per line)", 
    "2.0L Boxer Engine\nSymmetrical AWD\nEyeSight Safety\nPremium Interior\nApple CarPlay")

uploaded_files = st.file_uploader("Upload 3-4 car photos (front • interior • rear • side)", 
                                  type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files and len(uploaded_files) >= 3:
    st.success("Photos loaded – ready to generate!")
    cols = st.columns(4)
    for i in range(min(4, len(uploaded_files))):
        cols[i].image(uploaded_files[i], use_column_width=True)

if st.button("🎬 Generate Ad with Upbeat Music", type="primary"):
    if len(uploaded_files) < 3:
        st.error("Upload at least 3 photos")
    else:
        with st.spinner("Downloading music & generating ad..."):
            # Images
            temp_images = []
            for i in range(min(4, len(uploaded_files))):
                path = f"temp_{i}.jpg"
                Image.open(uploaded_files[i]).save(path)
                temp_images.append(path)
            while len(temp_images) < 4:
                temp_images.append(temp_images[-1])

            # Download music
            music_path = download_music(MUSIC_URL)

            # Video setup
            size = (1080, 1920)
            duration = 10
            fps = 30

            # Pan & zoom slides
            clips = []
            durations = [3.2, 3.0, 2.0, 1.8]
            zooms = [[1.0, 1.4], [1.05, 1.35], [1.0, 1.3], [1.1, 1.15]]
            pans = [["center", "center"], ["center", "left"], ["center", "top"], ["right", "center"]]

            current_time = 0
            for i in range(4):
                clip = ImageClip(temp_images[i]).set_duration(durations[i]).set_start(current_time)
                clip = clip.resize(height=size[1] * max(zooms[i]))
                clip = clip.resize(lambda t: zooms[i][0] + (zooms[i][1] - zooms[i][0]) * (t / durations[i]))
                start_pos, end_pos = pans[i]
                x_map = {"left": 0.3, "center": 0.5, "right": 0.7}
                y_map = {"top": 0.3, "center": 0.5, "bottom": 0.7}
                clip = clip.set_position(lambda t: (
                    x_map[start_pos] + (t / durations[i]) * (x_map[end_pos] - x_map[start_pos]),
                    y_map.get(start_pos, 0.5) + (t / durations[i]) * (y_map.get(end_pos, 0.5) - y_map.get(start_pos, 0.5))
                ))
                clips.append(clip)
                current_time += durations[i]

            bg = ColorClip(size=size, color=(8, 12, 30), duration=duration)
            video = CompositeVideoClip([bg] + clips)

            # Hook (model name)
            hook = TextClip(model.upper(), fontsize=100, color="white", font="Arial-Black")
            hook = hook.set_position("center").set_start(0.5).set_duration(4).fadein(1).fadeout(1)

            # Specs
            specs_clip = TextClip("\n".join(specs.split("\n")), fontsize=50, color="#FFD700", align="center")
            specs_clip = specs_clip.set_position("center").set_start(3).set_duration(4).fadein(1.2)

            # CTA (price, location, phone, text)
            cta_lines = [f"From {price}", location, phone, cta_text]
            cta_clip = TextClip("\n".join(cta_lines), fontsize=65, color="white", font="Arial-Bold", align="center")
            cta_clip = cta_clip.set_position("center").set_start(7).set_duration(3).fadein(0.8)

            # Logo
            logo_clip = ImageClip(np.array(logo_img.convert("RGBA"))).resize(height=120).set_duration(duration)
            logo_clip = logo_clip.set_position(("center", "bottom")).margin(bottom=50, opacity=0).fadein(1)

            # Social icons in CTA
            wa_clip = ImageClip(np.array(whatsapp_img)).resize(width=100).set_duration(3).set_start(7)
            wa_clip = wa_clip.set_position((0.35, 0.85), relative=True)
            tt_clip = ImageClip(np.array(tiktok_img)).resize(width=100).set_duration(3).set_start(7)
            tt_clip = tt_clip.set_position((0.65, 0.85), relative=True)

            video = CompositeVideoClip([video, hook, specs_clip, cta_clip, logo_clip, wa_clip, tt_clip], size=size)

            # Music
            music = AudioFileClip(music_path).subclip(0, duration).volumex(0.35)  # Perfect volume balance
            video = video.set_audio(music)

            # Export
            video_bytes = io.BytesIO()
            video.write_videofile(video_bytes, fps=fps, codec="libx264", audio_codec="aac", bitrate="10000k")
            video_bytes.seek(0)

            st.success("🎉 Premium ad ready with your upbeat music!")
            st.video(video_bytes)
            st.download_button("📥 Download MP4", data=video_bytes, file_name=f"CarAndHomesHub_{model.replace(' ', '_')}.mp4", mime="video/mp4")

            # Cleanup
            for f in temp_images + [music_path]:
                if os.path.exists(f):
                    os.remove(f)

st.caption("© Car & Homes Hub • Professional 10s ads for social media")