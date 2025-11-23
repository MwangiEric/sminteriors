import streamlit as st
from moviepy.editor import *
import numpy as np
import textwrap

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
        char_index = int(t / char_duration)
        current_text = full_text[:char_index]
        
        # Create text clip for current text
        txt_clip = TextClip(current_text, fontsize=fontsize, color=color, font=font, align='center')
        txt_w, txt_h = txt_clip.size
        
        # Position text in the center
        txt_clip = txt_clip.set_position(('center', 'center'))
        
        # Composite on black background
        final_clip = CompositeVideoClip([txt_clip], size=(width, height)).set_duration(0.1)  # Short duration for frame
        return final_clip.get_frame(0)
    
    clip = VideoClip(make_frame, duration=duration)
    return clip

# Predefined DIY tips for SM Interiors (creatively generated)
diy_tips = [
    {
        "header": "EXPERT INSIGHT",
        "tip": "Group items in odd numbers (e.g., three small objects) for a more visually pleasing and balanced arrangement.",
        "footer": "Elevate Your Desk Style"
    },
    {
        "header": "EXPERT INSIGHT",
        "tip": "Use mirrors strategically to reflect light and make small rooms feel larger and more open.",
        "footer": "Maximize Your Space"
    },
    {
        "header": "EXPERT INSIGHT",
        "tip": "Incorporate plants to add life and improve air quality while enhancing the aesthetic appeal of your home.",
        "footer": "Bring Nature Indoors"
    },
    {
        "header": "EXPERT INSIGHT",
        "tip": "Mix textures like wood, metal, and fabric to create depth and interest in your decor.",
        "footer": "Texture Play"
    },
    {
        "header": "EXPERT INSIGHT",
        "tip": "Repurpose old furniture with a fresh coat of paint for an affordable and eco-friendly update.",
        "footer": "Sustainable Styling"
    }
]

st.title("SM Interiors DIY Tips Video Generator")

# Button to generate video
if st.button("Generate TikTok Video"):
    clips = []
    
    # Add title clip
    title_clip = TextClip("Text Typewriter", fontsize=60, color='gold', font='Courier', bg_color='black').set_position('center').set_duration(2)
    title_clip = title_clip.resize(newsize=(1080, 1920))
    clips.append(title_clip)
    
    for tip in diy_tips:
        # Header clip (static)
        header_clip = TextClip(tip["header"], fontsize=30, color='gold', font='Courier', bg_color='black').set_position(('center', 100)).set_duration(1)
        
        # Typewriter tip clip
        tip_clip = create_typewriter_clip(tip["tip"], duration=5)
        
        # Footer clip (static)
        footer_clip = TextClip(tip["footer"], fontsize=25, color='gray', font='Courier', bg_color='black').set_position(('center', height - 200)).set_duration(1)
        footer2_clip = TextClip("SM Interiors", fontsize=20, color='gold', font='Courier', bg_color='black').set_position(('center', height - 100)).set_duration(1)
        
        # Combine for this tip
        combined_tip = CompositeVideoClip([
            header_clip,
            tip_clip,
            footer_clip,
            footer2_clip
        ], size=(1080, 1920)).set_duration(7)  # Total for this tip: 1 (header) + 5 (type) + 1 (footer)
        
        clips.append(combined_tip)
    
    # Concatenate all clips
    final_video = concatenate_videoclips(clips, method="compose")
    
    # Write to file
    video_path = "sm_interiors_diy_tips.mp4"
    final_video.write_videofile(video_path, fps=30, codec='libx264')
    
    # Display video in Streamlit
    st.video(video_path)

st.markdown("Note: This app requires MoviePy and FFmpeg installed. Install via `pip install moviepy` and ensure FFmpeg is in your PATH.")
