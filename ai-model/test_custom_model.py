from ultralytics import YOLO

model = YOLO("yolov8n.pt")

print("Model loaded successfully")
print(model.names)