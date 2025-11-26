import os
import io
import base64
import logging
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from dotenv import load_dotenv
from PIL import Image
import requests

load_dotenv()
logging.basicConfig(level=logging.INFO)


# ---------- IMAGE RESIZE FUNCTION ----------
def resize_image(raw_bytes, max_width=1024, quality=75):
    """Resize image to reduce OpenAI tokens."""
    try:
        img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        w, h = img.size

        # If already small, return as-is
        if w <= max_width:
            out = io.BytesIO()
            img.save(out, format="JPEG", quality=quality)
            return out.getvalue()

        scale = max_width / w
        new_size = (int(w * scale), int(h * scale))

        img = img.resize(new_size, Image.LANCZOS)

        out = io.BytesIO()
        img.save(out, format="JPEG", quality=quality)
        return out.getvalue()

    except Exception as e:
        logging.exception("Error resizing image")
        raise e


# ---------- CREATE FLASK APP ----------
def create_app():
    app = Flask(__name__)

    # CORS for all routes (works with ngrok + Figma)
    CORS(app, resources={r"/*": {"origins": "*"}})

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type,Authorization,X-Requested-With,Accept"
        )
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        response.headers["Access-Control-Expose-Headers"] = "Content-Type,Authorization"
        return response

    @app.route("/<path:_any>", methods=["OPTIONS"])
    @app.route("/", methods=["OPTIONS"])
    def options_preflight(_any=None):
        resp = make_response("", 200)
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = (
            "Content-Type,Authorization,X-Requested-With,Accept"
        )
        resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        return resp

    @app.route("/")
    def index():
        return jsonify({"message": "Flask server is running"}), 200

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    # ---------- MAIN ENDPOINT ----------
    @app.route("/analyze-image", methods=["POST"])
    def analyze_image():
        logging.info("=== HIT /analyze-image ===")

        try:
            openai_key = os.environ.get("OPENAI_API_KEY")
            if not openai_key:
                return jsonify({"error": "OPENAI_API_KEY not configured"}), 500

            # -------- CASE 1: multipart upload --------
            if "image" in request.files:
                file = request.files["image"]
                prompt = request.form.get("prompt", "Explain what you see in this image.")
                raw = file.read()
                logging.info(f"Received multipart image: {file.filename} ({len(raw)} bytes)")

            # -------- CASE 2: JSON base64 upload --------
            else:
                data = request.get_json(silent=True) or {}
                if "image" not in data:
                    return jsonify({"error": "Missing 'image'"}), 400

                b64 = data["image"]
                prompt = data.get("prompt", "Explain what you see in this image.")
                raw = base64.b64decode(b64)
                logging.info(f"Received JSON base64 image ({len(raw)} bytes)")

            # -------- RESIZE IMAGE (MASSIVE TOKEN REDUCTION) --------
            raw_resized = resize_image(raw, max_width=1024, quality=75)
            logging.info(f"Resized image size: {len(raw_resized)} bytes")

            # Convert to base64 for OpenAI
            final_b64 = base64.b64encode(raw_resized).decode("utf-8")
            data_url = f"data:image/jpeg;base64,{final_b64}"

            # -------- BUILD OPENAI API PAYLOAD --------
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }
                ],
                "max_tokens": 512,
            }

            # -------- SEND TO OPENAI --------
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json",
                },
                timeout=60,
            )

            if resp.status_code != 200:
                logging.error(f"OpenAI error: {resp.text[:200]}")
                return jsonify({"error": "OpenAI API error", "details": resp.text}), 500

            result = resp.json()
            explanation = (
                result.get("choices", [{}])[0].get("message", {}).get("content", "")
            )

            return jsonify(
                {
                    "explanation": explanation,
                    "model": result.get("model"),
                    "usage": result.get("usage"),
                }
            )

        except Exception as e:
            logging.exception("ERROR in /analyze-image")
            return jsonify({"error": str(e)}), 500

    return app


# ---------- MAIN ----------
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
