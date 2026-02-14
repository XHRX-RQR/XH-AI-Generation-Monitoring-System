"""
AI Generated Content Detection System - Backend Server

Flask-based API server with OpenAI-compatible endpoint support.
"""

import os
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
from detector import AIDetector, DetectionError

app = Flask(__name__, static_folder="static", template_folder="templates")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/detect", methods=["POST"])
def detect():
    """Run AI content detection on submitted text."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    text = data.get("text", "").strip()
    api_base = data.get("api_base", "").strip()
    api_key = data.get("api_key", "").strip()
    model = data.get("model", "").strip()
    temperature = data.get("temperature", 0.1)

    # Validation
    errors = []
    if not text:
        errors.append("Text content is required.")
    if not api_base:
        errors.append("API Base URL is required.")
    if not api_key:
        errors.append("API Key is required.")
    if not model:
        errors.append("Model name is required.")
    if errors:
        return jsonify({"error": " ".join(errors)}), 400

    try:
        detector = AIDetector(
            api_base=api_base,
            api_key=api_key,
            model=model,
            temperature=float(temperature),
        )
        result = detector.detect(text)
        return jsonify({"success": True, "result": result})
    except DetectionError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": f"Internal error: {str(e)}"}), 500


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8765))
    app.run(host="0.0.0.0", port=port, debug=True)
