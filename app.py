from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import os
import json

# Initialize Flask app
app = Flask(__name__)

# Configure Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel("gemini-1.5-flash")
else:
    gemini_model = None

# Load trained model
# IMPORTANT: Make sure the model file is in the same directory or provide the correct path.
model = load_model("cultural_site_model.h5")

# Load site info from JSON
with open("site_info.json", "r", encoding="utf-8") as f:
    site_info = json.load(f)

# Create class names list
class_names = list(site_info.keys())

# --- NEW: Define a confidence threshold ---
# You can adjust this value (0.0 to 1.0) based on your model's performance.
# 0.80 means the model must be at least 80% confident.
CONFIDENCE_THRESHOLD = 0.80

# Home route
@app.route("/")
def home():
    return render_template("index.html")

# Predict route (handles image upload)
@app.route("/predict", methods=["POST"])
def predict():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"})
    
    file = request.files['file']
    # Ensure the 'static' folder exists for temporary files
    if not os.path.exists('static'):
        os.makedirs('static')
    img_path = os.path.join("static", "temp.jpg")
    file.save(img_path)
    
    # Preprocess image
    img = image.load_img(img_path, target_size=(224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x /= 255.0
    
    # Predict
    predictions = model.predict(x)
    
    # --- MODIFIED LOGIC ---
    # Get the confidence score of the top prediction
    confidence = np.max(predictions)
    
    # Check if the confidence is above our threshold
    if confidence > CONFIDENCE_THRESHOLD:
        # If confident, get the class name
        predicted_index = np.argmax(predictions)
        pred_class = class_names[predicted_index]
        
        # Delete temp image after use
        os.remove(img_path)
        
        # Redirect to AR info page
        return render_template("ar.html", site_name=pred_class)
    else:
        # If not confident, it's an unknown site
        # Delete temp image after use
        os.remove(img_path)
        
        # Return a page indicating the site was not found
        return render_template("not_found.html")

def generate_section_with_gemini(prompt: str) -> str:
    if not gemini_model:
        return ""
    try:
        resp = gemini_model.generate_content(prompt)
        return (resp.text or "").strip()
    except Exception:
        return ""

# Route to serve site info (Gemini-augmented)
@app.route("/site/<site_name>")
def site_details(site_name):
    base = site_info.get(site_name, {})

    # Build prompts
    history_prompt = f"Provide a concise, engaging historical background for {site_name} in 120-180 words. Avoid markdown headings."
    overview_prompt = f"Provide a visitor-friendly overview of {site_name} in 80-120 words, covering where it is and why it matters."
    facts_prompt = f"List 5-7 interesting facts about {site_name}. Return as a semicolon-separated list with no numbering."

    # Generate with Gemini (fallback to JSON when empty)
    history_ai = generate_section_with_gemini(history_prompt)
    overview_ai = generate_section_with_gemini(overview_prompt)
    facts_ai = generate_section_with_gemini(facts_prompt)

    result = {
        "history": history_ai or base.get("history", ""),
        "overview": overview_ai or base.get("overview", ""),
        "facts": facts_ai or base.get("facts", ""),
        "video": base.get("video", ""),
    }

    if any(result.values()):
        return jsonify(result)
    return jsonify({"error": "Site info not found"})

# Anchored AR route (marker-based using AR.js/A-Frame)
@app.route("/ar/<site_name>/anchor")
def ar_anchor(site_name):
    return render_template("ar_anchor.html", site_name=site_name)

# Run the app
if __name__ == "__main__":
    app.run(debug=True)