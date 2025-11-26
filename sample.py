import requests
import base64
import os

# Use local image from test_image_data folder
image_path = r"test_image_data\download.jpg"

with open(image_path, "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode("utf-8")

url = "http://127.0.0.1:5000/analyze-image"

payload = {
    "image": image_b64,
    "media_type": "image/jpeg",
    "prompt": "Describe this building and its architectural features, materials, and spatial layout."
}

res = requests.post(url, json=payload)
print("Status:", res.status_code)
print("Response:")
print(res.json())

