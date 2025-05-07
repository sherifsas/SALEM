import streamlit as st
import io
import base64
import re
import requests
from PIL import Image
import google.generativeai as genai

# Configuration
API_KEY = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else st.text_input("Enter your Google API Key", type="password")
MAX_RETRIES = 3

if not API_KEY:
    st.warning("Please enter your API key to continue.")
    st.stop()

genai.configure(api_key=API_KEY)

# Helper to encode image to base64
def encode_image_to_base64(image):
    buffer = io.BytesIO()
    image = image.convert('RGB')
    image.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

# Analyze completion using Gemini
def get_completion_percentage(current_image, complete_image, runs=10):
    current_base64 = encode_image_to_base64(current_image)
    complete_base64 = encode_image_to_base64(complete_image)

    model = genai.GenerativeModel("gemini-1.5-flash")

    percentages = []
    responses = []

    prompt = [
        {"text": (
            "I'm showing you two images of a construction or structure project. "
            "The first image shows the current state, and the second image shows what the completed project in Building information modeling"
            "which should look like. Based on these images, give me an estimated percentage of completion (just the number, e.g., '65%'). "
            "Then provide a detailed explanation of your reasoning and make a full report in PDF "
        )},
        {"inline_data": {
            "mime_type": "image/jpeg",
            "data": current_base64
        }},
        {"inline_data": {
            "mime_type": "image/jpeg",
            "data": complete_base64
        }}
    ]

    for i in range(runs):
        try:
            response = model.generate_content(prompt)
            text = response.text
            responses.append(text)
            match = re.search(r'(\d+)%', text)
            if match:
                percentages.append(int(match.group(1)))
        except Exception as e:
            responses.append(f"Error in run {i+1}: {str(e)}")

    if percentages:
        average = round(sum(percentages) / len(percentages), 2)
        return average, responses, percentages
    else:
        return None, responses, []

# Streamlit UI
st.title("🏗️ Project Completion Estimator")

st.write("""
Upload two images of your project:
1. The current state of the project
2. What the completed project should look like

The AI will analyze both images and estimate the percentage of completion.
""")

# File upload
current_image_file = st.file_uploader("📷 Upload current state image", type=["jpg", "jpeg", "png"])
complete_image_file = st.file_uploader("🏁 Upload completed state image", type=["jpg", "jpeg", "png"])

if current_image_file and complete_image_file:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Current State")
        current_image = Image.open(current_image_file)
        st.image(current_image, use_container_width=True)

    with col2:
        st.subheader("Completed State")
        complete_image = Image.open(complete_image_file)
        st.image(complete_image, use_container_width=True)

    if st.button("Analyze Completion Percentage"):
        with st.spinner("Analyzing images with 10 runs..."):
            average, responses, percentages = get_completion_percentage(current_image, complete_image)

        st.subheader("📊 Individual Results")
        for i, res in enumerate(responses, 1):
            st.markdown(f"**Run {i}:** {res}")

        if average is not None:
            st.subheader("✅ Final Result")
            st.metric("Average Completion Percentage", f"{average}%")
            st.progress(average / 100)
        else:
            st.warning("Couldn't extract any valid percentages from the AI responses.")
else:
    st.info("Please upload both images to continue.")