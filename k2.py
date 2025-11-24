# app.py  (bullet-proof for Pyodide / Cloud)
import streamlit as st
import numpy as np
import imageio
import tempfile
import shutil
from pathlib import Path
from PIL import Image, ImageDraw

st.set_page_config(page_title="Typing → MP4", layout="centered")

st.markdown(
    """
    <style>
    .main {background: linear-gradient(-45deg,#0f0c29,#302b63,#24243e,#0f0c29); background-size:400% 400%; animation:gradientShift 12s ease infinite;}
    .glass {background:rgba(255,255,255,0.06); border-radius:16px; box-shadow:0 4px 30px rgba(0,0,0,.2); backdrop-filter:blur(7px); border:1px solid rgba(255,255,255,.1); padding:2rem 3rem; margin:3rem auto; max-width:700px;}
    </style>
    """,
    unsafe_allow_html=True,
)

def frame(text: str, W=1920, H=1080):
    img = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    for i in range(H):
        draw.line([(0, i), (W, i)], fill=(30-i//20, 15-i//25, 60-i//30))
    # default bitmap font – no size, no path
    tw, th = draw.textsize(text)
    draw.text(((W-tw)//2, (H-th)//2), text, fill=(0, 245, 255))
    return np.asarray(img)

with st.container():
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;color:#fff'>✨ Typing → MP4 ✨</h2>", unsafe_allow_html=True)
    sentence = st.text_input("", "Hello! This text will be typed in exactly six seconds.")
    if st.button("▶️ Generate MP4"):
        if not sentence: st.warning("Empty text."); st.stop()
        fps, total_frames = 30, 6 * 30
        tmpdir = Path(tempfile.mkdtemp())
        for frm in range(total_frames):
            n = min(int(round(len(sentence) * (frm+1) / total_frames)), len(sentence))
            imageio.imwrite(tmpdir/f"{frm:05d}.png", frame(sentence[:n]))
        out_mp4 = tmpdir/"typing.mp4"
        with imageio.get_writer(out_mp4, fps=fps, codec="libx264", pix_fmt="yuv420p") as w:
            for frm in range(total_frames): w.append_data(imageio.imread(tmpdir/f"{frm:05d}.png"))
        with open(out_mp4,"rb") as f: st.download_button("⬇️ Download MP4", f, "typing.mp4", "video/mp4")
        shutil.rmtree(tmpdir, ignore_errors=True)
    st.markdown("</div>", unsafe_allow_html=True)
