import streamlit as st
from moviepy.editor import *
from moviepy.config import change_settings
import numpy as np
import textwrap
from groq import Groq
import json

# Configure ImageMagick for MoviePy
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

# Function to generate DIY tips using Groq AI
def generate_diy_tips(num_tips=5):
    client = Groq(api_key=st.secrets["groq_key"])
    prompt = f"""
    Generate {num_tips} creative DIY interior design tips for SM Interiors. 
    Each tip should be in the following JSON format:
    {{
        "header": "EXPERT INSIGHT",
        "tip": "The tip text here, as a quote.",
        "footer": "A short catchy phrase for the footer"
    }}
    Make them visually appealing and balanced, inspired by grouping items, using colors, etc.
    Output as a JSON list of these objects.
    """
    
    completion = client.chat.completions.create(
        model="mixtral-8x7b-32768",  # Or use a faster model like llama
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1024,
    )
    
    response = completion.choices[0].message.content
    try:
        tips = json.loads(response)
    except:
        st.error("Failed to parse AI response. Using default tips.")
        tips = [
            {
                "header": "EXPERT INSIGHT",
                "tip": "Group items in odd numbers (e.g., three small objects) for a more visually pleasing and balanced arrangement.",
                "footer": "Elevate Your Desk Style"
            }
        ] * num_tips
    return tips

# Function to generate typewriter animation clip for a given text
def create_typewriter_clip(text, duration=5, fps=30, font='Courier', fontsize=40, color='gold', bg_color='black', width=1080, height=1920):
    # Wrap text to fit within the width
    wrapped_text = textwrap.wrap(text, width=30)  # Adjust width as needed
    full_text = '\n'.join(wrapped_text)
    
    # Calculate number of frames
    num_frames = int(duration * fps)
    char_duration = duration / len(full_text)
    
    def make_frame(t):
        # Create a black background
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Determine how many characters to show
        char_index = min(int(t / char_duration) + 1, len(full_text))
        current_text = full_text[:char_index]
        
        # Create text clip for current text
        txt_clip = TextClip(current_text, fontsize=fontsize, color=color, font=font, bg_color=bg_color)
        txt_w, txt_h = txt_clip.size
        
        # Position text in the center
        txt_clip = txt_clip.set_position(('center', 'center'))
        
        # Composite on background - but since bg_color is set, might not need, but for safety
        return txt_clip.get_frame(0)
    
    clip = VideoClip(make_frame, duration=duration)
    return clip

st.title("SM Interiors DIY Tips Video Generator")

# Generate tips using AI
diy_tips = generate_diy_tips(5)

# Button to generate video
if st.button("Generate TikTok Video"):
    clips = []
    
    # Add title clip
    title_clip = TextClip("Text Typewriter", fontsize=60, color='gold', font='Courier', bg_color='black').set_position('center').set_duration(2)
    title_clip = title_clip.on_color(size=(1080, 1920), color=(0,0,0), pos=('center', 'center'))
    clips.append(title_clip)
    
    for tip in diy_tips:
        # Full duration for this tip section
        section_duration = 7
        
        # Background clip
        bg_clip = ColorClip(size=(1080, 1920), color=(0,0,0)).set_duration(section_duration)
        
        # Header clip (static, full duration)
        header_clip = TextClip(tip["header"], fontsize=30, color='gold', font='Courier').set_position(('center', 100)).set_duration(section_duration)
        
        # Typewriter tip clip (starts after 1 second, duration 5)
        tip_clip = create_typewriter_clip(tip["tip"], duration=5).set_start(1)
        
        # Footer clip (static, appears after 6 seconds)
        footer_clip = TextClip(tip["footer"], fontsize=25, color='gray', font='Courier').set_position(('center', 1920 - 200)).set_duration(1).set_start(6)
        footer2_clip = TextClip("SM Interiors", fontsize=20, color='gold', font='Courier').set_position(('center', 1920 - 100)).set_duration(1).set_start(6)
        
        # Combine for this tip
        combined_tip = CompositeVideoClip([
            bg_clip,
            header_clip,
            tip_clip,
            footer_clip,
            footer2_clip
        ])
        
        clips.append(combined_tip)
    
    # Concatenate all clips
    final_video = concatenate_videoclips(clips, method="compose")
    
    # Write to file
    video_path = "sm_interiors_diy_tips.mp4"
    final_video.write_videofile(video_path, fps=30, codec='libx264')
    
    # Display video in Streamlit
    st.video(video_path)

st.markdown("""
Note: 
- This app requires MoviePy, Groq, and FFmpeg installed. Install via `pip install moviepy groq`.
- For Streamlit Cloud, create a `packages.txt` file in your repo with:
