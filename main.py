import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io
import re
import google.generativeai as genai
import ast

# ─────────────────────────────────────────────
# Configure Gemini API
# IMPORTANT: Replace with your actual Gemini API key, preferably using st.secrets
genai.configure(api_key="YOUR_GEMINI_API_KEY") 

# ─────────────────────────────────────────────
# Streamlit UI
st.set_page_config(page_title="AI POWERED CALCULATOR", layout="centered")
st.title("🧠 AI-POWERED MATHS SOLVER")

st.sidebar.header("🎨 Drawing Tools")
pen_color = st.sidebar.color_picker("Pen Color", "#FFFF00")
stroke_width = st.sidebar.slider("Pen Width", 1, 50, 7)
bg_color = st.sidebar.color_picker("Canvas Background", "#000000")
drawing_mode = st.sidebar.selectbox("Drawing Mode", ["freedraw", "transform"])

# ─────────────────────────────────────────────
# Canvas
canvas_result = st_canvas(
    fill_color="rgba(0, 0, 0, 0)",
    stroke_width=stroke_width,
    stroke_color=pen_color,
    background_color=bg_color,
    update_streamlit=True,
    height=400,
    width=600,
    drawing_mode=drawing_mode,
    key="canvas",
)

# ─────────────────────────────────────────────
# Image Preparation
byte_im = None
if canvas_result.image_data is not None and canvas_result.image_data.any():
    img = Image.fromarray(canvas_result.image_data.astype("uint8"))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    byte_im = buf.getvalue()

    # Show download option
    st.download_button(
        label="⬇️ Download Drawing as PNG",
        data=byte_im,
        file_name="drawing.png",
        mime="image/png"
    )

# ─────────────────────────────────────────────
# Solve Image with Gemini
def analyze_image(image_bytes):
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    
    # The prompt has been slightly simplified for clarity
    prompt = (
        "You are an expert math problem solver. Analyze the user's drawing of a math problem. "
        "Identify the mathematical expression and solve it. "
        "Return the result ONLY as a Python list of dictionaries, like: [{'expr': '2 + 2', 'result': 4}]. "
        "Do NOT use markdown, backticks, or any other formatting. The output must be a clean string that can be parsed by Python's `ast.literal_eval`."
    )

    image = Image.open(io.BytesIO(image_bytes))
    response = model.generate_content([prompt, image])
    
    try:
        # **FIX 1: CLEAN THE RESPONSE TEXT**
        # Remove markdown backticks and the 'json' language specifier.
        cleaned_text = re.sub(r'^```json\s*|```$', '', response.text.strip())
        
        # Parse the cleaned string
        parsed = ast.literal_eval(cleaned_text)

    except Exception as e:
        st.error(f"❌ Could not parse Gemini response: {e}")
        st.text("Raw response from API:")
        st.code(response.text, language="text") # Use st.code to display raw response
        return None
    
    return parsed

# ─────────────────────────────────────────────
# Trigger solve button
if st.button("🔍 Solve Drawing with Gemini", type="primary"):
    if byte_im:
        with st.spinner("🧠 Gemini is thinking..."):
            answers = analyze_image(byte_im)
        
        if answers:
            # **FIX 2: DISPLAY RESULTS IN A SEPARATE BOX**
            with st.container(border=True):
                st.success("✅ Solved!")
                for item in answers:
                    # Using LaTeX for better math formatting
                    st.write(f"**Expression:** `${item['expr']}$`")
                    st.write(f"**Result:** **`${item['result']}`**")
        else:
            # This message will show if parsing failed or Gemini returned nothing.
            st.warning("Could not get a valid result from Gemini. Please try again.")
    else:
        st.error("❌ Canvas is empty. Please draw a math problem first.")
