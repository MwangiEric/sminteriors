# app.py
import streamlit as st, time

st.set_page_config(page_title="6-s typing animation", layout="centered")

# --------------  CSS: animated gradient background + glass card --------------
st.markdown(
    """
    <style>
    /* animated gradient background */
    @keyframes gradientShift {
        0%   {background-position: 0% 50%;}
        50%  {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }
    .main {
        background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e, #0f0c29);
        background-size: 400% 400%;
        animation: gradientShift 12s ease infinite;
    }
    /* glass-morphism card */
    .glass {
        background: rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(7px);
        -webkit-backdrop-filter: blur(7px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 2rem 3rem;
        margin: 3rem auto;
        max-width: 700px;
    }
    /* glowing cursor */
    .cursor {
        display: inline-block;
        width: 2px;
        height: 1.2em;
        background: #00f9ff;
        box-shadow: 0 0 5px #00f9ff, 0 0 10px #00f9ff;
        animation: blink 1s infinite;
    }
    @keyframes blink {
        50% { opacity: 0; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------  UI inside glass card -----------------------
with st.container():
    st.markdown('<div class="glass">', unsafe_allow_html=True)

    st.markdown(
        "<h2 style='text-align:center;color:#ffffff'>"
        "✨ 6-second typing animation ✨</h2>",
        unsafe_allow_html=True,
    )

    sentence = st.text_input(
        "",
        "Hello! This text will be typed in exactly six seconds.",
        placeholder="Type your own sentence…",
    )

    if st.button("▶️ Animate & download"):
        chars = len(sentence)
        delay = 6.0 / max(chars, 1)

        placeholder = st.empty()
        for i in range(1, chars + 1):
            # add glowing cursor while typing
            placeholder.markdown(
                f"<h3 style='font-family:monospace;color:#00f9ff;'>"
                f"{sentence[:i]}<span class='cursor'></span></h3>",
                unsafe_allow_html=True,
            )
            time.sleep(delay)

        # final frame (no cursor)
        placeholder.markdown(
            f"<h3 style='font-family:monospace;color:#00f9ff;'>{sentence}</h3>",
            unsafe_allow_html=True,
        )

        st.download_button(
            label="⬇️ Download final text",
            data=sentence,
            file_name="typed_text.txt",
            mime="text/plain",
        )

    st.markdown("</div>", unsafe_allow_html=True)
