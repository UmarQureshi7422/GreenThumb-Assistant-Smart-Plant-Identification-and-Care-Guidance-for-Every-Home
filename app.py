import os
import json
import base64
import difflib
import requests
from flask import Flask, render_template, request
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("PLANT_ID_API_KEY")

app = Flask(__name__)
UPLOAD_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load plant care data
with open("plant_care_data.json") as f:
    plant_care = json.load(f)

# Identify using Plant.id API
def identify_with_plant_id(image_path):
    with open(image_path, "rb") as image_file:
        img_bytes = image_file.read()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")

    url = "https://api.plant.id/v2/identify"

    payload = {
        "images": [img_base64],
        "organs": ["leaf"],  # You can change to 'flower', 'fruit' etc.
        "modifiers": ["crops_fast", "similar_images"],
        "plant_language": "en",
        "plant_details": ["common_names", "url", "name_authority"]
    }

    headers = {
        "Content-Type": "application/json",
        "Api-Key": api_key
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        result = response.json()
        print("DEBUG API RESPONSE:", json.dumps(result, indent=2))
    except Exception as e:
        print("API ERROR:", e)
        return "Unknown", 0.0

    if "suggestions" in result and result["suggestions"]:
        top = result["suggestions"][0]
        name = top["plant_name"]
        score = top["probability"]
        return name, score

    return "Unknown", 0.0

# Main route
@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        file = request.files.get("image")
        if file:
            path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(path)

            # Identify the plant
            plant, confidence = identify_with_plant_id(path)

            # Match with care data
            match = difflib.get_close_matches(plant, plant_care.keys(), n=1, cutoff=0.5)
            tips = plant_care.get(match[0], {
                "water": "No data available.",
                "sunlight": "No data available."
            }) if match else {
                "water": "No data available.",
                "sunlight": "No data available."
            }

            result = {
                "name": plant,
                "confidence": f"{confidence * 100:.2f}%",
                "image": path,
                "tips": tips
            }

    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)

