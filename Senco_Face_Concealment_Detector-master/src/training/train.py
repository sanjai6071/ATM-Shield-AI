import os
import argparse
import yaml
from ultralytics import YOLO
from src.utils.logger import setup_logger

logger = setup_logger("FaceConcealmentTrainer")

def train_model(
    data_yaml: str = "config/concealment_data.yaml",
    model_name: str = "yolov8n.pt",
    epochs: int = 50,
    imgsz: int = 640,
    batch: int = 16,
    device: str = "auto",
    project: str = "runs/train",
    name: str = "concealment_model"
):
    """Fine-tunes YOLO model for Face Concealment & Masking Detection."""
    if not os.path.exists(data_yaml):
        raise FileNotFoundError(f"Data config '{data_yaml}' not found.")

    logger.info(f"Starting training run: Model={model_name}, Epochs={epochs}, ImgSz={imgsz}, Batch={batch}")
    
    # Initialize YOLO backbone
    model = YOLO(model_name)

    # Train with domain-specific augmentations for face surveillance
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        project=project,
        name=name,
        mosaic=1.0,         # Heavy mosaic for small occluded face targets
        mixup=0.15,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=10.0,
        translate=0.1,
        scale=0.5,
        fliplr=0.5,
        save=True,
        plots=True
    )

    best_weights = os.path.join(project, name, "weights", "best.pt")
    logger.info(f"Training completed successfully! Best weights saved to: {best_weights}")
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Face Concealment & Masking Detection Model")
    parser.add_argument("--data", type=str, default="config/concealment_data.yaml", help="Path to data.yaml")
    parser.add_argument("--model", type=str, default="yolov8n.pt", help="Pretrained model weights / backbone")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--device", type=str, default="auto", help="Device (cpu, 0, auto)")
    parser.add_argument("--name", type=str, default="senco_concealment_v1", help="Experiment name")
    args = parser.parse_args()

    train_model(
        data_yaml=args.data,
        model_name=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        name=args.name
    )
