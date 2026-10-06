import os
import argparse
from ultralytics import YOLO
from src.utils.logger import setup_logger

logger = setup_logger("FaceConcealmentExporter")

def export_model(
    weights: str = "models/face_concealment_yolov8.pt",
    format_type: str = "onnx",
    imgsz: int = 640,
    half: bool = True
):
    """Exports fine-tuned YOLO model to optimized deployment formats."""
    if not os.path.exists(weights):
        logger.warning(f"Weights '{weights}' not found. Using 'yolov8n.pt' for export...")
        weights = "yolov8n.pt"

    logger.info(f"Exporting model {weights} to format: {format_type} (half={half})...")
    model = YOLO(weights)
    
    exported_path = model.export(
        format=format_type,
        imgsz=imgsz,
        half=half,
        dynamic=True,
        simplify=True
    )
    
    logger.info(f"Model exported successfully! File location: {exported_path}")
    return exported_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Face Concealment Model")
    parser.add_argument("--weights", type=str, default="models/face_concealment_yolov8.pt", help="Model weights path")
    parser.add_argument("--format", type=str, default="onnx", choices=["onnx", "engine", "openvino", "torchscript", "tflite"], help="Export format")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    parser.add_argument("--half", action="store_true", help="Enable FP16 half precision")
    args = parser.parse_args()

    export_model(
        weights=args.weights,
        format_type=args.format,
        imgsz=args.imgsz,
        half=args.half
    )
