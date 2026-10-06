import cv2
from ultralytics import YOLO

# Load YOLO model (loads only once)
model = YOLO("yolov8n.pt")

# Open camera
camera = cv2.VideoCapture(0)

def get_frame():

    success, frame = camera.read()

    if not success:
        return None

    # Run YOLO detection
    results = model.predict(frame, device="cpu", verbose=False)

    # Draw bounding boxes
    frame = results[0].plot()

    return frame