# app.py  (Pillow 10 + Pyodide compatible)
import streamlit as st
import numpy as np
import imageio
import tempfile
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="Typing → MP4", layout="centered")

st.markdown(
    """
    <style>
    @keyframes gradientShift{
      0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%}
    }
    .main {
        background: linear-gradient(-45deg,#0f0c29,#302b63,#24243e,#0f0c29);
        background-size:400% 400%; animation:gradientShift 12s ease infinite;
    }
    .glass {
        background:rgba(255,255,255,0.06); border-radius:16px;
        box-shadow:0 4px 30px rgba(0,0,0,.2); backdrop-filter:blur(7px);
        border:1px solid rgba(255,255,255,.1); padding:2rem 3rem;
        margin:3rem auto; max-width:700px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------  frame draw (Pillow 10 safe) -------------
def frame(text: str, W: int = 1920, H: int = 1080):
    img = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    # gradient background
    for i in range(H):
        draw.line([(0, i), (W, i)], fill=(30 - i // 20, 15 - i // 25, 60 - i // 30))

    # font selection (cross-platform)
    try:
        font = ImageFont.truetype(
            ImageFont.FreeTypeFont().font  # default FreeType face
            if hasattr(ImageFont, "FreeTypeFont") and ImageFont.FreeTypeFont
            else ImageFont.load_default(),  # fallback
            size=120,
        )
    except Exception:
        font = ImageFont.load_default()  # last resort bitmap

    # Pillow 10+ API
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    tw, th = right - left, bottom - top
    x, y = (W - tw) // 2, (H - th) // 2 - top
    draw.text((x, y), text, font=font, fill=(0, 245, 255))

    return np.asarray(img)  # RGB numpy array

# -------------  UI -------------
with st.container():
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;color:#ffffff'>✨ Typing animation → MP4 ✨</h2>", unsafe_allow_html=True)

    sentence = st.text_input("", "Hello! This text will be typed in exactly six seconds.", placeholder="Type your own sentence…")

    if st.button("▶️ Generate MP4"):
        if not sentence:
            st.warning("Please enter some text.")
            st.stop()

        fps = 30
        total_frames = 6 * fps
        chars_per_frame = len(sentence) / total_frames

        tmpdir = Path(tempfile.mkdtemp())
        progress = st.progress(0)

        # write frames
        for frm in range(total_frames):
            n = int(round(chars_per_frame * (frm + 1)))
            n = min(n, len(sentence))
            imageio.imwrite(tmpdir / f"{frm:05d}.png", frame(sentence[:n]))
            if frm % 15 == 0:  # reduce I/O
                progress.progress(frm / total_frames)

        progress.empty()

        # assemble MP4
        out_mp4 = tmpdir / "typing.mp4"
        try:
            with imageio.get_writer(out_mp4, fps=fps, codec="libx264", pix_fmt="yuv420p") as w:
                for frm in range(total_frames):
                    w.append_data(imageio.imread(tmpdir / f"{frm:05d}.png"))
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

        # download
        with open(out_mp4, "rb") as f:
            st.download_button(label="⬇️ Download MP4", data=f, file_name="typing.mp4", mime="video/mp4")
        st.success("MP4 ready – right-click → save, or use the button above.")

    st.markdown("</div>", unsafe_allow_html=True)
