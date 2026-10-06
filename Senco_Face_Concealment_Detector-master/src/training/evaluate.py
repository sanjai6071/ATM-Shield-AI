import os
import argparse
from ultralytics import YOLO
from src.utils.logger import setup_logger

logger = setup_logger("FaceConcealmentEvaluator")

def evaluate_model(
    weights: str = "models/face_concealment_yolov8.pt",
    data_yaml: str = "config/concealment_data.yaml",
    imgsz: int = 640,
    batch: int = 16,
    device: str = "auto"
):
    """Evaluates fine-tuned model against validation set reporting mAP, precision, and recall."""
    if not os.path.exists(weights):
        logger.warning(f"Weights '{weights}' not found. Falling back to pretrained baseline 'yolov8n.pt'")
        weights = "yolov8n.pt"

    logger.info(f"Evaluating model weights: {weights} on dataset: {data_yaml}")
    model = YOLO(weights)
    
    metrics = model.val(
        data=data_yaml,
        imgsz=imgsz,
        batch=batch,
        device=device,
        plots=True
    )

    logger.info("================ EVALUATION METRICS ================")
    logger.info(f"mAP@50     : {metrics.box.map50:.4f}")
    logger.info(f"mAP@50-95  : {metrics.box.map:.4f}")
    logger.info(f"Precision  : {metrics.box.mp:.4f}")
    logger.info(f"Recall     : {metrics.box.mr:.4f}")
    logger.info("====================================================")
    return metrics

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Face Concealment Model")
    parser.add_argument("--weights", type=str, default="models/face_concealment_yolov8.pt", help="Model weights path")
    parser.add_argument("--data", type=str, default="config/concealment_data.yaml", help="Dataset yaml path")
    parser.add_argument("--imgsz", type=int, default=640, help="Evaluation image size")
    parser.add_argument("--device", type=str, default="auto", help="Device (cpu, 0, auto)")
    args = parser.parse_args()

    evaluate_model(
        weights=args.weights,
        data_yaml=args.data,
        imgsz=args.imgsz,
        device=args.device
    )
