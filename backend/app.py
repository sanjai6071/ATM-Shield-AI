from flask import Flask, render_template, Response
from camera import get_frame
from detect_api import detect_objects
from flask import request, jsonify
import numpy as np
import cv2

import os
import base64

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

import sys
sys.path.append(os.path.join(BASE_DIR, "database"))

from db import add_incident, get_incidents

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

@app.route("/")
def dashboard():
    return render_template("dashboard.html")
@app.route("/v2")
def dashboard_v2():
    return render_template("dashboard_v2.html")

@app.route("/detect", methods=["POST"])
def detect():

    file = request.files["frame"]

    file_bytes = np.frombuffer(file.read(), np.uint8)

    frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    detections = detect_objects(frame)

    return jsonify(detections)



# =========================================
# SAVE EVIDENCE SCREENSHOT
# =========================================

@app.route("/save_evidence", methods=["POST"])
def save_evidence():

    data = request.json

    image_data = data["image"]

    image_data = image_data.split(",")[1]

    image_bytes = base64.b64decode(image_data)

    screenshot_dir = os.path.join(BASE_DIR, "screenshots")

    os.makedirs(screenshot_dir, exist_ok=True)

    filename = "ATM_Evidence_" + str(int(__import__("time").time())) + ".png"

    filepath = os.path.join(screenshot_dir, filename)

    with open(filepath, "wb") as file:
        file.write(image_bytes)

    return jsonify({
        "success": True,
        "filename": filename
    })

@app.route("/test_incident", methods=["GET"])
def test_incident():

    add_incident(
        "knife",
        35.0,
        "HIGH",
        95,
        "ATM LOCKED",
        "test_evidence.png"
    )

    return jsonify({
        "success": True,
        "message": "Test incident stored"
    })

# =========================================
# SAVE SECURITY INCIDENT
# =========================================

@app.route("/save_incident", methods=["POST"])
def save_incident():

    data = request.get_json()

    add_incident(
        data["threat_type"],
        data["confidence"],
        data["threat_level"],
        data["threat_score"],
        data["status"],
        data["evidence_file"]
    )

    return jsonify({
        "success": True,
        "message": "Incident saved successfully"
    })

# =========================================
# GET INCIDENT HISTORY
# =========================================

@app.route("/incidents", methods=["GET"])
def incidents():

    data = get_incidents()

    return jsonify({
        "success": True,
        "incidents": data
    })

@app.route("/video_feed")
def video_feed():

    def generate():

        while True:

            frame = get_frame()

            if frame is None:
                continue

            _, buffer = cv2.imencode(".jpg", frame)

            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' +
                   frame + b'\r\n')

    return Response(
        generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    app.run(debug=True)

    

if __name__ == "__main__":
    app.run(debug=True)