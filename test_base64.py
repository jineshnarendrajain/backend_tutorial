# test_base64.py
import base64
import requests
import os

path = r"C:\Users\ROG\Desktop\download.jpg"   # change if the image is elsewhere
if not os.path.exists(path):
    print("ERROR: file not found:", path)
    raise SystemExit(1)

with open(path, "rb") as f:
    b64 = base64.b64encode(f.read()).decode("utf-8")

url = "http://127.0.0.1:5000/analyze-image"
payload = {"image": b64, "prompt": "testing base64 JSON", "media_type": "image/jpeg"}

r = requests.post(url, json=payload, timeout=60)
print("STATUS:", r.status_code)
print("CONTENT-TYPE:", r.headers.get("content-type"))
print("BODY:", r.text)
