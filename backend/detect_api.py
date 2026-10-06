import os
from ultralytics import YOLO

# =========================
# PROJECT BASE DIRECTORY
# =========================

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

# =========================
# LOAD ALL AI MODELS
# =========================

helmet_model = YOLO(
    os.path.join(
        BASE_DIR,
        "runs",
        "detect",
        "helmet_training",
        "fast_helmet",
        "weights",
        "best.pt"
    )
)

mask_model = YOLO(
    os.path.join(
        BASE_DIR,
        "models",
        "mask_detector.pt"
    )
)

object_model = YOLO(
    os.path.join(
        BASE_DIR,
        "yolov8n.pt"
    )
)

# =========================
# DETECTION
# =========================

def detect_objects(frame):

    detections = []

    # -------------------------
    # 1. HELMET
    # -------------------------

    helmet_results = helmet_model.predict(
        frame,
        device="cpu",
        verbose=False
    )

    for box in helmet_results[0].boxes:

        cls = int(box.cls[0])
        conf = float(box.conf[0])
        name = helmet_model.names[cls]

        x1, y1, x2, y2 = box.xyxy[0].tolist()

        detections.append({
            "object": name,
            "confidence": round(conf * 100, 2),
            "source": "helmet"
        })


    # -------------------------
    # 2. MASK
    # -------------------------

    mask_results = mask_model.predict(
    frame,
    device="cpu",
    conf=0.70,
    verbose=False
)

    for box in mask_results[0].boxes:

        cls = int(box.cls[0])
        conf = float(box.conf[0])
        name = mask_model.names[cls]

        detections.append({
            "object": name,
            "confidence": round(conf * 100, 2),
            "source": "mask"
        })


    # -------------------------
    # 3. YOLOv8 OBJECTS
    # -------------------------

    object_results = object_model.predict(
        frame,
        device="cpu",
        verbose=False
    )

    for box in object_results[0].boxes:

        cls = int(box.cls[0])
        conf = float(box.conf[0])
        name = object_model.names[cls]

        # Only ATM-relevant objects
        if name in ["person", "knife"]:

            detections.append({
                "object": name,
                "confidence": round(conf * 100, 2),
                "source": "yolo"
            })


    # =========================
    # AI FUSION
    # =========================

    threat_objects = []

    for item in detections:

        if item["object"] in [
            "knife",
            "Without Helmet",
            "mask"
        ]:
            threat_objects.append(item["object"])


    if "knife" in threat_objects:
        threat_level = "CRITICAL"
        threat_type = "WEAPON"

    elif "With Helmet" in threat_objects:
        threat_level = "HIGH"
        threat_type = "HELMET"

    elif "mask" in threat_objects:
        threat_level = "HIGH"
        threat_type = "FACE MASK"

    else:
        threat_level = "SAFE"
        threat_type = "NONE"


    # =========================
    # FINAL UNIFIED RESULT
    # =========================

    return {
        "detections": detections,
        "threat_level": threat_level,
        "threat_type": threat_type,
        "status": "THREAT DETECTED"
        if threat_level != "SAFE"
        else "SECURE"
    }