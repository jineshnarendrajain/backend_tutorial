from flask import Flask, jsonify, request
from dotenv import load_dotenv
import os
import base64
import requests

load_dotenv()


def create_app(config_object=None):
    app = Flask(__name__)

    # Basic configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev_secret"),
    )

    # Simple routes
    @app.route("/")
    def index():
        return jsonify({"message": "Hello from Flask boilerplate!"})

    @app.route("/test")
    def test():
        # get  text prompt from request
        # send prompt to chatgpt api
        # return response
        return jsonify({"status": "ok"})

    @app.route("/analyze-image", methods=["POST"])
    def analyze_image():
        """
        Accepts an image (base64 or URL) and returns an explanation from OpenAI Vision API.
        Expected JSON body:
        {
            "image": "base64_encoded_image_or_url",
            "prompt": "optional custom prompt (defaults to image explanation)",
            "media_type": "image/jpeg"  # optional, defaults to jpeg
        }
        """
        try:
            data = request.get_json(silent=True)
            print("Received data:", data)
            if not data or "image" not in data:
                return jsonify({"error": "Missing 'image' field"}), 400

            image_data = data.get("image")
            custom_prompt = data.get(
                "prompt",
                "Explain what you see in this image in detail."
            )
            media_type = data.get("media_type", "image/jpeg")
            openai_api_key = os.environ.get("OPENAI_API_KEY")

            if not openai_api_key:
                return jsonify({"error": "OPENAI_API_KEY not configured"}), 500

            # Prepare image content in CURRENT OpenAI chat format
            if isinstance(image_data, str) and image_data.startswith("http"):
                # URL-based image
                image_content = {
                    "type": "image_url",
                    "image_url": {"url": image_data}
                }
            else:
                # Assume base64-encoded image (no data: prefix)
                image_content = {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{media_type};base64,{image_data}"
                    }
                }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openai_api_key}"
            }

            payload = {
                "model": "gpt-4o-mini",   # make sure ALL old gpt-4-vision refs are gone
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": custom_prompt
                            },
                            image_content
                        ]
                    }
                ],
                "max_tokens": 512
            }
            print("DEBUG payload model:", payload["model"])
            print("DEBUG payload:", payload)    

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code != 200:
                return jsonify({
                    "error": f"OpenAI API error: {response.status_code}",
                    "details": response.text
                }), 500

            result = response.json()
            choices = result.get("choices")
            if not choices or not isinstance(choices, list) or not choices[0].get("message"):
                return jsonify({
                    "error": "Unexpected response structure from OpenAI API",
                    "details": result
                }), 500

            explanation = choices[0]["message"].get("content", "")

            return jsonify({
                "explanation": explanation,
                "model": result.get("model"),
                "usage": result.get("usage")
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 500


    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/echo", methods=["POST"])
    def echo():
        """Echo endpoint: returns the posted JSON payload."""
        data = request.get_json(silent=True)
        return jsonify({"received": data}), 200

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("FLASK_RUN_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1" or os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
