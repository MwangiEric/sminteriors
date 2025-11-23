import streamlit as st
import requests

# Set up Streamlit
st.set_page_config(page_title="SM Interiors - Smart Layout AI", layout="wide")

# Load your Groq API Key
try:
    groq_key = st.secrets["groq_key"]
except KeyError:
    st.error("❌ Groq API key not found. Please check your secrets.")
    st.stop()

# Function to generate AI content using Groq
def generate_ai_content(product_name):
    """Fetch AI-generated content based on the product name"""
    url = "https://api.groq.com/your-ai-endpoint"  # Replace with your actual endpoint
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }
    data = {
        "input": product_name  # Modify as needed based on your API requirements
    }

    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json()  # Return the JSON response
    else:
        st.error("❌ Unable to fetch AI content. Please check the input.")
        return None

# Integrate AI Copy Generation
if st.button("🤖 Generate AI Ad Copy", type="primary"):
    with st.spinner("AI creating marketing copy..."):
        product_name = "Modern Console"  # Example product name; modify as needed
        ai_content = generate_ai_content(product_name)
        
        if ai_content:
            # Assume ai_content has 'headline', 'description', etc.
            st.session_state.ai_copy = {
                "product_name": product_name,
                "headline": ai_content.get("headline"),
                "description": ai_content.get("description"),
                "urgency_text": ai_content.get("urgency"),
                "discount_offer": ai_content.get("discount"),
                "call_to_action": ai_content.get("cta")
            }
            st.success("✅ AI copy generated")
        else:
            st.error("❌ Failed to generate AI copy.")
