# app.py
import streamlit as st
import numpy as np
import imageio
import tempfile
import shutil
from pathlib import Path
import time

st.set_page_config(page_title="Typing → MP4", layout="centered")

# -------------  cool animated gradient background -------------
st.markdown(
    """
    <style>
    @keyframes gradientShift{
      0%{background-position:0% 50%}
      50%{background-position:100% 50%}
      100%{background-position:0% 50%}
    }
    .main {
        background: linear-gradient(-45deg,#0f0c29,#302b63,#24243e,#0f0c29);
        background-size:400% 400%;
        animation:gradientShift 12s ease infinite;
    }
    .glass {
        background:rgba(255,255,255,0.06);
        border-radius:16px;
        box-shadow:0 4px 30px rgba(0,0,0,.2);
        backdrop-filter:blur(7px);
        -webkit-backdrop-filter:blur(7px);
        border:1px solid rgba(255,255,255,.1);
        padding:2rem 3rem;
        margin:3rem auto;
        max-width:700px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------  draw 1 frame (RGB) -------------
def frame(text_so_far, W=1920, H=1080):
    img = np.zeros((H, W, 3), dtype=np.uint8)
    # vertical gradient
    for i in range(H):
        img[i, :] = (30-i//20, 15-i//25, 60-i//30)
    # glowing cyan text
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale, thick = 4, 8
    (tw, th), _ = cv2.getTextSize(text_so_far, font, scale, thick)
    x, y = (W - tw) // 2, (H + th) // 2
    cv2.putText(img, text_so_far, (x, y), font, scale, (0, 245, 255), thick, cv2.LINE_AA)
    return img[:, :, ::-1]  # BGR → RGB

# -------------  UI -------------
with st.container():
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;color:#ffffff'>✨ Typing animation → MP4 ✨</h2>", unsafe_allow_html=True)

    sentence = st.text_input("", "Hello! This text will be typed in exactly six seconds.", placeholder="Type your own sentence…")

    if st.button("▶️ Generate MP4"):
        chars = len(sentence)
        if chars == 0:
            st.warning("Please enter some text.")
            st.stop()

        fps = 30
        total_frames = 6 * fps
        chars_per_frame = chars / total_frames

        tmpdir = Path(tempfile.mkdtemp())
        progress = st.progress(0)

        # -------------  write frames  -------------
        for frm in range(total_frames):
            n = int(round(chars_per_frame * (frm + 1)))
            n = min(n, chars)
            imageio.imwrite(tmpdir / f"{frm:05d}.png", frame(sentence[:n]))
            if frm % 10 == 0:
                progress.progress(frm / total_frames)

        progress.empty()

        # -------------  assemble MP4  -------------
        out_mp4 = tmpdir / "typing.mp4"
        with imageio.get_writer(out_mp4, fps=fps, codec="libx264", pix_fmt="yuv420p") as w:
            for frm in range(total_frames):
                w.append_data(imageio.imread(tmpdir / f"{frm:05d}.png"))

        # -------------  download button  -------------
        with open(out_mp4, "rb") as f:
            st.download_button(
                label="⬇️ Download MP4",
                data=f,
                file_name="typing.mp4",
                mime="video/mp4"
            )
        st.success("MP4 ready – right-click → save, or use the button above.")

        shutil.rmtree(tmpdir)

    st.markdown("</div>", unsafe_allow_html=True)
