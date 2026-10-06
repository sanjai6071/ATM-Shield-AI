from ultralytics import YOLO
import cv2
from collections import deque

model = YOLO(
    r"D:\ATM-Shield-AI\runs\detect\helmet_training\fast_helmet\weights\best.pt"
)

cap = cv2.VideoCapture(0)

# Keep the last 10 predictions
history = deque(maxlen=10)

print("ATM Shield AI - Stable Helmet Detection")
print("Press Q to quit")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Camera error")
        break

    results = model(frame, conf=0.20)

    detected = None
    best_conf = 0

    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            class_name = model.names[class_id]

            if confidence > best_conf:
                best_conf = confidence
                detected = class_name

    if detected:
        history.append(detected)

    # Determine the most common result from recent frames
    if len(history) >= 5:
        with_count = history.count("With Helmet")
        without_count = history.count("Without Helmet")

        if with_count > without_count:
            stable_result = "WITH HELMET"
        else:
            stable_result = "WITHOUT HELMET"

        print(
            f"Stable: {stable_result} | "
            f"With={with_count} | Without={without_count}"
        )

    annotated_frame = results[0].plot()

    cv2.imshow(
        "ATM Shield AI - Stable Helmet Detection",
        annotated_frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

print("Camera test stopped")