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
def create_typewriter_clip(text, duration=5, fps=30, font='Courier', fontsize=40, color='gold', bg_color='black', width=1080, height=1920, position=('center', 'center')):
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
        
        # Position text
        txt_clip = txt_clip.set_position(position)
        
        # Get frame
        return txt_clip.get_frame(0)
    
    clip = VideoClip(make_frame, duration=duration)
    return clip

st.title("SM Interiors DIY Tips Video Generator")

# Photoshop-like layout controls: User inputs for coordinates and styles
st.subheader("Customize Layout (Photoshop-like Coordinates)")
width = 1080
height = 1920

# Header position
header_x = st.number_input("Header X Position (0 to 1080, or 'center')", value="center")
header_y = st.number_input("Header Y Position (0 to 1920)", min_value=0, max_value=height, value=100)
if header_x != "center":
    header_x = int(header_x)
header_position = (header_x, header_y)

# Tip position
tip_x = st.number_input("Tip X Position (0 to 1080, or 'center')", value="center")
tip_y = st.number_input("Tip Y Position (0 to 1920)", min_value=0, max_value=height, value="center")
if tip_x != "center":
    tip_x = int(tip_x)
if tip_y != "center":
    tip_y = int(tip_y)
tip_position = (tip_x, tip_y)

# Footer position
footer_x = st.number_input("Footer X Position (0 to 1080, or 'center')", value="center")
footer_y = st.number_input("Footer Y Position (0 to 1920)", min_value=0, max_value=height, value=height - 200)
if footer_x != "center":
    footer_x = int(footer_x)
footer_position = (footer_x, footer_y)

# SM Interiors footer position
sm_x = st.number_input("SM Interiors X Position (0 to 1080, or 'center')", value="center")
sm_y = st.number_input("SM Interiors Y Position (0 to 1920)", min_value=0, max_value=height, value=height - 100)
if sm_x != "center":
    sm_x = int(sm_x)
sm_position = (sm_x, sm_y)

# Other customizations
header_fontsize = st.number_input("Header Font Size", min_value=10, max_value=100, value=30)
tip_fontsize = st.number_input("Tip Font Size", min_value=10, max_value=100, value=40)
footer_fontsize = st.number_input("Footer Font Size", min_value=10, max_value=100, value=25)
sm_fontsize = st.number_input("SM Interiors Font Size", min_value=10, max_value=100, value=20)

font = st.text_input("Font", value="Courier")
header_color = st.color_picker("Header Color", value="#FFD700")  # Gold
tip_color = st.color_picker("Tip Color", value="#FFD700")
footer_color = st.color_picker("Footer Color", value="#808080")  # Gray
sm_color = st.color_picker("SM Interiors Color", value="#FFD700")
bg_color = st.color_picker("Background Color", value="#000000")

# Generate tips using AI
diy_tips = generate_diy_tips(5)

# Button to generate video
if st.button("Generate TikTok Video"):
    clips = []
    
    # Add title clip
    title_clip = TextClip("Text Typewriter", fontsize=60, color=tip_color, font=font, bg_color=bg_color).set_position('center').set_duration(2)
    title_clip = title_clip.on_color(size=(width, height), color=(0,0,0), pos=('center', 'center'))
    clips.append(title_clip)
    
    for tip in diy_tips:
        # Full duration for this tip section
        section_duration = 7
        
        # Background clip
        bg_clip = ColorClip(size=(width, height), color=(0,0,0)).set_duration(section_duration)
        
        # Header clip (static, full duration)
        header_clip = TextClip(tip["header"], fontsize=header_fontsize, color=header_color, font=font).set_position(header_position).set_duration(section_duration)
        
        # Typewriter tip clip (starts after 1 second, duration 5)
        tip_clip = create_typewriter_clip(tip["tip"], duration=5, fps=30, font=font, fontsize=tip_fontsize, color=tip_color, bg_color=bg_color, width=width, height=height, position=tip_position).set_start(1)
        
        # Footer clip (static, appears after 6 seconds)
        footer_clip = TextClip(tip["footer"], fontsize=footer_fontsize, color=footer_color, font=font).set_position(footer_position).set_duration(1).set_start(6)
        sm_clip = TextClip("SM Interiors", fontsize=sm_fontsize, color=sm_color, font=font).set_position(sm_position).set_duration(1).set_start(6)
        
        # Combine for this tip
        combined_tip = CompositeVideoClip([
            bg_clip,
            header_clip,
            tip_clip,
            footer_clip,
            sm_clip
        ])
        
        clips.append(combined_tip)
    
    # Concatenate all clips
    final_video = concatenate_videoclips(clips, method="compose")
    
    # Write to file
    video_path = "sm_interiors_diy_tips.mp4"
    final_video.write_videofile(video_path, fps=30, codec='libx264')
    
    # Display video in Streamlit
    st.video(video_path)

st.markdown("Note: \n- This app requires MoviePy, Groq, and FFmpeg installed. Install via `pip install moviepy groq`.\n- For Streamlit Cloud, create a `packages.txt` file in your repo with:\n```\nimagemagick\nfonts-dejavu\n```\n- This ensures ImageMagick is installed for text rendering and fonts are available.\n- Coordinates are in pixels, with (0,0) at top-left. Use 'center' for automatic centering on that axis.")
