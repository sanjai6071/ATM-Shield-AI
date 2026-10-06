from ultralytics import YOLO
import cv2

# Load YOUR trained helmet detection model
model = YOLO(r"D:\ATM-Shield-AI\runs\detect\helmet_training\fast_helmet\weights\best.pt")

# Open laptop camera
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()

    if not ret:
        print("Camera not available")
        break

    # Run your custom helmet model
    results = model.predict(
        frame,
        conf=0.25,
        device="cpu",
        verbose=False
    )

    # Draw detections
    annotated_frame = results[0].plot()

    cv2.imshow("ATM Shield AI - Helmet Detection", annotated_frame)

    # Press Q to close
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()