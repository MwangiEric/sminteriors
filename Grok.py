import streamlit as st
import random
import hashlib
import requests
import base64

st.set_page_config(page_title="SM DIY Reels Pro", layout="centered")

# Your logo
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png"
logo_b64 = base64.b64encode(requests.get(LOGO_URL, timeout=10).content).decode()

# 20+ Viral DIY Furniture Tip Topics (Nairobi-tested)
DIY_TOPICS = [
    "How to clean white fabric sofa with only Ksh 50 items",
    "Remove scratches from wooden table in 60 seconds",
    "Make your old chair look brand new (no painting)",
    "Eco-friendly polish for teak furniture",
    "Fix wobbly dining table forever",
    "Turn Ksh 200 bleach into luxury leather cleaner",
    "Remove ink stains from couch instantly",
    "Make glass table shine like diamond",
    "Stop leather sofa from cracking (Kenyan weather hack)",
    "Clean velvet headboard without water",
    "Refresh outdoor plastic chairs in 5 minutes",
    "Remove candle wax from wooden surface",
    "Deep clean marble coffee table naturally",
    "Stop fabric sofa from fading in sun",
    "Fix peeling veneer on wardrobe",
    "Remove permanent marker from white furniture",
    "Make brass handles shine again",
    "Clean dusty wooden carvings easily",
    "Restore shine to dull laminate floors",
    "Follow for more tips → DM 0710 895 737"
]

# Brand themes
THEMES = [
    ("#2C1810", "#D4A574", "#FFFFFF"),
    ("#0F0A05", "#FFD700", "#FFFFFF"),
    ("#1E293B", "#FCD34D", "#1E293B"),
]

def get_theme(text):
    h = int(hashlib.md5(text.encode()).hexdigest(), 16)
    return THEMES[h % len(THEMES)]

st.title("SM Interiors — 6-Second DIY Reel Pro")
st.caption("Random viral tip • Final CTA • Ready to charge Ksh 35k+")

# Topic selector
selected_topic = st.selectbox("Choose DIY Tip Topic", DIY_TOPICS, index=0)

if st.button("Generate 6-Second Reel Now", type="primary"):
    with st.spinner("Cooking viral content..."):
        tip = selected_topic
        bg1, bg2, txt_col = get_theme(tip)

        # Split tip and CTA (last line is always CTA)
        lines = tip.strip().split("\n")
        main_tip = "\n".join(lines[:-1]) if "Follow for more" in tip else tip
        cta_line = "Follow for more tips → DM 0710 895 737"

        html = f"""
        <style>body{{margin:0;background:#000;overflow:hidden}}</style>
        <canvas id="c"></canvas>
        <script>
        const canvas = document.getElementById('c');
        const ctx = canvas.getContext('2d');
        canvas.width = 1080; canvas.height = 1920;
        const logo = new Image(); logo.src = "data:image/png;base64,{logo_b64}";
        let frame = 0;
        const totalFrames = 180; // 6 sec @ 30fps

        function draw() {{
            // Background gradient
            const grad = ctx.createLinearGradient(0,0,0,1920);
            grad.addColorStop(0, "{bg1}"); grad.addColorStop(1, "{bg2}");
            ctx.fillStyle = grad; ctx.fillRect(0,0,1080,1920);

            // Logo (top-left, always visible)
            ctx.globalAlpha = 1;
            ctx.drawImage(logo, 60, 60, 180, 90);

            if (frame < 140) {{ // First 4.6s: Typewriter tip
                const shownChars = Math.floor((frame / 140) * {len(main_tip)});
                const text = "{main_tip}".substring(0, shownChars);

                ctx.font = "bold 86px Arial";
                ctx.fillStyle = "{txt_col}";
                ctx.strokeStyle = "#000";
                ctx.lineWidth = 10;
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";

                text.split('\n').forEach((line, i) => {{
                    ctx.strokeText(line, 540, 860 + i*100);
                    ctx.fillText(line, 540, 860 + i*100);
                }});
            }} else {{ // Last 1.4s: CTA screen
                ctx.fillStyle = "rgba(0,0,0,0.7)";
                ctx.fillRect(0, 1200, 1080, 720);

                ctx.font = "bold 90px Arial";
                ctx.fillStyle = "#FFD700";
                ctx.strokeStyle = "#000";
                ctx.lineWidth = 10;
                ctx.textAlign = "center";
                ctx.strokeText("{cta_line}", 540, 1500);
                ctx.fillText("{cta_line}", 540, 1500);

                // Big logo center
                ctx.drawImage(logo, 340, 1350, 400, 200);
            }}

            frame++;
            if (frame <= totalFrames) requestAnimationFrame(draw);
            else {{
                const a = document.createElement('a');
                a.download = 'sm_diy_tip.mp4';
                a.href = canvas.captureStream(30).getVideoTracks?.()[0]?.requestFrame?.() || canvas.toDataURL();
                a.click();
            }}
        }}
        draw();
        </script>
        """
        st.components.v1.html(html, height=1920, width=1080)
        st.success(f"Reel Ready → {tip.split(' → ')[0][:50]}...")
        st.caption("Download starts automatically • 6 seconds • <3MB • Charge Ksh 35k+")