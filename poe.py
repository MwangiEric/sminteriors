import streamlit as st
import json
import base64
from PIL import Image
from io import BytesIO

# Load the JSON content
json_content = '''YOUR_JSON_HERE'''  # Replace with actual JSON content

# Parse the JSON
data = json.loads(json_content)

# Streamlit app setup
st.set_page_config(page_title="Futuristic Canvas Viewer", layout="wide")

# Header and layout
st.title("Futuristic Canvas Viewer")
st.subheader(f"Version: {data['version']}")

# Sidebar for options
st.sidebar.header("Customization Options")

# Display objects
for obj in data['objects']:
    if obj['type'] == 'rect':
        # Settings for rectangles
        st.sidebar.subheader("Rectangle Properties")
        left = st.sidebar.number_input("Left", value=obj['left'])
        top = st.sidebar.number_input("Top", value=obj['top'])
        width = st.sidebar.number_input("Width", value=obj['width'])
        height = st.sidebar.number_input("Height", value=obj['height'])
        fill_color = st.sidebar.color_picker("Fill Color", obj['fill'])

        st.write(f"Rectangle: left={left}, top={top}, width={width}, height={height}, fill={fill_color}")

    elif obj['type'] == 'image':
        if 'src' in obj:
            image_data = obj['src'].split(',')[1]
            image = Image.open(BytesIO(base64.b64decode(image_data)))
            st.image(image, caption="Image", use_column_width=True)

    elif obj['type'] == 'group':
        st.write(f"Group: left={obj['left']}, top={obj['top']}, has controls={obj['hasControls']}")

# Button to save changes
if st.button("Save Changes"):
    # Here you can implement saving logic
    st.success("Changes saved successfully!")

# Footer
st.markdown("""
---
&copy; 2025 Futuristic Canvas Viewer
Made with ❤️ by [Your Name](https://www.yourwebsite.com)
""")
